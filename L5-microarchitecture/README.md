# L5 — Microarchitecture: RTL refines the ISA

> **Spec below:** `⟦RTL⟧` (L4). **Spec above:** `ISA` (L6). **Kind: theorem** — the irreducible one.

## Statement

`⟦RTL⟧ ⊑ ISA`: a stuttering simulation `(I, α, m)` — invariant, abstraction at commit points, measure — conditional on the bus contract (L7) and stated over the shipped configuration (L4). Displayed in full in [01](01-refinement.md); inventing `I` is the one thing in the entire project no tool produces ([02](02-invariant.md)).

## Subcomponents

| | | status |
|---|---|---|
| [00](00-microarchitecture.md) | **What the machine actually is** — the arch-class tour of picorv32, measured from source; the absence table with each absence priced | descriptive; days |
| [01](01-refinement.md) | The statement: `(I, α, m)`, commit points = FSM structure, **RVFI as the designer's own α**, IRQ preemption in the diagram, the conditional measure | weeks; do first |
| [02](02-invariant.md) | The invariant: entropy argument, the six-clause sketch, IC3 calibration plan | **the heart of the estimate** |
| [03](03-instruction-obligations.md) | Wide-shallow per-instruction lemmas: decode bijection + unimplemented sweep, ALU, iterative shifts, load/store, counters | months; harness-dominated |
| [04](04-memory-pcpi.md) | The bus as assume-guarantee (G1–G3 + the look-ahead consistency lemma `LA`); PCPI loop invariants; the memory-hierarchy counterfactual priced | weeks |
| [05](05-interrupts.md) | The custom IRQ unit vs S3: five obligations, **non-interference first**; breaking the spec-implementation circularity with independent anchors | months; risk concentrated |

## Interfaces

**Consumes:** `⟦RTL⟧` + configuration record (L4), the licence to reason discretely (L2), the bus contract and its latency bound `B` (L7), the Sail import + authored S3 (L6). **Exports:** the refinement theorem — the tower's ← THE WORK arrow.

## Axioms introduced

None of its own; this is where the others are cashed in. The conditionality is explicit: on `B` (L7), on the S3 spec's fidelity (L6's ledger), on the shipped configuration.

## The layer's shape

[00](00-microarchitecture.md) fixes what is being verified — an 8-state one-hot FSM with one instruction ever in flight, whose absences (cache, pipeline, speculation, OOO, MMU) are each priced and are collectively *why this core was chosen*. The FSM's structure then does triple duty: it defines the commit points ([01](01-refinement.md)), organises the invariant per state ([02](02-invariant.md)), and cuts every cross-instruction dependency so the per-instruction obligations are independent ([03](03-instruction-obligations.md)). The two ports where the world enters are assume-guarantee pairs ([04](04-memory-pcpi.md)), and the one genuinely bespoke-vs-bespoke confrontation — custom hardware against authored spec — is quarantined behind a non-interference theorem ([05](05-interrupts.md)).

## Open problems

1. **The invariant** ([02](02-invariant.md)) — irreducible; the IC3 calibration decides how much of it is tedium vs. thought.
2. The S3 anchor corpus ([05](05-interrupts.md)) — gates the IRQ half; do the firmware extraction early.
3. The S4 choices (L6) the lemmas are stated against — decide and record before proving, not during.

## First experiments

- **Write the refinement statement and α before any proof** ([01](01-refinement.md)) — against RVFI's retirement semantics, checked on simulation traces as a cheap oracle.
- Formalise the FSM state graph from the RTL; extract path bounds for the measure ([00](00-microarchitecture.md), [01](01-refinement.md)).
- The IC3 calibration on clauses 1/2/4 ([02](02-invariant.md)) — cheap, and it sizes the layer's real cost.

## Effort

3–5 years, least compressible in the project — yet the irreducible content is plausibly a few hundred lines of clauses plus a glue lemma; the years are the surrounding machinery (symbolic simulation, bitvector automation, the stuttering framework). picorv32 sits at the baseline of every effort multiplier: store buffer ×1.5, non-blocking cache ×3, precise exceptions on a deep pipe ×3, VM ×5, FP ×10, multicore/RVWMO ×20 — all absent.

## Reading

[Burch & Dill](../BIBLIOGRAPHY.md#burch-dill-1994) on flushing — the technique this core makes unnecessary, and the baseline for everything that isn't a multicycle FSM. Manolios on WEB refinement (where flushing fails). Sawada & Hunt on intermediate abstractions. [Fox](../BIBLIOGRAPHY.md#fox-2003)'s ARM6 verification — the closest existing analogue to this layer's deliverable. riscv-formal's picorv32 checks — the RVFI-based prior art α should stay comparable with.
