#!/usr/bin/env python3
"""check-l5 — L5 (microarchitecture): obligations as an executable scoreboard.

Nothing here runs yet: every obligation is blocked on either the configuration
record (a fetch decision) or the proof-shaped work the checkers phase defers.
The stubs are the layer's structured TODO list, each pointing into the book.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer, PASS, FAIL, DATA, need

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
    ok = (not r["compressed"] and not r["muldiv"] and not r["atomics"]
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
L.todo("bus-guarantee", "check the Wishbone guarantee clauses (Gi/Gd) on testbench traces",
       doc="src/L5-microarchitecture/04-buses-debug.md",
       blocked_on="the simulation harness; a trace checker is checker-phase work once traces exist")
L.todo("irq-anchors", "extract the interrupt-facing firmware paths (the residual-spec anchor corpus)",
       doc="src/L5-microarchitecture/05-interrupts.md",
       blocked_on="fetching the BIOS/firmware tree at a pinned commit")

if __name__ == "__main__":
    sys.exit(L.main())
