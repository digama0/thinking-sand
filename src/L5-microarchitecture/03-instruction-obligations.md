# L5/03 — The per-instruction obligations

## Background

With the invariant ([02](02-invariant.md)) holding the machine's global coherence, what remains is to check each instruction individually: that the hardware's handling of `add` matches the spec's `add`, the hardware's `beq` matches the spec's `beq`, and so on through the instruction set. The technique that discharges each one is **symbolic execution**: instead of running the hardware on particular values, run it on *variables*. Start from an invariant state with the instruction at a known station and symbols in the registers, walk the machine to the instruction's retirement, and the final state comes out as a formula — "register `rd` now holds `x + y`, the committed pc advanced by 4." The obligation is then that this formula equals what the Sail clause computes, which is a question about fixed-width integers (**bitvectors**) that **SMT solvers** — SAT solvers extended with built-in theories of arithmetic — answer mechanically. One symbolic run covers all 2⁶⁴ concrete operand pairs at once; that is the entire trick.

The reason this chapter can promise "a lot of lemmas, almost no thinking" is a structural dividend from the invariant: the interlock clauses cut every dependency *between* instructions at the register file. Whatever ran previously, an instruction reads its sources only when no in-flight writer targets them — so each per-instruction lemma starts from the same characterised conditions, independent of its neighbours, and the set of lemmas is embarrassingly parallel. The cost structure follows: build the symbolic-execution harness once (the real expense), then each additional instruction is a template instantiation. Per-case thought reappears only where an instruction contains an internal *loop* — the iterative shifter — in the form of a small **loop invariant**, the classic Floyd–Hoare pattern in miniature.

## Statement

The wide-shallow quantification: for each instruction of the [configuration record](../tools/config-record.py), the retirement case of [01](01-refinement.md)'s cell — from an invariant state with this instruction in flight, the retiring effect equals the Sail step. High spec entropy, near-zero invariant entropy: a lot of lemmas, almost no thinking, and most of it plausibly automatable per instruction.

## The obligation classes

**Decode** — the bridge between L6's Sail decoder and the generated decoder of the [shipped core](https://github.com/efabless/caravel_mgmt_soc_litex/blob/503eda0790085712ffef7f4ad8934c7daed3237f/verilog/rtl/VexRiscv_MinDebugCache.v):

```
∀ word w:  the control bundle produced for w  =  image of Sail-decode(w)
           (exhaustive: every word decodes or raises the illegal trap;
            exclusive: one instruction class per word)
```

Per-encoding, SAT-shaped, ~40 base patterns plus the **trap sweep**: every word the decoder *rejects* must reach the illegal-instruction trap step (all of C, M, A, and the reserved space minus the UB set), and the counter/absent-CSR reads trap at execute. The words in L6/03's **spec-UB set** — reserved encodings the decoder accepts — generate no obligation at all: the spec's havoc step is refined by anything, which is precisely why the UB clause exists.

**ALU and comparisons** — word-level lemmas per operator ([`IntAluPlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/IntAluPlugin.scala), [`SrcPlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/SrcPlugin.scala)): the Execute-stage result equals the Sail arithmetic — bitvector identities, discharged by SMT; the *netlist* structure of the adder was L3/05's business and never appears here. Branches: the comparison drives the redirect exactly as Sail's branch semantics, with the flush obligation carried by the invariant's clause 5.

**Shifts** — the one place [02](02-invariant.md)'s clause 3 has real content: the [`LightShifter`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/ShiftPlugins.scala)'s one-bit-per-cycle loop needs the invariant `acc = x shifted by (k − counter)` with the measure ticking; the lemma composes the loop to the Sail shift.

**Loads/stores** — via [`DBusSimplePlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/DBusSimplePlugin.scala): address generation, byte-lane select and sign/zero extension vs. the Sail memory access, alignment traps per the spec's choice, and the bus's role contract-abstracted — the lemma says "the value the contract returns for this address," never what RAM did.

**CSR instructions** — `csrrw`/`csrrs`/`csrrc` and immediates against each implemented CSR's semantics: the machine-mode registers from the Sail import, and the two [external-interrupt array](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/ExternalInterruptArrayPlugin.scala) CSRs against the residual authored spec ([05](05-interrupts.md)). Reads of the *absent* CSRs (`mscratch`, `misa`, the counters) belong to the trap sweep.

**Fences** — `fence` is a no-op on this single-hart, in-order machine (a lemma, not an assumption); `fence.i` invalidates the two cache lines and refetches — the obligation pairs with the invariant's cache-agreement clause.

## Why this class is cheap per element

Each lemma is: symbolic execution of one instruction's pipeline transit from an `I`-state, compared against one Sail clause — bounded, automatable, independent of every other lemma, with the interlocks supplying the independence. The cost is proportional to the *number* of instructions, not to any interaction between them.

## Obligations

1. The decode equivalence + the unimplemented sweep (gated on the [configuration record](../tools/config-record.py) and L6's Sail import).
2. Per-class lemma templates: one worked instance each (an ALU op, a shift, a load, a CSR op), then mechanise the remainder.
3. The `fence.i` lemma, jointly with the invariant's cache clause.

## Effort

Months, dominated by building the symbolic-execution harness once; per-instruction marginal cost should approach mechanical. If it does not, something is wrong with the harness, not the instructions.
