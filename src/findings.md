# Findings — measured data

Everything in this appendix was **measured on the artifacts this repository generates**, by the tools in `tools/` and the flow runs under `flow/` — never transcribed from documentation. Each finding names its instrument. Statuses use the [scoreboard](scoreboard.md)'s vocabulary; rows the re-anchored checker suite has not yet re-measured are listed in the scoreboard as TODO rather than duplicated here.

## The generation chain

**The chain reproduces from pinned sources.** Chisel elaboration (Chipyard, pinned by commit) → FIRRTL → SystemVerilog (`firtool`, pinned release, checksum-verified) → synthesis (Yosys under Hammer) → place-and-route (OpenROAD) → signoff (Magic, KLayout, Netgen). Every stage runs from this repository; the [data-provenance appendix](data-provenance.md) carries the pins.

**The elaboration declares the design's headline facts.** From the emitted device tree: ISA `rv32imaczicsr_zifencei_zihpm_xrocket`; one Rocket core; 4 KiB instruction cache (64 sets × 64 B); 16 KiB data memory at `0x8000_0000`; PMP with 8 regions at granularity 4; 1 hardware breakpoint; debug module at `0x0` (JTAG); CLINT at `0x200_0000`; PLIC at `0xC00_0000` with one device source; UART at `0x1002_0000`; 64 KiB boot ROM at `0x1_0000`. The `ChipTop` boundary is 18 signals: UART pair, `custom_boot`, JTAG ×5, `reset_io`, `clock_uncore`, `clock_tap`, and the serial TileLink port (32-bit phits + link clock).

## The RTL, measured (L4)

Census over the emitted SystemVerilog (322 files, 80 K lines including simulation collateral; the design cone is ~230 modules):

- **Zero** `casex`/`casez`, `force`-class constructs, UDPs, `fork`, negedge blocks, delays-in-design.
- **303** `always @(posedge …)` blocks, uniformly non-blocking; the census's blocking-assignment sites are in one DPI harness file outside the design cone. (An earlier count of 608 also swept firtool's `end // always @(posedge)` closing comments — the census now strips comments, and the checker regression pins the honest number.)
- **One** `always @*` block in the entire design — `EICG_wrapper`, the clock-gate model, a *deliberate* latch (the ICG primitive, L4/02).
- **23** `'bx` literals, all one idiom: behavioural memory models yielding X on a disabled read.
- **212** `initial` blocks, every one simulation-only (SYNTHESIS/RANDOMIZE-guarded or the initializer idiom) — no register carries a power-up value. (The earlier 425 double-counted closing comments, as above.)
- **3,938** assertion mentions across 85 files (the TileLink monitors and friends) — generator-emitted verification collateral, an adequacy asset (L4/04).

## Synthesis (L3)

From the Hammer/Yosys run of the tiny Rocket configuration:

- **51,359 standard-cell instances** drawn from **96 cell types**; **10,416 flops**; **zero unmapped cells**; 228 modules, 9.4 MB mapped netlist.
- **Three SRAM macro kinds, five instances**: 2 × `sram22_2048x32m8w8` (data memory banks), 2 × `sram22_512x32m4w8` (icache data), 1 × `sram22_64x32m4w8` (icache tags). All memories resolved to macros; the behavioural `*_ext` models appear nowhere in the mapped netlist.
- A flop-mapping interaction worth its own line: sky130 has no synchronous-reset or enable flop, so the synthesis script must let Yosys *synthesise* those flop types from what exists. A `-map-only` discipline (correct for pad libraries, which carry no flops) leaves thousands of abstract `$_SDFFE_*` cells in the netlist, and the failure surfaces only at P&R ("LEF master not found"). The corrected mapping adds ≈ 6,900 cells of reset/enable gating — cells that were previously "free" only because they were placeholders that could never have been placed.

## The constraint set (L2)

The generated SDC, measured: **one** `create_clock` (`clock_uncore`, 50 ns, 2 ns uncertainty), one trivial clock group, **zero** false paths, **zero** case analysis, **zero** multicycle paths. The JTAG (`jtag_TCK`) and serial-link (`serial_tl_0_clock_in`) clock domains are **absent** — their paths are unanalysed, not excepted. This is F3's content: for a generated constraint set the audit's weight falls on *completeness*, there being no assertions to audit.

## The independent hardening run

The same RTL was also hardened through a second, independently configured flow (librelane driving the same underlying tools, with the PDK's OpenRAM-family macros — 20 instances banked behind hand-written muxes — in place of SRAM22). It ran end to end and produced a GDS, and its value is exactly that its results are *independent measurements* of the same design under different physical decisions:

- **Timing risk concentrates at the fast corners.** Setup passed at all nine corners with 3–10 ns of margin while **hold failed at the six fast and typical corners** (−0.05 … −0.09 ns worst slack), the slow corners passing — F1's row cites this as the live risk shape, measured rather than guessed.
- **Domain violations are real.** 6,186 max-slew, 526 max-cap, 185 max-fanout violations on stretched nets in the loose floorplan — F2's evidence that "inside the characterisation range" is a hypothesis that fails in practice and must be checked, not assumed.
- **Fill dominates the census.** Fill insertion took the instance count from 271,473 placed cells to 3,564,849 — a 13× multiplication by cells that compute nothing, L3/02's deletion classes made vivid.
- **The met4 story.** Detailed routing settled at 14 violations, all on the layer carrying the PDN straps (9 spacing, 5 shorts); LVS independently caught one of the shorts electrically (one net of 84,586 mismatched, all 84,051 devices matching — a slew-repair buffer chain extracted onto the power rail). Congestion, DRC, and LVS told one consistent story from three directions.

## The flow of record (rocket-sram22)

The layout the book's physical layers name: upstream's floorplan (3588 × 2992 µm ≈ **10.73 mm²**, five rotated SRAM22 macros) hardened through librelane. Measured on run `gds3`:

- **Detailed routing: 0 violations** — the first fully clean route of this design in any configuration; the floorplan (rotated macros, real channels) is what changed.
- **Timing: all nine corners pass** at the 100 ns clock — hold +0.05…+0.26 ns, setup +25.6…+28.3 ns. The clock is the conservative-verification choice made concrete: at 50 ns, hold passes everywhere and setup fails on unrepaired high-fanout nets (worst path ≈ 83 ns).
- **The F2 rows stay open**: 19,110 max-slew, 1,145 max-cap, 1,817 max-fanout violations — the priced cost of skipping OpenROAD's `repair_design`, which is unrunnable on 32 GB hardware: it retains ~600 KB *per iteration* (independent of repairs performed) and was OOM-killed at the same iteration in four runs across two flows, once taking the machine with it. Every flow launch now runs under `ulimit -v`.
- **BEOL DRC (KLayout, tiled): 150 flow-owned violations, all at macro interfaces.** The raw report says 90,081 — of which 89,931 sit strictly inside the SRAM macros: bitcell geometry checked against logic rules it was never meant to satisfy, because the deck's `sram_exclude` guards FEOL only and SRAM22's GDS carries no `areaid` waiver markers. Coordinate clustering against the macro boxes separates the two classes in minutes and belongs in the layer checker.
- **DRC needed deck surgery to run at all**: the PDK deck's monolithic deep mode wants >14 GiB and 5–16 h (died twice in the 16M-polygon `mcon` block); enabling the deck's own commented-out tiling (500 µm tiles, `deep` off) runs the same rules in 1 h 44 m at 2.5 GB peak. The tiled deck is in `flow/rocket-sram22/`.
- **LVS is blocked** on this design: Magic cannot read the SRAM22 GDS at all (`sky130_fd_bd_sram` cells, unknown layer 64/44) — which also explains why upstream's own flow sets `drc.magic.generate_only: true`. Connectivity signoff needs a non-Magic extraction route; until then the row is TODO, not green.

The signoff-coverage summary this adds to F8: for macro-bearing sky130 designs, open-tools signoff is one engine deep exactly where it claims to be redundant — Magic hard-stops on the macros, KLayout needs surgery and has no bitcell waiver mechanism, and LVS inherits Magic's limits.

## Instruction-for-instruction against the golden model

Spike co-simulation closes the L5 oracle gap: `tools/run-sim.sh cosim` runs the design with **every committed instruction checked against spike, the RISC-V golden ISA model**, per commit — PC, register writeback, CSR effects. A pure-compute RV32IMAC image (`sim/cotest.c`) runs to a `tohost` pass with **1,631 committed instructions and zero mismatches** — the same 1,631 every time it clears the boot window. The RTL the flow hardens *refines the ISA*, verified instruction-by-instruction — the executable precursor to L5's refinement proof, with the core's own trace port as the α anchor.

Two boundaries fell out, both diagnosed rather than papered over ([COSIM-NOTES](https://github.com/digama0/thinking-sand/blob/master/flow/rocket-sram22/COSIM-NOTES.md)): ISA co-simulation ends at MMIO — a UART poll loop diverges because the golden model has no UART, the fundamental scope of core-level co-sim — and the boot/wake window needs deterministic Verilator reset init (`+verilator+rand+reset+0`) to escape X-propagation nondeterminism.

The cosim tooling itself is a finding: cospike is written and CI'd for 64-bit out-of-order cores, and took **eight portability patches** to run RV32/in-order/custom-extension (`cospike-rv32.patch`) — the ISA-string custom-extension strip, an RV64 page-level assert, the xlen-1 interrupt bit, sign-vs-zero-extension in the PC and writeback compares, and the pre-boot X-cause guard. Each is a real incompatibility, of a piece with F8's theme: the ecosystem's verification tooling assumes the mainstream target.

## The design executes

The functional gap is closed: the generated SoC runs programs. Chipyard's Verilator harness (`tools/run-sim.sh`) simulates the full `ChipTop` with the `SimTSI` host model driving the **serial TileLink port** — L7/03's load path exercised literally — and the UART adapter echoing TX:

- A bare-metal image (built with stock clang: `--target=riscv32`, freestanding, lld — no riscv-gcc needed) is loaded over the serial link into the DTIM at `0x8000_0000`; the core boots from the ROM, takes the TSI wake interrupt, jumps, and runs it.
- The image prints **`hello from rocket`** over the UART and exits through the riscv-tests `tohost` protocol — pass signalled, `$finish`, exit 0. ~1 ms of simulated time, ~80 s of wall clock.
- The B3 statement of L7/01 is thereby *instantiated end to end* (load path → execution → observable output → clean exit), and the scoreboard row `L7/b3-smoke` runs the simulation itself — the check is the execution.

The harness rested on three small portability findings, recorded in `tools/run-sim.sh`: Spike v1.1.0 needs `-include cstdint` under GCC 13 and does not install `libriscv.a` (the simulator links it for trace disassembly); the `radiance` generator's make hook unconditionally injects GPU collateral from un-checked-out submodules into every config's simulator build; and Verilator bakes `$RISCV` include paths at Verilation time, so the env must be right *before* Verilating, not just at link.

## Signoff engines disagree (F8)

On one and the same layout: **Magic DRC reported 0 violations; KLayout DRC reported 4** (2 × met4 minimum width, 2 × met4 minimum spacing). Netgen LVS meanwhile flagged the power short the geometric engines split on. Additional engine-behaviour findings from the same runs: Magic's GDS stream-out emitted the SRAM macro's internal subcells as 13 *top-level* cells (breaking any consumer that resolves a single top; KLayout's stream-out of the same design has exactly one), and the flow's nine-corner STA step runs all corners in parallel against the fill-expanded netlist — exhausting a 31 GB machine and dying on SIGKILL, with each corner completing cleanly when run alone. The register's conclusion (F8): a single engine's verdict is one witness, never the verdict.

## Upstream flow drift

The framework's own physical-flow path (Hammer with its sky130 plugin, the documented tutorial configuration) did not run as shipped against current components: **ten distinct interface breakages** stood between the documented invocation and a result — a PDK workaround that crashes once the bug it patches is fixed upstream; four SRAM-collateral mismatches (lib-file naming, gzipped GDS, six of thirteen cache entries naming macros that no longer exist, a stale generated memory mapping whose make rule cannot rebuild it); the flop-mapping discipline above; and four OpenROAD command-interface changes (`source` flags, `place_cell` → `place_inst`, `place_pins -random` obsoleted — the last *warning and placing nothing*, so the failure surfaced three steps downstream as an unplaced-port error). All ten fixes are small patches to open Python; the finding is not that the flow is broken but that **pinned-flow reproducibility decays by default**, and only patchable flows can be walked forward — the property the toolchain was chosen for.

## Memory macro placement

The physical-design facts that constrain any floorplan of this configuration, measured across both hardening runs: the SRAM22 macros bring the memory to 5 instances (the OpenRAM alternative needs 20 banked instances at 0.142 mm²/KiB); macro power pins sit on **met2** while a met4/met5 strap plan connects macro grids at met3→met4 by default — a mismatch that yields an empty macro power grid unless the grid is built from the *pin* layers up; and a packed central macro block fails global routing where edge-pinned banks with wide channels route. The upstream reference floorplan places `ChipTop` in **3588 × 2992 µm ≈ 10.7 mm²** with rotated macros — comfortably inside a ~15 mm² pad-frame budget.

## Interpretation discipline

Three habits these findings enforce, recorded so they survive the people who learned them:

1. **A green single-engine verdict is one witness** (F8). Signoff claims are stated engine-independently and measured per layout.
2. **"By construction" is a claim to check** (F7). The one-elaboration property is real and valuable, and the re-elaboration diff is what keeps it a fact rather than a memory.
3. **Absence of constraints is not absence of risk** (F3). A minimal generated SDC moves the audit from exceptions to completeness; unconstrained-is-unchecked is the sharper failure mode.
