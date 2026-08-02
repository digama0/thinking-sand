# L6/02 — The choice register (S4)

## Background

A standard written for many implementers cannot pin everything down, and does not want to. If the RISC-V spec dictated the reset value of every register, the handling of every misaligned access, and the priority of every simultaneous event, it would outlaw legitimate design choices and burden every implementation with someone else's decisions. So standards **deliberately underspecify**: "the contents of registers after reset are unspecified"; "a misaligned load may trap, or may be handled"; "pending interrupts are taken eventually." Each such sentence licenses a *family* of behaviours, and any member of the family is *conformant*. This is a feature — for implementers.

For a refinement proof it is a complication with a precise shape. Refinement (`⊑`) says every implementation behaviour is among the spec's allowed behaviours, so spec-side freedom is fine *in principle* — nondeterminism in the spec is exactly how "unspecified" is expressed formally. The problem is practical: a proof about *this* chip constantly needs to know which member of the family it is facing. When an L5 lemma about the trap handler needs to know whether a misaligned load traps, "the standard permits either" is not an answer the proof can use; the proof needs *the* answer for the shipped core, and that answer is not derivable from the standard — only from the implementation and its configuration. It is a **choice**: a decision that narrows the standard's family down to the one behaviour this implementation exhibits.

Choices of this kind are epistemically different from theorems, and that difference is why they get their own register in the axiom ledger (S4). That the RTL *agrees with* a recorded choice is checkable — a lemma. That the choice itself is the right reading of the standard's freedom is not checkable by anything; it is legislative, like an editor resolving an ambiguity. The danger is not making choices — that is unavoidable — but making them *invisibly*: a proof that silently assumes registers reset to zero has narrowed the spec without anyone deciding to, and the narrowing is now load-bearing and unrecorded. Hence the discipline of this file: every choice is written down before it is used, with what the standard left open, what was picked, and which proof consumes it. (One instance of the pattern has a standard name worth knowing: **WARL** fields — "write any, read legal" — register bits where software may write anything and the hardware is free to read back any legal value, the standard's own idiom for per-field underspecification.)

## Statement

Where RISC-V is deliberately underspecified, **conformance is not a statement** — the spec admits many behaviours, and a refinement proof needs *one*. This file is the register of choices: each entry picks a refinement of the standard, records that the pick is a choice, and becomes part of what `ISA` means. Deciding them *before* L5's proof starts is the discipline; discovering them mid-proof converts each into a stall.

## The known entries

| # | underspecified in the standard | the choice (= what the shipped core does, to be recorded) |
|---|---|---|
| C1 | reset state of general registers | unspecified by the standard — and *used*: L4/03's X-matching refines into exactly this nondeterminism (the [regfile](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/RegFilePlugin.scala) powers up unwritten) |
| C2 | misaligned loads/stores | **measured** ([config-record](../tools/config-record.py)): they trap — cause 4 (load) / 6 (store), detected at Execute (`addr[1:0]≠0` for words, `addr[0]≠0` for halves), and the bus command is *suppressed*, so a misaligned access has no side effect |
| C3 | illegal/unimplemented encodings | **measured**: trap with cause 2, `mtval` = the faulting instruction word — feeds [03](03-coverage.md)'s sweep |
| C4 | interrupt timing ("eventually") | taken at the next retirement boundary when enabled — L5/05's preemption obligation makes this precise |
| C5 | `mtvec` writability and mode bits (WARL) | **measured**: `base[31:2]` and `mode[1:0]` are both fully writable *storage*, but the trap redirect is unconditionally `{base, 00}` — vectored mode does not exist behaviourally, and the mode field reads back whatever was written (including reserved values — a WARL readback to adjudicate). `mtvec` has **no reset value**: software must write it before enabling any trap source |
| C6 | trap-value details (`mtval` on each cause) | **measured**: one context register feeds `mtval` on every trap; for the *reachable* causes — misaligned load/store: the effective address; branch/jump to a misaligned target (cause 0): the target; illegal: the instruction word (the access-fault `mtval` sources exist but are dead logic, [01](01-irq-spec.md)) |
| C7 | the custom-CSR fields ([01](01-irq-spec.md)) | **measured** ([irqmap](../tools/irqmap.py)): the mask (`0xBC0`) is a full 32-bit read/write register reset to 0; the pending view (`0xFC0`) is read-only — writes trap |

The table is expected to grow; its *shape* is the point. Every entry has the same three fields: what the standard leaves open, what we fix, and where the fix is used. An entry whose third field is empty is a choice nobody needed — delete it rather than carry it.

Measuring the rows also surfaced behaviours that are **not** choices, because the standard does not offer them: `ebreak` has no breakpoint-exception path, `ecall` writes the instruction word into `mtval` where the standard says zero, and no access fault is reachable at all — the core's bus bridges tie their error inputs to zero. Those are *deviations* and live in [01](01-irq-spec.md)'s authored residue — this register only holds picks the standard's freedom licenses.

## Two disciplines

**Choices are S4-axioms, not theorems.** "The choice is acceptable" is unfalsifiable in the same sense as S3's fidelity — the standard blesses the whole family, and picking is legislative. What *is* checkable: that the RTL agrees with the pick (an L5 lemma per entry, and for the measurable rows a [config-record](../tools/config-record.py) extension *now*), and that no lemma silently depends on an unrecorded pick (reviewable by grepping proofs for appeals to behaviour not derivable from Sail ⊕ S3 ⊕ this table).

**Choices flow down, never up.** A pick is made here and consumed by L5/L7; an L5 proof discovering it needs a behaviour fixed must *stop and file the entry*, not embed the assumption. The register is what makes "the spec" a single referent across three layers.

## Relation to L7's clauses

L7's operating-conditions clause (out-of-envelope configuration → X-flood) and boundary decisions are the *system-level* analogue of this file — same S4 character, different layer's objects. Keep them separate: this register fixes meanings of *architectural* behaviours; L7's fixes the domain of the system claim.

## Obligations

1. The measurable rows carry their RTL-extracted values (pinned by [`check-l6.py`](../tools/check-l6.py)); what remains is adjudicating the flagged readbacks (C5's reserved-mode WARL question) and the standing review discipline.
2. The per-entry agreement lemmas, handed to L5/03.
3. The grep-shaped audit: no proof appeals to un-registered behaviour.

## Effort

Days to seed; the cost is the discipline, not the writing — and the payoff is that mid-proof stalls become filing operations.
