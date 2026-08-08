#!/usr/bin/env python3
"""check-l2 — L2 (timing): obligations as an executable scoreboard.

Re-anchored to the Chipyard target. Implemented: the generated-SDC inventory
(zero exceptions — the audit's subject is completeness), the clock-domain
census against the declared clock set (F3's table, measured), the gating-cell
census, and the nine-corner verdict from the flow's own STA. The TODOs are the
verified engine and the bridge theorem's remaining hypotheses.
"""
import re
import sys
import collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer, PASS, FAIL, FINDING, FINAL_NL, FINAL_SDC, STA_DIR, need
import netgraph

L = Layer("L2", "timing")

# The design's clock-capable ports (from ChipTop's boundary):
CLOCK_PORTS = {"clock_uncore", "jtag_TCK", "serial_tl_0_clock_in"}


@L.check("sdc-inventory", "the constraint file: declared clocks and (absent) exceptions", doc="src/L2-timing/04-sdc-exceptions.md")
def _(ctx):
    if need(FINAL_SDC):
        return FINDING, f"SDC absent (rerun the flow): {FINAL_SDC}"
    txt = FINAL_SDC.read_text(errors="replace")
    clocks = re.findall(r"create_clock.*?-name\s+(\S+)", txt) or re.findall(r"create_clock\s+(?:\[[^\]]*\]\s+)?(\S+)", txt)
    counts = {k: len(re.findall(rf"\b{k}\b", txt)) for k in
              ("set_false_path", "set_case_analysis", "set_multicycle_path")}
    exceptions = sum(counts.values())
    declared = set(re.findall(r"create_clock\s+.*", txt))
    ndecl = len(declared)
    msg = (f"{ndecl} create_clock line(s) ({', '.join(sorted(set(clocks))) or 'unnamed'}); "
           f"exceptions: {counts['set_false_path']} false-path, {counts['set_case_analysis']} case-analysis, "
           f"{counts['set_multicycle_path']} multicycle")
    if exceptions == 0:
        return FINDING, msg + " — zero exceptions to audit: the whole risk is completeness (F3), see domain-census"
    return PASS, msg


@L.check("domain-census", "every sequential clock pin traces to a declared clock (F3's table)", doc="src/L2-timing/04-sdc-exceptions.md")
def _(ctx):
    if need(FINAL_NL, FINAL_SDC):
        return FINDING, "netlist/SDC absent (rerun the flow)"
    insts, ports, _ = netgraph.parse(str(FINAL_NL))
    sdc = FINAL_SDC.read_text(errors="replace")
    declared = {c for c in CLOCK_PORTS if re.search(rf"create_clock\b.*\b{c}\b", sdc)}

    # driver map over clock-path cells only
    driver_of = {}
    CLKCELL = re.compile(r"clkbuf|clkinv|clkdly|dlygate|dlymetal|buf_|inv_|dlclk|sdlclk")
    gate_cells = 0
    for cell, name, pins in insts:
        d = dict()
        for p, n in pins:
            d[p.split('[')[0]] = n
        if re.search(r"dlclk|sdlclk", cell):
            gate_cells += 1
        if CLKCELL.search(cell):
            out = d.get("X") or d.get("Y") or d.get("GCLK")
            src = d.get("A") or d.get("CLK")
            if out and src:
                driver_of[out] = src

    # every sequential CLK pin: walk to a root
    roots = collections.Counter()
    unresolved = set()
    for cell, name, pins in insts:
        if not netgraph.SEQ.search(cell):
            continue
        clknet = None
        for p, n in pins:
            if p in ("CLK", "CLK_N", "GATE", "GATE_N"):
                clknet = n
                break
        if clknet is None:
            continue
        seen = set()
        while clknet in driver_of and clknet not in seen:
            seen.add(clknet)
            clknet = driver_of[clknet]
        base = clknet.lstrip("\\").split("[")[0]
        if base in CLOCK_PORTS:
            roots[base] += 1
        else:
            roots["(internal: " + base[:40] + ")"] += 1
            unresolved.add(base)
    undeclared_roots = {r: n for r, n in roots.items() if r in CLOCK_PORTS and r not in declared}
    rows = ", ".join(f"{r}: {n} flops" for r, n in roots.most_common(6))
    if undeclared_roots:
        return FINDING, (f"clock roots {rows}. UNDECLARED in the SDC: "
                         f"{sorted(undeclared_roots)} — their domains are unanalysed, not excepted (F3). "
                         f"{len(unresolved)} internal roots (gated/derived — each needs its own trace)")
    if unresolved:
        return FINDING, f"clock roots {rows}; {len(unresolved)} internal roots need classification"
    return PASS, f"all sequential clock pins trace to declared clocks: {rows}"


@L.check("gating-census", "the clock-gate cells enumerated (the ICG primitive's instances)", doc="src/L2-timing/05-clock.md")
def _(ctx):
    if need(FINAL_NL):
        return FINDING, "netlist absent (rerun the flow)"
    insts, _, _ = netgraph.parse(str(FINAL_NL))
    gates = collections.Counter(c for c, _, _ in insts if re.search(r"dlclk|sdlclk", c))
    latches = collections.Counter(c for c, _, _ in insts if re.search(r"dlxt|dlrt", c))
    n = sum(gates.values())
    if n == 0 and latches:
        return FINDING, (f"zero integrated ICG cells, but {sum(latches.values())} latch(es) {dict(latches)}: "
                         f"the EICG wrapper synthesized as a DISCRETE latch+AND gated clock (the debug domain's "
                         f"1,067 flops sit behind it). Topologically glitch-free (latch transparent while clock "
                         f"low), but the guarantee now rests on a routed latch-to-AND timing race between two "
                         f"cells, not inside one characterized ICG — the L2/05 enable-stability obligation "
                         f"sharpens to an explicit path check")
    if n == 0:
        return PASS, "zero gating cells and zero gating latches — the tree is ungated"
    return PASS, (f"{n} clock-gate cell(s): {dict(gates)} — each carries the enable-stability obligation "
                  f"(L2/05); the collapse licence becomes 'flops whose gate is enabled update together'")


@L.check("nine-corner", "the flow's multi-corner STA verdict (F1's instrument)", doc="src/L2-timing/02-verified-sta.md")
def _(ctx):
    if need(STA_DIR):
        return FINDING, "STA reports absent (rerun the flow)"
    corners = sorted(d for d in STA_DIR.iterdir() if d.is_dir() and (d / "ws.min.rpt").exists())
    if not corners:
        return FINDING, f"no corner reports under {STA_DIR}"
    def last_num(p):
        t = p.read_text(errors="replace").strip().splitlines()[-1]
        m = re.findall(r"-?\d+\.\d+|-?\d+", t)
        return float(m[-1]) if m else None
    fails, table = [], []
    for c in corners:
        hw, sw = last_num(c / "ws.min.rpt"), last_num(c / "ws.max.rpt")
        table.append(f"{c.name}: hold {hw:+.3f} setup {sw:+.3f}")
        if hw is not None and sw is not None and (hw <= 0 or sw <= 0):
            fails.append(c.name)
    if fails:
        return FINDING, f"{len(fails)}/{len(corners)} corners fail: {fails} — F1 open"
    return PASS, (f"all {len(corners)} corners pass at the conservative clock; " + "; ".join(table[:3]) +
                  " … (full table in the run reports). Setup/hold closure — the domain checks are separate (F2)")


@L.check("domain-violations", "table lookups inside the characterised region (F2's instrument)", doc="src/L2-timing/00-timed-model.md")
def _(ctx):
    if need(STA_DIR):
        return FINDING, "STA reports absent (rerun the flow)"
    chk = STA_DIR / "nom_tt_025C_1v80" / "checks.rpt"
    if not chk.exists():
        return FINDING, f"checks report absent: {chk}"
    txt = chk.read_text(errors="replace")
    tail = txt[txt.find("report_check_types"):]
    import re as _re
    n = len(_re.findall(r"VIOLATED", tail))
    if n:
        return FINDING, (f"{n:,} slew/cap/fanout VIOLATED entries at the nominal corner — F2 open: timing numbers "
                         f"on those nets are outside the characterised region (the priced cost of the skipped "
                         f"repair step; see findings)")
    return PASS, "zero slew/cap/fanout violations — every lookup inside its table's domain"


L.todo("verified-sta", "re-derive the timing verdict with verified interval rules",
       doc="src/L2-timing/02-verified-sta.md", blocked_on="proof-phase machinery")
L.todo("sync-inventory", "every crossing lands on a framework synchroniser shape; the P1 ledger",
       doc="src/L2-timing/06-boundaries.md",
       blocked_on="enumerating AsyncQueue/AsyncResetSynchronizer instances against the domain census")
L.extern("P6", "environment within spec — now carrying the board clock's period/jitter contract",
         doc="axioms.md", note="no theorem constrains the world; the clock_tap pad makes the contract bench-checkable")

if __name__ == "__main__":
    sys.exit(L.main())
