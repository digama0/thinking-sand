# L6/03 — Coverage: the encoding sweep and the cheap bulk

## Statement

The wide, shallow obligations that make `ISA` *total* over the 32-bit word space: every encoding is either implemented (and matched to its Sail clause) or unimplemented (and proven to trap). Skip the second half and the refinement is simply **false** — a claim about all executions cannot ignore the words a program might contain.

## The partition

From L4's configuration record, the word space partitions:

```
implemented    RV32I base  ⊕  M (iff PCPI)  ⊕  C (iff COMPRESSED_ISA)
               ⊕ counters  ⊕  the six custom-0 IRQ instructions (S3)
unimplemented  everything else — including, if C is off, all words with [1:0] ≠ 11
```

Each implemented encoding gets the decode-bijection + execute lemma pair (L5/03, templated by [00](00-sail-base.md)'s `addi`/`beq` example). Each unimplemented encoding gets **traps-correctly**: decode raises no flag, the FSM reaches `trap` (`CATCH_ILLINSN`), matching the spec's illegal-instruction step per choice C3.

## Why this is the model case of cheap entropy

~40 implemented patterns and the unimplemented complement: high raw *spec* entropy, **zero invariant entropy** — each obligation is one SAT-shaped query, independent of all others, because L5's invariant cuts every cross-instruction dependency at the fetch boundary. A lot of typing, almost no thinking; the thinking concentrated in S3 ([01](01-irq-spec.md)) and S4 ([02](02-underspecification.md)). Most of L6 has this character, and the layer's effort estimate is dominated by it.

The sweep is also where **encoding-space structure pays**: the partition is decided by major opcode and format fields, so the unimplemented half is a small set of *regions*, not 2³² cases — the custom-0 occupancy by the IRQ instructions being the one subtlety (a standard-RISC-V-only reading would call them illegal; `ISA = Sail ⊕ S3` calls them implemented; the sweep must use the ⊕).

## The PCPI timeout edge

One coverage case is neither decode-time nor static: an M-extension word with `ENABLE_PCPI` variants live but *no unit claiming it* resolves to the illegal trap only after the PCPI timeout (L5/04's nobody-claims clause). Coverage must treat "implemented" as configuration-*and*-topology dependent: the letter M is implemented iff the claiming unit is instantiated, and the sweep's partition follows the instantiated design, not the parameter alone.

## Obligations

1. Generate the partition from the configuration record; publish it as the single source both L5/03 and the compliance harness consume.
2. The traps-correctly sweep, mechanised (regions, not words).
3. The custom-0 and PCPI-timeout edges as explicit cases with their own lemmas.

## Effort

Months of mechanised typing once L5/03's harness exists; near-zero marginal thought per encoding — by design, and worth preserving: any coverage case that starts requiring thought belongs in [01](01-irq-spec.md) or [02](02-underspecification.md) instead.
