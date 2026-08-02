# L5 — Microarchitecture: RTL refines the ISA

> **Spec below:** `⟦RTL⟧` (L4). **Spec above:** `ISA` (L6). **Kind: theorem** — the irreducible one.

## Background

This is the layer a computer-architecture course would recognise: prove that the processor implements its instruction set. It is also the tower's irreducible theorem — the one piece no tool produces and no measurement substitutes for. The proof technique is the **simulation**: an abstraction function reads architectural state out of the hardware at commit points, an invariant describes the machine's in-flight state well enough to survive induction, and a measure bounds how long any instruction can take — all introduced from scratch in [01](01-refinement.md)'s Background, with the machine's anatomy toured in [00](00-microarchitecture.md). The invariant ([02](02-invariant.md)) is where the thinking concentrates; the rest is wide, shallow, and largely mechanisable ([03](03-instruction-obligations.md)–[05](05-interrupts.md)).

## Statement

`⟦RTL⟧ ⊑ ISA`: a stuttering simulation `(I, α, m)` — invariant, abstraction read at retirement, measure — conditional on the bus contract (L7) and stated over the [configuration record](../tools/config-record.py) (L4). Displayed in full in [01](01-refinement.md); inventing `I` is the one thing in the entire project no tool produces ([02](02-invariant.md)).

## Subcomponents

| | | status |
|---|---|---|
| [00](00-microarchitecture.md) | **What the machine actually is** — the arch-class tour of the shipped [VexRiscv](https://github.com/SpinalHDL/VexRiscv) core, measured from source: pipeline, I-cache, hazards, CSRs, debug; presence *and* absence priced | measured |
| [01](01-refinement.md) | The statement: `(I, α, m)`, retirement as the commit point, **RVFI as the designer-declared α anchor**, trap steps in the diagram; the measure read quantitatively = **retirement-gap bounds**, hard real time | weeks; do first |
| [02](02-invariant.md) | The invariant: entropy argument, the per-stage clause sketch, IC3 calibration plan | **the heart of the estimate** |
| [03](03-instruction-obligations.md) | Wide-shallow per-instruction lemmas: the generated decoder vs Sail, ALU, the iterative shifter, load/store, CSR ops, the trap sweep | months; harness-dominated |
| [04](04-buses-debug.md) | The two Wishbone buses as assume-guarantee pairs (burst refill on iBus, single-beat dBus); the debug port and its conditionality | weeks |
| [05](05-interrupts.md) | Traps and interrupts against the standard machine-mode spec; the custom external-interrupt array as the residual authored semantics | months |

## Interfaces

**Consumes:** `⟦RTL⟧` + the [configuration record](../tools/config-record.py) (L4), the licence to reason discretely (L2), the bus contract and its latency bound `B` (L7), the Sail import including the machine-mode subset (L6). **Exports:** the refinement theorem — the tower's ← THE WORK arrow — plus the retirement-gap bounds (the measure read quantitatively, [01](01-refinement.md)), consumed by L7/04's epilogue sizing.

## Axioms introduced

None of its own; this is where the others are cashed in. The conditionality is explicit: on `B` (L7), on S2/S3's spec fidelity (L6's ledger), on the configuration record, and on **debug-inactive** ([00](00-microarchitecture.md), [04](04-buses-debug.md)).

## The layer's shape

[00](00-microarchitecture.md) fixes what is being verified — a 4+fetch-stage in-order pipeline with a two-line instruction cache, interlock-only hazards, and standard machine-mode trap machinery. The pipeline's stage structure organises everything: retirement at WriteBack defines the commit points ([01](01-refinement.md)), the inter-stage register banks organise the invariant per stage ([02](02-invariant.md)), and the interlocks are precisely what restores the cross-instruction independence the per-instruction obligations need ([03](03-instruction-obligations.md)). The two ports where the world enters are assume-guarantee pairs, and the debug port is quarantined behind a conditionality ([04](04-buses-debug.md)); the interrupt machinery is checked against the *imported* standard spec, with the small custom residue isolated ([05](05-interrupts.md)).

## Open problems

1. **The invariant** ([02](02-invariant.md)) — irreducible; the IC3 calibration decides how much of it is tedium vs. thought.
2. The `fence.i` / I-cache agreement story ([00](00-microarchitecture.md), [02](02-invariant.md)) — small state, real content.
3. The residual authored semantics — the external-interrupt array CSRs ([05](05-interrupts.md)) — decide and record before proving.

## First experiments

- **Write the refinement statement and α before any proof** ([01](01-refinement.md)) — against RVFI's retirement semantics ([riscv-formal](https://github.com/YosysHQ/riscv-formal) supports VexRiscv), checked on simulation traces as a cheap oracle.
- Extract the stall/flush/arbitration structure from the [pinned source](https://github.com/efabless/caravel_mgmt_soc_litex/blob/503eda0790085712ffef7f4ad8934c7daed3237f/verilog/rtl/VexRiscv_MinDebugCache.v) and derive the retirement-gap bounds ([00](00-microarchitecture.md), [01](01-refinement.md)).
- The IC3 calibration on the structural clauses ([02](02-invariant.md)) — cheap, and it sizes the layer's real cost.

## Effort

1.5–3 years. The pipeline and cache put this machine two rows up the effort-multiplier table from a multicycle core, but the mitigations are real: interlock-only hazards (no forwarding clauses), a two-line cache (a two-entry agreement invariant), no hardware M/C/A, and RVFI as a ready-made α anchor. The irreducible content remains plausibly a few hundred lines of clauses plus glue; the rest is the project-wide infrastructure item (the overview's accounting: symbolic simulation, bitvector automation, the stuttering framework).

## Reading

The [VexRiscv](https://github.com/SpinalHDL/VexRiscv) repository — the architecture is literally a list of plugins, and the shipped set is the spec of what to verify. [Burch & Dill](../bibliography.md#burch-dill-1994) on flushing, and Manolios on WEB refinement — the two standard α constructions for pipelined machines. Sawada & Hunt on intermediate abstractions. [Fox](../bibliography.md#fox-2003)'s ARM6 verification — a pipelined commercial ISA against a real microarchitecture, the closest existing analogue. [riscv-formal](https://github.com/YosysHQ/riscv-formal)'s VexRiscv integration — the RVFI-based prior art α should stay comparable with.
