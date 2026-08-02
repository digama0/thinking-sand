# L5/05 — Traps and interrupts

## Background

An **interrupt** is the mechanism by which the outside world interrupts a running program: a device raises a wire, and the processor — at a suitable boundary — suspends the program, saves enough state to resume it, and jumps to a *handler*. RISC-V specifies this machinery in its privileged architecture: on a **trap** (an interrupt, or a synchronous exception like an illegal instruction), the machine saves the interrupted pc to `mepc`, records the reason in `mcause`, stacks the interrupt-enable bit inside `mstatus`, and jumps to the handler address in `mtvec`; the handler returns with `mret`, which unstacks and resumes. Interrupt delivery is governed by two CSRs — `mip` (which interrupts are *pending*) and `mie` (which are *enabled*) — gated by the global enable bit `mstatus.MIE`. The shipped core implements exactly this machine-mode machinery, so the specification is **imported** — the Sail privileged subset, ratified standard — not authored.

Two deviations from the plain standard are the chapter's residue, and both are measured facts of the [configuration record](../tools/config-record.py). First, the standard's software and timer interrupts (MSIP/MTIP) are **structurally dead** — their input wires are tied to zero at [instantiation](https://github.com/efabless/caravel_mgmt_soc_litex/blob/503eda0790085712ffef7f4ad8934c7daed3237f/verilog/rtl/mgmt_core.v) — so the spec must say they are *never pending*, and the LiteX timer interrupts through the external path like every other device. Second, external interrupts arrive through a **32-line array** with its own mask/pending pair exposed as two custom CSRs (`0xBC0`/`0xFC0`, the [`ExternalInterruptArrayPlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/ExternalInterruptArrayPlugin.scala)) that funnel into the standard external-interrupt pending bit. The array's semantics — the read/write mask, the read-only pending *view* (a live window on `mask ∧ lines`, not a latch — writes to it trap; the measured facts are L6/01's), the funnel — is the **residual authored specification**: small, but outside the ratified model, and carrying the same unfalsifiable fidelity character as any authored spec (the doc-first-then-diff discipline applies).

## Statement

Prove the trap and interrupt machinery refines the machine-mode spec: the imported Sail subset for everything standard, plus the authored array residue. The proof obligations:

1. **Trap-entry atomicity**: `mepc`/`mcause`/`mstatus` update and the redirect to `mtvec` happen as one spec step — no observable intermediate, no partially-retired instruction underneath ([01](01-refinement.md)'s disjunction stays clean).
2. **`mret`** unstacks and redirects exactly per the spec.
3. **Preemption only at retirement boundaries**: an instruction in flight is either retired or flushed, never half-committed — an invariant clause ([02](02-invariant.md)), and the reason the simulation cell needs no third case.
4. **Delivery gating**: a trap step is taken exactly when `mstatus.MIE ∧ (mip ∧ mie) ≠ 0` at a boundary (or a synchronous exception retires); no lost interrupts — the core holds no latch (L6/01), so "a line stays asserted until handled" is a property of the SoC's event blocks plus software clearing discipline, hence a `Sys(F)`-level claim, split explicitly.
5. **The array residue**: the custom CSRs' mask/pending semantics, the funnel into the external pending bit, and the never-pending status of MSIP/MTIP — checked against the authored spec.
6. **Non-interference**: with `mstatus.MIE` clear and no traps raised, behaviour is exactly the trap-free machine — the lemma that lets every other L5 file ignore this one, quarantining the risk.

## Anchors against spec-side error

The imported half is anchored by the standard's own artifacts: the [riscv-arch-test](https://github.com/riscv-non-isa/riscv-arch-test) suite run against the imported model, and [riscv-formal](https://github.com/YosysHQ/riscv-formal)'s VexRiscv checks for what "an interrupt retired correctly" observably means. The authored residue is anchored the usual way: formalise the plugin's documentation and the [LiteX](https://github.com/enjoy-digital/litex) interrupt-handling conventions *first*, then diff against RTL behaviour; the shipped BIOS/firmware's interrupt usage is the working-software corpus that the spec must make correct.

## Obligations

1. The six proof obligations above, non-interference (6) first.
2. The authored array spec: state, steps, and its funnel into `mip` — decided and recorded before proving (L6's register discipline).
3. The firmware corpus: extract the interrupt-facing code paths from the shipped BIOS; run each against the draft spec.

## Effort

Months, but mostly *standard* months: the imported half rides the Sail model and existing compliance machinery; the authored residue is two CSRs and a funnel. The open-ended risk — spec fidelity for the residue — is priced in the ledger as S3.
