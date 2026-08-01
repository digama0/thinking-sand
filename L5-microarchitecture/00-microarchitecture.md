# L5/00 — What the microarchitecture actually is

## Statement

The concrete anatomy of picorv32, measured from the source (`data/mgmt/picorv32.v`), organised as the standard computer-architecture tour — with each *absent* structure priced, because the absences are the target-selection decision made visible.

## The control: an 8-state one-hot FSM

`reg [7:0] cpu_state`, one-hot over:

```
fetch → ld_rs1 → ld_rs2 → exec → (shift | stmem | ldmem) → fetch
                                   trap
```

One instruction in flight, ever. CPI ≈ 3–4. The FSM *is* the microarchitecture: every other structure hangs off which state is active, and the invariant ([02](02-invariant.md)) is largely a statement per state.

## The tour

**Decoder.** Instructions decode into ~50 one-hot latched flags (`instr_lui … instr_timer`, plus `is_*` group flags), computed as the word arrives and **latched** — so decode happens once, and the invariant must say the latched flags stay coherent with the latched instruction word. Exhaustiveness and mutual exclusion of the one-hot set against the Sail decoder is [03](03-instruction-obligations.md)'s wide-shallow obligation. `CATCH_ILLINSN=1` (default): undecodable words trap.

**ALU / datapath.** One shared adder-subtractor-comparator serving arithmetic, branches, and address generation — sharing by FSM phase instead of by port arbitration, which is why there are no structural hazards to reason about. Shifts default to `TWO_STAGE_SHIFT=1`: an *iterative* shifter (by 4, then by 1) with its own FSM state — a loop invariant, not a mux tree. `BARREL_SHIFTER=0` in the defaults; `TWO_CYCLE_ALU`/`TWO_CYCLE_COMPARE` (default 0) would insert a register mid-datapath — the one place "pipelining" could appear, still with one instruction in flight; the shipped configuration decides whether even that exists.

**Register file.** 32×32 flops (`ENABLE_REGS_16_31=1`, dual-port read option), `REGS_INIT_ZERO=0` — the file powers up X, which is exactly L4/03's spec-nondeterminism-matching case.

**Memory interface.** No cache. The native bus is the valid/ready handshake (`mem_valid/ready`, `addr/wdata/wstrb/rdata`, `mem_instr` tagging fetches) **plus a second, look-ahead interface** (`mem_la_*`) exposing the request combinationally a cycle early — two views of one transaction whose mutual consistency is an internal obligation ([04](04-memory-pcpi.md)).

**Coprocessor port.** PCPI (`pcpi_valid/insn/rs1/rs2 → pcpi_wr/rd/wait/ready`) — mul/div live outside the core as iterative units (`ENABLE_MUL/DIV`, default 0; the shipped configuration decides).

**Interrupts.** A custom unit — 32 lines, latching/masking (`MASKED_IRQ`, `LATCHED_IRQ`), q-registers, timer, vector `PROGADDR_IRQ`, six custom instructions. The implementation side of S3; risk concentrated in [05](05-interrupts.md).

**The observer that ships in the source.** Behind the `RISCV_FORMAL` compile guard sit **RVFI ports** — `rvfi_valid/order/insn/trap/intr…` — the riscv-formal *retirement interface*: the designer's own declaration of where commit happens and what retires. Whether or not it is in the shipped netlist, it is the natural template for α ([01](01-refinement.md)) and the prior art (riscv-formal's per-instruction BMC of this very core) for the commit-point discipline.

## The absence table — each absence priced

| absent structure | what it would have cost the proof |
|---|---|
| pipeline | hazard/forwarding invariants; Burch–Dill flushing as the abstraction function |
| branch prediction / speculation | "any prediction is recoverable" — invariant clauses independent of predictor size |
| cache | in-flight miss state in the invariant (×3); blocking cache ≈ a function of memory |
| store buffer | pending-write delta on memory in every obligation (×1.5) |
| OOO | flushing dies; WEB refinement + ROB invariant (order-of-magnitude) |
| MMU/TLB | walker-vs-mutable-page-tables (×5); privileged spec |
| multicore | RVWMO, unattempted at any scale (×20) |

picorv32 sits at the baseline of every row. That is not an accident of the tour — it is *why this core was chosen*, and the table is the quantitative form of the choice.

## Obligations

1. Pin the shipped parameterisation (L4's extraction) against every "default" above — `ENABLE_IRQ` in particular *must* be on for the SoC (the wrapper wires 6 IRQs), so the defaults are provably not the shipped values.
2. Confirm the regfile implementation in the shipped build (flops vs. the replaceable `picorv32_regs` module).

## Effort

Days — descriptive, but it is the document every other L5 file points into.
