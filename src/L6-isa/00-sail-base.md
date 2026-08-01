# L6/00 — RISC-V's structure, and its Sail formalisation

## Statement

Import `Sail-RV32I(config)` as the received core of `ISA` — and first, fix what the object being imported *is*, since the standard's structure is what makes the import modular and the subsetting principled.

## How RISC-V is structured

**Two volumes.** The *unprivileged* spec (Volume I): the instructions a program sees. The *privileged* spec (Volume II): machine/supervisor modes, CSRs, traps, virtual memory. **picorv32 implements only a fragment of Volume I** — no privilege levels, no standard trap machinery; the custom IRQ scheme ([01](01-irq-spec.md)) occupies the place Volume II would.

**Base + extension letters.** A base ISA (`RV32I`: ~40 instructions — integer ops, loads/stores, branches, jumps) plus optional extensions, each a letter with its own ratification: `M` (8 instructions: multiply/divide), `C` (compressed 16-bit re-encodings), `Zicsr`/`Zicntr` (CSR access / counters), and many more (`A`, `F`, `D`, `V`… — all absent here). The letters are the configuration vocabulary: L4's record picks out exactly `RV32I` ⊕ (M iff PCPI live) ⊕ (C iff `COMPRESSED_ISA`) ⊕ counters. Crucially **C is a decode-layer extension**: each 16-bit encoding *expands to* a base instruction — new syntax, no new semantics — so its spec cost is a second decoder, not a second execution model.

**The encoding space.** 32-bit words with `[1:0] = 11` (the other three values are the compressed quadrants); major opcode in `[6:2]`; then six **formats** fixing where operands live:

```
R:  funct7 | rs2 | rs1 | funct3 | rd | opcode      register-register
I:  imm[11:0]    | rs1 | funct3 | rd | opcode      register-immediate, loads
S/B:  imm split around rs2|rs1, funct3, imm|opcode  stores / branches
U/J:  imm[31:12]              | rd | opcode         lui, auipc / jal
```

The immediates in S/B/J are bit-scrambled — deliberately, so that register fields sit at fixed positions and the sign bit is always bit 31: the standard is shaped for cheap decoders, and the scrambling is spec content the decode lemmas must get right. The space reserves **custom-0/custom-1** major opcodes for vendor instructions — which is where picorv32's six IRQ instructions live, so the custom extension occupies sanctioned space rather than colliding with future standard extensions.

## How Sail specifies it — a worked example

`sail-riscv` organises each instruction as three clauses: an **AST constructor**, a bidirectional **encode/decode mapping**, and an **execute** function clause. For `addi` (I-format, major opcode OP-IMM, funct3 000), lightly abridged:

```sail
union clause ast = ITYPE : (bits(12), regidx, regidx, iop)

mapping clause encdec =
  ITYPE(imm, rs1, rd, RISCV_ADDI) <-> imm @ rs1 @ 0b000 @ rd @ 0b0010011

function clause execute (ITYPE(imm, rs1, rd, RISCV_ADDI)) = {
  let result : xlenbits = X(rs1) + sign_extend(imm);
  X(rd) = result;
  RETIRE_SUCCESS
}
```

Three properties of this shape matter to the project. The `encdec` mapping is *bidirectional*, so decode totality/injectivity are properties of the clause set — exactly what L5/03's decode bijection is checked against. `execute` is a state transformer over `X` (the register file, with `X(0)` hard-wired zero) and `PC` — the transition system L5's α lands in. And `RETIRE_SUCCESS` vs. trap outcomes is the retirement event RVFI observes — the three-way agreement (Sail retirement, RVFI, α's commit points) is one object seen three ways.

A branch (`beq`, B-format) adds the two remaining ingredients: the scrambled immediate reassembled in `encdec`, and a *conditional* PC update in `execute` — together with `addi` it exercises every structural feature the other ~40 instructions repeat.

## Why the base is real, and the import path

`sail-riscv` is the **officially ratified** model — normatively, the model *is* the standard, which makes S2 smaller than it looks: its residue is "ratification captured community intent" plus the translation path. Mitigation: run the official architectural compliance suite against the *imported* model (post-translation, in our prover), not against upstream. The Sail→prover translation (which backend, which version, deep vs. shallow, how Sail bitvector primitives map) is conventionally trusted; state it as S2's ledger line and pin it like the toolchain.

**Subset by configuration, not by hand**: the implemented/unimplemented boundary is *derived* from L4's record and exported to [03](03-coverage.md) — a hand-maintained list would drift.

## Deliberately out of scope

The memory model (RVWMO — axiomatic↔operational equivalence plus a multicore RTL refinement, unattempted at any scale), virtual memory, floating point, and all of Volume II. picorv32 has none of them — a large part of why it was chosen — and the import must cut at the unprivileged boundary, with the counters as the only CSR-shaped survivors.

## Obligations

1. The pinned import with the translation's guarantees written down.
2. The compliance-suite harness against the imported model.
3. The configuration-derived subset boundary.
4. The `addi`/`beq` worked pair as the first end-to-end spec objects — cheap, and they template the rest.

## Effort

Weeks to import and pin; the compliance harness is the substantive piece.
