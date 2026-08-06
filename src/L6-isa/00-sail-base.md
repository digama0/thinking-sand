# L6/00 — RISC-V's structure, and its Sail formalisation

## Background

An **ISA** — instruction set architecture — is the contract between hardware and software: the complete list of instructions a processor executes, what state they act on (registers, the program counter, memory), and exactly what each one does to that state. It is the one interface in computing with different vendors on each side — compilers target it, processors implement it, and neither party ever sees the other's internals. RISC-V, the ISA of this project, is distinctive in being an *open standard*: its specification documents are public, governed by a nonprofit, and implementable by anyone without a license — which is why open-source cores like Rocket can exist at all.

For most of computing history, ISAs were specified in English. An instruction's behaviour would be given as a page of prose plus a register-transfer sketch, and the thousands of edge-case questions (what does a shift by 32 do? what happens to the upper bits? in what order do a trap and a pending interrupt resolve?) were settled by tribal knowledge, reference implementations, and vendor errata. A refinement proof cannot consume prose. It needs the ISA as a mathematical object — a **transition system**: a set of states and a step relation, in which "execute one instruction" is a defined function of the current state. Producing that object by hand from the manual would itself be a large, error-prone authoring job, and any mistakes would be *specification* errors — the kind no downstream proof can catch, since the proof would faithfully verify the processor against the wrong contract.

This is what **Sail** exists to fix. Sail is a programming language purpose-built for writing ISA specifications: a spec written in it is precise (every bitfield, every corner case forced to a decision), *executable* (you can run programs against the spec and compare with real hardware), and mechanically translatable into the input languages of proof assistants. The RISC-V organisation took the further step that matters most here: it adopted a Sail model, `sail-riscv`, as the standard's **official formal specification** — the "golden model" against which conformance is judged, with new extensions required to extend it for ratification. (The ratified prose manuals remain the normative documents; the model is the standard's own executable reading of them.) This chapter's job is to import that model, pin down what "import" means (which translation, which version, what is trusted about it), and carve out exactly the fragment this small core implements.

One structural fact to hold on to before the details: a RISC-V instruction is a 32-bit word, and the specification of the ISA has two separable halves — the **encoding** (which bit patterns denote which instructions, with operand fields at fixed positions) and the **semantics** (what each instruction does). Keeping the halves separate is what makes it possible to say, later, that the compressed extension adds new encodings but no new semantics, and that the decoder and the executor generate independent proof obligations.

## Statement

Import `Sail-RV32(config)` — the base ISA *and* the machine-mode subset of the privileged architecture — as the received core of `ISA`. First, fix what the object being imported *is*, since the standard's structure is what makes the import modular and the subsetting principled.

## How RISC-V is structured

**Two volumes.** The *unprivileged* spec (Volume I): the instructions a program sees. The *privileged* spec (Volume II): machine/supervisor modes, CSRs, traps, virtual memory. This core implements Volume I's base and extensions plus **Volume II's machine-and-user-mode fragment** — the trap/interrupt CSRs, PMP, and their semantics, declared by the elaboration and to be confirmed by the configuration record — and nothing above it: no supervisor mode, no virtual memory. So the import cuts *inside* Volume II, at the machine-mode boundary, and the subset must be carved by CSR rather than by volume.

**Base + extension letters.** A base ISA (`RV32I`: ~40 instructions — integer ops, loads/stores, branches, jumps) plus optional extensions, each a letter with its own ratification: `M` (multiply/divide), `C` (compressed 16-bit re-encodings), `Zicsr`/`Zicntr` (CSR access / counters), and many more (`A`, `F`, `D`, `V`…). The letters are the configuration vocabulary, and this core's string — declared by the elaboration itself — is **`rv32imac_zicsr_zifencei_zihpm_xrocket`**: the base plus multiply/divide, atomics, and the compressed re-encodings, plus CSR access, fence.i, and the performance counters — with the trailing `x` marking the custom fragment that [01](01-irq-spec.md) owns. Every *absent* letter (F, D, V, S-mode…) is spec the import does not carry and the coverage sweep must instead prove *traps*.

**The encoding space.** 32-bit words with `[1:0] = 11` (the other three values are the compressed quadrants); major opcode in `[6:2]`; then six **formats** fixing where operands live:

```
R:  funct7 | rs2 | rs1 | funct3 | rd | opcode      register-register
I:  imm[11:0]    | rs1 | funct3 | rd | opcode      register-immediate, loads
S/B:  imm split around rs2|rs1, funct3, imm|opcode  stores / branches
U/J:  imm[31:12]              | rd | opcode         lui, auipc / jal
```

The immediates in S/B/J are bit-scrambled — deliberately, so that register fields sit at fixed positions and the sign bit is always bit 31: the standard is shaped for cheap decoders, and the scrambling is spec content the decode lemmas must get right. The space reserves **custom-0/custom-1** major opcodes for vendor instructions; the shipped core uses none of them — its custom behaviour lives entirely in **CSR address space** (the two external-interrupt array registers, [01](01-irq-spec.md)), which is the tamer kind of custom: no new encodings, no new step relation, just two more registers with authored semantics.

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

`sail-riscv` is the standard's **official golden model** — adopted by RISC-V International, with extensions required to extend it for ratification — which makes S2 smaller than it looks: its residue is the model's fidelity to the ratified manuals plus the translation path. Mitigation: run the official architectural compliance suite against the *imported* model (post-translation, in our prover), not against upstream. The Sail→prover translation (which backend, which version, deep vs. shallow, how Sail bitvector primitives map) is conventionally trusted; state it as S2's ledger line and pin it like the toolchain.

**Subset by configuration, not by hand**: the implemented/unimplemented boundary is *derived* from the [configuration record](../tools/config-record.py) and exported to [03](03-coverage.md) — a hand-maintained list would drift. The machine-mode carve is part of the same derivation: exactly the measured CSR set, with reads of absent CSRs (`mscratch`, `misa`, the counters) landing in the trap sweep.

## Deliberately out of scope

The memory model (RVWMO — axiomatic↔operational equivalence plus a multicore RTL refinement, unattempted at any scale), virtual memory, floating point, supervisor mode, and PMP. The shipped core has none of them, and the import cuts at the machine-mode boundary — everything of Volume II above that line stays out.

## Obligations

1. The pinned import with the translation's guarantees written down.
2. The compliance-suite harness against the imported model.
3. The configuration-derived subset boundary.
4. The `addi`/`beq` worked pair as the first end-to-end spec objects — cheap, and they template the rest; a trap-entry/`mret` pair from the machine-mode subset alongside them, since the privileged clauses are new to the import.

## Effort

Weeks to import and pin; the compliance harness is the substantive piece.
