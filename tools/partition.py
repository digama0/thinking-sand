#!/usr/bin/env python3
"""partition.py — the L6/03 encoding partition, generated and CHECKED.

Two independent descriptions of "legal instruction word" are computed and
compared exactly:

  spec side     the (mask, match) patterns of the configuration record's ISA
                subset — RV32I + Zicsr + fence/fence.i + ecall/ebreak/mret/wfi —
                hand-tabulated from the RISC-V specification's encoding tables
  decoder side  the (mask, match) cubes extracted from the SHIPPED decoder's
                legality expression (decode_LEGAL_INSTRUCTION in the generated
                Verilog) — the union the hardware actually accepts

Exact set comparison over all 2^32 words via a small BDD. Differences are
reported as cubes with example words: `spec-only` cubes would be spec-legal
words the hardware traps (refinement-breaking in one direction); `decoder-only`
cubes are words the hardware ACCEPTS beyond the spec — reserved encodings that
execute as something instead of trapping.

Usage: partition.py            (prints the partition and the diff)
"""
import re
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VEX = ROOT / "data/mgmt/VexRiscv_MinDebugCache.v"

# --- the spec side: RV32I + Zicsr + privileged bits, per the config record ---
# (mask, match, name); masks/matches per the RISC-V unprivileged & privileged
# encoding tables (riscv-opcodes conventions).
R = 0xFE00707F   # funct7 | funct3 | opcode
I = 0x0000707F   # funct3 | opcode
U = 0x0000007F   # opcode
ALL = 0xFFFFFFFF

SPEC = [
    (U, 0x37, "lui"), (U, 0x17, "auipc"), (U, 0x6F, "jal"),
    (I, 0x67, "jalr"),
    (I, 0x63, "beq"), (I, 0x1063, "bne"), (I, 0x4063, "blt"),
    (I, 0x5063, "bge"), (I, 0x6063, "bltu"), (I, 0x7063, "bgeu"),
    (I, 0x03, "lb"), (I, 0x1003, "lh"), (I, 0x2003, "lw"),
    (I, 0x4003, "lbu"), (I, 0x5003, "lhu"),
    (I, 0x23, "sb"), (I, 0x1023, "sh"), (I, 0x2023, "sw"),
    (I, 0x13, "addi"), (I, 0x2013, "slti"), (I, 0x3013, "sltiu"),
    (I, 0x4013, "xori"), (I, 0x6013, "ori"), (I, 0x7013, "andi"),
    (R, 0x1013, "slli"), (R, 0x5013, "srli"), (R, 0x40005013, "srai"),
    (R, 0x33, "add"), (R, 0x40000033, "sub"), (R, 0x1033, "sll"),
    (R, 0x2033, "slt"), (R, 0x3033, "sltu"), (R, 0x4033, "xor"),
    (R, 0x5033, "srl"), (R, 0x40005033, "sra"), (R, 0x6033, "or"),
    (R, 0x7033, "and"),
    (I, 0x0F, "fence"), (I, 0x100F, "fence.i"),
    (ALL, 0x73, "ecall"), (ALL, 0x100073, "ebreak"),
    (ALL, 0x30200073, "mret"), (ALL, 0x10500073, "wfi"),
    (I, 0x1073, "csrrw"), (I, 0x2073, "csrrs"), (I, 0x3073, "csrrc"),
    (I, 0x5073, "csrrwi"), (I, 0x6073, "csrrsi"), (I, 0x7073, "csrrci"),
]


# --- the official side: riscv-opcodes' pinned extension files ----------------
OPCODES = ROOT / "data/opcodes"
OPCODE_FILES = ("rv_i", "rv32_i", "rv_zifencei", "rv_zicsr", "rv_system", "rv_s")


def opcodes_spec():
    """Parse the pinned riscv-opcodes extension files into name -> (mask, match).

    Line format: `name arg... hi..lo=val ...`; constraint tokens fix bits, named
    args are variable fields. `$pseudo_op parent name ...` lines carry the RV32
    shift variants (slli/srli/srai as refinements of the rv64 encodings); later
    files override earlier ones, so rv32_i's shifts win over any generic entry.
    """
    out = {}
    for fname in OPCODE_FILES:
        for line in (OPCODES / fname).read_text().splitlines():
            toks = line.split()
            if not toks or toks[0].startswith("#"):
                continue
            if toks[0] == "$pseudo_op":
                # assembler shorthands reuse real names (`jal offset` = jal x1);
                # a pseudo may FILL a name (rv32_i's shifts) but never override
                name, toks = toks[2], toks[3:]
                if name in out:
                    continue
            elif toks[0].startswith("$"):
                continue
            else:
                name, toks = toks[0], toks[1:]
            mask = match = 0
            for t in toks:
                m = re.fullmatch(r"(\d+)(?:\.\.(\d+))?=(0x[0-9a-fA-F]+|\d+)", t)
                if not m:
                    continue
                hi, lo = int(m.group(1)), int(m.group(2) or m.group(1))
                width = hi - lo + 1
                mask |= ((1 << width) - 1) << lo
                match |= (int(m.group(3), 0) & ((1 << width) - 1)) << lo
            out[name] = (mask, match)
    return out


def spec_vs_opcodes():
    """Diff SPEC's hand-tabulated patterns against the official tables.
    Returns (mismatches, missing); both empty means the spec side is validated."""
    official = opcodes_spec()
    mismatches, missing = [], []
    for mask, match, name in SPEC:
        if name not in official:
            missing.append(name)
        elif official[name] != (mask, match):
            om, ov = official[name]
            mismatches.append(f"{name}: ours ({mask:08x},{match:08x}) "
                              f"official ({om:08x},{ov:08x})")
    return mismatches, missing


# --- the decoder side: extract the legality cubes from the generated Verilog --
def decoder_cubes():
    txt = VEX.read_text(errors="replace")
    consts = {}
    for name, val in re.findall(
            r"assign (_zz_decode_LEGAL_INSTRUCTION(?:_\d+)?) = 32'h([0-9a-f]+);", txt):
        consts[name] = int(val, 16)
    # every equality comparison feeding the legality OR
    body = "".join(re.findall(
        r"assign (?:decode_LEGAL_INSTRUCTION|_zz_decode_LEGAL_INSTRUCTION(?:_\d+)?) = .*?;",
        txt, re.S))
    cubes = []
    for mask, match in re.findall(
            r"\(decode_INSTRUCTION & (32'h[0-9a-f]+|_zz_decode_LEGAL_INSTRUCTION(?:_\d+)?)\)\s*==\s*"
            r"(32'h[0-9a-f]+|_zz_decode_LEGAL_INSTRUCTION(?:_\d+)?)", body):
        def val(x):
            return int(x[4:], 16) if x.startswith("32'h") else consts[x]
        cubes.append((val(mask), val(match)))
    # comparisons written as (_zz_N == _zz_M) where _zz_N = (INSTRUCTION & const)
    for lhs, rhs in re.findall(
            r"\((_zz_decode_LEGAL_INSTRUCTION(?:_\d+)?) == (_zz_decode_LEGAL_INSTRUCTION(?:_\d+)?)\)",
            body):
        m = re.search(r"assign " + lhs + r" = \(decode_INSTRUCTION & 32'h([0-9a-f]+)\);", txt)
        if m and rhs in consts:
            cubes.append((int(m.group(1), 16), consts[rhs]))
    return sorted(set(cubes))


# --- exact set algebra over 2^32 via a tiny hash-consed BDD -------------------
# nodes: 0, 1, or (var, lo, hi) with var in 31..0 (MSB first)
_nodes = {}


def mk(var, lo, hi):
    if lo == hi:
        return lo
    key = (var, lo, hi)
    if key not in _nodes:
        _nodes[key] = key
    return _nodes[key]


def cube_bdd(mask, match, var=31):
    if var < 0:
        return 1
    rest = cube_bdd(mask, match, var - 1)
    if not (mask >> var) & 1:
        return mk(var, rest, rest)
    if (match >> var) & 1:
        return mk(var, 0, rest)
    return mk(var, rest, 0)


@lru_cache(maxsize=None)
def bdd_or(a, b):
    if a == 1 or b == 1:
        return 1
    if a == 0:
        return b
    if b == 0:
        return a
    (va, la, ha) = a
    (vb, lb, hb) = b
    if va == vb:
        return mk(va, bdd_or(la, lb), bdd_or(ha, hb))
    if va > vb:
        return mk(va, bdd_or(la, b), bdd_or(ha, b))
    return mk(vb, bdd_or(a, lb), bdd_or(a, hb))


@lru_cache(maxsize=None)
def bdd_andnot(a, b):   # a ∧ ¬b
    if a == 0 or b == 1:
        return 0
    if b == 0:
        return a
    if a == 1:
        (vb, lb, hb) = b
        return mk(vb, bdd_andnot(1, lb), bdd_andnot(1, hb))
    (va, la, ha) = a
    (vb, lb, hb) = b
    if va == vb:
        return mk(va, bdd_andnot(la, lb), bdd_andnot(ha, hb))
    if va > vb:
        return mk(va, bdd_andnot(la, b), bdd_andnot(ha, b))
    return mk(vb, bdd_andnot(a, lb), bdd_andnot(a, hb))


def union(cubes):
    r = 0
    for mask, match in cubes:
        r = bdd_or(r, cube_bdd(mask, match))
    return r


def paths(bdd, prefix=None, var=31):
    """Enumerate the 1-paths as (mask, match) cubes."""
    if prefix is None:
        prefix = (0, 0)
    if bdd == 0:
        return
    if bdd == 1:
        yield prefix
        return
    (v, lo, hi) = bdd
    for skip in range(var, v, -1):
        pass  # skipped vars are don't-cares: nothing to add to mask
    m, val = prefix
    yield from paths(lo, (m | (1 << v), val), v - 1)
    yield from paths(hi, (m | (1 << v), val | (1 << v)), v - 1)


def count(bdd, var=32):
    """Number of satisfying words."""
    if bdd == 0:
        return 0
    if bdd == 1:
        return 1 << var
    (v, lo, hi) = bdd
    return (count(lo, v) + count(hi, v)) << (var - 1 - v)


def name_word(w):
    for mask, match, name in SPEC:
        if (w & mask) == match:
            return name
    return "?"


def main():
    dec = decoder_cubes()
    spec_bdd = union([(m, v) for m, v, _ in SPEC])
    dec_bdd = union(dec)
    only_spec = bdd_andnot(spec_bdd, dec_bdd)
    only_dec = bdd_andnot(dec_bdd, spec_bdd)

    print(f"# The encoding partition, generated and checked\n")
    print(f"spec side    : {len(SPEC)} instruction patterns "
          f"({count(spec_bdd):,} legal words)")
    print(f"decoder side : {len(dec)} extracted legality cubes "
          f"({count(dec_bdd):,} accepted words)")
    print(f"spec-only (spec-legal, hardware would trap) : {count(only_spec):,} words")
    for m, v in paths(only_spec):
        print(f"   mask {m:08x} match {v:08x}  e.g. {v:08x} = {name_word(v)}")
    print(f"decoder-only (accepted beyond spec)         : {count(only_dec):,} words")
    fam = {}
    for m, v in paths(only_dec):
        free = 32 - bin(m).count("1")
        key = (v & 0x7F, (v >> 12) & 7)
        fam[key] = fam.get(key, 0) + (1 << free)
    for (op, f3), n in sorted(fam.items(), key=lambda kv: -kv[1]):
        print(f"   opcode {op:07b} funct3 {f3:03b} : {n:>12,} words")


if __name__ == "__main__":
    main()
