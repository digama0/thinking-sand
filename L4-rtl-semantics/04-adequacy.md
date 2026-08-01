# L4/04 — Adequacy: how a definition can be wrong

## Statement

`⟦·⟧` is a definition, so nothing downstream can *prove* it right — a wrong semantics yields a true theorem about the wrong object, and no checker catches it. Adequacy is established by making disagreement with independent interpretations **detectable**, three ways with different coverage.

## The three checks

**Differential simulation.** Elaborate under `⟦·⟧`, run the design's own testbenches, compare cycle-by-cycle against Verilator and Icarus — two independent implementations of the LRM's semantics. Cheap, catches the crude failure modes (wrong operator semantics, wrong commit order), coverage limited to what the testbenches exercise.

**The CEC cross-check — the strong one.** L3's equivalence compares `⟦RTL⟧` against a netlist produced by *Yosys's* interpretation of the same source. If our semantics differs from Yosys's anywhere the design's logic depends on, **the CEC fails** — the mismatch surfaces as a cone that won't prove, pointing at the construct responsible. Two independent implementations of the subset agreeing on a 275,608-instance design is real evidence, and crucially the failure mode is *detection*, not silence. This converts the scariest definitional risk in the top-down architecture into checked-on-this-instance.

**Scheduler independence, if proved** ([00](00-elaborated-object.md)) would upgrade the story from "agrees with two schedulers on this design" to "agrees with every LRM-conformant scheduler on every program in the subset." Bounded, genuine, deferred.

Honest limit shared by the first two: coverage is *this design's* constructs and behaviours. That is exactly the right scope for a validation project — the semantics needs to be right about picorv32, not about Verilog — and the subset boundary ([01](01-subset.md)) is what makes "right about this design" a closed question rather than an open-ended one.

## The counterfactual: the IR route

The clean architecture this layer exists *instead of*: take a generator's IR with a specified lowering — **FIRRTL** is the canonical case (word-level types, a written-down spec, a defined lowering to netlists) — lower it yourself, compare netlist-to-netlist, and Verilog appears only as a file format. Then L4 shrinks to nearly nothing.

Unavailable here: picorv32 has no generator and no IR — the hand-written Verilog *is* the source artifact. VexRiscv has SpinalHDL's internal representation, but nothing with FIRRTL's status as a specified interchange object. So the choice was: Chisel-class design with the better proof architecture, or Caravel+picorv32 with a theorem about silicon that exists. The project chose the silicon and pays this layer as the tax — 19 sites, three adequacy checks, one deferred theorem. If the project ever moves from validating to generating, the IR route is the right answer and this layer's replacement is already sketched.

## Obligations

1. The differential harness (elaborate, run, compare — days).
2. Wire semantics-mismatch triage into L3's CEC failure reporting, so a non-proving cone distinguishes "synthesis did something" from "our semantics disagrees with Yosys."
3. (Deferred) scheduler independence for the subset.

## Effort

Weeks for the harness; the cross-check comes free with L3. This file is small because the strategy is to *inherit* adequacy evidence from work other layers do anyway — which is the correct shape for a definition layer.
