# hwverif

### How to verify a computer down to physics

A scoping study. **Not** an attempt to carry out the proof — an attempt to determine how each phase *would* be done, what it would rest on, and what is genuinely unknown. The intended output is a roadmap: paper-length per layer, book-length overall.

**→ [MAIN.md](MAIN.md) is the mathematical content**: the top-level statement, the dispatch into layers, and how they compose. This file covers structure and tooling. Unfamiliar terms are in the [glossary](#glossary).

The framing throughout is **validation of an existing design**, not design of a new one. We assume the designers applied best practices that produce the error bounds needed to push the argument through; the job is to check that assumption, not to re-engineer the artifact. In practice, we may find that the original designers cut corners and so we may need to make minor modifications to get the theorem to hold. But we would like to lean on the wisdom of the elders whenever possible.

## Target

**[Caravel](https://github.com/efabless/caravel) on [SKY130](https://github.com/google/skywater-pdk), configured with [picorv32](https://github.com/YosysHQ/picorv32).**

Caravel is an open-source SoC *harness* — fixed pad frame, management core, RAM, and a user area — fabricated repeatedly on SkyWater's open 130 nm process. Chosen because the full chain is open (RTL, SDC, gate netlist, DEF, GDS, timing reports, tool version pins) on an open PDK, in a chip that physically exists. That intersection is narrow: Caravel and [Tiny Tapeout](https://tinytapeout.com) are approximately all of it.

[picorv32](https://github.com/YosysHQ/picorv32) — a small hand-written RV32IMC [RISC-V](https://riscv.org) core — over the alternatives ([VexRiscv](https://github.com/SpinalHDL/VexRiscv), [Ibex](https://github.com/lowRISC/ibex)) because it is 3,044 lines and semantically tame: 19 enumerated Verilog sites needing care, and none of the categories that make Verilog semantics awful. The others are ~550 KB of machine-emitted Verilog with mangled names — tamer in some respects, hostile to authoring an invariant. All three ship in [caravel_mgmt_soc_litex](https://github.com/efabless/caravel_mgmt_soc_litex) as configuration options.

The flow that produced the shipped artifacts is [OpenLane](https://github.com/The-OpenROAD-Project/OpenLane) ([Yosys](https://github.com/YosysHQ/yosys) for synthesis, [OpenROAD](https://github.com/The-OpenROAD-Project/OpenROAD) for place-and-route, [Magic](http://opencircuitdesign.com/magic/) and [netgen](http://opencircuitdesign.com/netgen/) for DRC/LVS), pinned to exact commits — see [FINDINGS](FINDINGS.md#toolchain-provenance).

**Alternative worth keeping live: [iCE40](https://github.com/YosysHQ/icestorm) FPGA ([iCEBreaker](https://github.com/icebreaker-fpga/icebreaker)) running [picosoc](https://github.com/YosysHQ/picorv32/tree/main/picosoc)** — the reference SoC bundled with picorv32: the same core plus an SPI-flash execute-in-place controller, a UART and block RAM, and small enough to fit the fabric. Deletes L1 entirely — no extraction, DRC, OPC or litho model, because the vendor ran the geometric stack once and the result is a finite, *empirically testable* arc table. Weaker claim (someone else's silicon, plus an opaque configuration engine), much shorter axiom list, and a complete chain that could actually be finished.

## Repository map

| | |
|---|---|
| **[MAIN.md](MAIN.md)** | the statement, the dispatch, how the layers compose |
| [AXIOMS.md](AXIOMS.md) | what the result would rest on — plus M1–M8, the open mathematics, kept separate |
| [FINDINGS.md](FINDINGS.md) | every number measured off the real artifacts, with provenance |
| [BIBLIOGRAPHY.md](BIBLIOGRAPHY.md) | one reference list; author mentions in the text link to per-entry anchors |
| [data/README.md](data/README.md) | what gets fetched, from which pinned commits |

Layers, bottom-up:

| | | effort |
|---|---|---|
| **L0** [device physics](L0-device-physics/) | transistor network ⟹ Boolean function; the error model | 2–4 yr |
| **L1** [geometry](L1-geometry/) | GDS ⟹ netlist + RC enclosures; DRC as theorem hypotheses | 4–6 yr |
| **L2** [timing](L2-timing/) | timing closure ⟹ the synchronous abstraction is sound | 2–3 yr |
| **L3** [netlist equivalence](L3-netlist-equivalence/) | shipped netlist ≡ RTL, by certificate not search | 1–2 yr |
| **L4** [RTL semantics](L4-rtl-semantics/) | the synthesisable subset this design actually uses | 1 yr |
| **L5** [microarchitecture](L5-microarchitecture/) | RTL refines the ISA — the irreducible content | 3–5 yr |
| **L6** [ISA](L6-isa/) | what the specification *is*, including the parts that don't exist | 1–2 yr |
| **L7** [system](L7-system/) | `Sys(F)` and `obs` — the pad-trace spec the top statement quantifies over | 1 yr |

Effort figures are for one competent person and are guesses. All eight layers are decomposed into numbered subcomponent files, one per major proof obligation. Each layer README opens with a **spec block** — spec below, spec above, theorem or definition — keyed to [MAIN's spec tower](MAIN.md#the-spec-tower).

## Tooling

Everything runs from the repository root with no dependencies beyond Python 3, `curl`, and (for the reflow tool) `python-markdown`.

### Fetch the design artifacts — [`tools/fetch-data.sh`](tools/fetch-data.sh)

```sh
tools/fetch-data.sh [all|small|caravel|mgmt|pdk]
```

~490 MB into `data/`, which is gitignored. **Refs are pinned commit SHAs, not branches** — FINDINGS quotes exact byte counts, instance counts and Liberty table values from these files, so a floating ref would silently invalidate the documents. `small` skips the two large binaries (~1 MB total) and is enough for most of the analysis.

If you deliberately move to newer upstream: bump the SHA in [the script](tools/fetch-data.sh), re-run, **and re-derive FINDINGS** — never one without the other.

### Structural checks on the netlist — [`tools/netgraph.py`](tools/netgraph.py)

```sh
tools/netgraph.py data/caravel/gl_caravel_core.v
```

7.5 s over 275,608 instances. Runs W1 (one driver per net), W2 (no floating reads), W3 (acyclicity), W4 (physical-cell inertness) — L3's well-formedness obligations, and the licence for its 85% instance deletion.

**It exits non-zero on a pin name it does not recognise rather than guessing a direction.** A misclassified output silently turns real contention into a clean bill of health, so the table of 43 pin directions is declared, not inferred. Re-pointing it at a different cell library is therefore a deliberate act.

### GDS inspection — [`tools/gdsdump.py`](tools/gdsdump.py), [`tools/bbox.py`](tools/bbox.py)

```sh
tools/gdsdump.py data/pdk/inv_1.gds     # record census, layers, elements, UNITS
tools/bbox.py    data/pdk/inv_1.gds     # per-layer bounding boxes in µm
```

Pure-Python GDSII record parsers — the format is simple enough that a dependency isn't worth it, and reading the bytes directly is how several FINDINGS entries were established.
## Where to start work

Three cheap, high-information experiments. Each is weeks rather than years, and each tells you whether the layer above is tractable before you invest in it.

1. **Reproduce the synthesis** (L3). Versions are pinned exactly. Reproduce the shipped netlist and you stop *inferring* what the tools did and start knowing — and the register-correspondence witness (F5) falls out for free. Failure to reproduce is itself a finding worth having early.

2. **Classify the 159 SDC exceptions** (L2). 112 `set_false_path`, 45 `set_case_analysis`, 2 `set_clock_groups`, zero multicycle. Each trades safety for frequency and no tool checks any of them. The one place where a *negative* result — a real gap in fabricated silicon — is as publishable as a positive one.

3. **Confront the signoff report** (L2). Three of nine corners fail `in2reg` hold; one passes only modulo `max_tran`/`max_cap`. The bridge theorem's hypotheses are *not currently established* for this design as shipped, and determining whether the failures are all covered by justified exceptions is concrete and bounded.

Within L0 and L1 specifically, the cheapest substantial entries are [L1/01](L1-geometry/01-topology-preservation.md) (the sandwich theorem — self-contained computational geometry, no analysis) and [L1/05](L1-geometry/05-geometric-checks.md) (G1–G6, near-linear checks gated only on extraction).

## Glossary

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

## Conventions

- Each layer directory has a `README.md` with the same sections: statement, interfaces, axioms introduced, established, open problems, first experiments, effort, reading.
- Layers decompose into numbered subcomponents (`00-…md`, `01-…md`), one per major proof obligation, indexed from the layer README.
- Prose is **unwrapped** — one source line per paragraph. (The reflow tool that enforced this was retired; keep the convention by hand.)
- Numbers taken from real artifacts are marked as such in FINDINGS and should be re-derived rather than trusted when they matter.
- Author citations link into BIBLIOGRAPHY by anchor.
- Findings that *contradict* the scoping are kept, labelled, and promoted — F1–F5 in AXIOMS exist because the shipped design does not satisfy assumptions the documents had been making.