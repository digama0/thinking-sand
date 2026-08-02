# L4/04 — Adequacy: how a definition can be wrong

## Background

Theorems are checked by proof; definitions are checked by nothing. When [00](00-elaborated-object.md) *defines* what the Verilog means, no downstream proof can catch an error in the definition itself — if the semantics says an operator does the wrong thing, every theorem built on it remains perfectly valid *about the wrong machine*, and the proof assistant will never complain. This is the deepest kind of gap in any formal verification project: it lives in the correspondence between a mathematical object and the informal thing it claims to formalise, where proof cannot reach. The property wanted is called **adequacy** — that the formal semantics faithfully captures what the artifact actually means — and since it cannot be proved, the engineering question becomes: how do you make *inadequacy detectable*?

The general answer is triangulation against independent interpretations, and its cheapest instrument is **differential testing**: run the same design under your semantics and under independently-written simulators, on the same inputs, and compare outputs cycle by cycle. Any disagreement pinpoints a construct whose meaning is contested. The method's power comes from independence (the comparison implementations — Verilator and Icarus here — were written by different people, from the standard, with different internal architectures; a shared bug across all three is unlikely) and its weakness is coverage: it only tests behaviours the test inputs exercise. The subtler and stronger instrument, particular to this project's structure, is described below: the L3 equivalence check between our semantics of the RTL and the netlist that *Yosys's* semantics of the same RTL produced is, unintentionally but effectively, a semantics-vs-semantics comparison over every gate of the design — with the decisive property that disagreement causes a visible proof failure rather than silence.

One reference point for the counterfactual discussion below: **FIRRTL** is an intermediate representation used by generator-based hardware flows (Chisel most prominently) — a small, precisely specified circuit language that designs are compiled *into*, with a documented lowering to netlists. Designs born in such an IR largely bypass this chapter's problem, because the IR's semantics is a written-down specification rather than a reconstruction from a simulator-defined language. picorv32 is hand-written Verilog, so no such object exists for it; this chapter is the tax the project pays for choosing silicon that exists over a proof architecture that would have been cleaner.

## Statement

`⟦·⟧` is a definition, so nothing downstream can *prove* it right — a wrong semantics yields a true theorem about the wrong object, and no checker catches it. Adequacy is established by making disagreement with independent interpretations **detectable**, three ways with different coverage.

## The three checks

**Differential simulation.** Elaborate under `⟦·⟧`, run the design's own testbenches, compare cycle-by-cycle against Verilator and Icarus — two independent implementations of the LRM's semantics. Cheap, catches the crude failure modes (wrong operator semantics, wrong commit order), coverage limited to what the testbenches exercise.

**The CEC cross-check — the strong one.** L3's equivalence compares `⟦RTL⟧` against a netlist produced by *Yosys's* interpretation of the same source. If our semantics differs from Yosys's anywhere the design's logic depends on, **the CEC fails** — the mismatch surfaces as a cone that won't prove, pointing at the construct responsible. Two independent implementations of the subset agreeing on a 275,608-instance design is real evidence, and crucially the failure mode is *detection*, not silence. This converts the scariest definitional risk in the top-down architecture into checked-on-this-instance.

**Scheduler independence, if proved** ([00](00-elaborated-object.md)) would upgrade the story from "agrees with two schedulers on this design" to "agrees with every LRM-conformant scheduler on every program in the subset." Bounded, genuine, deferred.

Honest limit shared by the first two: coverage is *this design's* constructs and behaviours. That is exactly the right scope for a validation project — the semantics needs to be right about picorv32, not about Verilog — and the subset boundary ([01](01-subset.md)) is what makes "right about this design" a closed question rather than an open-ended one.

## The counterfactual: the IR route

The clean architecture this layer exists *instead of*: take a generator's IR with a specified lowering — **FIRRTL** is the canonical case (word-level types, a written-down spec, a defined lowering to netlists) — lower it yourself, compare netlist-to-netlist, and Verilog appears only as a file format. Then L4 shrinks to nearly nothing.

Unavailable here: picorv32 has no generator and no IR — the hand-written Verilog *is* the source artifact. VexRiscv has SpinalHDL's internal representation, but nothing with FIRRTL's status as a specified interchange object. So the choice was: Chisel-class design with the better proof architecture, or Caravel+picorv32 with a theorem about silicon that exists. The project chose the silicon and pays this layer as the tax — the measured census, three adequacy checks, one deferred theorem. If the project ever moves from validating to generating, the IR route is the right answer and this layer's replacement is already sketched.

## Obligations

1. The differential harness (elaborate, run, compare — days).
2. Wire semantics-mismatch triage into L3's CEC failure reporting, so a non-proving cone distinguishes "synthesis did something" from "our semantics disagrees with Yosys."
3. (Deferred) scheduler independence for the subset.

## Effort

Weeks for the harness; the cross-check comes free with L3. This file is small because the strategy is to *inherit* adequacy evidence from work other layers do anyway — which is the correct shape for a definition layer.
