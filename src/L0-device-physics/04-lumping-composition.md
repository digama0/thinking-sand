# L0/04 — Lumping and composition

## Statement

The abstract argument that licenses gluing. Given per-cell terminal enclosures ([03](03-cell-enclosures.md)) and per-net RC enclosures (L1), conclude that the **true physical field lies within the enclosure the lumped circuit model predicts.**

This is the document that makes L0 and L1 add up to something, and it is the one with the least existing prior art.

## The four steps of lumping

**1. Terminals.** Choose surfaces where V and I are measured — for a cell, its pins. Definitional, but the choice must be consistent between L0/03's characterisation and L1's extraction, or the enclosures compose to nothing. And a cut is not licensed everywhere: it is legitimate only where the boundary is **restoring and near-unidirectional** — a MOS gate input is capacitive, with [Miller](../BIBLIOGRAPHY.md#miller-1919) feedthrough (C_gd back-injection into the driving net) as the bounded exception; a drain/source terminal is neither. Equivalently, components must be unions of **channel-connected components** ([Bryant](../BIBLIOGRAPHY.md#bryant-1984)'s partition — the one switch-level simulators compute), so that every bistable feedback loop is internal to some component. Cut inside a latch and no side condition saves the contract.

**2. Conductors are equipotential.** Each net is assigned one potential. Error is the IR drop within the conductor, bounded by `R·I`. Negligible for signal nets; *not* negligible for power, which is why the supply grid gets its own treatment and why decaps exist.

This is the **same condition** as L1's screening hypothesis, used for a different purpose. Worth noticing: the equipotential assumption is load-bearing twice.

**3. The capacitance matrix exists.** For N conductors in a linear electrostatic problem the map from potentials to charges is linear, `Q = C V`, and `C` exists precisely *because* the solution operator is linear and bounded — i.e. because of Lax–Milgram in [00](00-field-problem.md). The dependency is direct: **no well-posedness, no capacitance matrix, no RC enclosures, nothing above.**

**4. Kirchhoff's laws are theorems, not axioms.** KCL is `∇·J = 0` integrated over a surface enclosing a node; KVL is `∇×E = 0` integrated around a loop. Both are exact in the quasi-static limit and carry [01](01-quasistatic-reduction.md)'s `O((L/λ)²)` error otherwise. Circuit theory is normally introduced axiomatically; here it must be derived, and the derivation is where the field-to-circuit error enters. The cleanest existing formulation is [Bossavit](../BIBLIOGRAPHY.md#bossavit-1998)'s: on a discrete de Rham complex (Whitney forms), KCL and KVL are the *exactness of the complex* — the network is a coarse cochain model of the field, and the two Kirchhoff laws hold exactly at the discrete level while all approximation error lives in the constitutive (Hodge) map. That separation — topology exact, metric approximate — is precisely the structure a formalisation should copy.

## The composition theorem

The actual content. Given component enclosures and a topology, bound the network's solution.

```
∀ cells c:  terminal_behaviour(c) ∈ Encl_c        [L0/03]
∀ nets n:   RC(n) ∈ Encl_n                        [L1]
            topology = the netlist                [L3]
──────────────────────────────────────────────────────────
            circuit_behaviour ∈ compose(Encl_c, Encl_n)
```

**This is where it gets hard**, because you are composing enclosures through a nonlinear DAE, and naive interval propagation explodes: the same uncertainty is counted independently at every use site, admitting physically impossible combinations (this cell slow, its neighbour fast, the first one slow again). Sound, but potentially so pessimistic as to be useless. This is the interval *dependency problem*, and the standard remedies — affine arithmetic ([de Figueiredo & Stolfi](../BIBLIOGRAPHY.md#de-figueiredo-stolfi-2004)), Taylor models ([Makino & Berz](../BIBLIOGRAPHY.md#makino-berz-2003)), zonotopes ([Girard](../BIBLIOGRAPHY.md#girard-2005); [Althoff](../BIBLIOGRAPHY.md#althoff-cora-2015)'s [CORA](../BIBLIOGRAPHY.md#althoff-cora-2015)) — exist precisely to track which uncertainties are the same variable.

Two structural properties rescue it, and they are the real content of this document:

**Monotonicity ⟹ corners suffice.** If the network response is monotone in the uncertain parameters, the extremes occur at parameter *corners*, and you evaluate finitely many consistent assignments instead of propagating intervals. **This is exactly why corner-based STA works**, and it is universally assumed and never proved.

It is also **not universally true**: `cell_fall` is non-monotone in input slew at two grid points of the simplest cell in the library. So the theorem needed is not "the response is monotone" but a characterisation of *where* it is, plus a fallback where it isn't.

**Restoration ⟹ no accumulation across stages.** [05](05-digital-abstraction.md)'s contraction property means a chain of gates does not compound uncertainty — each stage pulls back toward a rail. So composition *along a combinational path* is well-behaved even though each stage carries an enclosure. Without this, a 20-deep logic cone would have a useless bound.

This has a name in control theory, and the theorem should be stated in its terms rather than reinvented: it is a **small-gain / contraction argument**. Each stage viewed as an input-to-state-stable (ISS) map with gain < 1 in the disturbance channel composes to a network-level invariant by the ISS small-gain theorem ([Jiang–Teel–Praly](../BIBLIOGRAPHY.md#jiang-teel-praly-1994) for two systems; [Dashkovskiy–Rüffer–Wirth](../BIBLIOGRAPHY.md#dashkovskiy-ruffer-wirth-2007) for arbitrary interconnections), and [Lohmiller–Slotine](../BIBLIOGRAPHY.md#lohmiller-slotine-1998) contraction analysis is the differential version. The lumping error from this document then enters not as a separate apology but as one more bounded disturbance input, which the same machinery absorbs.

## The factorisation this licenses

The practical payoff, and the reason the whole stack is computable:

> **Confine the nonlinear DAE solve to inside a cell. Compose at chip scale using a linear network plus a DAG traversal.**

SPICE solves the nonlinear DAE directly and cannot scale to a chip. The flow instead: characterises cells once by DAE solve (L0/03), treats interconnect as linear (L1), and composes by forward traversal (L2). L0/04 is what says that factorisation is *sound* and what the error term is.

Note the consequence for L2: its forward traversal — arrival time and slew propagating through a DAG — is not merely an algorithm, it is the chip-scale instance of this composition theorem. The two documents are describing the same thing at different granularity.

## What composition is not

"Plug together" is combinatorics *plus per-edge arithmetic*: each connection discharges finitely many side conditions — output load within the driver contract's domain (`max_capacitance`), input slew within the receiver's (`max_transition`), coupling within the local disturbance budget. Finite and decidable, but not vacuous: the shipped design currently fails exactly these checks (finding F2). The right formalism for the per-component object is an **assume-guarantee contract** ([Benveniste et al.](../BIBLIOGRAPHY.md#benveniste-2018)): guaranteed output trajectory classes given input trajectory classes, load, and disturbance budget, with an explicit domain of validity — which is precisely what an interval-valued Liberty arc is.

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

## Reading

[Haus & Melcher](../BIBLIOGRAPHY.md#haus-melcher-1989) for the field-to-circuit derivation of Kirchhoff. [Bossavit](../BIBLIOGRAPHY.md#bossavit-1998), *Computational Electromagnetism* — Whitney forms and network models as discrete Maxwell; [Tonti](../BIBLIOGRAPHY.md#tonti-2013) on the classification diagrams behind it. [Bryant](../BIBLIOGRAPHY.md#bryant-1984) (1984) for channel-connected components. [Benveniste et al.](../BIBLIOGRAPHY.md#benveniste-2018), *Contracts for System Design* (Foundations and Trends in EDA, 2018) — the assume-guarantee formalism the per-component contracts instantiate. [Jiang–Teel–Praly](../BIBLIOGRAPHY.md#jiang-teel-praly-1994) and [Dashkovskiy–Rüffer–Wirth](../BIBLIOGRAPHY.md#dashkovskiy-ruffer-wirth-2007) on ISS small-gain; [Lohmiller & Slotine](../BIBLIOGRAPHY.md#lohmiller-slotine-1998), "On contraction analysis for non-linear systems" (Automatica 1998). [de Figueiredo & Stolfi](../BIBLIOGRAPHY.md#de-figueiredo-stolfi-2004) (affine arithmetic), [Makino & Berz](../BIBLIOGRAPHY.md#makino-berz-2003) (Taylor models), [Girard](../BIBLIOGRAPHY.md#girard-2005) and [Althoff](../BIBLIOGRAPHY.md#althoff-cora-2015) (zonotopes, [CORA](../BIBLIOGRAPHY.md#althoff-cora-2015)) for the dependency problem. Note that circuit-theory texts almost universally *start* from Kirchhoff, so the derivation direction needed here is unusual.
