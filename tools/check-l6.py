#!/usr/bin/env python3
"""check-l6 — L6 (the ISA): obligations as an executable scoreboard.

Specification authoring dominates this layer, so most entries are TODO by
nature of the phase; the checkable fragments (encoding partition, doc-vs-RTL
diffs) are stubbed with their inputs named.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer, PASS, FAIL, FINDING

L = Layer("L6", "the ISA specification")

L.todo("sail-pin", "import sail-riscv at a pinned commit; record the translation/trust line (S2's ledger)",
       doc="src/L6-isa/00-sail-base.md",
       blocked_on="adding sail-riscv to fetch-data.sh with a pinned SHA (a fetch decision, cheap)")
L.todo("compliance", "run the architectural compliance suite against the imported model",
       doc="src/L6-isa/00-sail-base.md",
       blocked_on="sail-pin plus the riscv-arch-test harness")
@L.check("partition", "the encoding partition vs the shipped decoder's legal set",
         doc="src/L6-isa/03-coverage.md")
def _(ctx):
    from checklib import load, DATA, need
    if m := need(DATA / "mgmt/VexRiscv_MinDebugCache.v"):
        return FAIL, f"missing {m} (run tools/fetch-data.sh mgmt)"
    pt = load("partition")
    dec = pt.decoder_cubes()
    spec_bdd = pt.union([(m_, v, ) for m_, v, _ in pt.SPEC])
    dec_bdd = pt.union(dec)
    only_spec = pt.bdd_andnot(spec_bdd, dec_bdd)
    only_dec = pt.bdd_andnot(dec_bdd, spec_bdd)
    fam = {}
    for m_, v in pt.paths(only_dec):
        key = (v & 0x7F, (v >> 12) & 7)
        fam[key] = fam.get(key, 0) + (1 << (32 - bin(m_).count("1")))
    expect_fam = {(0x03, 6): 4194304, (0x13, 5): 65536, (0x13, 1): 32768, (0x73, 0): 1}
    if pt.count(only_spec) != 0 or pt.count(only_dec) != 4292609 or fam != expect_fam:
        return FAIL, (f"partition changed: spec-only {pt.count(only_spec)}, "
                      f"decoder-only {pt.count(only_dec)}, families {fam}")
    return PASS, ("spec-only 0: every RV32I+Zicsr word is accepted. The spec-UB set "
                  "is pinned at 4,292,609 words: all 2^22 words of LOAD funct3=110, "
                  "98,304 reserved shift-immediate variants, and exactly one SYSTEM "
                  "word, sret (0x10200073). The spec assigns these unspecified "
                  "architectural behaviour (L6/03); the layered guarantees below the "
                  "ISA still hold on them - no instruction is a halt-and-catch-fire")
L.todo("s3-draft-diff", "formalise the external-interrupt array from its plugin source, then diff against RTL behaviour",
       doc="src/L6-isa/01-irq-spec.md",
       note="the structural half is done (irqmap.py / L7 irq-map: mask R/W, pending read-only "
            "live view, funnel); the behavioural diff needs the authored draft plus a simulator harness")
@L.check("c-register", "the measurable choice-register rows (C2/C3/C5/C6) extracted from the shipped core",
         doc="src/L6-isa/02-underspecification.md")
def _(ctx):
    from checklib import load, DATA, need
    if m := need(DATA / "mgmt/VexRiscv_MinDebugCache.v"):
        return FAIL, f"missing {m} (run tools/fetch-data.sh mgmt)"
    cr = load("config-record")
    c = cr.choices()
    bad = []
    for row, val in c.items():
        if isinstance(val, dict):
            bad += [f"{row}.{k}" for k, v in val.items() if not v]
        elif not val:
            bad.append(row)
    if bad:
        return FAIL, f"a measured choice-register fact changed: {bad}"
    return FINDING, ("the C-rows are measured: misaligned accesses trap (causes 4/6) with the "
                     "bus command suppressed; illegal instructions trap with cause 2 and "
                     "mtval = the instruction word; mtvec has NO reset value, and its mode "
                     "bits are inert storage - the trap redirect is always {base,00}, so "
                     "vectored mode reads back as written but does not exist. Three "
                     "deviations from the ratified trap semantics: EBREAK has no breakpoint "
                     "exception path at all (debug-halt when a debug session is active, "
                     "otherwise it retires as a NOP); ecall writes the instruction word "
                     "into mtval (the spec says zero); and ALL access faults (causes 1/5/7) "
                     "are unreachable - the core's own Wishbone bridges tie both bus-error "
                     "inputs to zero, discarding the SoC's ERR wiring at the core boundary. "
                     "The complete reachable synchronous trap surface is causes 0/2/4/6/11, "
                     "plus the external interrupt. The deviations go to L6/01's authored "
                     "residue, not the choice register - they are not choices the standard "
                     "offers")
L.extern("S3-fidelity", "the authored residue (external-interrupt array) is what was intended",
         doc="src/axioms.md",
         note="unfalsifiable; anchored by the plugin source, LiteX conventions, and the firmware corpus - never checked")
L.extern("S4-choices", "the recorded choices are acceptable readings of the standard",
         doc="src/axioms.md",
         note="legislative by nature; what IS checkable (RTL agrees with each pick) lands in L5's lemmas")

if __name__ == "__main__":
    sys.exit(L.main())
