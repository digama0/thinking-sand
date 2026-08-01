# L6/02 — The choice register (S4)

## Background

A standard written for many implementers cannot pin everything down, and does not want to. If the RISC-V spec dictated the reset value of every register, the handling of every misaligned access, and the priority of every simultaneous event, it would outlaw legitimate design choices and burden every implementation with someone else's decisions. So standards **deliberately underspecify**: "the contents of registers after reset are unspecified"; "a misaligned load may trap, or may be handled"; "pending interrupts are taken eventually." Each such sentence licenses a *family* of behaviours, and any member of the family is *conformant*. This is a feature — for implementers.

For a refinement proof it is a complication with a precise shape. Refinement (`⊑`) says every implementation behaviour is among the spec's allowed behaviours, so spec-side freedom is fine *in principle* — nondeterminism in the spec is exactly how "unspecified" is expressed formally. The problem is practical: a proof about *this* chip constantly needs to know which member of the family it is facing. When an L5 lemma about the trap handler needs to know whether a misaligned load traps, "the standard permits either" is not an answer the proof can use; the proof needs *the* answer for picorv32, and that answer — trap, because the `CATCH_MISALIGN` parameter is set — is not derivable from the standard. It is a **choice**: a decision that narrows the standard's family down to the one behaviour this implementation exhibits.

Choices of this kind are epistemically different from theorems, and that difference is why they get their own register in the axiom ledger (S4). That the RTL *agrees with* a recorded choice is checkable — a lemma. That the choice itself is the right reading of the standard's freedom is not checkable by anything; it is legislative, like an editor resolving an ambiguity. The danger is not making choices — that is unavoidable — but making them *invisibly*: a proof that silently assumes registers reset to zero has narrowed the spec without anyone deciding to, and the narrowing is now load-bearing and unrecorded. Hence the discipline of this file: every choice is written down before it is used, with what the standard left open, what was picked, and which proof consumes it. (One instance of the pattern has a standard name worth knowing: **WARL** fields — "write any, read legal" — register bits where software may write anything and the hardware is free to read back any legal value, the standard's own idiom for per-field underspecification.)

## Statement

Where RISC-V is deliberately underspecified, **conformance is not a statement** — the spec admits many behaviours, and a refinement proof needs *one*. This file is the register of choices: each entry picks a refinement of the standard, records that the pick is a choice, and becomes part of what `ISA` means. Deciding them *before* L5's proof starts is the discipline; discovering them mid-proof converts each into a stall.

## The known entries

| # | underspecified in the standard | the choice (= what picorv32 does, recorded) |
|---|---|---|
| C1 | reset state of general registers | unspecified — and *used*: L4/03's X-matching refines into exactly this nondeterminism (`REGS_INIT_ZERO=0`) |
| C2 | misaligned loads/stores | trap (`CATCH_MISALIGN=1`); the standard permits trapping or handling |
| C3 | illegal/unimplemented encodings | trap (`CATCH_ILLINSN=1`) — feeds [03](03-coverage.md)'s sweep |
| C4 | interrupt timing ("eventually") | taken at the next commit point when unmasked — the S3 spec makes this precise ([01](01-irq-spec.md)) |
| C5 | simultaneous IRQ arbitration | S3-internal choice; record the line-priority order the RTL implements |
| C6 | counter width/rollover behaviour per `ENABLE_COUNTERS64` | per configuration; the 32-bit variant's rollover is a real choice |
| C7 | WARL-style register fields | largely moot (no standard CSR file), but the mask/timer registers have analogous writable-bits questions — record per register |

The table is expected to grow; its *shape* is the point. Every entry has the same three fields: what the standard leaves open, what we fix, and where the fix is used. An entry whose third field is empty is a choice nobody needed — delete it rather than carry it.

## Two disciplines

**Choices are S4-axioms, not theorems.** "The choice is acceptable" is unfalsifiable in the same sense as S3's fidelity — the standard blesses the whole family, and picking is legislative. What *is* checkable: that the RTL agrees with the pick (an L5 lemma per entry), and that no lemma silently depends on an unrecorded pick (reviewable by grepping proofs for appeals to behaviour not derivable from Sail ⊕ S3 ⊕ this table).

**Choices flow down, never up.** A pick is made here and consumed by L5/L7; an L5 proof discovering it needs a behaviour fixed must *stop and file the entry*, not embed the assumption. The register is what makes "the spec" a single referent across three layers.

## Relation to L7's clauses

L7's operating-conditions clause (out-of-envelope configuration → X-flood) and boundary decisions are the *system-level* analogue of this file — same S4 character, different layer's objects. Keep them separate: this register fixes meanings of *architectural* behaviours; L7's fixes the domain of the system claim.

## Obligations

1. Populate C1–C7 with their RTL-extracted values; open the standing review discipline.
2. The per-entry agreement lemmas, handed to L5/03.
3. The grep-shaped audit: no proof appeals to un-registered behaviour.

## Effort

Days to seed; the cost is the discipline, not the writing — and the payoff is that mid-proof stalls become filing operations.
