#!/usr/bin/env python3
"""check-l6 — L6 (the ISA): obligations as an executable scoreboard.

Specification authoring dominates this layer, so most entries are TODO by
nature of the phase; the checkable fragments (encoding partition, doc-vs-RTL
diffs) are stubbed with their inputs named.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer

L = Layer("L6", "the ISA specification")

L.todo("sail-pin", "import sail-riscv at a pinned commit; record the translation/trust line (S2's ledger)",
       doc="src/L6-isa/00-sail-base.md",
       blocked_on="adding sail-riscv to fetch-data.sh with a pinned SHA (a fetch decision, cheap)")
L.todo("compliance", "run the architectural compliance suite against the imported model",
       doc="src/L6-isa/00-sail-base.md",
       blocked_on="sail-pin plus the riscv-arch-test harness")
L.todo("partition", "generate the encoding + CSR-address partition from the configuration record",
       doc="src/L6-isa/03-coverage.md",
       note="unblocked: the configuration record is measured (RV32I + Zicsr subset, no C/M/A, no counters); the partition generator is checker-shaped work")
L.todo("s3-draft-diff", "formalise the external-interrupt array from its plugin source, then diff against RTL behaviour",
       doc="src/L6-isa/01-irq-spec.md",
       note="the plugin-first half is authoring; the DIFF is checker-shaped once a simulator harness exists")
L.todo("c-register", "populate the choice register C1-C7 with RTL-extracted values (misaligned behaviour, mtvec WARL fields, mtval details)",
       doc="src/L6-isa/02-underspecification.md",
       blocked_on="config-record extensions for the measurable rows (C2/C5/C6); the rest is recording discipline")
L.extern("S3-fidelity", "the authored residue (external-interrupt array) is what was intended",
         doc="src/axioms.md",
         note="unfalsifiable; anchored by the plugin source, LiteX conventions, and the firmware corpus - never checked")
L.extern("S4-choices", "the recorded choices are acceptable readings of the standard",
         doc="src/axioms.md",
         note="legislative by nature; what IS checkable (RTL agrees with each pick) lands in L5's lemmas")

if __name__ == "__main__":
    sys.exit(L.main())
