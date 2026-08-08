"""checklib — the tiny framework behind check-l0.py … check-l7.py.

Each layer checker is the *executable table of contents* of that layer's
obligations: every obligation the book states appears here exactly once, either
as a running check or as a documented TODO stub. The scoreboard statuses:

    PASS     the check ran and the obligation holds of the shipped artifacts
    FAIL     the check ran and found a violation nobody has recorded — stop and look
    FINDING  the check ran and confirms an adverse fact already recorded in
             findings.md (expected; not a checker failure)
    TODO     not yet checkable; the stub documents what the check must do and
             what it is blocked on
    EXTERN   not checkable by a program over the shipped data even in principle
             (empirical/axiom-register material) — documented so the layer's
             scoreboard is the complete obligation list

Exit code is nonzero iff any FAIL occurred. TODO/EXTERN never fail: the point
of the scoreboard is an honest census, not a green wall.

Usage in a checker:

    from checklib import Layer
    L = Layer("L3", "netlist ↔ RTL equivalence")

    @L.check("W1-W4", "netlist well-formedness", doc="src/L3-netlist-equivalence/01-well-formedness.md")
    def _(ctx): ...  # return (status, message)

    L.todo("rho", "register correspondence by flow reproduction",
           doc="src/L3-netlist-equivalence/03-register-correspondence.md",
           blocked_on="reproducing the pinned OpenLane run with instrumentation")

    if __name__ == "__main__": L.main()
"""
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import os

DATA = ROOT / "data"

# ---- The generated-artifact anchors (the Chipyard target) ----
# Every checker reads the flow's own outputs. All are regenerable
# (tools/build-rocket.sh + the librelane run in flow/rocket-sram22); none are
# fetched. Paths can be overridden by environment for out-of-tree runs.
FLOW = ROOT / "flow/rocket-sram22"
RUN = Path(os.environ.get("TS_RUN", FLOW / "runs/gds3"))
RTL_SRC = FLOW / "src"                     # emitted SystemVerilog cone (regenerable)
SYN_NL = RUN / "06-yosys-synthesis/ChipTop.nl.v"
FINAL_NL = RUN / "43-openroad-detailedrouting/ChipTop.nl.v"
FINAL_PNL = RUN / "43-openroad-detailedrouting/ChipTop.pnl.v"
FINAL_SDC = RUN / "43-openroad-detailedrouting/ChipTop.sdc"
GDS = RUN / "56-klayout-streamout/ChipTop.gds"
STA_DIR = RUN / "55-openroad-stapostpnr"
DRC_DB = RUN / "58-klayout-drc/reports/drc.klayout.beol2.lyrdb"
GENSRC = Path(os.environ.get(
    "TS_GENSRC",
    "/project/thinking-sand-tools/chipyard/vlsi/generated-src/"
    "chipyard.harness.TestHarness.TinyRocketConfig"))
DTS = GENSRC / "chipyard.harness.TestHarness.TinyRocketConfig.dts"
GEN_COLLATERAL = GENSRC / "gen-collateral"
SRAM22 = Path(os.environ.get("TS_SRAM22", "/project/thinking-sand-tools/sram22_sky130_macros"))

# SRAM macro kinds of this configuration: (name, instances-in-design)
SRAM_KINDS = {"sram22_2048x32m8w8": 2, "sram22_512x32m4w8": 2, "sram22_64x32m4w8": 1}

PASS, FAIL, FINDING, TODO, EXTERN = "PASS", "FAIL", "FINDING", "TODO", "EXTERN"
_COLORS = {PASS: "32", FAIL: "31;1", FINDING: "33", TODO: "36", EXTERN: "35"}


def _paint(s, code):
    return f"\033[{code}m{s}\033[0m" if sys.stdout.isatty() else s


class Layer:
    def __init__(self, name, title):
        self.name, self.title = name, title
        self.items = []   # (id, title, doc, kind, fn|note)

    def check(self, id, title, doc):
        def deco(fn):
            self.items.append((id, title, doc, "check", fn))
            return fn
        return deco

    def todo(self, id, title, doc, blocked_on=None, note=None):
        msg = note or ""
        if blocked_on:
            msg = (msg + " " if msg else "") + f"[blocked on: {blocked_on}]"
        self.items.append((id, title, doc, TODO, msg))

    def extern(self, id, title, doc, note):
        self.items.append((id, title, doc, EXTERN, note))

    def run(self, argv):
        """Execute (or just list) every obligation; return (rows, counts, rc)."""
        list_only = "--list" in argv
        rows, counts, rc = [], {}, 0
        for id, title, doc, kind, x in self.items:
            if kind in (TODO, EXTERN):
                status, msg = kind, x
            elif list_only:
                status, msg = "check", "(not run: --list)"
            else:
                t0 = time.time()
                try:
                    status, msg = x(self)
                except Exception:
                    status, msg = FAIL, "checker raised:\n" + traceback.format_exc(limit=3)
                msg = f"{msg}  ({time.time()-t0:.1f}s)" if status in (PASS, FAIL, FINDING) else msg
            counts[status] = counts.get(status, 0) + 1
            if status == FAIL:
                rc = 1
            rows.append((status, id, title, doc, str(msg)))
        return rows, counts, rc

    def main(self, argv=None):
        argv = argv if argv is not None else sys.argv[1:]
        rows, counts, rc = self.run(argv)
        summary = "  ".join(f"{k}:{v}" for k, v in sorted(counts.items()))
        if "--md" in argv:
            print(f"## {self.name} — {self.title}\n")
            print("| | obligation | detail |")
            print("|---|---|---|")
            for status, id, title, doc, msg in rows:
                link = doc.removeprefix("src/")
                cell = msg.replace("|", "\\|").replace("\n", " — ")
                print(f"| **{status}** | [`{self.name}/{id}`]({link}) — {title} | {cell} |")
            print(f"\n*{len(rows)} obligations — {summary}*\n")
            return rc
        print(f"=== {self.name} — {self.title} ===")
        for status, id, title, doc, msg in rows:
            tag = _paint(f"{status:7}", _COLORS.get(status, "0"))
            print(f"[{tag}] {self.name}/{id:<12} {title}")
            print(f"          doc: {doc}")
            if msg:
                for line in msg.splitlines():
                    print(f"          {line}")
        print(f"--- {self.name}: {len(rows)} obligations  {summary}")
        return rc


def need(*paths):
    """Return the missing data files (as strings), for graceful degradation."""
    return [str(p) for p in paths if not Path(p).exists()]


def load(toolname):
    """Import a tools/*.py file whose name may contain dashes (e.g. 'sdc-audit')."""
    import importlib.util
    p = Path(__file__).parent / f"{toolname}.py"
    spec = importlib.util.spec_from_file_location(toolname.replace("-", "_"), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
