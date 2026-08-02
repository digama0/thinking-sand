# L5/00 — What the microarchitecture actually is

## Background

The ISA says *what* the processor does; the **microarchitecture** is *how* — the actual arrangement of registers, adders, multiplexers, and control logic that carries each instruction out. The distinction is the deepest one in computer architecture: dozens of wildly different microarchitectures implement the same ISA, from a chip executing one instruction over several clock cycles to a server core juggling hundreds at once, and software cannot tell them apart except by speed. This chapter is the guided tour of the shipped core's microarchitecture, and since the tour uses the standard vocabulary of a computer-architecture course, here is the minimum of it.

The shipped core is **pipelined**: instead of finishing one instruction before starting the next, the machine is an assembly line of **stages**, each doing one phase of the work — fetch the instruction, decode it, execute the arithmetic, access memory, write the result back — with several instructions in flight at once, one per stage. The price of the overlap is **hazards**: instruction B may need a register value that instruction A, two stages ahead, has computed but not yet written back. The two standard remedies are **interlocks** (stall B until A's result lands — simple, slow) and **forwarding/bypassing** (route A's result sideways into B's stage — fast, more wiring and more invariant); this machine uses interlocks only. Branches add a second complication: by the time a branch's direction is known, younger instructions have already entered the pipe on the fall-through path and must be **flushed** — squashed as if they never happened — which is why serious cores add branch *prediction*, and why its absence here matters. A **cache** is the third piece: a small on-chip memory holding recently-used contents of a larger, slower one, consulted first on every access — here an **instruction cache** only, and a very small one, so fetch usually avoids a bus transaction at the cost of a little invisible state deciding when.

Everything else on the big-core menu is absent — no data cache, no store buffer, no prediction, no out-of-order execution, no MMU, no floating point, not even hardware multiply — and the presence/absence table below prices each item either way.

## Statement

The concrete anatomy of the shipped core — [**VexRiscv**](https://github.com/SpinalHDL/VexRiscv) in the [`MinDebugCache`](https://github.com/efabless/caravel_mgmt_soc_litex/blob/503eda0790085712ffef7f4ad8934c7daed3237f/verilog/rtl/VexRiscv_MinDebugCache.v) configuration, identified from the [netlist](https://github.com/efabless/caravel/blob/27cbe49c90ba5362ad52c9968dd98e035c30c74f/verilog/gl/caravel_core.v)'s own plugin registers ([`check-l5.py`](../tools/check-l5.py)) — measured from source and organised as the standard computer-architecture tour, with each *present* structure priced alongside each absence. The numeric facts live in the [configuration record](../tools/config-record.py) and [Findings](../findings.md#the-management-core-in-the-pinned-netlist-is-vexriscv).

## The pipeline, measured

Four main stages behind a two-stage cached fetch front end; the inter-stage register banks are read directly off the source (synthesizable declarations per bank):

```
Fetch (2 stages, inside IBusCachedPlugin: PC / cache-read | hit-check, injector)
  → Decode ──[17 regs]──▶ Execute ──[12]──▶ Memory ──[9]──▶ WriteBack
```

Five-ish instructions in flight. The stage registers (`decode_to_execute_*`, `execute_to_memory_*`, `memory_to_writeBack_*`) carry the decoded control signals *with* the instruction down the pipe, so the invariant's "decode coherence" clause becomes a per-stage family: what each stage's control bits must say about the instruction they travel with.

## The tour

**Fetch and the I-cache.** [`IBusCachedPlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/IBusCachedPlugin.scala): a **direct-mapped** instruction cache of exactly **64 bytes — 2 lines × 32 B** (measured from the array declarations; single way, single bank) — read in the first fetch stage, hit-checked in the second, with a miss triggering a burst refill over the iBus and a redo. Two lines is a fetch buffer more than a cache: the agreement invariant quantifies over two entries, and a miss-every-line timing bound is nearly tight. The real content it brings is `fence.i` — the ISA's synchronise-instruction-stream operation: with no D-cache, stores are visible in memory immediately, but the I-cache can hold stale code until flushed.

**Decode.** A generated decoder ([SpinalHDL](https://github.com/SpinalHDL/SpinalHDL) emits it as masked pattern-matches) producing the control bundle that rides the stage registers. Exhaustiveness/exclusivity obligations attach to the decoder function itself, per L6's coverage sweep.

**Hazards.** [`HazardSimplePlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/HazardSimplePlugin.scala), **interlock-only**: a younger instruction reading a register with an in-flight writer **stalls** in Decode until the value lands, and even a write-back-buffer address match raises a hazard (a stall) rather than forwarding — no bypass muxes exist. The invariant needs only "no reader advances past an unresolved writer"; the forwarding-correctness clause family is avoided entirely.

**Execute.** ALU and address generation ([`IntAluPlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/IntAluPlugin.scala), [`SrcPlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/SrcPlugin.scala)); [`LightShifterPlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/ShiftPlugins.scala) — an **iterative** shifter, one bit per cycle, a classic loop-invariant obligation; and branch resolution ([`BranchPlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/BranchPlugin.scala)): **no predictor** (measured: zero prediction structures), so a taken branch flushes the younger pipeline contents — the flush is a spec-visible stutter burst, and "flushed instructions have no architectural effect" is an invariant clause with real content.

**Memory.** [`DBusSimplePlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/DBusSimplePlugin.scala): an uncached, one-outstanding-transaction data bus. No store buffer, no reordering — loads and stores hit the bus in program order.

**WriteBack.** The register-file write ([`RegFilePlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/RegFilePlugin.scala)) and the **retirement point** — the natural commit point for α, and where RVFI pulses: [riscv-formal](https://github.com/YosysHQ/riscv-formal) supports VexRiscv, so the designer-declared retirement interface is available.

**CSRs and interrupts.** [`CsrPlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/CsrPlugin.scala) implements the **standard machine-mode subset** — measured: `mstatus`/`mie`/`mip`/`mtvec`/`mepc`/`mcause`/`mtval`, trap entry, `mret` — plus two **custom CSRs** (`0xBC0`/`0xFC0`, the [external-interrupt array](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/ExternalInterruptArrayPlugin.scala) mask/pending pair), and *without* `mscratch`, `misa`, or the counters (`rdcycle`/`rdinstret` trap). `softwareInterrupt`/`timerInterrupt` are tied to zero at [instantiation](https://github.com/efabless/caravel_mgmt_soc_litex/blob/503eda0790085712ffef7f4ad8934c7daed3237f/verilog/rtl/mgmt_core.v): the standard MSIP/MTIP mechanisms are structurally dead, and every interrupt arrives via the 32-bit external array. So the trap machinery is *imported* spec (the Sail machine-mode subset), while the custom CSR pair and the array semantics are the *residual authored* spec ([05](05-interrupts.md)). The **reset vector is a CSR-writable register** (init `0x10000000`, the flash XIP base) — a register-dependent spec hypothesis of the F4/F6 family.

**The debug unit.** [`DebugPlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/DebugPlugin.scala): halt, step, and instruction injection over a debug bus — out-of-band access to architectural state. The refinement must be stated **conditional on debug-inactive** (the same move as scan chains in L3/05's contingency table), with the debug session itself specced separately or excluded.

**No hardware M.** Multiply and divide trap to software. The M-extension obligations leave the hardware layer entirely.

## The presence/absence table — both directions priced

| structure | status | what it costs the proof |
|---|---|---|
| pipeline (4+fetch stages) | **present** | per-stage invariant families; interlock clauses; flushing- or WEB-style α at retirement |
| instruction cache (64 B, direct-mapped) | **present** | a two-entry agreement invariant; `fence.i` correctness; a miss-bounded fetch-timing term |
| iterative shifter | **present** | one loop invariant |
| debug unit | **present** | conditional refinement under debug-inactive |
| forwarding/bypass | absent | forwarding-correctness clauses — avoided (interlock-only) |
| branch prediction / speculation | absent | "any prediction is recoverable" clauses — avoided |
| data cache / store buffer | absent | pending-write deltas in every load lemma — avoided |
| OOO | absent | WEB + ROB invariant — avoided |
| MMU/TLB | absent | walker-vs-page-tables, privileged VM spec — avoided |
| hardware M | absent | multiplier cones (L3/05's PAC fallback) — avoided |
| multicore | absent | RVWMO — avoided |

(For scale: a hand-written multicycle core such as [picorv32](https://github.com/YosysHQ/picorv32) — also shipped as a configuration option of this SoC — sits at "absent" on *every* row, which is what made it the classic easy target; the shipped machine is one deliberate step up.)

## Obligations

1. The stall/flush/arbitration structure and per-instruction pipeline-occupancy bounds, extracted from source ([`check-l5.py`](../tools/check-l5.py) stub `stage-graph`).
2. The retirement/α story instantiated for this pipe ([01](01-refinement.md)) and the invariant's per-stage clause sketch ([02](02-invariant.md)).
3. The I-cache agreement invariant and the `fence.i` obligation, stated.
4. The debug-inactive conditionality, stated once and threaded.

## Effort

Days — descriptive, measured from source. What it feeds — the invariant and the per-instruction sweep — is priced in the layer README.

## Reading

The [VexRiscv](https://github.com/SpinalHDL/VexRiscv) plugin sources linked above — each plugin is a few hundred lines of SpinalHDL and *is* the design intent the generated Verilog implements. [Burch & Dill](../bibliography.md#burch-dill-1994) and Manolios (WEB) for the α constructions. Hennessy & Patterson for the pipeline/hazard/cache vocabulary at textbook depth.
