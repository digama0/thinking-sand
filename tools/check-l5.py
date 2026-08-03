#!/usr/bin/env python3
"""check-l5 — L5 (microarchitecture): obligations as an executable scoreboard.

Nothing here runs yet: every obligation is blocked on either the configuration
record (a fetch decision) or the proof-shaped work the checkers phase defers.
The stubs are the layer's structured TODO list, each pointing into the book.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer, PASS, FAIL, DATA, need, load

L = Layer("L5", "microarchitecture: RTL refines the ISA")

@L.check("core-variant", "the shipped core is VexRiscv MinDebugCache, identified from its own registers",
         doc="src/L5-microarchitecture/00-microarchitecture.md")
def _(ctx):
    import re
    gl = DATA / "caravel/gl_caravel_core.v"
    vex = DATA / "mgmt/VexRiscv_MinDebugCache.v"
    if m := need(gl, vex):
        return FAIL, f"missing {m}"
    plugins = set(re.findall(r"([A-Za-z]+Plugin)", gl.read_text(errors="replace")))
    expect = {"BranchPlugin", "CsrPlugin", "DBusSimplePlugin", "DebugPlugin",
              "HazardSimplePlugin", "IBusCachedPlugin", "LightShifterPlugin", "RegFilePlugin"}
    vexp = set(re.findall(r"([A-Za-z]+Plugin)", vex.read_text(errors="replace")))
    if plugins != expect or not plugins <= vexp or "MulDivIterativePlugin" in plugins:
        return FAIL, f"plugin census changed: GL={sorted(plugins)}"
    return PASS, ("GL plugin registers = {Branch, Csr, DBusSimple, Debug, HazardSimple, "
                  "IBusCached, LightShifter, RegFile} ⊆ MinDebugCache's set, and the "
                  "stateful MulDivIterativePlugin (LiteDebug's marker) is absent: "
                  "pipelined RV32I + I-cache + machine-mode CSRs + debug, no hardware M")


@L.check("config-record", "the shipped configuration record, extracted and pinned",
         doc="src/L5-microarchitecture/00-microarchitecture.md")
def _(ctx):
    from checklib import load
    cr = load("config-record")
    r = cr.record()
    ok = (not r["compressed"] and not r["muldiv"] and not r["atomics"] and r["wfi"]
          and r["csrs"] == [0x300, 0x304, 0x305, 0x341, 0x342, 0x343, 0x344, 0xBC0, 0xFC0]
          and r["icache"] == {"bytes": 64, "lines": 2, "line_bytes": 32,
                              "tag_bits": 28, "ways": 1}
          and r["hazards"].startswith("interlock")
          and r["reset_vector"]["init"] == "0x10000000"
          and r["sw_timer_irq_tied_0"] and r["ext_irq_array_bits"] == 32)
    if not ok:
        return FAIL, f"configuration record changed: {r}"
    return PASS, ("RV32I (no C/M/A); CSRs mstatus/mie/mtvec/mepc/mcause/mtval/mip + "
                  "custom 0xBC0/0xFC0 (no mscratch, no misa, NO counters); I-cache 64 B = "
                  "2x32 B direct-mapped; hazards interlock-only (writeBackBuffer match "
                  "stalls); reset vector = CSR-writable register init 0x10000000 (flash "
                  "XIP base); software/timer interrupts tied to 0, all IRQs via the "
                  "32-bit external array; both buses Wishbone with burst signals")
@L.check("pipeline", "the shipped pipeline's measured shape (stages, cache mapping, no predictor)",
         doc="src/L5-microarchitecture/00-microarchitecture.md")
def _(ctx):
    import re
    vex = DATA / "mgmt/VexRiscv_MinDebugCache.v"
    if m := need(vex):
        return FAIL, f"missing {m}"
    txt = vex.read_text(errors="replace")
    # count DECLARED, SYNTHESIZABLE registers per bank: declaration-anchored
    # (usage sites and derived wires share the prefix) and excluding the
    # simulation-only *_string waveform-debug regs (absent from the GL netlist).
    # This measurement corrected the chapter's first published numbers twice -
    # a sloppy grep gave 38/16/12, declarations-with-strings 24/13/10.
    decls = set(re.findall(r"^\s*reg\s*(?:\[[^\]]*\]\s*)?([A-Za-z_0-9]+)\s*(?:;|=)", txt, re.M))
    banks = {p: len([n for n in decls if n.startswith(p) and not n.endswith("_string")])
             for p in ("decode_to_execute_", "execute_to_memory_", "memory_to_writeBack_")}
    ways2 = len(re.findall(r"ways_1|banks_1", txt))
    pred = len(re.findall(r"BranchPredictor|BTB|branch.*predict", txt))
    expect = {"decode_to_execute_": 17, "execute_to_memory_": 12, "memory_to_writeBack_": 9}
    if banks != expect or ways2 != 0 or pred != 0:
        return FAIL, f"pipeline census changed: banks={banks}, multiway={ways2}, predictor={pred}"
    return PASS, ("4 main stages behind the cached fetch: 17/12/9 synthesizable "
                  "inter-stage registers; I-cache single-way single-bank (direct-mapped); "
                  "zero branch-prediction structures — the shape L5/00's tour describes")


L.todo("stage-graph", "extract the pipeline stall/flush/arbitration structure and per-instruction occupancy bounds",
       doc="src/L5-microarchitecture/01-refinement.md",
       blocked_on="a Verilog front end for the VexRiscv source (shared with L4's parser needs)")
L.todo("wcet-table", "derive w(i), the per-instruction WCET table, and validate against the README's cycle counts",
       doc="src/L5-microarchitecture/01-refinement.md",
       blocked_on="fsm-graph, plus B(config) from L7's bus contract")
L.todo("rvfi-alpha", "define alpha against RVFI and check it on simulation traces",
       doc="src/L5-microarchitecture/01-refinement.md",
       blocked_on="a simulation harness (Verilator) plus the RVFI-enabled build")
L.todo("decode-sweep", "decode equivalence of the generated decoder vs the Sail decoder, plus the trap sweep",
       doc="src/L5-microarchitecture/03-instruction-obligations.md",
       blocked_on="L6's imported decoder (the partition now follows the measured configuration record)")
L.todo("ic3-calibrate", "IC3 calibration on invariant clauses 1/2/4 (sizes the layer's real cost)",
       doc="src/L5-microarchitecture/02-invariant.md",
       blocked_on="a model-checking harness over the elaborated core (proof-adjacent; deferred by phase)")
@L.check("retire-gap", "the measure's B-dependence, measured: gap_max is affine in the bus bound",
         doc="src/L5-microarchitecture/01-refinement.md")
def _(ctx):
    from checklib import TODO
    root = Path(__file__).resolve().parent.parent
    sweep = root / "build-sim/sweep.txt"
    if not sweep.is_file():
        return TODO, "run tools/run-sim.sh --sweep (needs iverilog and a built image)"
    rows = [tuple(map(int, l.split())) for l in sweep.read_text().split("\n") if l.strip()]
    if len(rows) < 3:
        return FAIL, f"sweep has too few points: {rows}"
    slopes = {(rows[i + 1][1] - rows[i][1]) / (rows[i + 1][0] - rows[i][0])
              for i in range(len(rows) - 1)}
    if len(slopes) != 1:
        return FAIL, f"gap_max is not affine in B: points {rows}, slopes {slopes}"
    slope = slopes.pop()
    cr = load("config-record")
    line_words = cr.record()["icache"]["line_bytes"] // 4
    if slope != line_words:
        return FAIL, (f"slope {slope} != the measured cache line length {line_words} words "
                      f"— the miss model and the geometry disagree")
    return PASS, (f"L5/01 claims the I-cache-miss stutter is f(B), the bus latency bound. "
                  f"Measured over B = {', '.join(str(r[0]) for r in rows)}: the worst "
                  f"retirement gap is exactly affine, gap_max = {rows[0][1]} + {slope:.0f}B, "
                  f"and the SLOPE equals the {line_words}-word cache line measured "
                  f"independently in the configuration record - each word of the burst "
                  f"refill pays the bus latency once. The measure's shape and the cache "
                  f"geometry corroborate each other from different directions")

@L.check("bus-guarantee", "the Wishbone guarantee clauses, checked on a real execution trace",
         doc="src/L5-microarchitecture/04-buses-debug.md")
def _(ctx):
    import re, shutil
    from checklib import TODO
    root = Path(__file__).resolve().parent.parent
    log = root / "build-sim/sim.log"
    if not log.is_file():
        if not shutil.which("iverilog"):
            return TODO, ("needs a simulator — tools/install-toolchain.sh --only cad, "
                          "then tools/build-firmware.sh && tools/run-sim.sh")
        return TODO, "run tools/build-firmware.sh && tools/run-sim.sh"
    m = re.search(r"SUMMARY cycles=(\d+) ibus_txn=(\d+) dbus_txn=(\d+) "
                  r"dbus_writes=(\d+) violations=(\d+)", log.read_text())
    if not m:
        return FAIL, "build-sim/sim.log has no SUMMARY line — the run did not finish"
    cycles, itxn, dtxn, dwr, viol = (int(g) for g in m.groups())
    if viol:
        return FAIL, f"{viol} bus-guarantee violations in {cycles} cycles — see build-sim/sim.log"
    if itxn == 0 or dtxn == 0:
        return FAIL, f"the core issued no traffic (ibus {itxn}, dbus {dtxn}) — it did not run"
    if dwr != 14:
        return FAIL, (f"{dwr} data writes, expected the 14 the test payload stores — "
                      f"the image and the trace disagree")
    return PASS, (f"the shipped core EXECUTES the built image and its bus discipline holds: "
                  f"{cycles:,} cycles, {itxn} instruction fetches, {dtxn} data transactions "
                  f"of which {dwr} writes - exactly the 14 bytes the payload stores, so the "
                  f"program really ran - and ZERO violations of the L5/04 clauses (STB=>CYC, "
                  f"request attributes stable until ACK, bounded termination, iBus never "
                  f"writes). The monitor is validated by a negative control rather than "
                  f"trusted: tools/run-sim.sh --negative stretches memory latency past the "
                  f"termination bound and the clause duly fires")
@L.check("irq-anchors", "the interrupt-facing firmware paths, extracted as spec anchors",
         doc="src/L5-microarchitecture/05-interrupts.md")
def _(ctx):
    from checklib import load, DATA, need
    for f in ("crt0_vex.S", "isr.c", "irq_vex.h"):
        if m := need(DATA / "mgmt/firmware" / f):
            return FAIL, f"missing {m} (run tools/fetch-data.sh checks)"
    fa = load("fwanchors")
    c, u, i = fa.crt0(), fa.csr_usage(), fa.isr()
    if not (c["mtvec_written"] and c["mtvec_before_mie"] and c["trap_entry_mret"]
            and c["saves_caller_saved"] == 16):
        return FAIL, f"crt0 discipline changed: {c}"
    if c["mie_value"] != 0x880:
        return FAIL, f"crt0 mie value changed: {c['mie_value']}"
    if "CSR_IRQ_PENDING" in u["writes"] or "LITERAL_0xFC0" in u["writes"]:
        return FAIL, f"the firmware writes the read-only pending CSR: {u}"
    if not (i["defined"] and i["uses_setmask"]):
        return FAIL, f"isr shape changed: {i}"
    return PASS, ("the shipped firmware is consistent with the measured core semantics: "
                  "crt0 writes mtvec BEFORE setting mie (the discipline forced by mtvec "
                  "having no reset value), the trap entry saves the 16 caller-saved "
                  "registers and returns with mret, and across the corpus the mask CSR "
                  "(0xBC0) is read and written while the pending CSR (0xFC0) is only "
                  "ever READ - the trapping write is never exercised. One stale "
                  "expectation pinned: crt0 sets mie = 0x880 (MTIE|MEIE), but MTIE is "
                  "structurally dead on this SoC - the timer wire is tied to zero and "
                  "the LiteX timer arrives through external-array bit 0")

if __name__ == "__main__":
    sys.exit(L.main())
