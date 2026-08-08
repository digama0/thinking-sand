#!/usr/bin/env python3
"""check-l1 — L1 (geometry): obligations as an executable scoreboard.

All geometric checks are genuinely programmable (that is the layer's charm) but
each needs either polygon machinery over the GDS or placement data from the
DEF; the stubs record exactly which. gdsdump.py/bbox.py are the parsing seeds.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer, PASS, FAIL, FINDING, DRC_DB, SRAM_KINDS, need

L = Layer("L1", "geometry, manufacturing, and extraction")

# The five macro placements (µm) of the flow of record — the triage boxes.
MACRO_BOXES = [
    (49.68, 149.6, 49.68 + 782, 149.6 + 675),     # dcache bank 0 (R90)
    (49.68, 748.0, 49.68 + 782, 748.0 + 675),     # dcache bank 1 (R90)
    (2612.8, 149.6, 2612.8 + 449, 149.6 + 444),   # icache data 0 (MX90)
    (2612.8, 598.4, 2612.8 + 449, 598.4 + 444),   # icache data 1 (MX90)
    (2612.8, 1033.6, 2612.8 + 191, 1033.6 + 361), # icache tags (MX90)
]


@L.check("drc-triage", "BEOL DRC verdict, macro-internal hits separated by coordinate clustering", doc="src/L1-geometry/05-geometric-checks.md")
def _(ctx):
    if need(DRC_DB):
        return FINDING, f"DRC database absent (rerun the tiled deck): {DRC_DB}"
    import xml.etree.ElementTree as ET, re as _re, collections
    r = ET.parse(DRC_DB).getroot()
    PAD = 5.0
    inside = 0
    outside = collections.Counter()
    for item in r.findall(".//item"):
        v = item.findtext(".//value", "")
        m = _re.findall(r"(-?\d+\.?\d*),(-?\d+\.?\d*)", v)
        if not m:
            continue
        x, y = float(m[0][0]), float(m[0][1])
        if any(x0 + PAD <= x <= x1 - PAD and y0 + PAD <= y <= y1 - PAD for x0, y0, x1, y1 in MACRO_BOXES):
            inside += 1
        else:
            outside[item.findtext("category", "?").strip("'")] += 1
    nout = sum(outside.values())
    msg = (f"{inside + nout:,} raw items: {inside:,} macro-internal (SRAM22 bitcell geometry vs logic rules — "
           f"the collateral's property, no waiver markers in the macro GDS), {nout} flow-owned "
           f"({dict(outside.most_common(6))}), all at macro interfaces")
    if nout > 0:
        return FINDING, msg + " — the macro-pin interface class, actionable (F8's engine-coverage context in findings)"
    return PASS, msg


L.todo("gds-admissible", "the admissible-GDS subset check on the streamed layout (no PATH type 1, no self-intersection, 90-degree SREFs)",
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
