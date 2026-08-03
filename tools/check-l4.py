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
from checklib import Layer, PASS, FAIL, FINDING, DATA, need, load

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
    # falling-edge-clocked blocks (leading negedge in the sensitivity list;
    # a negedge RESET as the second term does not count)
    counts["negedge-clocked blocks"] = len(re.findall(r"always\s*@\s*\(\s*negedge", txt))
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


@L.check("soc-census", "the construct census over the SoC-level RTL",
         doc="src/L4-rtl-semantics/01-subset.md")
def _(ctx):
    zeros = {k: 0 for k in ("# delays", "x literals", "casex", "force/release/deassign",
                            "fork/join/UDP/event", "always @*", "casez", "initial",
                            "posedge blocks w/ blocking =", "posedge blocks",
                            "negedge-clocked blocks")}
    r = check_census(DATA / "caravel/rtl_caravel_core.v", zeros)
    if r:
        return r
    r = check_census(DATA / "mgmt/mgmt_core_wrapper.v", zeros)
    if r:
        return r
    r = check_census(DATA / "caravel/housekeeping.v",
                     {**zeros, "posedge blocks": 3, "posedge blocks w/ blocking =": 2})
    if r:
        return r
    r = check_census(DATA / "caravel/gpio_control_block.v",
                     {**zeros, "posedge blocks": 2, "posedge blocks w/ blocking =": 1,
                      "negedge-clocked blocks": 1})
    if r:
        return r
    return PASS, ("the SoC-side RTL is nearly construct-free: caravel_core and the "
                  "wrapper are pure structural wiring (zero always blocks); "
                  "housekeeping's 615 GL flops come from just 3 wide clocked blocks "
                  "(two containing blocking assigns - the normal-form rewrite "
                  "obligation extends to them; one clocked on csclk, the SPI domain "
                  "from the L2 finding); the gpio control block adds the one genuinely "
                  "new subset construct - a FALLING-edge-clocked serial-shift block. "
                  "No delays/casex/x-literals/initial anywhere in the SoC set")
@L.check("regen-facts", "the SoC facts re-derived from an INDEPENDENTLY REGENERATED mgmt_core.v",
         doc="src/findings.md")
def _(ctx):
    import subprocess
    root = Path(__file__).resolve().parent.parent
    regen = root / "build-regen/src/build/caravel_platform/gateware/mgmt_core_modified.v"
    if not regen.is_file():
        from checklib import TODO
        return TODO, ("run tools/regenerate-mgmt-core.sh to build it (pinned venv, ~2 min, "
                      "needs network); the shipped-file side of every fact is already "
                      "checked by the L5/L6/L7 rows")
    p = subprocess.run([sys.executable, str(root / "tools/replicate.py"), str(regen)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        return FAIL, "a fact differs between shipped and regenerated:\n" + p.stdout.strip()
    n = re.search(r"(\d+) facts reproduced", p.stdout)
    return PASS, (f"all {n.group(1) if n else '?'} SoC-level facts re-derive identically from "
                  "RTL regenerated by an independent run of the design's own LiteX "
                  "generator - the bus decode, CSR banks, interconnect timeout, interrupt "
                  "wiring, synchronisers, event blocks, flash master path, reset vector and "
                  "construct census are properties of the design, not of one build")
@L.check("latch-complete", "no combinational block infers a latch, and the RTL is acyclic",
         doc="src/L4-rtl-semantics/02-comb-blocks.md")
def _(ctx):
    import shutil, subprocess
    from checklib import TODO
    if not shutil.which("yosys"):
        return TODO, ("needs yosys as the Verilog front end — run "
                      "tools/install-toolchain.sh --only cad")
    rc = load("rtlcheck")
    rows = {label: rc.run(label, files) for label, files in rc.UNITS}
    err = {k: v["error"] for k, v in rows.items() if "error" in v}
    if err:
        return FAIL, f"yosys could not elaborate: {err}"
    latched = {k: v["latches"] for k, v in rows.items() if v["latches"]}
    looped = {k: v["sccs"] for k, v in rows.items() if v["sccs"]}
    if latched or looped:
        return FAIL, f"latches {latched}, combinational loops {looped}"
    closed = [k for k, v in rows.items() if v["closed"]]
    if closed != ["VexRiscv_MinDebugCache"]:
        return FAIL, f"which units are closed hierarchies changed: {closed}"
    dangling = rows["VexRiscv_MinDebugCache"]["undriven"]
    if len(dangling) != 2 or not all(
            "isRemoved" in w or "bypassTranslation" in w for w in dangling):
        return FAIL, f"the dangling-wire set changed: {dangling}"
    return FINDING, ("elaborated by yosys — an INDEPENDENT implementation of Verilog, "
                     "which is the point (L4/04). Across the shipped core, the SoC, "
                     "housekeeping and the GPIO control block: ZERO inferred latches, so "
                     "every combinational block assigns its outputs on every path, and "
                     "ZERO combinational loops. Both L4/02 questions answered. The "
                     "finding: the shipped core is a CLOSED hierarchy yet contains TWO "
                     "undriven wires, both fed as inputs to the instruction cache - "
                     "io_cpu_fetch_isRemoved (never read inside the cache) and "
                     "io_cpu_fetch_mmuRsp_bypassTranslation (latched into a register "
                     "nothing reads). Both are therefore X-inert, but they are real "
                     "dangling signals in shipped RTL. The other units' undriven wires "
                     "are macro-boundary artifacts - the RTL-level echo of the gate-level "
                     "W2 result")
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
