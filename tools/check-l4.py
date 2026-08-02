#!/usr/bin/env python3
"""check-l4 — L4 (RTL semantics): obligations as an executable scoreboard.

Implemented: the subset census — re-deriving the 19-sites table from the source
rather than trusting findings.md. The TODOs are the semantics itself and its
adequacy programme.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer, PASS, FAIL, DATA, need

L = Layer("L4", "RTL semantics")
PICO = DATA / "mgmt/picorv32.v"


def strip_comments(txt):
    txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
    return re.sub(r"//[^\n]*", "", txt)


def census(path):
    txt = strip_comments(path.read_text(errors="replace"))
    counts = {
        "# delays": len(re.findall(r"#\s*\d", txt)),
        "x literals": len(re.findall(r"'[bdh][0-9_]*[xX]", txt)),
        "casex": len(re.findall(r"\bcasex\b", txt)),
        "force/release/deassign": len(re.findall(r"\b(force|release|deassign)\b", txt)),
        "fork/join/UDP/event": len(re.findall(r"\b(fork|join|primitive)\b|->", txt)),
        "always @*": len(re.findall(r"always\s*@\s*(\*|\(\s*\*\s*\))", txt)),
        "casez": len(re.findall(r"\bcasez\b", txt)),
        "initial": len(re.findall(r"\binitial\b", txt)),
    }
    # posedge blocks containing blocking '=' (for-headers removed; <=/==/>=/!= masked)
    blocking_blocks = 0
    posedge_blocks = re.split(r"always\s*@\s*\(\s*posedge", txt)[1:]
    for chunk in posedge_blocks:
        body = re.split(r"\balways\b|\bendmodule\b", chunk)[0]
        b = re.sub(r"for\s*\([^)]*\)", "for(...)", body)
        if re.search(r"(?<![<>=!])=(?!=)", re.sub(r"<=|>=|==+|!=+", "@", b)):
            blocking_blocks += 1
    counts["posedge blocks w/ blocking ="] = blocking_blocks
    counts["posedge blocks"] = len(posedge_blocks)
    return counts


def check_census(path, expect):
    if m := need(path):
        return FAIL, f"missing {m} (run tools/fetch-data.sh mgmt)"
    counts = census(path)
    diffs = {k: (counts[k], expect[k]) for k in expect if counts[k] != expect[k]}
    if diffs:
        return FAIL, f"census disagrees with the recorded table (got, recorded): {diffs}"
    return None


@L.check("subset-shipped", "the construct census of the SHIPPED core pair (F7 target)",
         doc="src/L4-rtl-semantics/01-subset.md")
def _(ctx):
    vex = DATA / "mgmt/VexRiscv_MinDebugCache.v"
    lit = DATA / "mgmt/mgmt_core.v"
    r = check_census(vex, {"# delays": 0, "x literals": 7, "casex": 0,
                           "force/release/deassign": 0, "fork/join/UDP/event": 0,
                           "always @*": 186, "casez": 1, "initial": 0,
                           "posedge blocks w/ blocking =": 0, "posedge blocks": 13})
    if r:
        return r
    r = check_census(lit, {"# delays": 0, "x literals": 0, "casex": 0,
                           "force/release/deassign": 0, "fork/join/UDP/event": 0,
                           "always @*": 355, "casez": 0, "initial": 0,
                           "posedge blocks w/ blocking =": 2, "posedge blocks": 7})
    if r:
        return r
    return PASS, ("machine-emitted narrowness confirmed: VexRiscv - 7 'bx don't-cares, "
                  "186 always@*, 1 casez, 13 posedge blocks (0 blocking); mgmt_core "
                  "(LiteX) - clean except 355 always@* and 2 blocking blocks. No "
                  "delays/casex/force-class anywhere; 25x picorv32's block count")


@L.check("subset", "the construct census of picorv32.v (the comparison core)",
         doc="src/L4-rtl-semantics/01-subset.md")
def _(ctx):
    # The measured truth (this check CORRECTED the original findings table, which
    # claimed 0 X literals and 2-of-25 blocking blocks — see findings.md).
    r = check_census(PICO, {"# delays": 0, "x literals": 25, "casex": 0,
                            "force/release/deassign": 0, "fork/join/UDP/event": 0,
                            "always @*": 15, "casez": 1, "initial": 1,
                            "posedge blocks w/ blocking =": 5, "posedge blocks": 24})
    if r:
        return r
    return PASS, ("matches findings: 0 delays/casex/force-class, 25 'bx don't-cares, "
                  "15 always@*, 1 casez, 1 initial, 5 of 24 posedge blocks use blocking =")


L.todo("soc-census", "the same census over the SoC-level RTL (core-only today)",
       doc="src/L4-rtl-semantics/01-subset.md",
       blocked_on="fetching the SoC RTL set (rtl_caravel_core.v is here; housekeeping/wrapper RTL needs pinning)")
L.todo("latch-complete", "the 15 always@* blocks assign every output on every path",
       doc="src/L4-rtl-semantics/02-comb-blocks.md",
       blocked_on="a real Verilog parser (regexes cannot do per-path analysis; consider slang/verible as the untrusted front end)")
L.todo("rtl-scc", "RTL-level combinational acyclicity (the conservative syntactic check)",
       doc="src/L4-rtl-semantics/02-comb-blocks.md",
       blocked_on="the same parser as latch-complete")
L.todo("blocking-rewrite", "normal-form rewrite of the 2 blocking-assignment blocks, checked equivalent",
       doc="src/L4-rtl-semantics/02-comb-blocks.md",
       blocked_on="the elaborated semantics existing to check equivalence against")
L.todo("ternary-reset", "ternary reset simulation: definite-claimed bits definite after reset",
       doc="src/L4-rtl-semantics/03-x-and-reset.md",
       blocked_on="an elaborator for the subset (the layer's central build)")
L.todo("initial-site", "resolve the one initial block against the shipped netlist",
       doc="src/L4-rtl-semantics/03-x-and-reset.md",
       note="check whether Yosys realised it as an initialised cell or dropped it; needs rho's reproduced run or netlist archaeology")
L.todo("differential", "differential simulation against Verilator/Icarus on the design's testbenches",
       doc="src/L4-rtl-semantics/04-adequacy.md",
       blocked_on="the elaborator, plus fetching the testbench tree")

if __name__ == "__main__":
    sys.exit(L.main())
