# Glossary

The flow's jargon, in the order a design passes through it. Terms are used throughout the layer documents without re-explanation.

**Design description**

| | |
|---|---|
| **RTL** | Register Transfer Level — the behavioural Verilog a human writes (`always` blocks, buses, arithmetic) |
| **netlist** | the same design as a flat graph of library cells and wires, after synthesis. Also "gate-level" |
| **ISA** | Instruction Set Architecture — the programmer-visible contract the whole project is proving the chip meets |
| **SoC** | System on Chip — core plus memory and peripherals on one die |

**The cell library and process**

| | |
|---|---|
| **PDK** | Process Design Kit — everything the foundry supplies about a process: cell layouts, timing, DRC rules, device models |
| **standard cell** | a pre-drawn logic gate (inverter, NAND, flip-flop) of fixed height, ~400 of them; designs are assembled from these |
| **Liberty** (`.lib`) | per-cell timing/power tables — delay as a 2-D function of input slew and output load, one file per PVT corner |
| **BSIM** | the fitted compact model giving a transistor's current from its terminal voltages. The project's one physical axiom (E1) |
| **PVT corner** | a (process, voltage, temperature) extreme the design must work at; SKY130 HD ships 17 |

**Physical implementation**

| | |
|---|---|
| **pad / IO cell** | the chip's physical interface: the *bond pad* is a bare metal square (~60 µm) on the die perimeter that a bond wire attaches to; the *IO cell* behind it is a large circuit doing level shifting (1.8 V core ↔ 3.3 V world), ESD protection, drive-strength output staging, input buffering, and direction control. In Caravel these are `sky130_fd_io` macros — at 60–77k polygons each, individually bigger than most logic blocks. `obs` is defined at the pad metal: the last point that is still "the chip" |
| **P&R** | Place and Route — choosing where each cell sits and how wires connect them |
| **LEF / DEF** | the abstract views P&R works in: cell outlines and pin locations (LEF), placements and routes (DEF) |
| **GDS / GDSII** | the layout interchange format — layer-tagged polygons; what goes to the mask shop |
| **CTS** | Clock Tree Synthesis — building the buffer tree that distributes the clock |
| **OPC** | Optical Proximity Correction — deliberately distorting the mask so the *printed* shape matches intent |
| **fill / decap / tap / antenna diode** | non-logic cells inserted for density, supply stability, well biasing and process protection. **~85% of instances** |

**Checks**

| | |
|---|---|
| **DRC** | Design Rule Check — geometric rules (min width, min spacing, enclosure) the layout must satisfy |
| **LVS** | Layout Versus Schematic — extract a netlist from the geometry and check it matches the intended one |
| **STA** | Static Timing Analysis — exhaustive longest/shortest-path delay analysis; no simulation |
| **setup / hold** | the two timing constraints. Setup is a *performance* limit (fixable by slowing the clock); **hold is a correctness limit, unfixable at any frequency** |
| **SDC** | the timing-constraint file. Also carries *exceptions* — human claims that a path need not be checked, which no tool verifies |
| **CEC** | Combinational Equivalence Check — proving two netlists compute the same function |

**Physics and reliability**

| | |
|---|---|
| **SEU** | Single Event Upset — a particle strike flipping a stored bit. Poisson, does not shrink with margin |
| **metastability** | a flip-flop sampled mid-transition settles after an unbounded time; the one failure that breaks the digital abstraction rather than giving a wrong value |
| **X** | the third logical value: *untracked* — the wire is somewhere in the electrically safe region but the abstraction has lost its value (settled-but-unpredicted, mid-swing, saddle, unpowered). Drive-recoverable, which is what distinguishes untracked from broken; reset is an X-elimination procedure |
| **ECC** | Error Correcting Code — redundancy that repairs upsets, at the cost of a layout-level independence assumption |
| **latch-up** | a parasitic thyristor turning on — a *second solution branch* of the device equations, which tap cells exist to destroy |
| **electromigration** | current gradually voiding a wire; a wearout criterion over a trajectory, not a state |
| **POR** | Power-On Reset — the circuit that holds the chip in reset from power-good until the supply is stable, supplying each power epoch's initial state. Caravel's (`simple_por`) is an RC ramp detector: it catches rise-from-zero, not sags |
| **BOR** | Brown-Out Reset — a supervisor that asserts reset whenever the supply *sags* below operating minimum, closing the gray band between "logic misbehaves" and "state is lost" that a ramp-only POR leaves open. Fail-safe by construction: below its own validity range, reset is the passive default |
| **MCU** | microcontroller — a commodity single-chip computer (STM32, AVR). Cited here as precedent: every MCU ships a BOR, so the gray-band fix is a solved industrial problem, not a research item |
