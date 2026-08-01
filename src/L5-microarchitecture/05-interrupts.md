# L5/05 — Interrupts: the implementation side of S3

## Background

[L6/01](../L6-isa/01-irq-spec.md)'s background introduced the two halves of this story: what interrupts are and how picorv32's custom scheme replaces the standard RISC-V machinery, and why a spec authored from the same RTL it will be checked against risks certifying bugs rather than catching them. That chapter authored the spec; this one proves the hardware meets it, and the proof side has its own vocabulary worth a moment.

The central concept is **non-interference** — a theorem shape borrowed from security verification, where it means "secret inputs don't affect public outputs." Here it does modularity work instead: *with interrupts masked and no interrupt instructions executed, the machine behaves exactly as if the interrupt unit did not exist.* This is what licenses every other L5 chapter to ignore interrupts entirely — their proofs are about the interrupt-free machine, and non-interference says that machine is faithfully embedded in the real one. Without it, every per-instruction lemma would need an "...and the IRQ unit doesn't intervene" side condition, and a bug in the interrupt hardware could silently invalidate the base refinement. Proving it first *quarantines* the layer's riskiest component.

The other recurring word is **atomicity**. Interrupt entry does several things — saves the return address, updates the mask, redirects the program counter — and the spec describes them as one indivisible step. The hardware necessarily spreads the work over wires and cycles; the obligation is that no *observable* intermediate exists: no cycle at which a commit-point readout would catch the machine half-entered, return address saved but mask not yet updated. Atomicity failures are classic interrupt bugs (they manifest as corruption when an interrupt arrives in exactly the wrong cycle — rare, unreproducible, and exactly what proofs exist to exclude), which is why the entry sequence gets its own obligation rather than being folded into the general invariant.

## Statement

Prove the custom IRQ machinery refines the authored IRQ specification (L6/S3). The layer's risk concentrates here, for a structural reason: everywhere else the spec is imported and battle-tested (Sail) while the implementation is simple; here **both sides are bespoke** — the spec must be written from the same RTL it will then be checked against, and circularity is the failure mode to engineer away.

## The machinery, concretely

32 IRQ lines in; per-line behaviour set by parameters (`MASKED_IRQ` — permanently masked; `LATCHED_IRQ` — a pulse latches until served); a mask register (`maskirq`); q-registers (`getq`/`setq`) holding return state; a timer (`timer`, counts down, raises its line); entry at `PROGADDR_IRQ` with return pc and pending-set delivered in q-registers; return via `retirq`; `waitirq` stalls until a line fires; `eoi` signals completion outward. Six custom instructions, occupying encoding space the sweep in [03](03-instruction-obligations.md) must treat as *implemented* — the configuration record (`ENABLE_IRQ`, necessarily on for the SoC: the wrapper wires 6 lines) governs.

## The proof obligations

1. **Preemption only at commit points** — an instruction in flight is never abandoned. An invariant clause ([02](02-invariant.md) clause 5), and the reason [01](01-refinement.md)'s simulation square stays a clean disjunction (instruction step ∨ IRQ-entry step) rather than acquiring a third, mid-instruction case.
2. **Entry atomicity**: the jump to `PROGADDR_IRQ`, the q-register writes, and the mask update happen as one spec step — no observable intermediate.
3. **No lost interrupts**: a latched line stays pending until served or explicitly cleared — a safety clause with a liveness shadow (served *eventually* — bounded by the handler's behaviour, hence conditional on software, hence a `Sys(F)`-level claim, not provable here; state the split explicitly).
4. **Non-interference**: with all lines masked and no IRQ instructions executed, the machine's behaviour is exactly the IRQ-free refinement — the theorem that lets every other L5 file ignore this one.
5. **`waitirq`** as the spec-visible waiting state ([01](01-refinement.md)'s measure carve-out).

Obligation 4 is the load-bearing one for project structure: it *modularises the risk*. If it holds, the rest of L5 is correct independently of anything in this file, and IRQ bugs cannot contaminate the base refinement.

## Breaking the circularity of S3

The spec and implementation sharing an author is unavoidable; sharing *evidence* is not. Independent anchors, in value order:

- **The shipped firmware** (Caravel's housekeeping/boot code) and picorv32's own test firmware use the IRQ instructions — the spec must make *observed, working* software correct. Software written by others against the documentation is the closest thing to an independent semantics.
- **The documentation** (picorv32 README) — written prose to formalise *first*, diffing the formalisation against RTL behaviour afterwards, so discrepancies surface as findings rather than being silently resolved toward the RTL.
- **riscv-formal's checks** for this core exercise IRQ retirement via RVFI's `rvfi_intr` — prior art for what "an interrupt retired correctly" observably means.

Discrepancies between these anchors and the RTL are *results* (documented-vs-actual bugs are a known genre for this core's ecosystem), and S4-style choices where the documentation is silent must be recorded in L6, not improvised here.

## Obligations (file-level)

1. The five proof obligations above, with non-interference (4) first.
2. The anchor corpus: extract every IRQ-instruction use from shipped firmware; run each against the draft S3 spec.
3. The timer's spec: its countdown semantics is architectural state (visible via `timer`), so it belongs in S3's state, not in the invariant's private clauses.

## Effort

Months, and the least parallelisable part of L5 — but bounded by the machinery being small (one unit, six instructions, five obligations). The open-ended risk is spec fidelity, and that lives in L6/S3's ledger entry, priced there as the sharpest surviving specification axiom.
