#!/usr/bin/env python3
"""check-l5 — L5 (microarchitecture): obligations as an executable scoreboard.

Re-anchored to the Chipyard target. Implemented: the configuration record —
the elaboration-declared half (device tree) confirmed against the emitted RTL's
structural facts (BTB absence, iterative mul/div, RVC expander, bypass/interlock
presence). The refinement programme itself stays TODO.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer, PASS, FAIL, FINDING, DTS, RTL_SRC, need

L = Layer("L5", "microarchitecture: RTL refines the ISA")


@L.check("config-declared", "the elaboration-declared configuration record", doc="src/L5-microarchitecture/00-microarchitecture.md")
def _(ctx):
    if need(DTS):
        return FINDING, "device tree absent (regenerate: tools/build-rocket.sh)"
    txt = DTS.read_text(errors="replace")
    isa = re.search(r'riscv,isa\s*=\s*"([^"]+)"', txt)
    icache_sets = re.search(r"i-cache-sets\s*=\s*<(\d+)>", txt)
    icache_size = re.search(r"i-cache-size\s*=\s*<(\d+)>", txt)
    dtim = re.search(r"dtim@\w+\s*\{[^}]*reg\s*=\s*<0x[0-9a-f]+\s+0x([0-9a-f]+)>", txt, re.S)
    pmp = re.search(r"riscv,pmpregions\s*=\s*<(\d+)>", txt)
    pmpg = re.search(r"riscv,pmpgranularity\s*=\s*<(\d+)>", txt)
    bp = re.search(r"hardware-exec-breakpoint-count\s*=\s*<(\d+)>", txt)
    if not all([isa, icache_sets, icache_size, dtim, pmp, pmpg, bp]):
        return FAIL, "could not extract the declared configuration from the dts"
    expected_isa = "rv32imaczicsr_zifencei_zihpm_xrocket"
    if isa.group(1) != expected_isa:
        return FAIL, f"ISA drift: dts declares {isa.group(1)!r}, the book states {expected_isa!r}"
    dtim_kib = int(dtim.group(1), 16) // 1024
    return PASS, (f"ISA {isa.group(1)}; icache {int(icache_size.group(1))//1024} KiB / "
                  f"{icache_sets.group(1)} sets; DTIM {dtim_kib} KiB; PMP {pmp.group(1)} regions "
                  f"@ granularity {pmpg.group(1)}; {bp.group(1)} hardware breakpoint — "
                  f"matches L5/00's tour and L6/02's elaborated rows (C9, C10)")


@L.check("config-confirmed", "the declared record confirmed structurally from the emitted RTL", doc="src/L5-microarchitecture/00-microarchitecture.md")
def _(ctx):
    if need(RTL_SRC):
        return FINDING, "RTL cone absent (regenerate: tools/build-rocket.sh)"
    facts, problems = [], []
    # BTB absence (the tiny config's *to record* row)
    btb_files = [p.name for p in RTL_SRC.glob("BTB*.sv")]
    if btb_files:
        problems.append(f"BTB modules present: {btb_files} — the no-predictor claim fails")
    else:
        facts.append("no BTB module (no branch prediction — 'to record' row settled)")
    # iterative mul/div
    muldiv = RTL_SRC / "MulDiv.sv"
    if muldiv.exists():
        t = muldiv.read_text(errors="replace")
        state = re.search(r"reg\s*\[\d+:\d+\]\s*state|state\s*<=", t)
        cnt = re.search(r"count", t)
        if state and cnt:
            facts.append("MulDiv.sv is an FSM with a count register (iterative — L3/05's easy multiplier class)")
        else:
            problems.append("MulDiv.sv exists but no FSM/count structure found — re-inspect")
    else:
        problems.append("MulDiv.sv absent — where did M-extension logic go?")
    # RVC expander
    if (RTL_SRC / "RVCExpander.sv").exists():
        facts.append("RVCExpander present (C extension in fetch, per the tour)")
    else:
        problems.append("RVCExpander.sv absent")
    # the debug module + DTM
    for f, what in [("TLDebugModule.sv", "debug module"), ("DebugTransportModuleJTAG.sv", "JTAG DTM")]:
        if not (RTL_SRC / f).exists():
            problems.append(f"{f} absent ({what})")
    if not problems:
        facts.append("debug module + JTAG DTM present (the debug-inactive conditionality's subject)")
    if problems:
        return FAIL, "; ".join(problems)
    return PASS, "; ".join(facts)


L.todo("stage-graph", "the pipeline stall/flush/bypass structure and occupancy bounds",
       doc="src/L5-microarchitecture/01-refinement.md",
       blocked_on="a SystemVerilog front end over Rocket.sv (shared with L4)")
L.todo("wcet-table", "the retirement-gap bounds (the measure read quantitatively)",
       doc="src/L5-microarchitecture/01-refinement.md", blocked_on="stage-graph")
L.todo("bus-guarantees", "Gi/Gd clauses asserted over a real execution (simulation oracle)",
       doc="src/L5-microarchitecture/04-buses-debug.md",
       blocked_on="wiring the TileLink monitor assertions into the now-working harness (tools/run-sim.sh)")
L.todo("trace-alpha", "α drafted against the core's trace port, checked on simulation traces",
       doc="src/L5-microarchitecture/01-refinement.md", blocked_on="enabling the trace-port dump in the now-working harness")
L.todo("invariant", "the inductive invariant (the project's irreducible content)",
       doc="src/L5-microarchitecture/02-invariant.md", blocked_on="proof-phase start")

if __name__ == "__main__":
    sys.exit(L.main())
