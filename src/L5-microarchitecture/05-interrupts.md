# L5/05 — Traps and interrupts

## Background

An **interrupt** is the mechanism by which the outside world interrupts a running program: a device raises a wire, and the processor — at a suitable boundary — suspends the program, saves enough state to resume it, and jumps to a *handler*. RISC-V specifies this machinery in its privileged architecture: on a **trap** (an interrupt, or a synchronous exception like an illegal instruction), the machine saves the interrupted pc to `mepc`, records the reason in `mcause`, stacks the interrupt-enable bit inside `mstatus`, and jumps to the handler address in `mtvec`; the handler returns with `mret`, which unstacks and resumes. Interrupt delivery is governed by two CSRs — `mip` (which interrupts are *pending*) and `mie` (which are *enabled*) — gated by the global enable bit `mstatus.MIE`. The core implements exactly this machine-mode machinery, so the specification is **imported** — the Sail privileged subset, ratified standard — not authored.

The system side is the standard shape as well, which is worth appreciating as a cost that *didn't* materialise: all three standard interrupt lines are live. The **CLINT** drives the software-interrupt and timer-interrupt pending bits (`msip` from its software-interrupt register, `mtip` from the `mtime`/`mtimecmp` compare), and the **PLIC** drives the external-interrupt bit, funnelling its device sources (the UART) through gateways, priorities, and a claim/complete protocol. Both devices sit behind the memory map, so their register semantics are *device models* — L7/03's business — while the core-side delivery machinery is entirely the imported spec. What remains authored at the core is only the custom control CSRs ([L6/01](../L6-isa/01-irq-spec.md)), and their spec must say they never alter delivery semantics.

The synchronous side is the standard's full surface: illegal instruction, misaligned load/store, access faults (a denied TileLink response *does* arrive as a precise access-fault trap — the error device makes even unmapped addresses well-behaved, L7/03), breakpoint, and the environment calls. The exact per-cause behaviour is the choice register's to record (L6/02); this chapter's lemmas consume it.

## Statement

Prove the trap and interrupt machinery refines the machine-mode spec: the imported Sail subset for everything standard. The proof obligations:

1. **Trap-entry atomicity**: `mepc`/`mcause`/`mstatus` update and the redirect to `mtvec` happen as one spec step — no observable intermediate, no partially-retired instruction underneath ([01](01-refinement.md)'s disjunction stays clean).
2. **`mret`** unstacks and redirects exactly per the spec.
3. **Preemption only at retirement boundaries**: an instruction in flight is either retired or flushed, never half-committed — an invariant clause ([02](02-invariant.md)), and the reason the simulation cell needs no third case.
4. **Delivery gating**: a trap step is taken exactly when `mstatus.MIE ∧ (mip ∧ mie) ≠ 0` at a boundary (or a synchronous exception retires); no lost interrupts — the *persistence* of a source lives in the CLINT and the PLIC's gateway/pending machinery (a device-model property plus software's claim/complete discipline), hence a `Sys(F)`-level claim, split explicitly.
5. **Precise exceptions on the memory path**: a faulting access (denied response, misaligned, PMP-refused) traps with the correct cause and no side effect — the lemma family where the memory system meets the trap machinery.
6. **Non-interference**: with `mstatus.MIE` clear and no traps raised, behaviour is exactly the trap-free machine — the lemma that lets every other L5 file ignore this one, quarantining the risk.

## Anchors against spec-side error

The imported half is anchored by the standard's own artifacts: the [riscv-arch-test](https://github.com/riscv-non-isa/riscv-arch-test) suite run against the imported model, and RVFI-style retirement checking for what "an interrupt retired correctly" observably means. The device half (CLINT/CLINT-compare semantics, PLIC claim/complete) is anchored by the de-facto and ratified documents those devices implement, formalised *first* and then diffed against the generated RTL. The working-software corpus — the ecosystem's own interrupt-handling code and test suites — is what the composed spec must make correct; extracting the interrupt-facing paths and running them against the draft spec is the standing check.

## Obligations

1. The six proof obligations above, non-interference (6) first.
2. The delivery split stated precisely: core-side gating proved here, source-side persistence delegated to L7/03's CLINT/PLIC models by name.
3. The software corpus: extract interrupt-facing code paths from the ecosystem's test programs; run each against the draft spec.

## Effort

Months, but mostly *standard* months: the imported half rides the Sail model and existing compliance machinery, and the interrupt sources are standard devices with documents. The open-ended risk — spec fidelity for the small authored residue — is priced in the ledger as S3.
