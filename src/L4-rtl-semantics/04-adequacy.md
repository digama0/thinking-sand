# L4/04 — Adequacy: how a definition can be wrong

## Background

Theorems are checked by proof; definitions are checked by nothing. When [00](00-elaborated-object.md) *defines* what the SystemVerilog means, no downstream proof can catch an error in the definition itself — if the semantics says an operator does the wrong thing, every theorem built on it remains perfectly valid *about the wrong machine*, and the proof assistant will never complain. This is the deepest kind of gap in any formal verification project: it lives in the correspondence between a mathematical object and the informal thing it claims to formalise, where proof cannot reach. The property wanted is called **adequacy** — that the formal semantics faithfully captures what the artifact actually means — and since it cannot be proved, the engineering question becomes: how do you make *inadequacy detectable*?

The general answer is triangulation against independent interpretations, and its cheapest instrument is **differential testing**: run the same design under your semantics and under independently-written simulators, on the same inputs, and compare outputs cycle by cycle. Any disagreement pinpoints a construct whose meaning is contested. The method's power comes from independence and its weakness is coverage: it only tests behaviours the test inputs exercise. This design adds a structural instrument most projects lack: the RTL is not the top of its own derivation. It is *compiler output* — the design exists first as **FIRRTL**, an intermediate representation with a written specification, and CIRCT's `firtool` lowers it to the SystemVerilog the flow consumes. A specified IR one storey above the RTL means the semantics can be *cross-anchored*: define the meaning of the emitted subset, define (or import) the meaning of the FIRRTL, and check that `firtool`'s lowering relates them. Disagreement at any triangle edge is a detection.

## Statement

`⟦·⟧` is a definition, so nothing downstream can *prove* it right — a wrong semantics yields a true theorem about the wrong object, and no checker catches it. Adequacy is established by making disagreement with independent interpretations **detectable**, four ways with different coverage.

## The four checks

**Differential simulation.** Elaborate under `⟦·⟧`, run the ecosystem's own test programs, compare cycle-by-cycle against Verilator (the framework's native simulation path) and a second independent simulator. Cheap, catches the crude failure modes (wrong operator semantics, wrong commit order), coverage limited to what the tests exercise — and this design ships an unusual asset here: thousands of generator-emitted assertions (the TileLink monitors alone are 85 files of them), which run *inside* the differential harness as behaviour probes written by the design's own authors.

**The CEC cross-check — the strong one.** L3's equivalence compares `⟦RTL⟧` against a netlist produced by *Yosys's* interpretation of the same source. If our semantics differs from Yosys's anywhere the design's logic depends on, **the CEC fails** — the mismatch surfaces as a cone that won't prove, pointing at the construct responsible. Two independent implementations of the subset agreeing on a 50-thousand-cell design is real evidence, and crucially the failure mode is *detection*, not silence. This converts the scariest definitional risk in the top-down architecture into checked-on-this-instance.

**The IR anchor — the structural one.** The FIRRTL file the design passes through has a specification independent of any simulator, and the elaboration that produced it is deterministic and re-runnable from the pinned generator. Two uses, increasing in strength. Today: *re-elaboration* — regenerate the FIRRTL and the SystemVerilog from the pinned sources and diff, which separates properties of the design from properties of one build. Eventually: a semantics for the FIRRTL subset the design occupies, with the lowering checked — at which point L4's SystemVerilog semantics stops being load-bearing and becomes a checked artifact of the flow, the "shrink to nearly nothing" this layer's architecture aims at. The obligation between here and there is honest: `firtool` is a large unverified compiler, and until the lowering is checked per-design (CEC between FIRRTL semantics and emitted-SV semantics), the IR anchor detects drift without certifying the lowering.

**Scheduler independence, if proved** ([00](00-elaborated-object.md)) would upgrade the story from "agrees with two schedulers on this design" to "agrees with every LRM-conformant scheduler on every program in the subset." Bounded, genuine, deferred.

Honest limit shared by the first two: coverage is *this design's* constructs and behaviours. That is exactly the right scope for a validation project — the semantics needs to be right about the generated core, not about SystemVerilog — and the subset boundary ([01](01-subset.md)) is what makes "right about this design" a closed question rather than an open-ended one.

## Why this layer is small here

The classic version of this chapter, for a hand-written design, carries the whole weight of "what does this Verilog mean" with only simulators to triangulate against. Here the design descends through a specified IR emitted by a disciplined compiler: the subset is one generator's idiom ([01](01-subset.md)), the dark corners are absent by construction, and the IR gives the semantics a second, independent anchor with a specification document. The layer's long-term shape is exactly the IR route: put the semantic weight on FIRRTL, check the lowering per design, and let the SystemVerilog semantics be the small, checked bridge it deserves to be. That is also where the project's certification endgame naturally lands — a lowering that emits an equivalence certificate per module would discharge this layer's residue as a by-product.

## Obligations

1. The differential harness (elaborate, run, compare — days), with the emitted assertion collateral enabled.
2. Wire semantics-mismatch triage into L3's CEC failure reporting, so a non-proving cone distinguishes "synthesis did something" from "our semantics disagrees with Yosys."
3. The re-elaboration check: regenerate FIRRTL + SystemVerilog from the pinned generator and diff against the artifacts of record.
4. (Deferred) scheduler independence for the subset; the FIRRTL-subset semantics and the per-design lowering check.

## Effort

Weeks for the harness; the cross-check comes free with L3. This file is small because the strategy is to *inherit* adequacy evidence from work other layers do anyway — which is the correct shape for a definition layer.
