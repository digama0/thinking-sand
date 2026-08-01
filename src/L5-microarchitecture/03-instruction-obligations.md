# L5/03 — The per-instruction obligations

## Background

With the invariant ([02](02-invariant.md)) holding the machine's global coherence, what remains is to check each instruction individually: that the hardware's handling of `add` matches the spec's `add`, the hardware's `beq` matches the spec's `beq`, and so on through the instruction set. The technique that discharges each one is **symbolic execution**: instead of running the hardware on particular values, run it on *variables*. Start from a state where the registers hold symbols `x` and `y` rather than numbers, walk the FSM through the three-or-four-state path this instruction takes, and the final state comes out as a formula — "register `rd` now holds `x + y`, the pc advanced by 4." The obligation is then that this formula equals what the Sail spec clause computes, which is a question about fixed-width integers (**bitvectors**, in the field's vocabulary) that **SMT solvers** — SAT solvers extended with built-in theories of arithmetic — answer mechanically. One symbolic run covers all 2⁶⁴ concrete operand pairs at once; that is the entire trick.

The reason this chapter can promise "a lot of lemmas, almost no thinking" is a structural dividend from the invariant: its clauses cut every dependency *between* instructions at the fetch boundary. Whatever instruction executed previously, the invariant says the machine re-enters fetch in a clean, fully-described state — so each per-instruction lemma starts from the same characterised starting line, independent of all the others, and the set of lemmas is embarrassingly parallel. The cost structure follows: build the symbolic-execution harness once (the real expense), then each additional instruction is a template instantiation. Only where an instruction contains an internal *loop* — the iterative shifter, which shifts by four per cycle rather than in one step — does per-case thought reappear, in the form of a small **loop invariant**: a statement like "the accumulator holds the input shifted by (requested − remaining) places," preserved each iteration, the classic Floyd-Hoare pattern in miniature.

## Statement

The wide-shallow quantification: for each instruction of the shipped configuration, the commit-case square of [01](01-refinement.md) — from a state satisfying `I` with this instruction latched, the FSM path's cumulative effect equals the Sail step. High spec entropy, near-zero invariant entropy: a lot of lemmas, almost no thinking, and most of it plausibly automatable per instruction.

## The obligation classes

**Decode** — the bridge between L6's Sail decoder and [00](00-microarchitecture.md)'s ~50 one-hot flags:

```
∀ word w:  the latched flag set after decode(w)  =  one-hot image of Sail-decode(w)
           (exhaustive: some flag or the illegal-trap; exclusive: at most one class)
```

Per-encoding, SAT-shaped, ~40 patterns plus the **unimplemented-encoding sweep**: every word the configuration does not implement must set no flag and reach `trap` (`CATCH_ILLINSN`) — L6's "traps correctly" obligation landing here as the picorv32 half. Wide, mechanical, unskippable: the refinement is simply false without it.

**ALU and comparisons** — word-level lemmas per operator: the shared adder's output under the `exec`-state mux equals the Sail arithmetic (bitvector identities, discharged by SMT; the *netlist* structure of the adder was L3/05's business and never appears here). Branches: comparator result drives the pc update exactly as Sail's branch semantics.

**Shifts** — the one place [02](02-invariant.md)'s clause 3 has real content: `TWO_STAGE_SHIFT`'s iterative loop (by 4, then 1) needs the loop invariant `acc = x shifted by (k − counter)` with the measure ticking; the lemma composes the loop to the Sail shift. If the shipped config has `BARREL_SHIFTER`, this degenerates to a mux-tree bitvector lemma.

**Loads/stores** — the densest class: address generation (adder reuse), `wstrb` byte-lane encoding vs. the Sail memory access width, sign/zero extension on `ldmem` writeback, and `CATCH_MISALIGN`'s trap vs. the S4 choice for misaligned access (L6 must *pick* — trap, as picorv32 does — and record it; the lemma is against the pick). The bus's role is contract-abstracted: the lemma says "the value the contract returns for this address," never what RAM did.

**Compressed** (`COMPRESSED_ISA`, config-dependent) — if on: the 16-bit decoder and, more substantively, the fetch alignment machinery (instructions straddling word boundaries) which adds latched-partial-word state to clause 3 and to ρ's reset story. If off: the sweep above must show 16-bit-aligned encodings trap as the config demands. Either way the configuration record decides *before* budgeting.

**Counters** (`ENABLE_COUNTERS*`) — `rdcycle/rdinstret`: the lemma ties the counter registers to the *spec's* cycle/retirement counts, which is the one place the ISA-visible state references stuttering structure — instret increments exactly at commit points, tying directly to α's retirement definition.

## Why this class is cheap per element

Each lemma is: symbolic execution of a ≤5-state FSM path from an `I`-state, compared against one Sail clause — bounded, automatable, independent of every other lemma. This is L6's "decode is the model case of entropy that costs nothing" made concrete: the cost is proportional to the *number* of instructions, not to any interaction between them, because [02](02-invariant.md)'s clauses cut every cross-instruction dependency at the fetch boundary.

## Obligations

1. The decode bijection + unimplemented sweep (gated on the configuration record and L6's Sail import).
2. Per-class lemma templates: one worked instance each (an ALU op, a shift, a load), then mechanise the remainder.
3. The counter/α consistency lemma — small, but it is the only place spec state mentions the abstraction map, so get it right early.

## Effort

Months, dominated by building the symbolic-execution harness once; per-instruction marginal cost should approach mechanical. If it does not, something is wrong with the harness, not the instructions.
