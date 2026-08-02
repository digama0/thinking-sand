#!/usr/bin/env python3
"""sdc-audit.py — elaborate caravel.sdc over its full mode space and classify
every timing exception (L2/04 steps 1-2).

Runs tools/sdc-elaborate.tcl for all 8 combinations of the three mode
variables (io_4_mode x ios_mode x IO_SYNC), aggregates the flat constraint
sets, and emits a markdown report: per-mode inventory, the case-analysis pin
map with cross-mode value conflicts, and a first-pass classification of every
false path into the L2/04 classes (asynchronous / logically-false / static),
with set_case_analysis constituting the mode class by definition.

Usage: tools/sdc-audit.py [path/to/caravel.sdc]   (default: data/caravel/caravel.sdc)
"""
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SDC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/caravel/caravel.sdc"
TCL = ROOT / "tools/sdc-elaborate.tcl"

MODES = [(io4, ios, sync) for io4 in ("SCK", "GPIO") for ios in ("IN", "OUT") for sync in ("0", "1")]
SHIPPED = ("SCK", "OUT", "0")  # the values set in the shipped file


def elaborate(mode):
    io4, ios, sync = mode
    r = subprocess.run(
        ["tclsh", str(TCL), str(SDC), io4, ios, sync],
        capture_output=True, text=True, check=True)
    for line in r.stderr.splitlines():
        if line.startswith("UNKNOWN-COMMAND"):
            print(f"warning: {mode}: {line}", file=sys.stderr)
    out = []
    for line in r.stdout.splitlines():
        if line.startswith("#"):
            continue
        lineno, cmd, args = line.split("\t", 2)
        out.append((int(lineno), cmd, args))
    return out


def classify_false_path(args):
    """First-pass classification per L2/04's four classes.

    The classifier is deliberately conservative: anything not matching a known
    asynchronous-interface pattern is 'unclassified' and must be triaged by
    hand, never defaulted into a discharged class.
    """
    if re.search(r"get_ports \{?(mprj_io|gpio\b|resetb)", args):
        return "asynchronous (external pin)"
    if re.search(r"-through .*mgmt_gpio_(in|out|oeb)", args):
        return "asynchronous (external pin, via housekeeping path)"
    if re.search(r"-from \[get_clocks", args) and re.search(r"-to \[get_clocks", args):
        return "clock-domain exclusion"
    return "UNCLASSIFIED"


def main():
    per_mode = {m: elaborate(m) for m in MODES}

    print("# SDC audit — elaborated mode space of caravel.sdc\n")
    print(f"Source: `{SDC.name}`, {sum(1 for _ in open(SDC))} lines of Tcl; "
          f"mode variables `io_4_mode` (SCK|GPIO), `ios_mode` (IN|OUT), `IO_SYNC` (0|1); "
          f"shipped setting {SHIPPED}.\n")

    # --- per-mode command inventory ---------------------------------------
    cmds = sorted({c for v in per_mode.values() for _, c, _ in v})
    print("## Per-mode constraint counts\n")
    print("| mode | " + " | ".join(c.removeprefix("set_") for c in cmds) + " | total |")
    print("|---|" + "---|" * (len(cmds) + 1))
    for m, v in per_mode.items():
        n = defaultdict(int)
        for _, c, _ in v:
            n[c] += 1
        star = " **(shipped)**" if m == SHIPPED else ""
        print(f"| {'/'.join(m)}{star} | " + " | ".join(str(n[c]) for c in cmds) + f" | {len(v)} |")

    # --- case analysis map -------------------------------------------------
    pins = defaultdict(dict)  # pin -> mode -> value
    for m, v in per_mode.items():
        for _, c, args in v:
            if c != "set_case_analysis":
                continue
            val, target = args.split(" ", 1)
            pins[target][m] = val
    conflicts = {p: mv for p, mv in pins.items() if len(set(mv.values())) > 1}
    partial = {p: mv for p, mv in pins.items() if len(mv) < len(MODES)}
    print(f"\n## Case analysis (the mode class): {len(pins)} distinct pins\n")
    print(f"- constant across all modes where set: {len(pins) - len(conflicts)}")
    print(f"- value differs by mode: {len(conflicts)}")
    print(f"- set in only some modes: {len(partial)}\n")
    if conflicts:
        print("Pins whose pinned value differs across modes "
              "(each is a mode-select or direction-dependent pad control; "
              "F4's coverage obligation is that reachable configurations land in an analysed mode):\n")
        for p, mv in sorted(conflicts.items()):
            groups = defaultdict(list)
            for m, val in mv.items():
                groups[val].append("/".join(m))
            desc = "; ".join(f"={val} in {', '.join(ms)}" for val, ms in sorted(groups.items()))
            print(f"- `{p}` — {desc}")

    # --- false paths -------------------------------------------------------
    print("\n## False paths (classified)\n")
    for m, v in per_mode.items():
        fps = [(ln, args) for ln, c, args in v if c == "set_false_path"]
        cls = defaultdict(list)
        for ln, args in fps:
            cls[classify_false_path(args)].append((ln, args))
        star = " **(shipped)**" if m == SHIPPED else ""
        summary = ", ".join(f"{k}: {len(xs)}" for k, xs in sorted(cls.items()))
        print(f"- {'/'.join(m)}{star}: {len(fps)} false paths — {summary}")
        for ln, args in cls.get("UNCLASSIFIED", []):
            print(f"    - UNCLASSIFIED (line {ln}): `{args}`")

    # --- clock structure ---------------------------------------------------
    print("\n## Clocks and clock groups\n")
    for m in (SHIPPED, ("GPIO", "OUT", "0")):
        v = per_mode[m]
        print(f"mode {'/'.join(m)}:")
        for ln, c, args in v:
            if c in ("create_clock", "set_clock_groups"):
                print(f"- line {ln}: `{c} {args}`")
        print()


if __name__ == "__main__":
    main()
