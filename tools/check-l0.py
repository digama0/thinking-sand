#!/usr/bin/env python3
"""check-l0 — L0 (device physics): obligations as an executable scoreboard.

The layer is analysis-dominated; its checker-shaped fragments are the
combinatorial cut-discipline checks (blocked on transistor netlists) and the
per-cell enclosure experiment (blocked on validated-numerics tooling). The
EXTERN entries are the axiom-register material a program cannot reach.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer

L = Layer("L0", "device physics and the digital abstraction")

L.todo("ccc", "C1-C3: channel-connected components, PUN/PDN duality, bistables CCC-internal, per cell",
       doc="src/L0-device-physics/09-cut-discipline.md",
       blocked_on="extracted transistor netlists for the library cells (magic/netgen over data/pdk GDS, "
                  "or fetching the PDK spice models at pinned SHAs)")
L.todo("v1a-tristate", "the non-static-CMOS exception list (einv*/ebuf/conb) with per-cell contracts",
       doc="src/L0-device-physics/09-cut-discipline.md",
       blocked_on="ccc (same transistor netlists)")
L.todo("inv1-enclosure", "the inv_1 end-to-end enclosure experiment against the shipped Liberty oracle",
       doc="src/L0-device-physics/03-cell-enclosures.md",
       blocked_on="an interval DAE integrator wired to an interval BSIM4 evaluation (the layer's central build)")
L.todo("envelope-num", "numeric envelope margins: operating voltage vs avalanche rating, F2 slew sites vs crowbar",
       doc="src/L0-device-physics/07-operating-envelope.md",
       blocked_on="the PDK device ratings at pinned SHAs")
L.todo("noise-exponent", "the thermal-discharge arithmetic as a checked computation (barrier / kT per node class)",
       doc="src/L0-device-physics/06-error-model.md",
       note="pure arithmetic over C, V, T once node capacitances are extracted; cheap after L1 extraction exists")
L.todo("quantum-budget", "gate leakage + RTN + dopant scatter vs the noise-margin budget (L0/08 open problem 2)",
       doc="src/L0-device-physics/08-quantum-floor.md",
       blocked_on="the SKY130 BSIM4 model cards at pinned SHAs")
L.extern("E1", "the compact-model enclosure contains the true device",
         doc="src/axioms.md",
         note="the tower's one physical axiom; validated by measurement, not checkable from shipped data")
L.extern("M1-M8", "the open mathematics (uniqueness, screening, lumping, monotonicity, bridge, constants, regimes, eigenvalue)",
         doc="src/axioms.md",
         note="proof-phase material by definition; listed so the scoreboard is the complete census")

if __name__ == "__main__":
    sys.exit(L.main())
