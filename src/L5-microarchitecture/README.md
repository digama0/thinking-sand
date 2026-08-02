# L5 — Microarchitecture: RTL refines the ISA

> **Spec below:** `⟦RTL⟧` (L4). **Spec above:** `ISA` (L6). **Kind: theorem** — the irreducible one.

> **Retarget note (2026-08-02, F7).** [00](00-microarchitecture.md) now tours the shipped core — VexRiscv `MinDebugCache`, a pipelined RV32I with a direct-mapped I-cache, measured from source — with both presences and absences priced. [01](01-refinement.md)–[05](05-interrupts.md) remain worked against picorv32 (the pinned comparison core): the method they teach transfers, their concrete numbers do not. What the pipeline and cache change: hazard/flush invariant families, flushing- or WEB-style α at retirement instead of visit-the-abstraction-every-cycle, an I-cache agreement invariant, history-dependent WCET. In the target's favour: RVFI supports VexRiscv, the plugin structure seams the invariant, and interrupts are the *standard* machine-mode machinery. Estimates stale until 01–05 are re-scoped.

## Background

This is the layer a computer-architecture course would recognise: prove that the processor implements its instruction set. It is also the tower's irreducible theorem — the one piece no tool produces and no measurement substitutes for. The proof technique is the **simulation**: an abstraction function reads architectural state out of the hardware at commit points, an invariant describes the machine's in-flight state well enough to survive induction, and a measure bounds how long any instruction can take — all introduced from scratch in [01](01-refinement.md)'s Background, with the machine's anatomy toured in [00](00-microarchitecture.md). The invariant ([02](02-invariant.md)) is where the thinking concentrates; the rest is wide, shallow, and largely mechanisable ([03](03-instruction-obligations.md)–[05](05-interrupts.md)).

## Statement

`⟦RTL⟧ ⊑ ISA`: a stuttering simulation `(I, α, m)` — invariant, abstraction at commit points, measure — conditional on the bus contract (L7) and stated over the shipped configuration (L4). Displayed in full in [01](01-refinement.md); inventing `I` is the one thing in the entire project no tool produces ([02](02-invariant.md)).

## Subcomponents

| | | status |
|---|---|---|
| [00](00-microarchitecture.md) | **What the machine actually is** — the arch-class tour of the shipped VexRiscv core (pipeline stages, I-cache, hazards, CSRs, debug — measured from source); presence *and* absence priced; picorv32 compressed as the comparison baseline | re-derived for the target |
| [01](01-refinement.md) | The statement: `(I, α, m)`, commit points = FSM structure, **RVFI as the designer's own α**, IRQ preemption in the diagram; the measure read quantitatively = **the WCET table**, hard real time for free | weeks; do first |
| [02](02-invariant.md) | The invariant: entropy argument, the six-clause sketch, IC3 calibration plan | **the heart of the estimate** |
| [03](03-instruction-obligations.md) | Wide-shallow per-instruction lemmas: decode bijection + unimplemented sweep, ALU, iterative shifts, load/store, counters | months; harness-dominated |
| [04](04-memory-pcpi.md) | The bus as assume-guarantee (G1–G3 + the look-ahead consistency lemma `LA`); PCPI loop invariants; the memory-hierarchy counterfactual priced | weeks |
| [05](05-interrupts.md) | The custom IRQ unit vs S3: five obligations, **non-interference first**; breaking the spec-implementation circularity with independent anchors | months; risk concentrated |

## Interfaces

**Consumes:** `⟦RTL⟧` + configuration record (L4), the licence to reason discretely (L2), the bus contract and its latency bound `B` (L7), the Sail import + authored S3 (L6). **Exports:** the refinement theorem — the tower's ← THE WORK arrow — plus the per-instruction WCET table (the measure read quantitatively, [01](01-refinement.md)), consumed by L7/04's epilogue sizing.

## Axioms introduced

None of its own; this is where the others are cashed in. The conditionality is explicit: on `B` (L7), on the S3 spec's fidelity (L6's ledger), on the shipped configuration.

## The layer's shape

[00](00-microarchitecture.md) fixes what is being verified — for the shipped core, a 4+fetch-stage pipeline with a direct-mapped I-cache, whose *presences* now carry the pricing the old absence table only threatened. The structural role the comparison core's FSM played (commit points, invariant organisation, cross-instruction independence — [01](01-refinement.md)/[02](02-invariant.md)/[03](03-instruction-obligations.md)) passes to the pipeline's stage structure: retirement at WriteBack defines the commit points, the stage registers organise the invariant per stage, and the hazard interlocks are precisely what restores per-instruction independence where the pipeline broke it. The two ports where the world enters are assume-guarantee pairs ([04](04-memory-pcpi.md)), and the one genuinely bespoke-vs-bespoke confrontation — custom hardware against authored spec — is quarantined behind a non-interference theorem ([05](05-interrupts.md)).

## Open problems

1. **The invariant** ([02](02-invariant.md)) — irreducible; the IC3 calibration decides how much of it is tedium vs. thought.
2. The S3 anchor corpus ([05](05-interrupts.md)) — gates the IRQ half; do the firmware extraction early.
3. The S4 choices (L6) the lemmas are stated against — decide and record before proving, not during.

## First experiments

- **Write the refinement statement and α before any proof** ([01](01-refinement.md)) — against RVFI's retirement semantics, checked on simulation traces as a cheap oracle.
- Formalise the FSM state graph from the RTL; extract path bounds for the measure ([00](00-microarchitecture.md), [01](01-refinement.md)).
- The IC3 calibration on clauses 1/2/4 ([02](02-invariant.md)) — cheap, and it sizes the layer's real cost.

## Effort

1–2 years *as scoped against picorv32*, which sat at the baseline of every effort multiplier. The shipped core occupies two multiplier rows (pipeline, I-cache — each the old table's ~×3 class), so the honest current statement is: **stale, pending the re-scoping of 01–05**; the irreducible-content observation (a few hundred lines of clauses plus glue, the rest infrastructure) is expected to survive with more clauses.

## Reading

[Burch & Dill](../bibliography.md#burch-dill-1994) on flushing — the technique this core makes unnecessary, and the baseline for everything that isn't a multicycle FSM. Manolios on WEB refinement (where flushing fails). Sawada & Hunt on intermediate abstractions. [Fox](../bibliography.md#fox-2003)'s ARM6 verification — the closest existing analogue to this layer's deliverable. riscv-formal's picorv32 checks — the RVFI-based prior art α should stay comparable with.
