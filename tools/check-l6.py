#!/usr/bin/env python3
"""check-l6 — L6 (the ISA specification): obligations as an executable scoreboard.

Re-anchored to the Chipyard target. Implemented: the subset-scope check (the
elaboration's ISA string against the partition scope the book states). The
partition itself, the Sail import, and the compliance run are the layer's
pending programme — the previous target's decoder-extraction results do not
carry over and are not claimed.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer, PASS, FAIL, FINDING, DTS, RTL_SRC, need

L = Layer("L6", "the ISA specification")

BOOK_ISA = "rv32imaczicsr_zifencei_zihpm_xrocket"


@L.check("isa-scope", "the elaboration's ISA string fixes the partition scope", doc="src/L6-isa/00-sail-base.md")
def _(ctx):
    if need(DTS):
        return FINDING, "device tree absent (regenerate: tools/build-rocket.sh)"
    m = re.search(r'riscv,isa\s*=\s*"([^"]+)"', DTS.read_text(errors="replace"))
    if not m:
        return FAIL, "no riscv,isa in the dts"
    if m.group(1) != BOOK_ISA:
        return FAIL, f"ISA drift: {m.group(1)!r} vs the book's {BOOK_ISA!r} — L6's scope moved"
    return PASS, (f"{m.group(1)} — base + M/A/C + Zicsr/Zifencei/Zihpm, with the trailing x marking "
                  f"the custom fragment (S3's scope). The import cut and both sweep widths follow from this string")


@L.check("xrocket-surface", "the custom fragment's structural surface in the emitted core", doc="src/L6-isa/01-irq-spec.md")
def _(ctx):
    if need(RTL_SRC):
        return FINDING, "RTL cone absent (regenerate: tools/build-rocket.sh)"
    csr = RTL_SRC / "CSRFile.sv"
    if not csr.exists():
        return FINDING, "CSRFile.sv absent — the CSR surface extraction needs the emitted core"
    txt = csr.read_text(errors="replace")
    # 12-bit CSR addresses appear as decode literals; the custom space is 0x7c0-0x7ff (and 0xbc0.., 0xfc0..)
    lits = set(re.findall(r"12'h([0-9a-fA-F]{1,3})\b", txt))
    custom = sorted(int(h, 16) for h in lits if 0x7c0 <= int(h, 16) <= 0x7ff)
    if custom:
        return FINDING, (f"custom-CSR decode literals in CSRFile: {[hex(a) for a in custom]} — the xrocket "
                         f"enumeration's seed (L6/01 obligation 1); each needs its authored row")
    return FINDING, ("no 0x7c0–0x7ff decode literals found by the shallow scan — the xrocket enumeration "
                     "needs the real decoder extraction, not a literal grep (TODO partition)")


L.todo("sail-pin", "import sail-riscv at a pinned commit; record the translation/trust line (S2's ledger)",
       doc="src/L6-isa/00-sail-base.md",
       blocked_on="adding sail-riscv to the fetch script with a pinned SHA (cheap)")
L.todo("compliance", "run the architectural compliance suite against the imported model",
       doc="src/L6-isa/00-sail-base.md", blocked_on="sail-pin + the riscv-arch-test harness")
L.todo("spec-pin", "the spec patterns from riscv-opcodes at a pinned commit, both widths",
       doc="src/L6-isa/03-coverage.md",
       blocked_on="regenerating the pattern tables for the full extension set (I/M/A/C + Zicsr/Zifencei)")
L.todo("partition", "the encoding partition vs the generated decoder's legal set",
       doc="src/L6-isa/03-coverage.md",
       blocked_on="decoder legality-cube extraction from the emitted Rocket decode (yosys-based)")
L.todo("c-register", "the measurable choice-register rows extracted from the core",
       doc="src/L6-isa/02-underspecification.md",
       blocked_on="the C2–C8 extractions (trap behaviour needs simulation or careful RTL reading)")
L.todo("ub-free-image", "a real boot image contains no spec-UB instruction word",
       doc="src/L6-isa/03-coverage.md", blocked_on="partition; then per-image, mechanical")
L.extern("S3-fidelity", "the authored residue is what was intended",
         doc="axioms.md", note="unfalsifiable; anchored by generator source and ecosystem software — never checked")
L.extern("S4-choices", "the recorded choices are acceptable readings of the standard",
         doc="axioms.md", note="legislative by nature; what IS checkable (RTL agrees with each pick) lands in L5's lemmas")

if __name__ == "__main__":
    sys.exit(L.main())
