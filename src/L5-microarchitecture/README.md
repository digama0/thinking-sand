# L5 — Microarchitecture: RTL refines the ISA

> **Spec below:** `⟦RTL⟧` (L4). **Spec above:** `ISA` (L6). **Kind: theorem** — the irreducible one.

## Background

This is the layer a computer-architecture course would recognise: prove that the processor implements its instruction set. It is also the tower's irreducible theorem — the one piece no tool produces and no measurement substitutes for. The proof technique is the **simulation**: an abstraction function reads architectural state out of the hardware at commit points, an invariant describes the machine's in-flight state well enough to survive induction, and a measure bounds how long any instruction can take — all introduced from scratch in [01](01-refinement.md)'s Background, with the machine's anatomy toured in [00](00-microarchitecture.md). The invariant ([02](02-invariant.md)) is where the thinking concentrates; the rest is wide, shallow, and largely mechanisable ([03](03-instruction-obligations.md)–[05](05-interrupts.md)).

## Statement

`⟦RTL⟧ ⊑ ISA`: a stuttering simulation `(I, α, m)` — invariant, abstraction read at retirement, measure — conditional on the bus contract (L7) and stated over the [configuration record](../tools/config-record.py) (L4). Displayed in full in [01](01-refinement.md); inventing `I` is the one thing in the entire project no tool produces ([02](02-invariant.md)).

## Subcomponents

| | | status |
|---|---|---|
| [00](00-microarchitecture.md) | **What the machine actually is** — the arch-class tour of the generated [Rocket](https://github.com/chipsalliance/rocket-chip) core: pipeline, I-cache, bypassing, extensions, CSRs, debug; presence *and* absence priced | declared by elaboration; re-measurement pending |
| [01](01-refinement.md) | The statement: `(I, α, m)`, retirement as the commit point, **the core's trace port as the designer-declared α anchor**, trap steps in the diagram; the measure read quantitatively = **retirement-gap bounds**, hard real time | weeks; do first |
| [02](02-invariant.md) | The invariant: entropy argument, the per-stage clause sketch, IC3 calibration plan | **the heart of the estimate** |
| [03](03-instruction-obligations.md) | Wide-shallow per-instruction lemmas: the generated decoder vs Sail, ALU, the iterative mul/div, load/store/atomics, CSR ops, the trap sweep | months; harness-dominated |
| [04](04-buses-debug.md) | The TileLink ports as assume-guarantee pairs (burst refill on the fetch side, the tile's master port); the debug module and its conditionality | weeks |
| [05](05-interrupts.md) | Traps and interrupts against the standard machine-mode spec; CLINT/PLIC delivery through the fabric as the system half | months |

## Interfaces

**Consumes:** `⟦RTL⟧` + the [configuration record](../tools/config-record.py) (L4), the licence to reason discretely (L2), the bus contract and its latency bound `B` (L7), the Sail import including the machine-mode subset (L6). **Exports:** the refinement theorem — the tower's ← THE WORK arrow — plus the retirement-gap bounds (the measure read quantitatively, [01](01-refinement.md)), consumed by L7/04's epilogue sizing.

## Axioms introduced

None of its own; this is where the others are cashed in. The conditionality is explicit: on `B` (L7), on S2/S3's spec fidelity (L6's ledger), on the configuration record, and on **debug-inactive** ([00](00-microarchitecture.md), [04](04-buses-debug.md)).

## The layer's shape

[00](00-microarchitecture.md) fixes what is being verified — a five-stage in-order pipeline with a 4 KiB instruction cache, a full bypass network, three ratified extensions (M, A, C), and standard machine-mode trap machinery. The pipeline's stage structure organises everything: retirement at WriteBack defines the commit points ([01](01-refinement.md)), the inter-stage register banks organise the invariant per stage ([02](02-invariant.md)), and the bypass/interlock discipline is precisely what restores the cross-instruction independence the per-instruction obligations need ([03](03-instruction-obligations.md)). The ports where the world enters are assume-guarantee pairs, and the debug port is quarantined behind a conditionality ([04](04-buses-debug.md)); the interrupt machinery is checked against the *imported* standard spec, with the small custom residue isolated ([05](05-interrupts.md)).

## Open problems

1. **The invariant** ([02](02-invariant.md)) — irreducible; the IC3 calibration decides how much of it is tedium vs. thought.
2. The `fence.i` / I-cache agreement story ([00](00-microarchitecture.md), [02](02-invariant.md)) — small state, real content.
3. The residual authored semantics — the custom control CSRs ([L6/01](../L6-isa/01-irq-spec.md)) — decide and record before proving.

## First experiments

- **Write the refinement statement and α before any proof** ([01](01-refinement.md)) — against the core's own trace port (the retirement interface the ecosystem's co-simulation uses), checked on simulation traces as a cheap oracle.
- Extract the stall/flush/bypass structure from the emitted RTL and derive the retirement-gap bounds ([00](00-microarchitecture.md), [01](01-refinement.md)).
- The IC3 calibration on the structural clauses ([02](02-invariant.md)) — cheap, and it sizes the layer's real cost.

## Effort

1.5–3 years. The pipeline, the bypass network, and three live extensions put this machine several rows up the effort-multiplier table from a multicycle core, but the mitigations are real: no data-cache miss machinery (the data side is a scratchpad), no speculation in this configuration, no virtual memory, no FPU, and a designer-declared trace port as a ready-made α anchor. The irreducible content remains plausibly a few hundred lines of clauses plus glue; the rest is the project-wide infrastructure item (the overview's accounting: symbolic simulation, bitvector automation, the stuttering framework).

## Reading

The [rocket-chip](https://github.com/chipsalliance/rocket-chip) repository — the generator source is the design intent. [Burch & Dill](../bibliography.md#burch-dill-1994) on flushing, and Manolios on WEB refinement — the two standard α constructions for pipelined machines. Sawada & Hunt on intermediate abstractions. [Fox](../bibliography.md#fox-2003)'s ARM6 verification — a pipelined commercial ISA against a real microarchitecture, the closest existing analogue. [riscv-formal](https://github.com/YosysHQ/riscv-formal)'s RVFI discipline — the retirement-interface prior art α should stay comparable with.
