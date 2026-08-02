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


L.todo("config-record", "extract the shipped configuration record (LiteX CSR map, cache geometry, VexRiscv plugin parameters)",
       doc="src/L5-microarchitecture/00-microarchitecture.md",
       note="the shipped RTL pair is now pinned (mgmt_core.v + VexRiscv_MinDebugCache.v); the record is read out of them — checker-shaped, next in line for this layer")
L.todo("fsm-graph", "extract the 8-state FSM graph and its per-instruction path bounds",
       doc="src/L5-microarchitecture/01-refinement.md",
       blocked_on="a Verilog front end for picorv32.v (shared with L4's parser needs)")
L.todo("wcet-table", "derive w(i), the per-instruction WCET table, and validate against the README's cycle counts",
       doc="src/L5-microarchitecture/01-refinement.md",
       blocked_on="fsm-graph, plus B(config) from L7's bus contract")
L.todo("rvfi-alpha", "define alpha against RVFI and check it on simulation traces",
       doc="src/L5-microarchitecture/01-refinement.md",
       blocked_on="a simulation harness (Verilator) plus the RVFI-enabled build")
L.todo("decode-sweep", "decode exhaustiveness/exclusivity of the ~50 one-hot flags vs the Sail decoder",
       doc="src/L5-microarchitecture/03-instruction-obligations.md",
       blocked_on="config-record (the partition depends on it) and L6's imported decoder")
L.todo("ic3-calibrate", "IC3 calibration on invariant clauses 1/2/4 (sizes the layer's real cost)",
       doc="src/L5-microarchitecture/02-invariant.md",
       blocked_on="a model-checking harness over the elaborated core (proof-adjacent; deferred by phase)")
L.todo("bus-guarantee", "check G1-G3 and the LA preview lemma on testbench traces",
       doc="src/L5-microarchitecture/04-memory-pcpi.md",
       blocked_on="the simulation harness; a trace checker is checker-phase work once traces exist")
L.todo("irq-anchors", "extract the IRQ-instruction uses from shipped firmware (S3's anchor corpus)",
       doc="src/L5-microarchitecture/05-interrupts.md",
       blocked_on="fetching the firmware tree at a pinned commit")

if __name__ == "__main__":
    sys.exit(L.main())
