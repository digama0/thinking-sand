#!/usr/bin/env python3
"""rtlcheck.py — the RTL-level structural checks, using yosys as the front end.

L4/02 asks two questions the regex tools could not answer, because both need
real elaboration rather than pattern matching:

  latch-complete  does every `always @*` block assign all its outputs on every
                  path? A path that does not is a LATCH, and an accidental
                  latch is a semantics landmine (state where the design meant
                  none). Yosys answers structurally: elaborate, then look for
                  $dlatch/$adlatch/$sr cells. Zero means every combinational
                  block is complete.
  rtl-scc         is the RTL combinationally acyclic? Yosys's `scc` pass finds
                  strongly-connected components through combinational logic.

Both are answered by an INDEPENDENT implementation of Verilog elaboration — the
same tool whose interpretation L3's equivalence check compares against, which is
the point (L4/04): a disagreement between our reading and yosys's shows up as a
finding rather than as silence.

`check` additionally reports wires that are read but never driven — potential X
sources. Those need adjudicating, not counting, and the discriminator is whether
the unit is a CLOSED hierarchy: if `hierarchy -check` reports no missing module,
every driver that should exist is in the files read, so an undriven wire is a
real dangling signal. If the unit instantiates macros we do not have (DFFRAM,
the sky130 cells), undriven wires are hierarchy-boundary artifacts — exactly the
gate-level W2 result one level down, where 1,609 undriven reads were all macro
boundaries with residue 0.

Usage: rtlcheck.py            (checks every RTL file the book relies on)
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (label, [files to read in order]) — some need their `define` file first
UNITS = [
    ("VexRiscv_MinDebugCache", ["data/mgmt/VexRiscv_MinDebugCache.v"]),
    ("mgmt_core", ["data/mgmt/mgmt_core.v"]),
    ("housekeeping", ["data/caravel/defines.v", "data/caravel/housekeeping.v"]),
    ("gpio_control_block", ["data/caravel/gpio_control_block.v"]),
]

LATCH_TYPES = ("$dlatch", "$adlatch", "$dlatchsr", "$sr")


def have_yosys():
    return shutil.which("yosys") is not None


def yosys(script):
    return subprocess.run(["yosys", "-p", script], capture_output=True, text=True)


def run(label, files):
    """Elaborate one unit. Returns a dict of results, or {'error': ...}."""
    paths = [str(ROOT / f) for f in files]
    for p in paths:
        if not Path(p).is_file():
            return {"error": f"missing {p}"}
    read = f"read_verilog -sv {' '.join(paths)}"

    # Is the hierarchy closed? Only then does "undriven" mean "dangling".
    h = yosys(f"{read}; hierarchy -check")
    missing = re.findall(r"Module `\\?(\w+)' referenced in module .*? "
                         r"is not part of the design", h.stdout)
    closed = h.returncode == 0 and not missing

    p = yosys(f"{read}; proc; opt_clean; check; scc; stat")
    if p.returncode != 0:
        tail = [l for l in p.stdout.splitlines() if "ERROR" in l]
        return {"error": tail[-1] if tail else "yosys failed"}
    out = p.stdout
    return {
        "closed": closed,
        "missing": sorted(set(missing)),
        "latches": sum(int(n) for n, t in
                       re.findall(r"^\s*(\d+)\s+(\$\w+)\s*$", out, re.M)
                       if t in LATCH_TYPES),
        "sccs": sum(int(n) for n in re.findall(r"^Found (\d+) SCCs\.$", out, re.M)),
        "undriven": sorted(set(re.findall(
            r"Warning: Wire (\S+) is used but has no driver", out))),
    }


def main():
    if not have_yosys():
        print("yosys not found — run tools/install-toolchain.sh --only cad",
              file=sys.stderr)
        return 2
    bad = 0
    print("# RTL structural checks (yosys as the front end)\n")
    print(f"  {'unit':<24} {'latches':>8} {'loops':>6} {'hierarchy':>11}  undriven")
    for label, files in UNITS:
        r = run(label, files)
        if "error" in r:
            print(f"  {label:<24} {'ERROR':>8}  {r['error']}")
            bad += 1
            continue
        kind = "closed" if r["closed"] else "open"
        note = "" if (r["latches"] == 0 and r["sccs"] == 0) else "   <-- ATTENTION"
        print(f"  {label:<24} {r['latches']:>8} {r['sccs']:>6} {kind:>11}  "
              f"{len(r['undriven'])}{note}")
        if r["undriven"]:
            if r["closed"]:
                for w in r["undriven"]:
                    print(f"      DANGLING (hierarchy is closed): {w}")
            else:
                print(f"      all at the boundary of absent macros "
                      f"({', '.join(r['missing']) or 'blackbox cells'}) — "
                      f"not adjudicable from these files")
        if r["latches"] or r["sccs"]:
            bad += 1
    print("\n  latches 0 everywhere => every combinational block assigns its "
          "outputs on every path (L4/02)")
    print("  loops 0 everywhere   => the RTL is combinationally acyclic (L4/02)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
