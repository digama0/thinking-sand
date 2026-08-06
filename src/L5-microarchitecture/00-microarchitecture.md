# L5/00 — What the microarchitecture actually is

## Background

The ISA says *what* the processor does; the **microarchitecture** is *how* — the actual arrangement of registers, adders, multiplexers, and control logic that carries each instruction out. The distinction is the deepest one in computer architecture: dozens of wildly different microarchitectures implement the same ISA, from a chip executing one instruction over several clock cycles to a server core juggling hundreds at once, and software cannot tell them apart except by speed. This chapter is the guided tour of the core's microarchitecture, and since the tour uses the standard vocabulary of a computer-architecture course, here is the minimum of it.

The core is **pipelined**: instead of finishing one instruction before starting the next, the machine is an assembly line of **stages**, each doing one phase of the work — fetch the instruction, decode it, execute the arithmetic, access memory, write the result back — with several instructions in flight at once, one per stage. The price of the overlap is **hazards**: instruction B may need a register value that instruction A, two stages ahead, has computed but not yet written back. The two standard remedies are **interlocks** (stall B until A's result lands — simple, slow) and **forwarding/bypassing** (route A's result sideways into B's stage — fast, more wiring and more invariant); this machine has a full bypass network, so the forwarding-correctness clause family is part of the price of realism here. Branches add a second complication: by the time a branch's direction is known, younger instructions have already entered the pipe on the fall-through path and must be **flushed** — squashed as if they never happened — which is why serious cores add branch *prediction*, and why its absence in this configuration matters. A **cache** is the third piece: a small on-chip memory holding recently-used contents of a larger, slower one, consulted first on every access — here an **instruction cache** on the fetch side, while the data side is a **tightly-integrated memory** (a scratchpad at a fixed address) rather than a cache, which deletes the entire miss/refill/writeback machinery from the data path.

Everything else on the big-core menu is absent — no data cache, no store buffer, no out-of-order execution, no MMU, no floating point — and the presence/absence table below prices each item either way.

## Statement

The concrete anatomy of the generated core — [**Rocket**](https://github.com/chipsalliance/rocket-chip) in the framework's tiny configuration, as declared by the elaboration (the device tree carries the headline numbers) and to be re-measured from the emitted RTL by the layer's checker. The tour is organised as the standard computer-architecture walk, with each *present* structure priced alongside each absence. Facts marked *to record* await the re-anchored configuration record.

## The pipeline

Rocket's classic five stages:

```
Fetch (icache, RVC expansion) → Decode → Execute (ALU, branch) → Memory (DTIM, atomics) → WriteBack
```

Roughly five instructions in flight, with bypass paths routing results backwards from Execute/Memory/WriteBack into younger instructions' operand reads. The control bundle rides the pipe with each instruction, so the invariant's "decode coherence" clause becomes a per-stage family: what each stage's control bits must say about the instruction they travel with.

## The tour

**Fetch and the I-cache.** A **4 KiB, direct-mapped** instruction cache (64 sets × 64-byte blocks — the elaboration's own numbers), read and hit-checked in the front end, with a miss triggering a TileLink refill burst. Because the C extension is implemented, fetch groups are 16-bit aligned and an **RVC expander** rewrites compressed instructions to their 32-bit forms before decode — an extra function to verify, with the standard's own expansion table as its spec. The cache brings the `fence.i` obligation — the ISA's synchronise-instruction-stream operation: stores land in the DTIM immediately, but the I-cache can hold stale code until flushed.

**Decode.** A generated decoder (elaborated from the instruction table in the generator source) producing the control bundle. Exhaustiveness/exclusivity obligations attach to the decoder function itself, per L6's coverage sweep.

**Hazards.** Full **bypassing** with interlocks where bypassing cannot help (load-use, mul/div in flight, CSR side effects) — so the invariant carries both clause families: forwarding-correctness ("the value routed sideways equals the value that will be written back") and stall-correctness ("no reader advances past an unresolvable writer").

**Execute.** ALU and address generation; branch resolution with **no predictor in this configuration** (*to record*: the tiny config elides the branch-target buffer) — a taken branch flushes the younger pipeline contents, the flush a spec-visible stutter burst, "flushed instructions have no architectural effect" an invariant clause with real content. The **multiply/divide unit is iterative** (small-configuration parameters — *to record*), a classic loop-invariant obligation.

**Memory.** The data side is the **16 KiB DTIM** — a scratchpad, not a cache: fixed address window, no tags, no misses, near-single-cycle. The **A extension** lives here: an atomic ALU performs the `amo*` read-modify-writes at the memory, and an LR/SC reservation tracks the conditional pair (its granularity and progress conditions are S4 rows — L6/02's C7).

**WriteBack.** The register-file write and the **retirement point** — the natural commit point for α. Rocket exposes a designer-declared **instruction trace port** (the retirement interface the ecosystem's co-simulation uses), which is the α anchor: architectural effects are read where the design itself says instructions retire.

**CSRs and interrupts.** The CSR file implements the **standard machine-and-user-mode subset**: the trap/interrupt CSRs (`mstatus`/`mie`/`mip`/`mtvec`/`mepc`/`mcause`/`mtval`/`mscratch`), the counters (Zihpm), **PMP** (8 regions, granularity 4), and the custom `xrocket` control CSRs ([L6/01](../L6-isa/01-irq-spec.md)'s enumeration). All three standard interrupt lines are live — software and timer from the CLINT, external from the PLIC — so the trap machinery is *imported* spec end to end, with the custom CSRs as the only authored residue. The **reset vector is a constant** (the boot ROM base).

**The debug module.** The standard RISC-V debug architecture, reached over JTAG: halt, step, abstract commands, out-of-band access to architectural state. The refinement must be stated **conditional on debug-inactive** (the same move as scan chains in L3/05's contingency table), with the debug session itself specced separately via the debug spec's own register model.

## The presence/absence table — both directions priced

| structure | status | what it costs the proof |
|---|---|---|
| pipeline (5 stages) | **present** | per-stage invariant families; flushing- or WEB-style α at retirement |
| forwarding/bypass network | **present** | forwarding-correctness clauses — the priced cost of a real pipeline |
| instruction cache (4 KiB, direct-mapped) | **present** | a set-indexed agreement invariant; `fence.i` correctness; a miss-bounded fetch-timing term |
| RVC expansion (C extension) | **present** | the expansion function vs. the standard's table |
| iterative mul/div (M extension) | **present** | one loop invariant per operation family |
| atomics + LR/SC (A extension) | **present** | the AMO read-modify-write lemmas; the reservation invariant |
| PMP | **present** | the permission-check lemma on every access path |
| debug module | **present** | conditional refinement under debug-inactive |
| branch prediction / speculation | absent (this config) | "any prediction is recoverable" clauses — avoided |
| data cache / store buffer | absent (DTIM instead) | pending-write deltas in every load lemma — avoided |
| OOO | absent | WEB + ROB invariant — avoided |
| MMU/TLB | absent | walker-vs-page-tables, privileged VM spec — avoided |
| FPU | absent | FP correctness — avoided |
| multicore | absent | RVWMO — avoided |

The configuration sits deliberately in the middle of the ladder: a real pipeline with real bypassing and three ratified extensions, but with the data-side miss machinery, speculation, and virtual memory all absent — each absence a clause family the proof never pays for.

## Obligations

1. The stall/flush/bypass structure and per-instruction pipeline-occupancy bounds, extracted from the emitted RTL (the re-anchored stage-graph checker).
2. The retirement/α story instantiated for this pipe ([01](01-refinement.md)) and the invariant's per-stage clause sketch ([02](02-invariant.md)).
3. The I-cache agreement invariant and the `fence.i` obligation, stated.
4. The debug-inactive conditionality, stated once and threaded.
5. The *to record* rows (BTB absence, mul/div parameters) pinned by measurement.

## Effort

Days — descriptive, measured from source. What it feeds — the invariant and the per-instruction sweep — is priced in the layer README.

## Reading

The [rocket-chip](https://github.com/chipsalliance/rocket-chip) generator source — the Scala is the design intent the generated SystemVerilog implements. [Burch & Dill](../bibliography.md#burch-dill-1994) and Manolios (WEB) for the α constructions. Hennessy & Patterson for the pipeline/hazard/cache vocabulary at textbook depth.
