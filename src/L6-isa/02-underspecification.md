# L6/02 — The choice register (S4)

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
