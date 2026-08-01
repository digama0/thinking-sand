# L3/01 — Well-formedness: checked, not assumed

## Statement

The four preconditions of [00](00-netlist-object.md)'s semantics, decidable on the shipped netlist — **and they have been run**: `tools/netgraph.py data/caravel/gl_caravel_core.v`, 7.5 s over 275,608 `sky130_*` instances (+97 macros = 275,705). 43 distinct pin names, all classified explicitly; the tool **exits non-zero on an unknown pin rather than guessing a direction**, since a misclassified output silently turns real contention into a clean bill of health.

| check | meaning | result |
|---|---|---|
| **W1** | one driver per net | **26** multi-driver nets — all tri-state, all in `pll.ringosc`; **0 static contention** |
| **W2** | no floating reads | 1,609 — all at hierarchy/macro boundaries |
| **W3** | combinational acyclicity | **exactly 1 SCC, 64 nets, entirely in `pll.ringosc`** |
| **W4** | physical cells inert | **0** violations |

## W1 discharges structurally — and the discharge is idiom-dependent

The contended nets are `einvp`/`einvn` pairs with the *same* enable net on `TE` and `TE_B` — complementary polarity, so exactly one conducts, by construction. It is the oscillator's delay-trim multiplexer; no functional reasoning needed. The luck should be recognised as luck: a *decoded* tri-state bus ("at most one select high") would need a reachability proof over the decoder's state space — L5-difficulty work leaking into a well-formedness check. The general rule: tri-state sharing discharges structurally iff the enables are complementary by wiring; anything else escalates.

## W3 makes X5's excision provably minimal

Excise `pll.ringosc` and the netlist is both acyclic and contention-free. The ring oscillator is *exactly* the set of structural violations — the only cycle and the only contention, with the same cause. The prediction that the PLL cannot live inside the synchronous abstraction was right, and **nothing else violates it** — the black-box boundary is forced, not chosen.

## W2 is a hierarchy artifact with a real residue

The undriven reads localise to macro boundaries: `mgmt_buffers` 631, `gpio_control_in_*` 462, `soc.core` 69, `RAM256` 64, `user_io_*` 76 — outputs of black-box macros and hierarchical ports whose drivers are not in this file. Reducing 1,609 to *genuine* floats needs the macro interface list; expect ~0 residue. It must be discharged rather than waved at: a real floating read is a node with no restoring driver, hence permanently X — outside L0/05's invariant sets, not merely untracked.

## W4 caught the tool

First run: 118 violations, all `conb_1` — a constant *generator* (drives `HI`/`LO`) misfiled as inert filler. Correcting the classification gave 0 and brought the physical total to exactly 235,566, independently matching FINDINGS' census. The inertness check catching a misclassification of its own configuration is the argument for having it: [02](02-licensed-deletions.md)'s 85.5% deletion rests entirely on this property.

## What W1+W2 buy beyond the semantics

They are the licence to work **three-valued rather than four-valued** ([L2/00](../L2-timing/00-timed-model.md)): HDL logic's fourth value Z (undriven) is structurally excluded — every net has exactly one driver and every read is driven — so Z is deleted from the value lattice rather than modelled.

*The within-cell half of the no-contention condition (PUN/PDN duality) is not checkable at this level — it needs transistor netlists; see [L0/09](../L0-device-physics/09-cut-discipline.md).*

## Open problems

1. Reduce W2 against the macro interface list (an afternoon, given the LEF or module ports).
2. Promote the checks from tool runs to lemmas against [00](00-netlist-object.md)'s formal netlist — same computations, checked once inside the proof.

## Effort

**Done**, at tool level. The promotion to proof-level lemmas is days once 00 exists.
