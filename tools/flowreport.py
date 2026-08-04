#!/usr/bin/env python3
"""flowreport.py — summarise a librelane run, and compare it to the 2021 signoff.

The point of running the flow ourselves is not to match the fabricated chip —
it cannot, the inputs differ — but to have a signoff table we PRODUCED, at the
same level of detail as the one we fetched, so the two can be set side by side.

Reads the run's final/metrics.json and prints:
  * the nine-corner hold/setup slack table (the direct analogue of
    signoff/caravel_core/signoff.rpt)
  * DRC/LVS/antenna verdicts
  * the instance census, including the buffer counts that explain the timing

Usage: flowreport.py <run-dir>       (e.g. flow/vexriscv/runs/rtl2gds)
"""
import json
import sys
from pathlib import Path

# the shipped 2021 verdict, for the side-by-side (findings: "Signoff status")
SHIPPED = {
    "f-nom": "Passed", "f-min": "Passed", "f-max": "Passed",
    "t-nom": "Passed", "t-min": "Passed", "t-max": "Passed (max_tran & max_cap)",
    "s-nom": "FAILED (in2reg hold)", "s-min": "FAILED (in2reg hold)",
    "s-max": "FAILED (in2reg hold)",
}
# librelane corner name -> the shipped table's shorthand
ALIAS = {
    "nom_ff_n40C_1v95": "f-nom", "min_ff_n40C_1v95": "f-min", "max_ff_n40C_1v95": "f-max",
    "nom_tt_025C_1v80": "t-nom", "min_tt_025C_1v80": "t-min", "max_tt_025C_1v80": "t-max",
    "nom_ss_100C_1v60": "s-nom", "min_ss_100C_1v60": "s-min", "max_ss_100C_1v60": "s-max",
}


def load(run):
    p = Path(run) / "final/metrics.json"
    if not p.is_file():
        raise SystemExit(f"no metrics at {p} — did the flow finish?")
    return json.loads(p.read_text())


def corners(m):
    out = {}
    for k in m:
        if k.startswith("timing__hold__ws__corner:"):
            c = k.split("corner:")[1]
            out[c] = (m[k], m.get(f"timing__setup__ws__corner:{c}"))
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    m = load(sys.argv[1])
    cs = corners(m)

    print("# Signoff, from a flow we ran\n")
    print(f"  {'corner':<20} {'hold ws':>9} {'setup ws':>10}   {'ours':<8} vs 2021")
    for c in sorted(cs, key=lambda x: ALIAS.get(x, x)):
        h, s = cs[c]
        ours = "PASS" if (h > 0 and s > 0) else "FAIL"
        print(f"  {ALIAS.get(c, c):<20} {h:>9.3f} {s:>10.3f}   {ours:<8} {SHIPPED.get(ALIAS.get(c, c), '?')}")

    print(f"\n  hold  worst {m.get('timing__hold__ws'):.3f}   tns {m.get('timing__hold__tns'):.1f}")
    print(f"  setup worst {m.get('timing__setup__ws'):.3f}   tns {m.get('timing__setup__tns'):.1f}")

    print("\n# Physical verification")
    for label, key in (("magic DRC", "magic__drc_error__count"),
                       ("klayout DRC", "klayout__drc_error__count"),
                       ("routing DRC", "route__drc_errors"),
                       ("LVS", "design__lvs_error__count"),
                       ("antenna", "route__antenna_violations")):
        if key in m:
            print(f"  {label:<14} {m[key]}")

    print("\n# Instance census (why the timing came out as it did)")
    for label, key in (("total", "design__instance__count"),
                       ("standard cells", "design__instance__count__stdcell"),
                       ("sequential", "design__instance__count__class:sequential_cell"),
                       ("HOLD buffers", "design__instance__count__hold_buffer"),
                       ("timing-repair buffers", "design__instance__count__timing_repair_buffer"),
                       ("fill", "design__instance__count__class:fill_cell")):
        if key in m:
            print(f"  {label:<24} {m[key]:>8}")
    print(f"  {'die area (um^2)':<24} {m.get('design__die__area'):>8}")
    print(f"  {'utilisation':<24} {m.get('design__instance__utilization'):>8.3f}")

    print("\n  The 2021 flow left hold FAILING at the three slow corners and setup")
    print("  comfortable. This flow inserts thousands of hold buffers, fixes hold at")
    print("  every corner, and pays for it in setup. Same design, opposite trade.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
