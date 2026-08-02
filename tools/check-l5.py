#!/usr/bin/env python3
"""check-l5 — L5 (microarchitecture): obligations as an executable scoreboard.

Nothing here runs yet: every obligation is blocked on either the configuration
record (a fetch decision) or the proof-shaped work the checkers phase defers.
The stubs are the layer's structured TODO list, each pointing into the book.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer

L = Layer("L5", "microarchitecture: RTL refines the ISA")

L.todo("config-record", "extract the shipped picorv32 parameterisation (the configuration record)",
       doc="src/L5-microarchitecture/00-microarchitecture.md",
       blocked_on="fetching the management-SoC integration that instantiates picorv32 with parameters "
                  "(mgmt_core_wrapper.v instantiates an opaque mgmt_core; the binding site is in the "
                  "generated mgmt SoC source, which needs pinning like the rest of the data)")
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
