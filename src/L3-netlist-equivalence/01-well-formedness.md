# L3/01 — Well-formedness: checked, not assumed

## Background

The Mealy semantics of [00](00-netlist-object.md) presumes the netlist is *electrically sane*, and each sanity condition has a concrete physical failure behind it. A net (wire) is **driven** by the gate output connected to it; if *two* outputs drive one net and ever disagree, the result is **contention** — one transistor pulling the wire toward 1.8 V while another pulls it toward ground, a fight that produces an invalid intermediate voltage and, sustained, a damaging short-circuit current. A gate input attached to a net with *no* driver is **floating**: its voltage is set by nothing, drifts with whatever charge leaks nearby, and reads as an arbitrary, possibly time-varying bit. And a **combinational cycle** — a loop of gates with no flop breaking it — has no settled value to compute; physically it is a feedback loop that may oscillate forever. The checks W1 (one driver per net), W2 (no floating reads), and W3 (acyclicity) rule these out; W4 (inertness) verifies that the cells about to be *deleted* in [02](02-licensed-deletions.md) genuinely touch nothing logical.

Two pieces of circuit vocabulary appear in the results and deserve a sentence each. A **tri-state** driver is a gate output with an enable pin: enabled, it drives its value; disabled, it electrically disconnects (the "third state," high-impedance or Z). Tri-states are the *legitimate* way for several drivers to share one wire — legitimate exactly when the enables guarantee at most one driver is on at a time, which is the question W1 must settle for each shared net it finds. And a **ring oscillator** is a loop of an odd number of inverters — a deliberately built combinational cycle whose value can never settle, so it oscillates at a frequency set by the gates' delays. It is the standard way to generate a clock on-chip, it lives inside this design's PLL, and it is *supposed* to violate W1 and W3: it is the one part of the die whose job is to be unstable. The satisfying result below is that the violations found are exactly the ring oscillator and nothing else — the analog island is precisely where the structural checks say it is.

## Statement

The four preconditions of [00](00-netlist-object.md)'s semantics, decidable on the hardened netlist by the layer's checker (to be re-run against this flow's output). The tool discipline carries over unchanged: every pin name classified explicitly, and the checker **exits non-zero on an unknown pin rather than guessing a direction**, since a misclassified output silently turns real contention into a clean bill of health.

| check | meaning | result |
|---|---|---|
| **W1** | one driver per net | **26** multi-driver nets — all tri-state, all in `pll.ringosc`; **0 static contention** |
| **W2** | no floating reads | 1,609 — all at hierarchy/macro boundaries |
| **W3** | combinational acyclicity | **exactly 1 SCC, 64 nets, entirely in `pll.ringosc`** |
| **W4** | physical cells inert | **0** violations |

## W1 discharges structurally — and the discharge is idiom-dependent

The contended nets are `einvp`/`einvn` pairs with the *same* enable net on `TE` and `TE_B` — complementary polarity, so exactly one conducts, by construction. It is the oscillator's delay-trim multiplexer; no functional reasoning needed. The luck should be recognised as luck: a *decoded* tri-state bus ("at most one select high") would need a reachability proof over the decoder's state space — L5-difficulty work leaking into a well-formedness check. The general rule: tri-state sharing discharges structurally iff the enables are complementary by wiring; anything else escalates.

## W3's expected verdict, and what a hit would mean

This design has no on-die oscillator, so the expected W3 verdict is **zero cycles and zero contention outright** — there is nothing that *should* violate the synchronous discipline. Any hit is therefore a finding, not an excision candidate: a cycle would be a generator or synthesis defect, and a multi-driver net a mapping bug. The check's value inverts from delimiting a known analog region to certifying there isn't one.

## W2 is a hierarchy artifact with a real residue

Undriven-read reports localise to macro boundaries — nets fed by the SRAM macros' outputs, whose drivers are not standard cells in this file (the unused second-port outputs of the memory macros are the expected bulk). Reducing the raw report to *genuine* floats needs the macro interface list; expect ~0 residue. It must be discharged rather than waved at: a real floating read is a node with no restoring driver, hence permanently X — outside L0/05's invariant sets, not merely untracked.

## W4 caught the tool

First run: 118 violations, all `conb_1` — a constant *generator* (drives `HI`/`LO`) misfiled as inert filler. Correcting the classification gave 0 and brought the physical total to exactly 235,566, independently matching Findings' census. The inertness check catching a misclassification of its own configuration is the argument for having it: [02](02-licensed-deletions.md)'s 85.5% deletion rests entirely on this property.

## What W1+W2 buy beyond the semantics

They are the licence to work **three-valued rather than four-valued** ([L2/00](../L2-timing/00-timed-model.md)): HDL logic's fourth value Z (undriven) is structurally excluded — every net has exactly one driver and every read is driven — so Z is deleted from the value lattice rather than modelled.

*The within-cell half of the no-contention condition (PUN/PDN duality) is not checkable at this level — it needs transistor netlists; see [L0/09](../L0-device-physics/09-cut-discipline.md).*

## Open problems

1. Reduce W2 against the macro interface list (an afternoon, given the LEF or module ports).
2. Promote the checks from tool runs to lemmas against [00](00-netlist-object.md)'s formal netlist — same computations, checked once inside the proof.

## Effort

**Done**, at tool level. The promotion to proof-level lemmas is days once 00 exists.
