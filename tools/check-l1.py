#!/usr/bin/env python3
"""check-l1 — L1 (geometry): obligations as an executable scoreboard.

All geometric checks are genuinely programmable (that is the layer's charm) but
each needs either polygon machinery over the GDS or placement data from the
DEF; the stubs record exactly which. gdsdump.py/bbox.py are the parsing seeds.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer

L = Layer("L1", "geometry, manufacturing, and extraction")

L.todo("gds-admissible", "the admissible-GDS subset check (no PATH type 1, no self-intersection, 90-degree SREFs)",
       doc="src/L1-geometry/00-layout-object.md",
       note="record-level scan; gdsdump.py already walks the records — promote it to a verdict. "
            "Cheapest L1 item and the front end for everything below.")
L.todo("h1h2-inv1", "(H1)/(H2) — erode-connectivity and colour-aware spacing on inv_1, then a cell row",
       doc="src/L1-geometry/01-topology-preservation.md",
       blocked_on="polygon morphology (erosion/dilation + union-find over scanline geometry)")
L.todo("lvs-inv1", "extraction + LVS of inv_1 against its schematic; (D1)-(D3) sized on the same cell",
       doc="src/L1-geometry/02-extraction-lvs.md",
       blocked_on="magic/netgen in the environment, or a minimal extractor over the flattened colouring")
L.todo("g1-taps", "G1: every device within d_max of a well tap (discharges V5/M1's side condition)",
       doc="src/L1-geometry/05-geometric-checks.md",
       blocked_on="parsing placement from caravel_core.def (398,259 COMPONENTS) + the extraction for device sites")
L.todo("g3-antenna", "G3: antenna ratios over process-order prefixes",
       doc="src/L1-geometry/05-geometric-checks.md",
       blocked_on="the process layer order (a fab-recipe fact; may only be assumable, in which case this documents it)")
L.todo("g5g6-shield", "G5/G6: shielding coverage and tied-fill (M2's design-side hypotheses)",
       doc="src/L1-geometry/05-geometric-checks.md",
       blocked_on="GDS polygon connectivity over the power grid; G6 (is the fill tied?) is the high-value quick answer")
L.todo("density-map", "pattern-density map (feeds the CMP thickness correction and local-bias r(x))",
       doc="src/L1-geometry/00-layout-object.md",
       note="windowed area sums over the GDS — mechanical once the polygon front end exists")
L.extern("E7-H3", "as-fabricated geometry within tolerance; no spurious islands (H3)",
         doc="src/axioms.md",
         note="quantifies over the fabricated set A — no program over shipped data reaches it")

if __name__ == "__main__":
    sys.exit(L.main())
