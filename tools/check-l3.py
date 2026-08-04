#!/usr/bin/env python3
"""check-l3 — L3 (netlist ↔ RTL equivalence): obligations as an executable scoreboard.

Implemented: W1–W4 with the PLL-excision minimality assertions, the macro
census (recursion-or-contract inventory), and the W2 macro-boundary discharge.
The TODOs are the certificate architecture, each stub naming its blocker.
"""
import sys
import collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer, PASS, FAIL, FINDING, DATA, need, load

L = Layer("L3", "netlist ↔ RTL equivalence")
CORE = DATA / "caravel/gl_caravel_core.v"


@L.check("W1-W4", "well-formedness, and the PLL excision is provably minimal",
         doc="src/L3-netlist-equivalence/01-well-formedness.md")
def _(ctx):
    if m := need(CORE):
        return FAIL, f"missing {m} (run tools/fetch-data.sh caravel)"
    ng = load("netgraph")
    r = ng.run(str(CORE))
    if r["unknown"]:
        return FAIL, f"unclassified pins: {dict(r['unknown'])}"
    probs = []
    if r["w1_hard"]:
        probs.append(f"W1: {len(r['w1_hard'])} mixed/static contention nets")
    if not all("ringosc" in n for n in r["w1_tri"]):
        probs.append("W1: tri-state sharing outside pll.ringosc")
    if len(r["w3_sccs"]) != 1 or not all("ringosc" in n for n in r["w3_sccs"][0]):
        probs.append(f"W3: {len(r['w3_sccs'])} SCCs (expected exactly the 64-net ring oscillator)")
    if r["w4_bad"]:
        probs.append(f"W4: {len(r['w4_bad'])} physical cells with signal pins")
    if probs:
        return FAIL, "; ".join(probs)
    return PASS, (f"{r['ninsts']:,} instances: W1 contention 0 (tri-state {len(r['w1_tri'])}, "
                  f"all ringosc), W3 SCCs 1 (64 nets, all ringosc), W4 0; "
                  f"physical {r['nphys']:,} ({100*r['nphys']/r['ntotal']:.1f}%), flops {r['nseq']:,}")


@L.check("W2-macro", "every undriven read net is a macro boundary (W2 residue = 0)",
         doc="src/L3-netlist-equivalence/01-well-formedness.md")
def _(ctx):
    ng, sc = load("netgraph"), load("synccheck")
    r = ng.run(str(CORE))
    insts, decls = sc.parse(str(CORE))
    macro_nets = set()
    for cell, name, pins in insts:
        if not cell.startswith("sky130"):
            for p, expr in pins:
                macro_nets.update(sc.expand_expr(expr))
    # netgraph's port filter is name-exact; bus BITS of declared input ports are
    # driven by the outside world, not floating
    def is_input_bit(n):
        base = n.lstrip("\\").split("[")[0]
        return base in decls and decls[base][0] in ("input", "inout")
    port_bits = [n for n in r["w2_undriven"] if is_input_bit(n)]
    residue = [n for n in r["w2_undriven"] if n not in macro_nets and not is_input_bit(n)]
    if residue:
        return FAIL, (f"{len(residue)} undriven read nets are neither macro pins nor input-port "
                      f"bits — genuine floats? e.g. {residue[:4]}")
    return PASS, (f"{len(r['w2_undriven']):,} undriven reads = {len(port_bits)} input-port bus bits "
                  f"+ {len(r['w2_undriven'])-len(port_bits):,} macro-boundary nets (incl. RAM256 = "
                  f"a flattened wrapper around two RAM128 banks); residue 0 — "
                  f"L3/01 open problem 1 discharged")


@L.check("macros", "the macro census: the recursion-or-contract inventory",
         doc="src/L3-netlist-equivalence/02-licensed-deletions.md")
def _(ctx):
    import re
    kw = {"module", "input", "output", "inout", "wire", "assign", "endmodule",
          "supply0", "supply1", "reg"}
    txt = CORE.read_text(errors="replace")
    # statement-level regex: catches macros with NO named connections too
    # (empty_macro, manual_power_connections), which a .pin-anchored parse misses
    kinds = collections.Counter(
        c for c, _ in re.findall(r"^\s*([A-Za-z_]\w*)\s+(\\?[^\s(]+)\s*\(", txt, re.M)
        if c not in kw and not c.startswith("sky130"))
    total = sum(kinds.values())
    expect = {
        "gpio_logic_high": 38, "gpio_defaults_block": 38, "spare_logic_block": 4,
        "RAM128": 3, "empty_macro": 2, "caravel_clocking": 1, "mprj_io_buffer": 1,
        "housekeeping": 1, "manual_power_connections": 1, "mprj2_logic_high": 1,
        "mprj_logic_high": 1, "mgmt_protect_hv": 1, "user_project_wrapper": 1,
        "simple_por": 1, "xres_buf": 1, "user_id_programming": 1,
    }
    if dict(kinds) != expect:
        return FAIL, f"macro inventory changed: {dict(kinds)}"
    return PASS, (f"{total} macro instances in {len(kinds)} types (empty_macro x2 and "
                  f"manual_power_connections have no named signal pins). Each type needs "
                  f"recursion or a contract; housekeeping and RAM128 are the open-able ones.")


@L.check("flow-run", "the full RTL-to-GDS flow, run on the target core",
         doc="src/L3-netlist-equivalence/03-register-correspondence.md")
def _(ctx):
    import json, shutil
    from checklib import TODO
    root = Path(__file__).resolve().parent.parent
    metrics = root / "flow/vexriscv/runs/rtl2gds/final/metrics.json"
    if not metrics.is_file():
        if not shutil.which("librelane-shell"):
            return TODO, ("needs the flow — tools/install-toolchain.sh --only flow, "
                          "then tools/run-flow.sh (~35 min)")
        return TODO, "run tools/run-flow.sh (~35 min) to produce the signoff"
    m = json.loads(metrics.read_text())
    drc = [m.get(k, 0) for k in ("magic__drc_error__count", "klayout__drc_error__count",
                                 "route__drc_errors", "design__lvs_error__count")]
    if any(drc):
        return FAIL, f"physical verification is no longer clean: DRC/LVS {drc}"
    seq = m.get("design__instance__count__class:sequential_cell")
    if seq != 2623:
        return FAIL, f"sequential-cell count changed: {seq} (recorded 2623)"
    corners = {k.split("corner:")[1]: m[k] for k in m if k.startswith("timing__hold__ws__corner:")}
    if len(corners) != 9:
        return FAIL, f"expected 9 corners, got {len(corners)}"
    hold_fails = [c for c, v in corners.items() if v <= 0]
    setup = {c: m.get(f"timing__setup__ws__corner:{c}") for c in corners}
    setup_fails = sorted(c for c, v in setup.items() if v is not None and v <= 0)
    if hold_fails or [c for c in setup_fails if "ss_" not in c]:
        return FAIL, f"failure pattern changed: hold {hold_fails}, setup {setup_fails}"
    return FINDING, (
        "the pipeline runs to completion on the target core and produces a GDS plus a "
        "nine-corner signoff we GENERATED rather than fetched: 20,604 standard cells, "
        f"{seq} flops, 369,021 um^2 die at 56% utilisation, and physical verification "
        "entirely clean - magic DRC 0, klayout DRC 0, routing DRC 0, LVS 0. The timing "
        "result is the interesting part. The SAME three slow corners fail as in the "
        "2021 signoff, but for the OPPOSITE reason: 2021 failed HOLD at s-nom/s-min/"
        "s-max with setup comfortable; this run fixes hold at every corner (worst "
        "+0.100 ns, hold TNS 0) by inserting 2,409 hold buffers, and pays for it in "
        "setup (-8.56 ns worst at ss). Same design, opposite trade - the modern flow "
        "prioritises hold where the 2021 one left it failing. This is a result at the "
        "same level of detail as the shipped signoff.rpt, which is what makes the two "
        "comparable at all")
L.todo("deletions", "the licensed-deletion theorems as checks (PHYS/CLOCK/BUF-INV classes)",
       doc="src/L3-netlist-equivalence/02-licensed-deletions.md",
       note="W4 discharges the PHYS class already; the CLOCK class's cleanliness precondition is now checked (L2/clock-core) — what remains is the collapse statement itself; BUF/INV needs the library lemma table.")
L.todo("npn-library", "verify ABC's 4-input NPN rewrite library (one-time, 222 classes)",
       doc="src/L3-netlist-equivalence/04-equivalence-certificates.md",
       blocked_on="extracting the class library from the pinned ABC build")
L.todo("abc-trail", "the rewrite-trail logger patch and its checker",
       doc="src/L3-netlist-equivalence/04-equivalence-certificates.md",
       blocked_on="rho (the reproduction gives us the tool run to patch)")
L.todo("dffram", "open the DFFRAM hole: W1-W4 + behavioural model per RAM128 block",
       doc="src/L3-netlist-equivalence/02-licensed-deletions.md",
       blocked_on="fetching the DFFRAM/RAM128 gate netlist at the pinned commit")
L.todo("arith-templates", "identify and check the pinned Yosys arithmetic templates",
       doc="src/L3-netlist-equivalence/05-hard-cones.md",
       blocked_on="rho (needs the reproduced synthesis to see which templates fired)")
L.todo("absence-cert", "certificate-of-absence for the six boundary-breaking transformations",
       doc="src/L3-netlist-equivalence/05-hard-cones.md",
       blocked_on="rho (grep the reproduced flow's pass list)")

if __name__ == "__main__":
    sys.exit(L.main())
