# thinking-sand

### How to verify a computer down to physics

**📖 Read the book: [digama0.github.io/thinking-sand](https://digama0.github.io/thinking-sand/)**

> *We tricked sand into thinking. This repository is the audit of the trick.*

**What this is.** Between "my program ran correctly" and "electrons obey Maxwell's equations" stands a tower of trust: the instruction set means what its manual says; the processor implements the instruction set; the netlist computes what the RTL describes; the digital story the netlist tells is what the analog circuit actually settles to; the circuit is what the geometry realises; the geometry is what the fab printed; and the transistors do what the device models claim. Industrial practice verifies one or two storeys of this tower and takes the rest on faith — reasonably, but the faith is unaudited. This repository is a scoping study for auditing *all of it*: what it would take to produce a machine-checked proof that one specific, physical, purchasable chip runs its programs correctly, starting from field equations over the silicon and ending at the instruction set, with every claim that cannot be a theorem recorded, classified, and priced in an explicit ledger.

**What it is not**: the proof itself. Carrying it out is a decade-scale project; the deliverable here is the map — for each of eight layers, what the theorem is, how it would be proved, what it rests on, and what is genuinely unknown. Paper-length per layer, book-length overall. The organising principle: with unbounded proof capacity, everything merely hard collapses to time, and what remains — the assumptions no proof can reach — *is* the result. That ledger is [AXIOMS](src/AXIOMS.md). The study is grounded throughout in the shipped artifacts of a chip that has actually been fabricated; the numbers measured off them, including a few genuine gaps found in the shipped design, are in [FINDINGS](src/FINDINGS.md).

**Where to read**: [MAIN.md](src/MAIN.md) is the mathematical content — the top-level statement and how the eight layers compose into it — and is the front page of the rendered book. This file covers project structure and tooling. Unfamiliar terms are in the [glossary](src/glossary.md).

The framing throughout is **validation of an existing design**, not design of a new one. We assume the designers applied best practices that produce the error bounds needed to push the argument through; the job is to check that assumption, not to re-engineer the artifact. In practice, we may find that the original designers cut corners and so we may need to make minor modifications to get the theorem to hold. But we would like to lean on the wisdom of the elders whenever possible.

## Target

**[Caravel](https://github.com/efabless/caravel) on [SKY130](https://github.com/google/skywater-pdk), configured with [picorv32](https://github.com/YosysHQ/picorv32).**

Caravel is an open-source SoC *harness* — fixed pad frame, management core, RAM, and a user area — fabricated repeatedly on SkyWater's open 130 nm process. Chosen because the full chain is open (RTL, SDC, gate netlist, DEF, GDS, timing reports, tool version pins) on an open PDK, in a chip that physically exists. That intersection is narrow: Caravel and [Tiny Tapeout](https://tinytapeout.com) are approximately all of it.

[picorv32](https://github.com/YosysHQ/picorv32) — a small hand-written RV32IMC [RISC-V](https://riscv.org) core — over the alternatives ([VexRiscv](https://github.com/SpinalHDL/VexRiscv), [Ibex](https://github.com/lowRISC/ibex)) because it is 3,044 lines and semantically tame: 19 enumerated Verilog sites needing care, and none of the categories that make Verilog semantics awful. The others are ~550 KB of machine-emitted Verilog with mangled names — tamer in some respects, hostile to authoring an invariant. All three ship in [caravel_mgmt_soc_litex](https://github.com/efabless/caravel_mgmt_soc_litex) as configuration options.

The flow that produced the shipped artifacts is [OpenLane](https://github.com/The-OpenROAD-Project/OpenLane) ([Yosys](https://github.com/YosysHQ/yosys) for synthesis, [OpenROAD](https://github.com/The-OpenROAD-Project/OpenROAD) for place-and-route, [Magic](http://opencircuitdesign.com/magic/) and [netgen](http://opencircuitdesign.com/netgen/) for DRC/LVS), pinned to exact commits — see [FINDINGS](src/FINDINGS.md#toolchain-provenance).

**Alternative worth keeping live: [iCE40](https://github.com/YosysHQ/icestorm) FPGA ([iCEBreaker](https://github.com/icebreaker-fpga/icebreaker)) running [picosoc](https://github.com/YosysHQ/picorv32/tree/main/picosoc)** — the reference SoC bundled with picorv32: the same core plus an SPI-flash execute-in-place controller, a UART and block RAM, and small enough to fit the fabric. Deletes L1 entirely — no extraction, DRC, OPC or litho model, because the vendor ran the geometric stack once and the result is a finite, *empirically testable* arc table. Weaker claim (someone else's silicon, plus an opaque configuration engine), much shorter axiom list, and a complete chain that could actually be finished.

## Repository map

| | |
|---|---|
| **[MAIN.md](src/MAIN.md)** | the statement, the dispatch, how the layers compose |
| [AXIOMS.md](src/AXIOMS.md) | what the result would rest on — plus M1–M8, the open mathematics, kept separate |
| [FINDINGS.md](src/FINDINGS.md) | every number measured off the real artifacts, with provenance |
| [BIBLIOGRAPHY.md](src/BIBLIOGRAPHY.md) | one reference list; author mentions in the text link to per-entry anchors |
| [src/data-provenance.md](src/data-provenance.md) | what gets fetched, from which pinned commits |

Layers, bottom-up:

| | | effort |
|---|---|---|
| **L0** [device physics](src/L0-device-physics/README.md) | transistor network ⟹ Boolean function; the error model | 2–5 yr |
| **L1** [geometry](src/L1-geometry/README.md) | GDS ⟹ netlist + RC enclosures; DRC as theorem hypotheses | 4–6 yr |
| **L2** [timing](src/L2-timing/README.md) | timing closure ⟹ the synchronous abstraction is sound | 2–3 yr |
| **L3** [netlist equivalence](src/L3-netlist-equivalence/README.md) | shipped netlist ≡ RTL, by certificate not search | 1–2 yr |
| **L4** [RTL semantics](src/L4-rtl-semantics/README.md) | the synthesisable subset this design actually uses | 1 yr |
| **L5** [microarchitecture](src/L5-microarchitecture/README.md) | RTL refines the ISA — the irreducible content | 3–5 yr |
| **L6** [ISA](src/L6-isa/README.md) | what the specification *is*, including the parts that don't exist | 1–2 yr |
| **L7** [system](src/L7-system/README.md) | `Sys(F)` and `obs` — the pad-trace spec the top statement quantifies over | 1 yr |

Effort figures are for one competent person and are guesses. All eight layers are decomposed into numbered subcomponent files, one per major proof obligation. Each layer README opens with a **spec block** — spec below, spec above, theorem or definition — keyed to [MAIN's spec tower](src/MAIN.md#the-spec-tower).

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

### Build the book — [`tools/build-book.sh`](tools/build-book.sh)

```sh
tools/build-book.sh          # needs mdbook; renders to book/index.html
```

The book's sources live in [`src/`](src/MAIN.md) (the conventional mdBook layout), with [SUMMARY.md](src/SUMMARY.md) as the table of contents and **MAIN as the front page** — this README stays at the root as the GitHub landing page and is not a chapter. The script checks SUMMARY and the chapter set agree in both directions (mdBook rewrites `.md` links to `.html` unconditionally, so a present-but-unlisted file would 404), builds, and copies `tools/` into the output so the raw-file links above resolve on Pages; `data/` stays outside `src/` because mdBook copies everything under its source directory into the output. [A GitHub Actions workflow](.github/workflows/book.yml) builds and deploys to GitHub Pages on every push to `master`; enable Pages with source "GitHub Actions" in the repository settings once a remote exists.

## Where to start work

Three cheap, high-information experiments. Each is weeks rather than years, and each tells you whether the layer above is tractable before you invest in it.

1. **Reproduce the synthesis** (L3). Versions are pinned exactly. Reproduce the shipped netlist and you stop *inferring* what the tools did and start knowing — and the register-correspondence witness (F5) falls out for free. Failure to reproduce is itself a finding worth having early.

2. **Classify the 159 SDC exceptions** (L2). 112 `set_false_path`, 45 `set_case_analysis`, 2 `set_clock_groups`, zero multicycle. Each trades safety for frequency and no tool checks any of them. The one place where a *negative* result — a real gap in fabricated silicon — is as publishable as a positive one.

3. **Confront the signoff report** (L2). Three of nine corners fail `in2reg` hold; one passes only modulo `max_tran`/`max_cap`. The bridge theorem's hypotheses are *not currently established* for this design as shipped, and determining whether the failures are all covered by justified exceptions is concrete and bounded.

Within L0 and L1 specifically, the cheapest substantial entries are [L1/01](src/L1-geometry/01-topology-preservation.md) (the sandwich theorem — self-contained computational geometry, no analysis) and [L1/05](src/L1-geometry/05-geometric-checks.md) (G1–G6, near-linear checks gated only on extraction).


## Conventions

- Each layer directory has a `README.md` with the same sections: statement, interfaces, axioms introduced, established, open problems, first experiments, effort, reading.
- Layers decompose into numbered subcomponents (`00-…md`, `01-…md`), one per major proof obligation, indexed from the layer README.
- Prose is **unwrapped** — one source line per paragraph. (The reflow tool that enforced this was retired; keep the convention by hand.)
- Numbers taken from real artifacts are marked as such in FINDINGS and should be re-derived rather than trusted when they matter.
- Author citations link into BIBLIOGRAPHY by anchor.
- Findings that *contradict* the scoping are kept, labelled, and promoted — F1–F5 in AXIOMS exist because the shipped design does not satisfy assumptions the documents had been making.