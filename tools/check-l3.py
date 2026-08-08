#!/usr/bin/env python3
"""check-l3 — L3 (netlist ↔ RTL equivalence): obligations as an executable scoreboard.

Re-anchored to the Chipyard target: the netlists are the flow's own outputs
(synthesis and post-route). Implemented: W1–W4 over both netlists via
netgraph.py (extended with the SRAM22 macro pin tables), the macro-instance
census, and the deletion-class fractions. The TODOs are ρ and the CEC.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer, PASS, FAIL, FINDING, SYN_NL, FINAL_NL, SRAM_KINDS, need
import netgraph

L = Layer("L3", "netlist ↔ RTL equivalence")


def wcheck(path, label):
    missing = need(path)
    if missing:
        return FINDING, f"{label} netlist absent (rerun the flow): {missing[0]}"
    r = netgraph.run(str(path))
    if r["unknown"]:
        return FAIL, f"{label}: unclassified pins {dict(r['unknown'])} — extend the pin tables, never guess"
    problems = []
    if r["w1_hard"]:
        problems.append(f"W1: {len(r['w1_hard'])} contended nets")
    if r["w2_undriven"]:
        problems.append(f"W2: {len(r['w2_undriven'])} floating reads")
    if r["w3_sccs"]:
        problems.append(f"W3: {len(r['w3_sccs'])} combinational cycles")
    if r["w4_bad"]:
        problems.append(f"W4: {len(r['w4_bad'])} physical cells with signal pins")
    if problems:
        return FAIL, f"{label}: " + "; ".join(problems)
    tot, nphys, nseq = r["ntotal"], r["nphys"], r["nseq"]
    return PASS, (f"{label}: {tot:,} cells — W1 0 contended, W2 0 floating, W3 0 cycles "
                  f"(no on-die oscillator, structurally confirmed), W4 physical inert "
                  f"({nphys:,} = {100*nphys/tot:.1f}% physical, {nseq:,} sequential)")


@L.check("W-syn", "W1–W4 on the synthesis netlist", doc="src/L3-netlist-equivalence/01-well-formedness.md")
def _(ctx):
    return wcheck(SYN_NL, "synthesis")


@L.check("W-routed", "W1–W4 on the post-route netlist", doc="src/L3-netlist-equivalence/01-well-formedness.md")
def _(ctx):
    return wcheck(FINAL_NL, "post-route")


@L.check("macros", "the SRAM macro census: five instances of three kinds", doc="src/L3-netlist-equivalence/02-licensed-deletions.md")
def _(ctx):
    if need(SYN_NL):
        return FINDING, "synthesis netlist absent (rerun the flow)"
    insts, _, _ = netgraph.parse(str(SYN_NL))
    import collections
    got = collections.Counter(c for c, _, _ in insts if c.startswith("sram22_"))
    if dict(got) != SRAM_KINDS:
        return FAIL, f"macro census mismatch: expected {SRAM_KINDS}, netlist has {dict(got)}"
    return PASS, (f"exactly {sum(SRAM_KINDS.values())} macro instances of {len(SRAM_KINDS)} kinds "
                  f"({', '.join(f'{v}x {k}' for k, v in SRAM_KINDS.items())}) — the parametric-contract "
                  f"amortisation base (one proof per kind)")


@L.check("deletion-classes", "the physical/clock/logic deletion fractions of the routed netlist", doc="src/L3-netlist-equivalence/02-licensed-deletions.md")
def _(ctx):
    if need(FINAL_NL):
        return FINDING, "post-route netlist absent (rerun the flow)"
    r = netgraph.run(str(FINAL_NL))
    tot, nphys, nseq = r["ntotal"], r["nphys"], r["nseq"]
    import re
    nclk = sum(k for c, k in r["ncells"].items() if re.search(r"clkbuf|clkinv|clkdly|dlygate|dlymetal|dlclk", c))
    nlogic = tot - nphys - nclk
    return PASS, (f"{tot:,} instances: {nphys:,} physical ({100*nphys/tot:.1f}%, licensed by W4), "
                  f"{nclk:,} clock/delay ({100*nclk/tot:.1f}%, licensed by L2's collapse), "
                  f"{nlogic:,} logic+seq — the Mealy machine. Each class carries its deletion licence, "
                  f"none deleted by convention")


L.todo("rho", "register correspondence extracted from an instrumented synthesis run",
       doc="src/L3-netlist-equivalence/03-register-correspondence.md",
       blocked_on="the opt_dff/opt_merge logging patch to the flow's yosys invocation (F5)")
L.todo("macro-contracts", "the three SRAM contracts stated; tie-offs verified structurally",
       doc="src/L3-netlist-equivalence/02-licensed-deletions.md",
       blocked_on="authoring the contract format; the macro Verilog is the draft source")
L.todo("cec", "combinational equivalence RTL ↔ netlist by certificate at register boundaries",
       doc="src/L3-netlist-equivalence/04-equivalence-certificates.md",
       blocked_on="rho; the unmap-to-generic-gates route")
L.extern("F5-until-run", "whether ρ survives synthesis is decidable only by the instrumented run",
         doc="axioms.md",
         note="not an axiom — a decidable unknown; the register row stays open until the logging patch lands")

if __name__ == "__main__":
    sys.exit(L.main())
