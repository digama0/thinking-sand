# L2/07 — Crosstalk and the power grid

## Background

Two wires running side by side for any distance form a capacitor: charge moved on one induces charge movement on the other, through nothing but proximity. On a chip whose routing layers are packed with parallel wires at minimum spacing, this **coupling capacitance** makes every net a potential radio: when an *aggressor* net switches, a neighbouring *victim* feels it. The interference — **crosstalk** — takes two forms, one for each state the victim can be in. If the victim is switching at the same moment, the aggressor's motion effectively changes how much capacitance the victim must charge (the "Miller factor" of the analysis below: an opposing transition can as much as double the effective coupling, an assisting one cancel it), which shifts the victim's *delay* — a timing effect. If the victim is sitting still, the aggressor's edge injects a **glitch** — a transient voltage bump that the victim's driver must fight down before any listening gate mistakes it for a real transition.

The defence against glitches is the digital abstraction's own **noise margin**: a gate does not respond to small wiggles — its input can move some hundreds of millivolts off the rail before the output does anything — so a glitch provably smaller than the margin is *nothing*, absorbed as if it never happened. (This restoration-by-indifference is the voltage-domain sibling of the restoration patterns met elsewhere in the tower.) The proof obligation is then a per-net inequality — worst-case sum of all aggressors' injections stays under the margin — and, at this design's generous 130 nm voltages, the inequality can be made to hold by *routing rules alone*: bounded parallel run lengths, spacing, or a grounded **shield wire** between critical nets. Geometry, checked once, and no trace of the phenomenon survives to any higher layer.

The chapter's second subject is the **power grid**. Supply voltage is not a given constant: every switching gate draws a current spike through a resistive metal mesh, and the resulting sags (**IR droop**) locally slow every gate — a potential back-door coupling between activity and timing that could entangle everything with everything. The design's counterweight is the decap army (the 125k+ decoupling capacitors of L3/02's census — local charge reservoirs that supply the spikes so the grid doesn't have to), and the verification strategy is to compress the entire phenomenon into a single **impedance bound**: the grid, decaps included, presents a low enough impedance across the relevant frequency band that no cell's supply leaves a stated window. Inside that window, supply variation is *already covered* by the voltage tier of [03](03-corners.md)'s corners; beyond it lives the small residual probability `P_droop`, the third and last summand of the project's ε.

## Statement

The two analog phenomena that could force their way into the discrete interface — coupling between nets, and supply variation — and the arguments that keep them out. Both are *absorbed at this layer*: nothing above L2 sees either, and preserving that is a design constraint, not an accident.

## Crosstalk: two effects, two absorptions

Coupling capacitance `C_x` between a victim and an aggressor (L1's coupling graph) acts twice:

**Delay shift (victim switching).** The classical model: effective coupling ranges over `{0, 1, 2}×C_x` by relative transition direction — the coupling *Miller factor*, named for the feedback-capacitance multiplication of [Miller](../BIBLIOGRAPHY.md#miller-1919) (1919). Absorb it by widening the victim's load interval — `C_eff ∈ [C_g, C_g + 2C_x]` for setup, `[C_g, ...]` floor for hold — and the coupling graph *disappears into the per-net RC interval*. Honesty note: the 2× ceiling is a fact about equal-slew ramp models, not a theorem — [Chen, Kirkpatrick & Keutzer](../BIBLIOGRAPHY.md#chen-kirkpatrick-keutzer-2000) showed the factor needed for worst-case *delay* exceeds the naive range with mismatched slews. The rigorous version derives the factor from the contract network (slew-dependent), which is exactly the kind of lemma L0/04's machinery exists for — assume the classical bound only until then, and say so.

**Glitch (victim quiet).** An aggressor transition injects charge; the victim's driver fights it. The check: worst-case over all aggressors switching together,

```
Σ_aggressors  (C_x / C_total) · ΔV · f(driver strength, slews)   <   NM
```

with NM from L0/05. If this passes *per net*, nothing is exported at all — a glitch that never leaves the noise margin never becomes a logical event.

**The discharge is geometric.** Both absorptions reduce to routing-rule checks: maximum parallel run length at minimum spacing, spacing or shielding on the exceptions. Structurally identical to tap coverage — a layout predicate, checked once (L1/G-machinery), never seen again. Feasible at 130 nm/1.8 V precisely because the margins are wide; at 7 nm the worst-case sum fails routinely and industry prunes by **timing-window intersection** instead — which still preserves the layering (no *functional* information flows downward), but couples the noise check to [02](02-verified-sta.md)'s arrival windows. Levers if a net fails, best first: shielding (topological, exactly zero — L1/04's Step 1), spacing, run-length limits, slower edges.

**The red line: treat any net needing a *functional* coupling constraint as a layout bug.** "These two nets never switch together because the FSM forbids it" entangles the noise argument with L5's invariant — the one dependency direction this project's layering exists to prevent. Fix the layout instead; the option always exists at this node.

## The power grid: enters exactly once

The grid could contaminate everything — every delay depends on V. It is kept to a single entry point:

> **The equipotential bound.** The grid's impedance to the rails, over the frequency band set by the design's edge rates, is below the threshold making supply excursions at any cell ≤ ΔV_grid. Established by the ~225k decaps (the impedance bound is *why they exist*); discharged once as a frequency-domain claim.

Downstream of this single bound: (i) the voltage tier of [03](03-corners.md)'s corners covers V ± ΔV_grid — supply variation becomes *corner content*, not a new mechanism; (ii) L1/04's screening theorem gets its Dirichlet hypothesis — the grid is a shield only if it is an equipotential, so **the decaps are doing double duty** (delay stability *and* shield quality); (iii) the residual — droop beyond the bound under worst-case simultaneous switching — is `P_droop` in MAIN's ε, a P6-class environment/design bound.

Slower edges relax the band over which the impedance bound must hold *and* shrink both crosstalk effects — one more independent way a conservatively-clocked design is cheaper to verify, and by now the third such coincidence (cf. F2's slew limits, the SPI round-trip hypothesis).

## Obligations

1. The Miller-factor lemma from the contract network (or the explicit assumption, flagged, until then).
2. The glitch check as a per-net computation over L1's coupling graph + L0's NM — plus the routing-rule predicate that makes it pass by construction (L1/G5-adjacent).
3. The grid impedance bound: state it, and identify what discharges it (decap census + package model — partially X4/P6 territory).
4. The `P_droop` term's definition, so MAIN's ε has three defined summands rather than two and a gesture.

## First experiments

- Extract the coupling graph for the worst few nets from the shipped SPEF-equivalent (or re-extract) and run the glitch sum against SKY130's noise margins. If the worst net passes with margin, the whole absorption strategy is confirmed cheap for this design.
- Census the parallel-run lengths in the routed DEF against a candidate rule — is the geometric discharge already true of the shipped layout, or does it need the timing-window fallback anywhere?

## Effort

Months, mostly tooling over DEF/extraction data; the two lemmas (Miller, equipotential) are the only theory, and both lean on machinery other files already need.
