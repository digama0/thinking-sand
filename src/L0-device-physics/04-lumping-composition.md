# L0/04 — Lumping and composition

## Background

Circuit theory is a *claim*, not a given. The field picture of [00](00-field-problem.md) knows nothing of "components" — there is one connected electromagnetic system spanning the die, every point coupled to every other. The circuit picture — discrete components with terminals, wires that are equipotential nodes, Kirchhoff's two laws — is an abstraction *of* that field, and the passage between them is called **lumping**: choosing surfaces at which to cut the continuum into pieces, assigning each piece a terminal behaviour, and asserting that the pieces' behaviours compose through the connection graph to predict the whole. Every engineer uses this abstraction from the first week of training; introductory texts axiomatise it (the honourable exception, Agarwal & Lang, states it as the "lumped matter discipline" — explicit assumptions before use); and this chapter has to *derive* it, error bounds included, because L0/03's per-cell enclosures and L1's per-net enclosures are worthless until a theorem says small pieces compose.

Two failure modes of naive composition organise the chapter. The first is the **interval dependency problem**, a classic trap of interval arithmetic: if the same underlying uncertainty (say, the die's process corner) enters an interval computation independently at every use site, the computation admits impossible combinations — this gate slow, its neighbour fast, from the same wafer spot — and the composed bound explodes into uselessness while remaining perfectly sound. The remedies (affine arithmetic, Taylor models, zonotopes — representations that carry *which* uncertainty each interval came from, so correlated uses cancel) exist off the shelf; the chapter's task is to identify where they are needed.

The second is accumulation: even with dependencies tracked, why doesn't uncertainty *compound* along a twenty-gate chain until the enclosure covers everything? The rescue is the restoration property of [05](05-digital-abstraction.md) — each gate's gain pulls its output back toward the rails, shrinking incoming analog uncertainty rather than passing it on — and the chapter's contribution is recognising this as a known theorem shape from control theory: a **small-gain argument**. That field studies feedback systems where each component amplifies disturbances by some factor ("gain"); when the gains around every loop multiply to less than one, disturbances die out instead of building up, and stability of the whole network follows from the components' gains alone. Stated in those terms, per-stage restoration composes to chip-scale stability by citation rather than by invention — one of several places where this project's job is to recognise which existing mathematics a piece of engineering folklore has been, unknowingly, all along.

## Statement

The abstract argument that licenses gluing. Given per-cell terminal enclosures ([03](03-cell-enclosures.md)) and per-net RC enclosures (L1), conclude that the **true physical field lies within the enclosure the lumped circuit model predicts.**

This is the document that makes L0 and L1 add up to something, and it is the one with the least existing prior art.

## The four steps of lumping

**1. Terminals.** Choose surfaces where V and I are measured — for a cell, its pins. Definitional, but the choice must be consistent between L0/03's characterisation and L1's extraction, or the enclosures compose to nothing. And a cut is not licensed everywhere: it is legitimate only where the boundary is **restoring and near-unidirectional** — a MOS gate input is capacitive, with [Miller](../bibliography.md#miller-1919) feedthrough (C_gd back-injection into the driving net) as the bounded exception; a drain/source terminal is neither. Equivalently, components must be unions of **channel-connected components** ([Bryant](../bibliography.md#bryant-1984)'s partition — the one switch-level simulators compute), so that every bistable feedback loop is internal to some component. Cut inside a latch and no side condition saves the contract.

**2. Conductors are equipotential.** Each net is assigned one potential. Error is the IR drop within the conductor, bounded by `R·I`. Negligible for signal nets; *not* negligible for power, which is why the supply grid gets its own treatment and why decaps exist.

This is the **same condition** as L1's screening hypothesis, used for a different purpose. Worth noticing: the equipotential assumption is load-bearing twice.

**3. The capacitance matrix exists.** For N conductors in a linear electrostatic problem the map from potentials to charges is linear, `Q = C V`, and `C` exists precisely *because* the solution operator is linear and bounded — i.e. because of Lax–Milgram in [00](00-field-problem.md). The dependency is direct: **no well-posedness, no capacitance matrix, no RC enclosures, nothing above.**

**4. Kirchhoff's laws are theorems, not axioms.** KCL is `∇·J = 0` integrated over a surface enclosing a node; KVL is `∇×E = 0` integrated around a loop. Both are exact in the quasi-static limit and carry [01](01-quasistatic-reduction.md)'s `O((L/λ)²)` error otherwise. Circuit theory is normally introduced axiomatically; here it must be derived, and the derivation is where the field-to-circuit error enters. The cleanest existing formulation is [Bossavit](../bibliography.md#bossavit-1998)'s: on a discrete de Rham complex (Whitney forms), KCL and KVL are the *exactness of the complex* — the network is a coarse cochain model of the field, and the two Kirchhoff laws hold exactly at the discrete level while all approximation error lives in the constitutive (Hodge) map. That separation — topology exact, metric approximate — is precisely the structure a formalisation should copy.

## The composition theorem

The actual content. Given component enclosures and a topology, bound the network's solution.

```
∀ cells c:  terminal_behaviour(c) ∈ Encl_c        [L0/03]
∀ nets n:   RC(n) ∈ Encl_n                        [L1]
            topology = the netlist                [L3]
──────────────────────────────────────────────────────────
            circuit_behaviour ∈ compose(Encl_c, Encl_n)
```

**This is where it gets hard**, because you are composing enclosures through a nonlinear DAE, and naive interval propagation explodes: the same uncertainty is counted independently at every use site, admitting physically impossible combinations (this cell slow, its neighbour fast, the first one slow again). Sound, but potentially so pessimistic as to be useless. This is the interval *dependency problem*, and the standard remedies — affine arithmetic ([de Figueiredo & Stolfi](../bibliography.md#de-figueiredo-stolfi-2004)), Taylor models ([Makino & Berz](../bibliography.md#makino-berz-2003)), zonotopes ([Girard](../bibliography.md#girard-2005); [Althoff](../bibliography.md#althoff-cora-2015)'s [CORA](../bibliography.md#althoff-cora-2015)) — exist precisely to track which uncertainties are the same variable.

Two structural properties rescue it, and they are the real content of this document:

**Monotonicity ⟹ corners suffice.** If the network response is monotone in the uncertain parameters, the extremes occur at parameter *corners*, and you evaluate finitely many consistent assignments instead of propagating intervals. **This is exactly why corner-based STA works**, and it is universally assumed and never proved.

It is also **not universally true**: `cell_fall` is non-monotone in input slew at two grid points of the simplest cell in the library. So the theorem needed is not "the response is monotone" but a characterisation of *where* it is, plus a fallback where it isn't.

**Restoration ⟹ no accumulation across stages.** [05](05-digital-abstraction.md)'s contraction property means a chain of gates does not compound uncertainty — each stage pulls back toward a rail. So composition *along a combinational path* is well-behaved even though each stage carries an enclosure. Without this, a 20-deep logic cone would have a useless bound.

This has a name in control theory, and the theorem should be stated in its terms rather than reinvented: it is a **small-gain / contraction argument**. Each stage viewed as an input-to-state-stable (ISS) map with gain < 1 in the disturbance channel composes to a network-level invariant by the ISS small-gain theorem ([Jiang–Teel–Praly](../bibliography.md#jiang-teel-praly-1994) for two systems; [Dashkovskiy–Rüffer–Wirth](../bibliography.md#dashkovskiy-ruffer-wirth-2007) for arbitrary interconnections), and [Lohmiller–Slotine](../bibliography.md#lohmiller-slotine-1998) contraction analysis is the differential version. The lumping error from this document then enters not as a separate apology but as one more bounded disturbance input, which the same machinery absorbs.

## The factorisation this licenses

The practical payoff, and the reason the whole stack is computable:

> **Confine the nonlinear DAE solve to inside a cell. Compose at chip scale using a linear network plus a DAG traversal.**

SPICE solves the nonlinear DAE directly and cannot scale to a chip. The flow instead: characterises cells once by DAE solve (L0/03), treats interconnect as linear (L1), and composes by forward traversal (L2). L0/04 is what says that factorisation is *sound* and what the error term is.

Note the consequence for L2: its forward traversal — arrival time and slew propagating through a DAG — is not merely an algorithm, it is the chip-scale instance of this composition theorem. The two documents are describing the same thing at different granularity.

## What composition is not

"Plug together" is combinatorics *plus per-edge arithmetic*: each connection discharges finitely many side conditions — output load within the driver contract's domain (`max_capacitance`), input slew within the receiver's (`max_transition`), coupling within the local disturbance budget. Finite and decidable, but not vacuous: the shipped design currently fails exactly these checks (finding F2). The right formalism for the per-component object is an **assume-guarantee contract** ([Benveniste et al.](../bibliography.md#benveniste-2018)): guaranteed output trajectory classes given input trajectory classes, load, and disturbance budget, with an explicit domain of validity — which is precisely what an interval-valued Liberty arc is.

And three quantities thread through every component without factoring through pins: the **supply rails** (equipotential fails exactly there — IR drop is a global property of the grid), the **clock tree**, and **temperature** (a global field sourced by aggregate activity). Each needs its own aggregate argument before any per-component contract's assumptions hold. They are the non-combinatorial residue of composition, and pretending they are edges in the graph is how power-integrity bugs escape verification.

## Open problems

1. **The composition theorem itself.** As far as I can tell nobody has stated "lumped circuit model is sound with respect to the field problem, with this error bound" in a form usable as a verification hypothesis. Everyone assumes it.
2. **Characterise where monotonicity holds**, given that production data violates it. This is the hypothesis under corner-based methodology across the entire industry.
3. Interval dependency: correlation-aware propagation, distinguishing global (process corner) from local (OCV) from shared-path (CPPR) uncertainty. Shared with L2.
4. The equipotential error bound for power nets, where it is *not* negligible.

## First experiments

- State the composition theorem formally with explicit error terms, before attempting a proof. The statement alone would be a contribution; several people would recognise it as the thing they have been assuming.
- Test monotonicity empirically across the shipped Liberty library: for all cells, all arcs, all corners, check monotonicity in each argument. We found violations in `inv_1`; a survey would show whether they are rare pathologies or systematic. **Cheap, mechanical, and directly informs how much of corner methodology is sound.**
- Build a small end-to-end instance: two inverters and a wire, field solve vs lumped model, and check the lumped enclosure actually contains the field solution.

## Effort

Months for the statement and the monotonicity survey; as the other dominant item (with [03](03-cell-enclosures.md)), its depth sets the layer total.

## Reading

[Haus & Melcher](../bibliography.md#haus-melcher-1989) for the field-to-circuit derivation of Kirchhoff. [Bossavit](../bibliography.md#bossavit-1998), *Computational Electromagnetism* — Whitney forms and network models as discrete Maxwell; [Tonti](../bibliography.md#tonti-2013) on the classification diagrams behind it. [Bryant](../bibliography.md#bryant-1984) (1984) for channel-connected components. [Benveniste et al.](../bibliography.md#benveniste-2018), *Contracts for System Design* (Foundations and Trends in EDA, 2018) — the assume-guarantee formalism the per-component contracts instantiate. [Jiang–Teel–Praly](../bibliography.md#jiang-teel-praly-1994) and [Dashkovskiy–Rüffer–Wirth](../bibliography.md#dashkovskiy-ruffer-wirth-2007) on ISS small-gain; [Lohmiller & Slotine](../bibliography.md#lohmiller-slotine-1998), "On contraction analysis for non-linear systems" (Automatica 1998). [de Figueiredo & Stolfi](../bibliography.md#de-figueiredo-stolfi-2004) (affine arithmetic), [Makino & Berz](../bibliography.md#makino-berz-2003) (Taylor models), [Girard](../bibliography.md#girard-2005) and [Althoff](../bibliography.md#althoff-cora-2015) (zonotopes, [CORA](../bibliography.md#althoff-cora-2015)) for the dependency problem. Note that circuit-theory texts almost universally *start* from Kirchhoff, so the derivation direction needed here is unusual.
