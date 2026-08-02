# L5/00 — What the microarchitecture actually is

## Background

The ISA says *what* the processor does; the **microarchitecture** is *how* — the actual arrangement of registers, adders, multiplexers, and control logic that carries each instruction out. The distinction is the deepest one in computer architecture: dozens of wildly different microarchitectures implement the same ISA, from a chip executing one instruction over several clock cycles to a server core juggling hundreds at once, and software cannot tell them apart except by speed. This chapter is the guided tour of the shipped core's microarchitecture, and since the tour uses the standard vocabulary of a computer-architecture course, here is the minimum of it.

The shipped core is **pipelined**: instead of finishing one instruction before starting the next, the machine is an assembly line of **stages**, each doing one phase of the work — fetch the instruction, decode it, execute the arithmetic, access memory, write the result back — with several instructions in flight at once, one per stage. The price of the overlap is **hazards**: instruction B may need a register value that instruction A, two stages ahead, has computed but not yet written back. The two standard remedies are **interlocks** (stall B until A's result lands — simple, slow) and **forwarding/bypassing** (route A's result sideways into B's stage — fast, more wiring and more invariant). Branches add a second complication: by the time a branch's direction is known, several younger instructions have already entered the pipe on the fall-through path and must be **flushed** — squashed as if they never happened — which is why serious cores add branch *prediction*, and why its absence here matters. A **cache** is the third piece: a small on-chip memory holding recently-used contents of a larger, slower one, consulted first on every access — here an **instruction cache** only, so fetches usually take a cycle instead of a bus transaction, at the cost of invisible state deciding which.

Everything else on the big-core menu is still absent from this machine — no data cache, no store buffer, no prediction, no out-of-order execution, no MMU, no floating point, not even hardware multiply — and the presence/absence table below prices each item either way. The book's original scoping was done against picorv32, a multicycle core with *none* of the above (one instruction in flight, ever); it remains pinned as the comparison core, its anatomy compressed into a section at the end, because the method chapters ([01](01-refinement.md)–[03](03-instruction-obligations.md)) were worked against it and read best with that machine in mind.

## Statement

The concrete anatomy of the shipped core — **VexRiscv in the `MinDebugCache` configuration** (F7; identified from the netlist's own plugin registers, `check-l5.py`) — measured from `VexRiscv_MinDebugCache.v` and the GL netlist, organised as the standard computer-architecture tour, with each *present* structure priced alongside each absence.

## The pipeline, measured

Four main stages behind a two-stage cached fetch front end; the inter-stage register banks are read directly off the source:

```
Fetch (2 stages, inside IBusCachedPlugin: PC / cache-read | hit-check, injector)
  → Decode ──[17 regs]──▶ Execute ──[12]──▶ Memory ──[9]──▶ WriteBack
```

(Register counts are declared synthesizable registers per inter-stage bank; the source also carries simulation-only `*_string` waveform-debug registers, absent from the netlist. The first published version of these numbers was a sloppy grep's 38/16/12 — `check-l5.py`'s declaration-anchored count is the authority.)

Five-ish instructions in flight. The stage registers (`decode_to_execute_*`, `execute_to_memory_*`, `memory_to_writeBack_*`) carry the decoded control signals *with* the instruction down the pipe — contrast picorv32's decode-once-and-latch — so the invariant's "decode coherence" clause becomes a per-stage family: what each stage's control bits must say about the instruction they travel with.

## The tour

**Fetch and the I-cache.** `IBusCachedPlugin`: a **direct-mapped** instruction cache of exactly **64 bytes — 2 lines × 32 B** (measured from the array declarations; single way, single bank) — read in the first fetch stage, hit-checked in the second, with a miss triggering a bus refill and a redo. Two lines is a fetch buffer more than a cache: the agreement invariant quantifies over two entries, and a miss-every-line WCET bound is nearly tight. The cache is the layer's biggest new proof object: an invariant tying every valid cache line to backing memory, an interaction with `fence.i` (the ISA's explicit synchronise-instruction-stream operation — with no D-cache, self-modifying code is visible in memory immediately, but the *I-cache* can hold stale code until flushed), and history-dependent fetch timing that breaks the naive per-instruction WCET addition of [01](01-refinement.md).

**Decode.** A generated decoder (SpinalHDL emits it as masked pattern-matches) producing the control bundle that rides the stage registers. No latched one-hot flags; exhaustiveness/exclusivity obligations attach to the decoder function itself, per L6's coverage sweep.

**Hazards.** `HazardSimplePlugin`, **interlock-only — resolved by the configuration record**: a younger instruction reading a register with an in-flight writer **stalls** in Decode until the value lands, and even a write-back-buffer address match raises a hazard (stall) rather than forwarding — no bypass muxes exist. The invariant needs only "no reader advances past an unresolved writer"; the forwarding-correctness clause family is avoided entirely.

**Execute.** ALU and address generation; `LightShifterPlugin` — an **iterative** shifter, one bit per cycle, the same loop-invariant obligation picorv32's two-stage shifter posed; and branch resolution: **no predictor** (measured: zero prediction structures), so a taken branch flushes the younger pipeline contents — the flush is a spec-visible stutter burst, and "flushed instructions have no architectural effect" is an invariant clause with real content.

**Memory.** `DBusSimplePlugin`: an uncached, one-outstanding-transaction data bus. No store buffer, no reordering — loads and stores hit the bus in program order, which keeps the memory half of the refinement close to picorv32's simplicity.

**WriteBack.** The register-file write and the **retirement point** — the natural commit point for α, and where RVFI pulses: riscv-formal supports VexRiscv, so the designer-declared retirement interface survives the retarget.

**CSRs and interrupts.** `CsrPlugin` implements the **standard machine-mode subset** — measured: `mstatus`/`mie`/`mip`/`mtvec`/`mepc`/`mcause`/`mtval`, trap entry, `mret` — plus two **custom CSRs** (`0xBC0`/`0xFC0`, the LiteX external-interrupt mask/pending pair), and *without* `mscratch`, `misa`, or the counters (`rdcycle`/`rdinstret` trap). `softwareInterrupt`/`timerInterrupt` are tied to zero at instantiation: the standard MSIP/MTIP mechanisms are structurally dead, and every interrupt arrives via the 32-bit external array. So the dissolved-S3 story lands precisely: the trap machinery is imported (Sail privileged subset), while the custom CSR pair and the array semantics are the *residual* authored spec. The **reset vector is a CSR-writable register** (init `0x10000000`, the flash XIP base) — a register-dependent spec hypothesis of the F4/F6 family.

**The debug unit.** `DebugPlugin`: halt, step, and instruction injection over a debug bus — out-of-band access to architectural state. The refinement must be stated **conditional on debug-inactive** (the same move as scan chains in L3/05's contingency table), with the debug session itself specced separately or excluded.

**No hardware M.** Multiply and divide trap to software (the netlist's lack of `MulDivIterativePlugin` state is how the variant was identified). The M-extension obligations leave the hardware layer entirely.

## The presence/absence table — both directions priced

| structure | status | what it costs the proof |
|---|---|---|
| pipeline (4+fetch stages) | **present** | per-stage invariant families; hazard-interlock clauses; flushing- or WEB-style α instead of visit-the-abstraction-every-cycle (~×3 on the old baseline) |
| instruction cache (direct-mapped) | **present** | cache-vs-memory agreement invariant; `fence.i` correctness; history-dependent fetch timing — WCET needs cache analysis or a miss-every-fetch bound |
| iterative shifter | **present** | one loop invariant (same shape as before) |
| debug unit | **present** | conditional refinement under debug-inactive |
| branch prediction / speculation | absent | "any prediction is recoverable" clauses — avoided |
| data cache / store buffer | absent | pending-write deltas in every load lemma — avoided |
| OOO | absent | WEB + ROB invariant — avoided |
| MMU/TLB | absent | walker-vs-page-tables (×5), privileged VM spec — avoided |
| hardware M | absent | multiplier cones (L3/05's PAC fallback) — avoided |
| multicore | absent | RVWMO — avoided |

## The comparison core, compressed

picorv32 (pinned; the original scoping target): an 8-state one-hot multicycle FSM, one instruction ever in flight, decode-once-latched flags, shared ALU by FSM phase, no cache, custom IRQ scheme, native valid/ready bus. Every structure in the table above sat at "absent" for it — which is why [01](01-refinement.md)–[03](03-instruction-obligations.md)'s worked analysis (commit points at fetch-return, the six-clause invariant, exact WCET addition) is so clean, and why that analysis is retained as the method's baseline while its concrete numbers no longer describe the target.

## Obligations

1. ~~The configuration record~~ — **extracted and pinned** (`tools/config-record.py`, checked by `check-l5.py`): RV32I, no C/M/A; the CSR set above; 64 B I-cache; interlock-only hazards; CSR-writable reset vector at `0x10000000`; interrupts via the external array only.
2. Re-derive [01](01-refinement.md)'s commit-point/α story for retirement-at-WriteBack with flushes (RVFI-anchored), and [02](02-invariant.md)'s clause sketch per stage.
3. The I-cache agreement invariant and `fence.i` obligation, stated.
4. The debug-inactive conditionality, stated once and threaded.

## Effort

Days — descriptive, measured from source like its predecessor. The *layer's* totals move: the pipeline and cache rows above are the old effort table's ×3 entries, and the 1–2 year picorv32-baseline estimate is stale until [01](01-refinement.md)–[05](05-interrupts.md) are re-scoped.

## Reading

The VexRiscv repository's plugin documentation — the architecture is literally a list of plugins, and the shipped set is the spec of what to verify. [Burch & Dill](../bibliography.md#burch-dill-1994) — flushing is now *relevant*, not avoided. Manolios on WEB refinement. riscv-formal's VexRiscv integration — the RVFI anchor. Hennessy & Patterson for the pipeline/hazard/cache vocabulary at textbook depth.
