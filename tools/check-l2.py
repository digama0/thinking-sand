#!/usr/bin/env python3
"""check-l2 — L2 (timing): the layer's obligations as an executable scoreboard.

Implemented: the SDC elaboration/classification regressions, the signoff-report
confrontation, and the synchroniser audit. The TODO stubs are the layer's
remaining programme, each with its blocking prerequisite named.
"""
import sys
import collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer, PASS, FAIL, FINDING, DATA, need, load

L = Layer("L2", "timing and the synchronous abstraction")

SDC = DATA / "caravel/caravel.sdc"
CORE = DATA / "caravel/gl_caravel_core.v"
HK = DATA / "caravel/gl_housekeeping.v"


@L.check("sdc-modes", "the SDC elaborates over its full 8-mode space",
         doc="src/L2-timing/04-sdc-exceptions.md")
def _(ctx):
    if m := need(SDC):
        return FAIL, f"missing {m} (run tools/fetch-data.sh small)"
    sa = load("sdc-audit")
    sizes = {}
    for mode in sa.MODES:
        sizes[mode] = len(sa.elaborate(mode))
    lo, hi = min(sizes.values()), max(sizes.values())
    shipped = sizes[sa.SHIPPED]
    return PASS, f"8 modes, {lo}-{hi} flat constraints; shipped {'/'.join(sa.SHIPPED)} = {shipped}"


@L.check("sdc-class", "every false path classifies (all asynchronous-external)",
         doc="src/L2-timing/04-sdc-exceptions.md")
def _(ctx):
    sa = load("sdc-audit")
    bad, total = [], 0
    for mode in sa.MODES:
        for ln, cmd, args in sa.elaborate(mode):
            if cmd != "set_false_path":
                continue
            total += 1
            if sa.classify_false_path(args) == "UNCLASSIFIED":
                bad.append((mode, ln, args))
    if bad:
        return FAIL, f"{len(bad)} unclassified false paths, e.g. {bad[0]}"
    return PASS, f"{total} false paths across 8 modes, all asynchronous-external"


@L.check("sdc-6817", "the _6817_ double-pin is two modes, not a bug",
         doc="src/L2-timing/04-sdc-exceptions.md")
def _(ctx):
    sa = load("sdc-audit")
    for mode in sa.MODES:
        for ln, cmd, args in sa.elaborate(mode):
            if cmd == "set_case_analysis" and "_6817_" in args:
                want = "0" if mode[0] == "SCK" else "1"
                if not args.startswith(want + " "):
                    return FAIL, f"mode {mode}: _6817_ pinned {args.split()[0]}, expected {want}"
    return PASS, "pad-4 function select: 0 in all SCK modes, 1 in all GPIO modes"


@L.check("signoff", "corner confrontation: which corners the shipped sign-off failed",
         doc="src/L2-timing/01-bridge-theorem.md")
def _(ctx):
    rpt = DATA / "caravel/signoff.rpt"
    if m := need(rpt):
        return FAIL, f"missing {m}"
    lines = [ln.split(None, 1) for ln in rpt.read_text().splitlines() if ln.strip()]
    verdicts = {name.removeprefix("caravel_core-").removesuffix("-sta"): rest
                for name, rest in (l for l in lines if len(l) == 2)}
    failed = sorted(k for k, v in verdicts.items() if "Failed" in v)
    excepted = sorted(k for k, v in verdicts.items() if "except" in v)
    expect_failed = ["s-max", "s-min", "s-nom"]
    expect_exc = ["t-max"]
    if failed != expect_failed or excepted != expect_exc:
        return FAIL, (f"signoff verdicts changed: failed={failed}, excepted={excepted} "
                      f"(recorded: {expect_failed} in2reg hold, {expect_exc} max_tran/max_cap)")
    return FINDING, ("confirms F1/F2: 3 of 9 corners fail in2reg hold (all slow-process), "
                     "t-max passes only modulo max_tran & max_cap (STA vacuous outside "
                     "the characterised region there)")


@L.check("sync-gpio", "gpio_in_core lands on a verified two-flop synchroniser",
         doc="src/L2-timing/06-boundaries.md")
def _(ctx):
    if m := need(CORE):
        return FAIL, f"missing {m} (run tools/fetch-data.sh caravel)"
    sc = load("synccheck")
    insts, decls = sc.parse(str(CORE))
    nets, outs_of, pins_of = sc.build(insts)
    hits, _ = sc.trace(nets, outs_of, pins_of, decls, "gpio_in_core")
    if list(hits) == ["capture SYNC"] and len(hits["capture SYNC"]) == 1:
        return PASS, hits["capture SYNC"][0]
    return FAIL, f"expected exactly one SYNC capture, got {dict((k, len(v)) for k, v in hits.items())}"


@L.check("sync-hk", "housekeeping endpoint census behind the mprj_io exceptions",
         doc="src/L2-timing/06-boundaries.md")
def _(ctx):
    if m := need(HK):
        return FAIL, f"missing {m} (run tools/fetch-data.sh caravel)"
    sc = load("synccheck")
    insts, decls = sc.parse(str(HK))
    nets, outs_of, pins_of = sc.build(insts)
    roles = collections.defaultdict(set)
    wb_caps, sync2 = set(), []
    for i in range(38):
        b = f"mgmt_gpio_in[{i}]"
        hits, _ = sc.trace(nets, outs_of, pins_of, decls, b)
        for k in hits:
            roles[k].add(i)
        sync2 += hits.get("capture SYNC", [])
        for x in hits.get("capture NOSYNC", []):
            inst = x.split(" ")[0]
            clk = next((pins_of[inst].get(c) for c in sc.CLOCK_PINS if c in pins_of[inst]), None)
            if clk and sc.clk_root(nets, pins_of, clk) == "wb_clk_i":
                wb_caps.add(inst)
    clk_bits = sorted(roles["clock/gate pin"])
    if sync2:
        return FAIL, f"two-flop synchronisers appeared in housekeeping: {sync2[:3]} — findings say none exist"
    if clk_bits != [3, 4] or len(wb_caps) != 40:
        return FAIL, (f"census changed: clock-role bits {clk_bits} (recorded [3,4]), "
                      f"wb_clk_i single-flop captures {len(wb_caps)} (recorded 40)")
    return FINDING, ("confirms the recorded census: no 2-flop synchroniser behind any mprj_io "
                     "exception; bits 3/4 act as clocks; 40 single-flop captures on wb_clk_i "
                     "(software-paced discharge required, N_sync at single-stage MTBF)")


L.todo("verified-sta", "re-derive the shipped timing verdict with sound interpolation rules",
       doc="src/L2-timing/02-verified-sta.md",
       blocked_on="a Liberty/SPEF-loading STA core (months of tooling; the layer's main build)")
L.todo("monotonicity", "library-wide Liberty monotonicity census (sizes M4)",
       doc="src/L2-timing/03-corners.md",
       blocked_on="fetching the full SKY130 HD Liberty set at pinned SHAs (data/pdk has 3 sample corners of inv_1 only)")
@L.check("clock-core", "clock cleanliness (core): every sink resolves to a declared root; gating censused",
         doc="src/L2-timing/05-clock.md")
def _(ctx):
    cc = load("clockcheck")
    _, nsinks, ngates, by_root, _, _, _ = cc.survey(str(CORE))
    roots = {d: len(m) for (k, d), m in by_root.items()}
    macro_ok = (roots.get("caravel_clocking.core_clk") == 4727
                and roots.get("housekeeping.serial_clock") == 530
                and roots.get("housekeeping.serial_load") == 494)
    stray = {d: n for d, n in roots.items()
             if d not in ("caravel_clocking.core_clk", "housekeeping.serial_clock",
                          "housekeeping.serial_load") and "ringosc" not in d}
    if nsinks != 5774 or ngates != 0 or not macro_ok or stray:
        return FAIL, f"census changed: sinks {nsinks}, gates {ngates}, roots {roots}"
    return PASS, ("5,774 sinks -> 4 roots: the SDC's three declared clocks via macro pins "
                  "(4,727 + 530 + 494) + 23 sinks inside pll.ringosc (exactly the X5 "
                  "excision); 0 clock-gate cells; every path outside the excision is pure "
                  "buffer/inverter — the licence for L3's clock-tree deletion")


@L.check("clock-hk", "clock cleanliness (housekeeping): the csclk mux and the undeclared bit-bang clock",
         doc="src/L2-timing/05-clock.md")
def _(ctx):
    cc = load("clockcheck")
    _, nsinks, ngates, by_root, _, nets, pins_of = cc.survey(str(HK))
    roots = {d: len(m) for (k, d), m in by_root.items()}
    mux = next((d for d in roots if "a22o" in d), None)
    kind, detail, _ = cc.classify_driver(nets, pins_of, "wbbd_sck")
    if (nsinks != 771 or ngates != 0 or roots.get(mux) != 615
            or roots.get("wb_clk_i") != 111 or roots.get("mgmt_gpio_in[4]") != 45
            or kind != "flop-out"):
        return FAIL, f"census changed: sinks {nsinks}, roots {roots}, wbbd_sck<-{kind} {detail}"
    return FINDING, ("confirms the recorded census: 615 sinks on csclk = a22o mux(external "
                     "SCK path, wbbd_sck); wbbd_sck is a FLOP OUTPUT (_7203_) — the "
                     "firmware bit-bang SPI clock is a register-generated clock that no "
                     "SDC mode declares, so the 615-flop domain is never timed from that "
                     "source in any analysed mode (F4)")
L.todo("f6-pll-range", "reachable PLL configurations vs the signoff clock period (F6)",
       doc="src/L2-timing/05-clock.md",
       blocked_on="the housekeeping register map for itrim/divider/source-mux reachable values")
L.todo("f1-match", "match the failing in2reg hold paths to their covering exceptions (close F1)",
       doc="src/L2-timing/04-sdc-exceptions.md",
       blocked_on="per-path signoff logs (signoff.rpt is verdict-only; needs the full STA reports or a re-run)")
L.todo("ac-export", "derive the exported AC-timing table (the outward guarantee)",
       doc="src/L2-timing/06-boundaries.md",
       blocked_on="the verified-sta core (same engine, backward direction)")
L.todo("glitch-budget", "crosstalk glitch sum vs noise margins on worst nets",
       doc="src/L2-timing/07-crosstalk-power.md",
       blocked_on="parasitic extraction data (SPEF or re-extraction from DEF)")

if __name__ == "__main__":
    sys.exit(L.main())
