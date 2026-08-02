#!/usr/bin/env python3
"""check-l7 — L7 (the system): obligations as an executable scoreboard.

The layer's deliverables are definitions and consolidations; the checker-shaped
work is the diffs (docs vs RTL vs generator) and the numeric epoch inequalities,
each stubbed with its missing input named.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer

L = Layer("L7", "the system specification")

L.todo("memmap-diff", "diff the memory map: caravel.py generator vs generated RTL vs documentation",
       doc="src/L7-system/03-memory-map-devices.md",
       blocked_on="fetching caravel_mgmt_soc_litex's caravel.py + mgmt_core.v + the RST docs at pinned SHAs")
L.todo("irq-map", "extract the 6-line IRQ wiring from mgmt_core_wrapper.v and diff against irq.rst",
       doc="src/L7-system/03-memory-map-devices.md",
       note="the wrapper is already fetched; the docs side needs the RST fetch. Half-unblocked.")
L.todo("pad-defaults", "diff gpio_defaults_block values and DM_INIT/OENB_INIT against pinout docs",
       doc="src/L7-system/04-power-epochs.md",
       blocked_on="the defaults-block per-instance values (defines.v is fetched; per-pad overrides live in the config)")
L.todo("b-config", "tabulate B(config): worst-case bus latency per XIP mode-bit setting",
       doc="src/L7-system/02-bus-contract.md",
       blocked_on="the housekeeping/spimemio RTL for the wait-state generator (fetch decision)")
L.todo("f-immutable", "the flash-immutability check: can software reach flash write commands?",
       doc="src/L7-system/04-power-epochs.md",
       blocked_on="the same spimemio/housekeeping RTL")
L.todo("holdup-ineq", "the supervisor/hold-up inequalities with datasheet + decap numbers",
       doc="src/L7-system/04-power-epochs.md",
       blocked_on="L5/wcet-table for t_epilogue, the decap census (done: 125k) times per-cell C from the PDK, and a chosen supervisor part")
L.todo("oc-rows", "the operating-conditions clause rows (F4, F6, B(config)) as one audited table",
       doc="src/L7-system/05-operating-conditions.md",
       note="the F4 rows sharpened by the SDC audit land here; F6 needs L2/f6-pll-range")
L.extern("X4", "external devices meet their datasheets (per B-level batch)",
         doc="src/axioms.md",
         note="other people's silicon; modelled from datasheets, never checked from shipped data")

if __name__ == "__main__":
    sys.exit(L.main())
