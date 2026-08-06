# Glossary

The jargon net for the whole book — hardware-flow terms first (in the order a design passes through the flow), then verification, timing, physics/mathematics, and reliability/test vocabularies. Terms are used throughout the layer documents without re-explanation; textbook-depth treatments are in the [reading list](reading-list.md).

## Design description

| | |
|---|---|
| **RTL** | Register Transfer Level — the behavioural Verilog a human writes (`always` blocks, buses, arithmetic) |
| **netlist** | the same design as a flat graph of library cells and wires, after synthesis. Also "gate-level" |
| **ISA** | Instruction Set Architecture — the programmer-visible contract the whole project is proving the chip meets |
| **SoC** | System on Chip — core plus memory and peripherals on one die |

## The cell library and process

| | |
|---|---|
| **PDK** | Process Design Kit — everything the foundry supplies about a process: cell layouts, timing, DRC rules, device models |
| **standard cell** | a pre-drawn logic gate (inverter, NAND, flip-flop) of fixed height, ~400 of them; designs are assembled from these |
| **Liberty** (`.lib`) | per-cell timing/power tables — delay as a 2-D function of input slew and output load, one file per PVT corner |
| **BSIM** | the fitted compact model giving a transistor's current from its terminal voltages. The project's one physical axiom (E1) |
| **PVT corner** | a (process, voltage, temperature) extreme the design must work at; SKY130 HD ships 17 |

## Physical implementation

| | |
|---|---|
| **pad / IO cell** | the chip's physical interface: the *bond pad* is a bare metal square (~60 µm) on the die perimeter that a bond wire attaches to; the *IO cell* behind it is a large circuit doing level shifting (1.8 V core ↔ 3.3 V world), ESD protection, drive-strength output staging, input buffering, and direction control. Here these are `sky130_fd_io` macros — at tens of thousands of polygons each, individually bigger than most logic blocks. `obs` is defined at the pad metal: the last point that is still "the chip" |
| **P&R** | Place and Route — choosing where each cell sits and how wires connect them |
| **LEF / DEF** | the abstract views P&R works in: cell outlines and pin locations (LEF), placements and routes (DEF) |
| **GDS / GDSII** | the layout interchange format — layer-tagged polygons; what goes to the mask shop |
| **CTS** | Clock Tree Synthesis — building the buffer tree that distributes the clock |
| **OPC** | Optical Proximity Correction — deliberately distorting the mask so the *printed* shape matches intent |
| **fill / decap / tap / antenna diode** | non-logic cells inserted for density, supply stability, well biasing and process protection. **~85% of instances** |

## Checks

| | |
|---|---|
| **DRC** | Design Rule Check — geometric rules (min width, min spacing, enclosure) the layout must satisfy |
| **LVS** | Layout Versus Schematic — extract a netlist from the geometry and check it matches the intended one |
| **STA** | Static Timing Analysis — exhaustive longest/shortest-path delay analysis; no simulation |
| **setup / hold** | the two timing constraints. Setup is a *performance* limit (fixable by slowing the clock); **hold is a correctness limit, unfixable at any frequency** |
| **SDC** | the timing-constraint file. Also carries *exceptions* — human claims that a path need not be checked, which no tool verifies |
| **CEC** | Combinational Equivalence Check — proving two netlists compute the same function |

## Physics and reliability

| | |
|---|---|
| **SEU** | Single Event Upset — a particle strike flipping a stored bit. Poisson, does not shrink with margin |
| **metastability** | a flip-flop sampled mid-transition settles after an unbounded time; the one failure that breaks the digital abstraction rather than giving a wrong value |
| **X** | the third logical value: *untracked* — the wire is somewhere in the electrically safe region but the abstraction has lost its value (settled-but-unpredicted, mid-swing, saddle, unpowered). Drive-recoverable, which is what distinguishes untracked from broken; reset is an X-elimination procedure |
| **ECC** | Error Correcting Code — redundancy that repairs upsets, at the cost of a layout-level independence assumption |
| **latch-up** | a parasitic thyristor turning on — a *second solution branch* of the device equations, which tap cells exist to destroy |
| **electromigration** | current gradually voiding a wire; a wearout criterion over a trajectory, not a state |
| **POR** | Power-On Reset — the circuit that holds the chip in reset from power-good until the supply is stable, supplying each power epoch's initial state. this design carries none on-die — the arrangement is board/harness territory (X4), and an RC ramp detector catches rise-from-zero, not sags |
| **BOR** | Brown-Out Reset — a supervisor that asserts reset whenever the supply *sags* below operating minimum, closing the gray band between "logic misbehaves" and "state is lost" that a ramp-only POR leaves open. Fail-safe by construction: below its own validity range, reset is the passive default |
| **MCU** | microcontroller — a commodity single-chip computer (STM32, AVR). Cited here as precedent: every MCU ships a BOR, so the gray-band fix is a solved industrial problem, not a research item |

## Verification and refinement

| | |
|---|---|
| **refinement (⊑)** | "every behaviour of the implementation is a behaviour the spec allows" — this project's notion of correctness; concretely, trace inclusion up to stuttering |
| **transition system** | states plus a step relation — the common shape of every spec-tower object |
| **Mealy machine** | a clocked finite-state machine whose outputs depend on state and current input — what a synchronous netlist *is* |
| **bisimulation** | two systems matching each other step-for-step in both directions; the equivalence L3 proves under the register map ρ |
| **stuttering / measure** | the implementation takes many steps per spec step; a measure function — a counter that strictly decreases — proves the stalling terminates. Read quantitatively (this core's measure components are constants), it yields per-instruction cycle bounds — see WCET |
| **UB, layered (spec UB)** | behaviour a spec leaves unspecified *at its own layer* while every layer below still holds: a reserved instruction (L6/03) havocs architectural state but the pipeline, bus, and envelope stay sound; an out-of-range knob (L7/05) floods X but the die stays safe. Never C-style anything-goes |
| **WCET** | worst-case execution time — a hard upper bound on how long code takes; an entire analysis discipline on cached/pipelined cores, literal addition of per-instruction bounds on this one (L5/01), and the input to L7/04's hold-up sizing |
| **(inductive) invariant** | a property true at reset and preserved by every step — the certificate form of "always true", and the one artifact no tool invents (L5/02) |
| **assume-guarantee** | contract style: the component guarantees G while its environment maintains A; the bus and PCPI ports are specified this way |
| **demonic nondeterminism** | unresolved choices read adversarially — the claim must hold under *every* resolution |
| **prefix closure** | every initial segment of an allowed trace is allowed — what makes stopping (power loss) spec-conformant for free |
| **SAT / SMT** | propositional satisfiability solving, and its extension with theories (bitvectors, arrays) — the workhorse decision procedures |
| **BMC** | bounded model checking: unroll k steps, hand to SAT; complete only to depth k |
| **IC3** | the model-checking algorithm that *invents* inductive invariants incrementally; used here as an untrusted generator whose output is cheaply checked |
| **DRAT / LRAT** | proof formats a SAT solver emits; LRAT is checkable by a small verified program — how "the solver said so" becomes a theorem |
| **PAC** | polynomial-calculus certificates over circuit polynomials — the algebraic proof format for multipliers, where SAT resolution provably blows up |
| **miter** | two circuits joined output-against-output through XOR; "always 0" ⇔ equivalent — the standard reduction of equivalence to SAT |
| **AIG** | And-Inverter Graph: the two-input-AND-plus-inverter normal form equivalence tools operate on; hash-consing makes shared structure pointer-equal |
| **NPN class** | Boolean functions up to input/output negation and permutation; the 4-input functions fall into 222 classes — a *finite* rewrite library |
| **ternary / X-prop** | simulation over {0,1,X}; sound for unknownness precisely because `X∧¬X=X` — it never asserts consistency between two reads of the same unknown |
| **symbolic simulation** | running a circuit on symbolic expressions rather than values; the outputs are theorems over all inputs at once |

## Tools and artifacts of this design

| | |
|---|---|
| **Yosys / ABC** | the open-source synthesis tool and its logic-optimisation engine — the pair that produces the hardened netlist |
| **Verilator / Icarus** | independent open-source Verilog simulators — L4's differential-testing oracles |
| **Sail** | the ISA-description language; its RISC-V model is the officially *ratified* one and exports to proof assistants |
| **trace port / RVFI** | RTL ports announcing each instruction retirement (the core's trace interface; RVFI is riscv-formal's version of the same discipline) — the designer's own commit-point map (L5/01) |
| **Rocket / Chisel / Chipyard** | the design stack: Rocket is the original RISC-V core generator, written in Chisel (a Scala-embedded HDL); Chipyard is the Berkeley framework that composes it with buses, devices, and harnesses into the SoC |
| **FIRRTL / CIRCT / firtool** | the specified intermediate representation Chisel elaborates to, the LLVM hardware-compiler project, and its FIRRTL-to-SystemVerilog compiler — the storey above the RTL (L4/04) |
| **SRAM22** | the open SRAM generator whose sky130 macros carry this design's memories — hard macros with *published* transistor-level collateral, so their contracts are checkable-by-effort rather than foundry-opaque (L3/02) |
| **serial TileLink** | the off-chip port: on-chip bus transactions serialised into 32-bit phits under the link's own clock — the load path for programs and the source of the bus latency bound's worst case |
| **JTAG / UART** | two of the chip's serial interfaces: JTAG is the five-wire debug port reaching the standard debug module; UART is asynchronous and baud-framed (the observable output channel) |
| **TileLink** | the on-chip interconnect protocol of the Rocket ecosystem: request/response channel pairs with source-ID tags — the bus contract's alphabet (L7/02) |
| **CSR / WARL** | RISC-V's control-and-status registers; WARL fields ("write any values, read legal values") are where the standard deliberately leaves behaviour implementation-defined (S4) |
| **CLINT / PLIC** | the standard RISC-V interrupt sources: the core-local interruptor (software + timer interrupts) and the platform-level interrupt controller (device interrupts, claim/complete) — device models in L7/03 |
| **LRM** | the Verilog Language Reference Manual — the event-driven semantics this project deliberately does *not* formalise (L4/00) |
| **Tcl** | the scripting language EDA tools embed; an SDC file is a Tcl *program*, which is why it must be elaborated before it can be analysed |

## Timing, in more detail

| | |
|---|---|
| **slew** | the transition time of a signal edge; delay tables are indexed by it, so it propagates through timing analysis like a value |
| **skew** | the difference in clock arrival between two flops — consumed directly by the hold constraint |
| **jitter** | cycle-to-cycle wobble of the clock edge — the oscillator's phase noise, integrated |
| **arrival / required / slack** | STA's three numbers per node: when the signal gets there, when it needed to, and the margin between them |
| **CPPR** | common-path pessimism removal: launch and capture clocks share a tree prefix whose variation cannot differ between them — credit it once |
| **OCV / derate** | on-chip variation (per-cell randomness) and the flat percentage margins that industrially stand in for its proper statistics |
| **false path** | a graph path STA can see but logic can never activate; *declaring* one is an unchecked human claim — the subject of L2/04 |
| **FSM / one-hot** | finite-state machine; one-hot encoding gives each state its own bit, exactly one set |
| **tri-state** | a driver that can disconnect (high impedance) as well as drive 0/1 — the one legitimate way two drivers share a net |
| **latch inference** | Verilog silently converting an incomplete combinational block into a state element — the classic way RTL grows unintended memory (L4/02) |
| **blocking / non-blocking** | Verilog's `=` vs `<=`: immediate sequential update vs two-phase simultaneous commit; the distinction that makes clocked logic order-independent |

## Physics and mathematics

| | |
|---|---|
| **weak solution / Lax–Milgram** | the PDE framework where fields live in energy spaces; Lax–Milgram is the short existence-and-uniqueness theorem for coercive linear problems (L0/00) |
| **Sobolev space (H¹)** | functions whose derivatives are square-integrable — the natural home of finite-energy fields |
| **maximum principle** | harmonic-type fields attain their extremes on the boundary — why `\|φ\| ≤ Vdd` everywhere is a theorem, not an assumption |
| **harmonic measure** | how much of a boundary region is "visible" to a point through the field — the rigorous form of screening leakage (M2) |
| **drift–diffusion / van Roosbroeck** | the standard semiconductor PDE system: Poisson's equation coupled to electron and hole transport |
| **Kramers escape** | thermally activated barrier crossing at rate ~`exp(−ΔE/kT)` — the mechanism whose ~7,500 kT barrier makes thermal upsets a 10⁻³⁰⁰⁰-class event |
| **Lyapunov function** | a quantity decreasing along every trajectory — the standard tool for proving that things settle |
| **Floquet exponent** | the per-cycle contraction rate of a periodic orbit; the *zero* exponent along an oscillator's phase is why jitter accumulates unboundedly |
| **Wiener process** | the continuous random walk; what an oscillator's phase performs |
| **noise margin** | the input range a gate tolerates while still emitting a valid output level — the robustness radius of the digital abstraction (L0/05) |
| **erosion / dilation** | shrinking or growing a shape by a radius — the morphological operations DRC decks and L1's sandwich theorem are built from |
| **LER / overlay** | line-edge roughness (random edge wiggle) and mask-to-mask misalignment — two of the three terms in the fabrication tolerance radius |
| **CMP** | chemical-mechanical polishing, which planarises each layer; its sensitivity to pattern density is why fill cells exist |
| **Poisson, twice** | the *equation* (electrostatics — L0, L1) and the *process* (random arrivals — SEU, defects) are unrelated results by the same mathematician; both are load-bearing here, and context always disambiguates |

## Reliability and test

| | |
|---|---|
| **FIT** | failures in time — expected failures per 10⁹ device-hours; the unit SEU rates are quoted in |
| **AVF** | architectural vulnerability factor: the fraction of raw bit-flips that matter architecturally — the masking discount inside ε |
| **SECDED / scrubbing** | single-error-correct double-error-detect coding; scrubbing rewrites memory periodically so single errors cannot age into uncorrectable doubles |
| **RTN** | random telegraph noise — single trapped charges switching a transistor's current on and off; individually visible at this node's scale |
| **ATPG / stuck-at** | automatic test-pattern generation against the stuck-at fault model — how a fabricated die is actually screened (P5) |
| **scan chain** | flops stitched into a shift register in test mode, making internal state controllable and observable from the pins |
| **SPEF** | the standard exchange file for extracted parasitic RC values |
