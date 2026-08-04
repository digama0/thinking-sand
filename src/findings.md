# Measured data

Everything here was read off the actual artifacts during scoping. Re-derive rather than trust if a number matters. Scripts in `tools/`.

Sources: `github.com/efabless/caravel`, `github.com/efabless/caravel_mgmt_soc_litex`, `github.com/google/skywater-pdk-libs-sky130_fd_sc_hd`.

## Toolchain provenance

Versions are pinned **exactly**, which makes reproduction plausible.

```
OpenLane        05fac72e4dcbaab8d56151495e1c77f29db1e576
open_pdks       12df12e2e74145e31c5a13de02f9a1e176b56e67
OPENLANE_TAG    ed194238ac359aca044c54fa8cbbbd12280e1a8c   (docker image)
SKYWATER_COMMIT f70d8ca46961ff92719d8870a18a076370b85f6c
MPW_TAG         2024.09.12-1
```

`signoff/caravel_core/cmds.log` is **170 lines of literal timestamped commands** (run 21 Apr 2023). `caravel_core` uses a bespoke `interactive.tcl` rather than the standard flow. So the process is *recorded*, not *specified* — the script is the only spec.

## Signoff status — the headline finding

`signoff/caravel_core/signoff.rpt`:

```
f-nom  Passed     f-min  Passed     f-max  Passed
t-nom  Passed     t-min  Passed     t-max  Passed (except: max_tran & max_cap)
s-nom  Failed (in2reg hold)
s-min  Failed (in2reg hold)
s-max  Failed (in2reg hold)
```

Three of nine corners fail **hold** — the frequency-independent, unfixable-in-silicon kind. A fourth passes only modulo transition/capacitance limits, i.e. parts of the design sit outside the Liberty characterisation range.

Caravel has been fabricated repeatedly and works, so these were waived — and the waiver's evidence trail is examined below ([F1 confronted](#f1-confronted-the-shipped-timing-evidence)): the failing paths are *real constrained paths* under the core signoff's own SDC (which sets `input_delay 4` on all inputs and false-paths nothing on `mprj_io_in`), and the per-path reports for the failing corners were never committed.

## Layout artifacts

| artifact | size |
|---|---|
| `sky130_fd_sc_hd__inv_1.gds` | 3,632 B |
| `sky130_fd_sc_hd__dfxtp_1.gds` | 12,216 B |
| `caravel.gds` | **291,239,174 B** (54,610,663 gz, 5.3×) |
| `caravel_core.def` | 118,195,151 B (13,738,708 gz) |
| `caravel_core.v` (gate netlist) | 32,767,977 B |

### caravel.gds structure

```
records            23,017,048
cell definitions        1,014
SREF placements       462,500
BOUNDARY            3,924,533
XY vertices        20,152,246
```

`caravel_core` alone holds **63.8%** of all polygons — that is *routing*, which is unique per net and does not instance. Cells compress to nothing; wires do not.

### Most-instantiated cells — ~75% of placements compute nothing

```
decap_12         125,086      tapvpwrvgnd_1     77,857
diode_2           50,710      decap_6           36,874
fill_1            26,261      decap_8           26,089
decap_3           19,639      decap_4           16,602
fill_2            15,145      clkdlybuf4s15_2    9,910   ← first logic cell, rank 10
```

Decoupling caps, well taps, antenna diodes, filler. Logic is a minority tenant.

### caravel_core.def

```
COMPONENTS   398,259   (matches the 398,259 SREFs exactly)
NETS          42,304
SPECIALNETS       12   (power)
VIA defs          55   ← vias are a tiny finite library
units       1000/µm    (1 nm, same as GDS — no rounding at stream-out)
```

42,304 nets expand to 2.5M polygons ≈ 59 polygons/net. The polygons are the *expansion*; DEF entropy is ~100× smaller than the GDS.

## Gate netlist composition (`caravel_core.v`, one hierarchy level)

275,704 instances (275,608 `sky130_*` + 96 macro instances; `check-l3.py` owns the census), 187 distinct cell types. Classification is heuristic on cell names.

| class | count | share | fate |
|---|---|---|---|
| PHYSICAL (decap/tap/fill/diode) | 235,566 | **85.4%** | delete (inertness check) |
| LOGIC | 15,853 | 5.7% | **keep** |
| CLOCK | 15,306 | 5.6% | delete (after L2) |
| SEQ (flops) | **5,774** | 2.1% | **keep — the state** |
| BUF/INV | 3,109 | 1.1% | collapse |
| macros | 96 | — | holes |

Reduction 275,704 → ~21,627 (≈13×). |S| = 2^5774 at this level alone, so **model checking is not on the table** — refinement plus induction only.

Macro holes, measured (16 types): `gpio_logic_high`×38, `gpio_defaults_block`×38, `spare_logic_block`×4, `RAM128`×3 (two of which are the banks of a flattened `RAM256` wrapper), `empty_macro`×2, and one each of `caravel_clocking`, `mprj_io_buffer`, `housekeeping`, `manual_power_connections`, `mprj2_logic_high`, `mprj_logic_high`, `mgmt_protect_hv`, `user_project_wrapper`, `simple_por`, `xres_buf`, `user_id_programming`. (`gpio_control_block` lives one level up, in `caravel.v`; the PLL is *flattened* into this netlist as `pll.*` cells, not a macro.)

## Structural checks on the gate netlist (L3)

`tools/netgraph.py data/caravel/gl_caravel_core.v` — 7.5 s. 275,608 `sky130_*` instances (+96 macro instances = 275,704), 48 top-level ports, 43 distinct pin names all classified explicitly (the tool exits non-zero on an unknown pin rather than guessing a direction).

| check | result |
|---|---|
| **W1** nets with >1 driver | **26** — all tri-state, all in `pll.ringosc`; **0 static contention** |
| **W2** read nets with no driver | 1,609 — all at hierarchy/macro boundaries |
| **W3** combinational cycles | **exactly 1 SCC, 64 nets, entirely in `pll.ringosc`** |
| **W4** physical cells with signal pins | **0** |
| | physical 235,566 (85.5%) · sequential 5,774 · nets 42,084 (DEF says 42,304, difference is power/special nets) |

**W1 discharges structurally.** The contended nets are `einvp`/`einvn` pairs with the *same* enable net on `TE` and `TE_B` — complementary polarity, so exactly one conducts. It is the oscillator's delay-trim multiplexer (`pll.itrim[k]` selects tapped path vs bypass). No functional reasoning required. Note this is idiom-dependent: a *decoded* tri-state bus would need a reachability proof instead.

**W3 makes X5's excision provably minimal.** Excise `pll.ringosc` and the netlist is contention-free and acyclic. The ring oscillator is *exactly* the set of structural violations — both the only cycle and the only contention, with the same cause. The prediction that the PLL cannot live inside the synchronous abstraction was right, and nothing else violates it.

**W2 is a hierarchy artifact — now discharged** (`check-l3.py`): the 1,609 undriven reads = 67 input-port bus bits (netgraph's port filter is name-exact and misses bus bits) + 1,542 macro-boundary nets, **residue 0**. The `RAM256.*` cluster resolved en route: RAM256 is a flattened wrapper whose two banks are `RAM128` macro instances.

**W4 caught the tool.** First run reported 118 violations, all `conb_1` — a constant *generator* wrongly filed as inert filler. Fixing the classification gave 0, and brought the physical total to exactly 235,566, matching the census above independently.

## The inverter, decoded

3,632 B, 44 BOUNDARY + 2 PATH + 8 TEXT, 240 vertices, one structure. Database unit **exactly 1 nm** (UNITS = 0.001 user, 1e-9 m).

```
cell boundary (81/4 areaid.standardc)   1.380 × 2.720 µm   (2.72 = HD row height)
overall bbox                            1.760 × 3.100 µm   ← nwell/implants OVERHANG
```

The overhang is deliberate: abutted cells' wells and implants **merge**. So the coloured image of a row is *not* the disjoint union of its cells — composition needs a merging theorem, not conjunction.

Layers present: nwell 64/20, diff 65/20, poly 66/20, licon1 66/44, li1 67/20, mcon 67/44, met1 68/20, hvtp 78/44, nsdm 93/44, psdm 94/20, npc 95/20, plus pin (×/16) and areaid metadata layers.

Structure readable directly: **poly (0.430 wide) crossing diff (0.670 × 2.250) is the gate** — a transistor is the intersection of two rectangles. nwell and psdm cover only the top half, nsdm the bottom: PMOS above, NMOS below.

Liberty `area` = 3.7536 µm² = 1.380 × 2.720 exactly. The two artifacts agree.

## Liberty timing (`sky130_fd_sc_hd__inv_1`, tt_025C_1v80)

7×7 tables. 17 corner files in the library.

```
index_1 (input slew)   0.010 .. 1.500 ns
index_2 (output load)  0.0005 .. 0.1813 pF

cell_rise   20.3 ps .. 1697 ps    ratio 83×
cell_fall   14.4 ps .. 1202 ps    ratio 84×
```

The 83× is the table's **domain**, not runtime variation — a given instance has a specific load and slew. Corner variation is more like 2–3×.

```
max_transition  = 1.5        = index_1's largest value
max_capacitance = 0.181284   = index_2's largest value
```

Identical. So "stay under max_cap" means literally "stay inside the characterised region"; violating it makes STA **vacuous**, not merely inaccurate. Cf. finding F2.

**`cell_fall` is NON-monotone in slew at (5,0) and (5,1)** — at the two lightest loads, going from 0.651 ns to 1.5 ns input slew, delay *drops* from 46.7 ps to 31.7 ps. Artifact of the 50%-crossing definition: with a slow ramp and no load the output starts falling before the input reaches 50%. Consequence: a rigorous interpolation enclosure must take **max over all four corners of the enclosing cell**, not the largest-index corner. The obvious shortcut is unsound, and this is the simplest cell in the library.

## SDC exceptions

43 `.sdc` files in the repo. `signoff/caravel/caravel.sdc` (406 lines):

```
set_false_path        112
set_case_analysis      45
set_clock_groups        2
create_clock            4
set_multicycle_path     0     ← a gift; multicycle is the harder one
```

Dominant false-path shapes: 40× `-from mprj_io[*] -through .../mgmt_gpio_out[*]`, 35× bare `-from`, 34× bare `-to`. The `mprj_io` ones are **asynchronous external GPIO** — the dangerous class, since declaring them false does not verify a synchroniser exists.

`set_case_analysis` includes legitimate pad configuration (`clock_pad/DM[2:0]`, `INP_DIS`) but also pins **flip-flop outputs** (`housekeeping/_6817_/Q`) to constants — and to *both* 0 and 1 in different Tcl branches, i.e. multi-mode analysis. Soundness requires the declared modes to cover all reachable configurations.

Practical note: **SDC is a Tcl script**, not declarative data — conditionals, variables (`$clk_period`), mode branches. Step zero of any validation is elaborating it to a flat constraint list.

### Elaborated (L2/04 steps 1–2 executed)

`tools/sdc-audit.py` (driving `tools/sdc-elaborate.tcl`, a tclsh harness that stubs every SDC command and logs resolved arguments) elaborates the file over its full mode space. The counts above describe the *text*; these describe the *constraint sets*:

- **The mode space is 8** = `io_4_mode` (SCK|GPIO) × `ios_mode` (IN|OUT) × `IO_SYNC` (0|1), with the shipped file pinning **SCK/OUT/0** (138 flat constraints). No mode sees more than 39 false paths; the 112 in the text are spread across mutually exclusive branches.
- **Every false path in every mode classifies as asynchronous-external** — `mprj_io[*]`, `gpio`, `resetb`, or (`IO_SYNC=1` variants) `-through` the housekeeping GPIO pins. **Zero logically-false, zero static-class entries; zero unclassified.** L2/04's four-class discharge problem collapses to one class, in two flavours: input-side (`-from` — the endpoint needs a synchroniser: F1/F3's check) and output-side (`-to`, dominant in the shipped OUT mode — the claim is about the *external consumer's* timing, discharged by L2/06's exported-interface guarantees, not by anything inside this netlist).
- **The `_6817_` "double pin" resolves as modes, not a bug**: 0 in all four SCK modes, 1 in all four GPIO modes — it is the pad-4 function select. The other cross-mode conflicts are exactly the `*mprj*/DM[2:0]` drive-mode bus (`110` in OUT modes, `001` in IN — matching `DM_INIT 3'b110`). 41 distinct case-analysis pins total: 37 mode-invariant where set, 4 mode-selects, 19 set in only some modes.
- **Clock structure is mode-dependent**: SCK modes create a fourth clock `hkspi_clk` on `mprj_io[4]` and declare all four clocks `-logically_exclusive`; GPIO modes have three. The exclusivity declaration is itself an unverified claim of the F4 family.
- **F4 sharpened, and checked against the run log**: the shipped file pins one mode, and `cmds.log` records exactly one signoff pass (3× `sta_multi_corner.tcl` for min/max/nom RC plus one `sta.tcl` — a single elaboration of the SDC). **The shipped run timed one of the eight modes**; the other seven, whose constraint sets genuinely differ, were not timed in this run. (Scope caveat: this is the run whose artifacts we have; other runs elsewhere could in principle have covered other modes, but nothing shipped records one.)
- Lint curiosity: the file's `puts "IO[4] …"` contains an unescaped command substitution — evidence the script only ever ran under shells with a forgiving `unknown` handler.

### The synchroniser audit (L2/04 step 3, L2/06's predicate; F1/F3)

`tools/synccheck.py` traces each async input's combinational fanout to its first sequential cells and tests the structural two-flop predicate (stage-1 Q → exactly one load → stage-2 D, same clock-tree root). Run over `gl_caravel_core.v` (275,701 instances, ~3 s) and `gl_housekeeping.v` (30,569 — the macro the async inputs enter; now fetched by `fetch-data.sh`).

**Core level.** `gpio_in_core` lands on a **verified two-flop synchroniser** on `caravel_clk` — the design's only one. All 38 `mprj_io_in` bits enter `user_project_wrapper.io_in` (the user area's own problem — a B-level boundary fact); 19 also enter `housekeeping.mgmt_gpio_in`. `rstb_h` enters the `xres_buf` macro (the reset path, X4-class). `flash_io*_di` pass through housekeeping to the management core unclocked.

**Housekeeping level — no two-flop synchroniser exists behind any `mprj_io` false path.** The 38 bits resolve into exactly three structures:

1. **Bits 3 and 4 are clocks.** Bit 4 (SPI SCK) clocks 15 shift flops directly, matching the SDC's `hkspi_clk`; bit 3 (SPI CSB) gates/clocks flops *and* async-resets 45 of them — and is **declared a clock in no SDC mode** (SCK modes pin it to a constant instead), so CSB-edge timing — the SPI transaction protocol itself — lies outside every analysed mode.
2. **615 flops capture on `csclk` — a muxed clock** (`a22o`: the external-SCK path OR `wbbd_sck`, the wishbone bit-bang clock — housekeeping's SPI is drivable from firmware too). Pad-data capture in this domain is *source-synchronous* (data and clock travel together from the external master): sound under its own assumptions — which are input delays relative to SCK, not synchronisers — plus a clock-mux-select condition that mode coverage must own.
3. **40 flops on the core clock (`wb_clk_i`) capture pad bits with a single flop, heavily muxed** (a typical bit reaches 4 of them). These are genuine unsynchronised asynchronous samples. Not automatically a bug — per-bit software-paced reads tolerate single-flop capture — but the discharge argument is then *software pacing plus single-stage settling*, a strictly weaker guarantee than the two-flop predicate, and P1's `N_sync` accounting must count these 40 at single-stage MTBF.

### Clock-network cleanliness (L2/05)

`tools/clockcheck.py` walks every sequential cell's clock pin backward to its root, classifying every path node; buffers/inverters are clean, everything else is enumerated.

**Core netlist: 5,774 sinks → 4 roots, 0 clock-gate cells.** `caravel_clocking.core_clk` 4,727 + `housekeeping.serial_clock` 530 + `housekeeping.serial_load` 494 — exactly the SDC's three declared clocks, arriving via macro pins — plus 23 sinks *inside* `pll.ringosc`, i.e. exactly the X5 excision. Outside the excision every clock path is pure buffer/inverter: **the cleanliness licence for L3's clock-tree deletion (15,306 cells) is established at this level**, conditional on `caravel_clocking`'s own internals — the external-vs-PLL clock mux lives inside that macro, so its contract inherits the selection.

**Housekeeping: 771 sinks → 3 roots, 0 clock-gate cells.** `csclk` 615 (the `a22o` mux of the pad-SCK path with `wbbd_sck`), `wb_clk_i` 111, `mgmt_gpio_in[4]` 45. **`wbbd_sck` is a flop output** (`_7203_`, dfrtp): the firmware bit-bang SPI clock is a *register-generated clock*, and **no SDC mode declares a generated clock for it** — from that source, the 615-flop SPI domain is untimed in every analysed mode. The F4-family list grows: one mode of eight timed; CSB never declared a clock; and now the bit-bang half of the SPI clock mux undeclared as well.

**A checker checked the checker.** Building synccheck exposed a latent bug in `netgraph.py`'s sequential-cell table: an over-broad `dl` alternative classified the `dly*` *delay buffers* (combinational hold-fix cells) as sequential, silently cutting the W3 cycle-search graph at every one. Fixed; **W1–W4 re-run clean with identical published numbers** (the bug was latent for `caravel_core`, whose hold fixing uses `clkdlybuf` cells that never matched, and live only for `housekeeping`'s `dlymetal` cells, where synccheck tripped over it).

## picorv32 Verilog tameness

3,044 lines. The semantics obligation is **finite and enumerable** (measured by `tools/check-l4.py`, whole file — all modules; the per-module split awaits the configuration record):

| construct | count | consequence |
|---|---|---|
| `#` delays | **0** | no scheduling games |
| `casex` | **0** | — |
| `force`/`release`/`deassign` | **0** | — |
| UDPs, `fork`/`join`, events | **0** | — |
| X literals (`'bx`) | **25** | deliberate don't-cares — see below |
| `always @*` | 15 | latch-inference risk — check complete assignment |
| posedge blocks with blocking `=` | 5 of 24 (38 statements) | order-dependent within block; normal-form rewrite obligation |
| `casez` | 1 | wildcard/don't-care pattern |
| `initial` | 1 | power-up value; part of the reset story |

**22 construct sites plus 25 don't-care literals**, each individually inspectable. Not "formalise Verilog".

The 25 `'bx` literals are the deliberate don't-care idiom — synthesis chooses freely while simulation propagates X, a real simulation/synthesis divergence class; each site is a value-independence obligation or refines into spec nondeterminism per L4/03. The 5 blocking-assignment blocks (decoder, state-decode, main FSM, regfile read, PCPI mux) are all local-temporary style. `check-l4.py` owns these numbers.

## F1 confronted: the shipped timing evidence

Fetching the per-path material at the pinned SHA (now in `fetch-data.sh checks`) resolved F1's structure — and turned up two artifacts nobody had looked at.

**There are two SDCs.** The 406-line, 8-mode file this audit elaborated is `signoff/caravel/caravel.sdc` — the *chip-level* constraints. The `caravel_core` run used its own `signoff/caravel_core/caravel_core.sdc`: 2.6 KB, **single mode**, and very different in effect — `input_delay 4 -clock clk` on **all** inputs (every `mprj_io_in` bit is constrained as a 4 ns *synchronous* input, which the pads are not), exactly **two** false paths (`rstb_h`, `gpio_in_core` — precisely the two structures `synccheck.py` verified: the xres_buf reset path and the design's one true two-flop synchroniser), `hkspi_clk` created on `mprj_io_in[4]`, and ±3.75% timing derates. Its comment also names `_6817_`: **`hkspi_disable`** (the "pad-4 function select" of the mode analysis, now with its real name).

**The failing corners' path evidence was never committed.** The shipped `42-rcx_sta.min.rpt` is the *final nom run*: every reported hold path is MET (worst slack **+0.58**; setup **+4.52**). The s-corner `in2reg` failures exist in the repo only as `signoff.rpt`'s one-line verdicts — the multi-corner STA logs the run produced (`37/39/41-rcx_mcsta.*`) are not in the tree. So the acceptance of three failing corners rests on evidence outside the shipped record.

**F1's shape.** The failing `in2reg` hold paths are, under the core SDC, real constrained paths from async pads treated as synchronous — not paths excused by exceptions (the 112 mprj false paths live only in the chip-level file).

**F1 closed: the method reproduces, the verdict does not** (`tools/sta-rerun.sh`, `tools/sta-rerun.tcl`; pinned by `check-l2.py`). The STA was re-run from entirely committed inputs — the shipped gate netlist, the `caravel_core` SDC, the RCX-extracted SPEF, the macro Liberty that `config.tcl`'s `EXTRA_LIBS` names, and `sky130_fd_sc_hd` from **the open_pdks build the chip was signed off with** (`12df12e2`, the SHA recorded in `PDK_SOURCES`, fetched prebuilt by `volare`).

*The setup is faithful*: at the nominal corner our run reproduces the committed hold number to **0.01 ns** — worst hold slack **+0.59** against the committed **+0.58**. That agreement is what makes the next sentence mean something.

*The verdict does not reproduce.* At the slow corner — `ss_100C_1v60`, one of the three `signoff.rpt` records as **failing** `in2reg` hold — the same inputs give worst hold slack **+1.29 ns and zero violating paths**. Hold *improves* at the slow corner, which is the expected direction when both data and clock paths slow together. **The committed artifacts do not reproduce the committed verdict.**

A concrete mechanism sits beside it, and it is the more damaging finding: **22,193 of the SPEF's 41,542 nets (53%) name nets that do not exist in the committed netlist** — the majority antenna-diode nets, consistent with the instance-renaming step `cmds.log` records between extraction and netlist write-out. Over half the parasitics never attach. That is also why *setup* does not reproduce (ours +12.42 against the committed +4.52): with most wire RC missing, paths are optimistically fast.

So F1 is no longer a suspicion about waived corners; it is a **documented reproducibility gap in a shipped signoff package**. The three failing corners' verdicts cannot be re-derived from what was committed, and the parasitic annotation that any faithful re-derivation would need is itself only half-applicable to the netlist shipped alongside it. Note the direction of the residual risk: this does **not** show the chip is fine — it shows the evidence for either conclusion is absent. Closing F1 properly now needs the *inputs the signoff actually used*, which are not in the repository.

(One preparation step is worth recording because it is licensed by an earlier result rather than by convenience: OpenSTA's Verilog reader rejects instance *arrays*, of which this netlist has exactly three — `decap_12`, `fill_4`, `fill_8`. Dropping them is timing-neutral precisely because L3's **W4** check proved physical cells carry no signal pins.)

## The management core in the pinned netlist is VexRiscv

Found while reading the hold report: its first path runs through `soc.core.VexRiscv.RegFilePlugin_regFile[7][12]`. Checked directly: the pinned `gl_caravel_core.v` contains **14,297** `VexRiscv`-prefixed identifiers and **zero** `picorv32` anywhere (the pinned `rtl_caravel_core.v` likewise). **The fabricated artifact this repository pins carries the VexRiscv/LiteX management core, not picorv32.** The picorv32 configuration exists in the ecosystem (`caravel_pico`), but it is not what this netlist is. Filed as F7 — resolved: **the target follows the silicon.** The shipped core is identified as **VexRiscv `MinDebugCache`** by plugin-set matching: the GL's register prefixes are {Branch, Csr, DBusSimple, Debug, HazardSimple, IBusCached, LightShifter, RegFile}Plugin — a subset of `MinDebugCache`'s (whose remaining plugins are stateless and leave no registers), while `LiteDebug`'s stateful `MulDivIterativePlugin` is absent, ruling it out. So: pipelined RV32I, instruction cache, simple data bus, machine-mode CSRs, hazard interlocks, iterative shifter, debug unit — **no hardware multiply/divide**. The shipped RTL pair (`mgmt_core.v` LiteX output + `VexRiscv_MinDebugCache.v` SpinalHDL output) is now pinned in `fetch-data.sh`; its construct census (same method as picorv32's): VexRiscv — 0 delays/casex/force-class, **7** `'bx` don't-cares, 186 `always @*`, 1 casez, 0 initial, 13 posedge blocks (0 with blocking); mgmt_core — all zeros except 355 `always @*` and 7 posedge blocks (2 with blocking). Machine-emitted narrowness, as the book predicted: fewer dark corners, vastly more blocks, no IR spec behind either generator. **Pipeline anatomy, measured** (`check-l5.py`): four main stages behind a two-stage cached fetch — the inter-stage register banks carry **17** (decode→execute), **12** (execute→memory), and **9** (memory→writeBack) declared synthesizable registers (excluding the simulation-only `*_string` debug regs); the I-cache is **direct-mapped** (single way, single bank); hazards are interlock-style (`HazardSimplePlugin` + write-back buffer, with `BYPASSABLE_*` stage signals present — the bypass configuration is config-record material); **zero** branch-prediction structures. L5/00 is re-derived around this machine.

**The encoding partition and the UB set** (`tools/partition.py`): the spec-side patterns (49 instructions: RV32I + Zicsr + fences + `ecall`/`ebreak`/`mret`/`wfi` — WFI is implemented) against the 20 legality cubes extracted from the shipped decoder's own `decode_LEGAL_INSTRUCTION` expression, compared exactly over all 2³² words by BDD. **Spec-only 0**: every spec-legal word is accepted. **Decoder-accepted-beyond-spec: 4,292,609 words** — all 2²² words of reserved LOAD funct3=110, 98,304 reserved shift-immediate variants (nonzero high `funct7` bits on `slli`/`srli`/`srai`), and exactly one SYSTEM word, **`sret`**, caught in `mret`'s slot via a don't-care bit (decoder-minimisation don't-cares throughout). These words execute rather than trap, and the spec's answer is L6/03's **spec-UB clause**: their architectural behaviour is unspecified — while the layered guarantees below the ISA (envelope, invariant, bus discipline, bounded retirement) still hold, so no instruction is a halt-and-catch-fire. This measured set *is* the UB set, pinned by `check-l6.py`. The spec side no longer rests on hand transcription: all 49 patterns are validated against the official `riscv-opcodes` tables at a pinned commit (`data/opcodes/`, assembler pseudo-forms excluded), which also confirm `sret`'s encoding as the UB set's lone SYSTEM word.

**The configuration record, extracted** (`tools/config-record.py`; pinned by `check-l5.py`): ISA **RV32I only** — no C, no hardware M (mul/div trap to software), no A. Implemented CSRs: `mstatus, mie, mtvec, mepc, mcause, mtval, mip` plus two **custom** CSRs `0xBC0`/`0xFC0` (the LiteX external-interrupt mask/pending pair); **no `mscratch`, no `misa`, and no counters** — `rdcycle`/`rdinstret` trap. The I-cache is **64 bytes**: 2 lines × 32 B, direct-mapped, 28-bit tags — a two-line fetch buffer, which shrinks the cache-invariant and WCET burden to nearly picorv32 levels while still requiring the `fence.i` story. Hazards are **interlock-only**: a writeBackBuffer address match raises `srcNHazard` (a stall), no forwarding muxes exist. The **reset vector is a CSR-writable register** (`mgmtsoc_vexriscv`, init `0x10000000` — the flash XIP base): software can retarget where reset jumps, a register-dependent hypothesis of the F4/F6 family for the spec. `softwareInterrupt` and `timerInterrupt` are **tied to zero** — the standard MSIP/MTIP mechanisms are structurally dead; every interrupt arrives through the 32-bit `externalInterruptArray` and the custom CSR pair. Both core buses are **Wishbone** with burst signals (CTI/BTE).

**The memory map, six ways** (`tools/memmap.py`; pinned by `check-l7.py`): the artifacts L7/03 predicted would drift — the shipped decode in `mgmt_core.v`, the LiteX generator source `litex/caravel.py`, the generated `mem.h` and linker `regions.ld`, the hand-written headers `defs.h`/`csr-defs.h`, and the housekeeping documentation `memory_map.rst` — extracted and diffed exactly. The shipped decode is seven windows: `dff` 0x0000_0000+1K, `dff2` 0x0000_0400+512, `flash` 0x1000_0000+16M, `hk` 0x2600_0000+4M, `mprj` 0x3000_0000+256M, `csr` 0xF000_0000+64K, `vexriscv_debug` 0xF00F_0000+256. All seven bases agree with the generator's `mem_map`, the reset vector equals the flash base, the CSR window's 20 LiteX banks (0x800 bytes each: ctrl, debug, SPI-flash, GPIO, logic analyzer, SPI master, timer, UART, the six `user_irq` event blocks, …) enumerate cleanly, and all 112 documented housekeeping addresses land inside the `hk` window. Three real diffs. **(1)** The generator declares `hk` as 3 MB but LiteX's power-of-two decode ships 4 MB: `0x2630_0000–0x263F_FFFF` also selects housekeeping — and **no software-visible description mentions that megabyte**. The generated `mem.h` says 3 MB, and so does the generated `regions.ld` that the firmware's own linker script `INCLUDE`s, so the shipped software is *linked* against a map strictly smaller than the hardware decodes. **(2)** Accesses to *unmapped* addresses do not trap — the shared interconnect times out after **10⁶ cycles** (a ~100 ms stall at 10 MHz), acks with `0xFFFF_FFFF`, and increments a `bus_errors` CSR; and `defs.h` contains four *live* pointers into unmapped space (`reg_rw_block0/1` at 0x0100_0000/0x0110_0000, `reg_ro_block0` at 0x0200_0000 — the "storage area" of a RAM that was configured out — and `reg_la_sample` at 0x2500_0030), each a dormant 10⁶-cycle stall in the shipped firmware headers. **(3)** `csr-defs.h` defines `CSR_DCACHE_INFO` = machine-CSR 0xCC0, which the shipped core does not decode (it has no data cache; reading it traps) — while independently confirming the custom 0xBC0/0xFC0 pair. **(4)** The linker script the DV flow actually builds with — `sections.lds`, selected by `verilog/dv/make/cpu.makefile`, where the vexriscv-specific `sections_vexriscv.lds` is commented out — **hardcodes its own copy of the memory map**: its `INCLUDE ../../generated/regions.ld` is commented out too. That seventh, hand-maintained copy has drifted on two windows, understating `mprj` as **1 MB** where the hardware decodes 256 MB and `hk` as **1 MB** where it decodes 4 MB. Nothing built by this flow can address the user project beyond its first megabyte. Bonus extraction: the external-interrupt array wiring is right there in `mgmt_core.v` — bit 0 = timer, bit 1 = UART, bits 2–7 = `user_irq[0:5]`, bits 8–31 unused — the system half of L6/01's funnel.

**The generated CSR header closes the map** (`check-l7.py` csr-header): the SoC's *fifth* description of its own address space is the firmware header `verilog/dv/generated/csr.h` — emitted by the same LiteX run as the RTL (its banner records the same revision, one second earlier) and the only artifact that names the CSR banks **semantically**. It agrees with the RTL decode **20-for-20**, and it disambiguates what the Verilog leaves generic: bank 10's `mgmtsoc_en`/`mgmtsoc_load`/`mgmtsoc_value` is `TIMER0`, and banks 13–18 are the six `USER_IRQ` event blocks — confirming the interrupt map from a third independent direction after the RTL and the docs. All 84 header symbols land inside decoded banks, and so do all **49** of `defs.h`'s symbolic pointers (previously only the 6 literal ones could be checked). The finding: **two `defs.h` macros are unbuildable** — `reg_debug_data` and `reg_debug_txfull` are defined in terms of `CSR_DEBUG_RXTX_ADDR` and `CSR_DEBUG_TXFULL_ADDR`, which the generated header never defines, because the debug UART is a Wishbone bridge rather than a CSR-mapped UART. Any firmware touching them fails to compile.

**The interrupt path, measured end to end** (`tools/irqmap.py`; pinned by `check-l7.py`): every hop of the external-interrupt path extracted from the shipped RTL and diffed against the generated `interrupts.rst` — which agrees exactly. Chip level: the wrapper's six lines are `{irq_spi[2:0], user_irq[2:0]}` — housekeeping drives the high three, the user project the low three. Inside `mgmt_core`, each line crosses the clock boundary through a **2FF MultiReg synchroniser** (LiteX inserts these in the RTL — a synchroniser discipline invisible to the gate-level audit's netlist-side census) and lands in a **latched event block**: configurable change/edge trigger, pending set on trigger and held until software writes one to clear, `irq = pending ∧ enable`. The timer and UART sources are the same EventManager shape. In the core, the custom CSR pair's semantics are sharper than any documentation states: **`0xBC0` (mask) is read/write, reset 0** — out of reset every line is masked; **`0xFC0` (pending) is read-only** — a CSR *write* to it raises illegal access and traps — and what it reads is a **live view** `mask ∧ RegNext(lines)`, *not a latch*: the core remembers nothing, and interrupt persistence is entirely the SoC event blocks' job. This settles the level-vs-latched question L6/01 had explicitly deferred to the RTL diff, and it splits L5/05's "no lost interrupts" obligation cleanly: the core-level half is the funnel equation, the persistence half belongs to `Sys(F)`'s device models.

**The trap surface, measured** (`tools/config-record.py` `choices()`; pinned by `check-l6.py`): the measurable choice-register rows (L6/02) plus three outright deviations from the ratified trap semantics. The choices: **misaligned accesses trap** (causes 4/6, detected at Execute) with the bus command *suppressed* — no side effect; **illegal instructions** trap with cause 2 and `mtval` = the instruction word; **`mtvec` has no reset value** (software must write it before enabling any trap source), its `base[31:2]` and `mode[1:0]` are both writable *storage* — but the trap redirect is unconditionally `{base, 00}`: **vectored mode does not exist behaviourally**, and the mode field reads back whatever was written, including reserved values (a WARL readback to adjudicate). The deviations: **`ebreak` has no breakpoint-exception path** — cause 3 does not exist; with a debug session it halts into the debug unit, without one it retires as a NOP; **`ecall` writes the instruction word (`0x00000073`) into `mtval`** where the standard says zero; and **no access fault is reachable** — the core's own Wishbone bridges tie both bus-error inputs to zero (`iBus_rsp_payload_error = 0`, `dBus_rsp_error = 0`), discarding the ERR wiring the SoC drives into the core's ports, and the MMU exception path is tied off, so the cause-1/5/7 logic in the plugins is structurally dead. Net: the complete reachable synchronous trap surface of the shipped core is causes **{0, 2, 4, 6, 11}**, plus the external interrupt as the only live asynchronous cause. The deviations go to L6/01's authored residue as overrides of the imported model; the choices populate L6/02's register.

**The pad power-up defaults, decoded** (`tools/pads.py`; pinned by `check-l7.py`): the 38 `gpio_defaults_block` constants extracted (pads 0–4 literal in `caravel_core.v`, 5–37 through `user_defines.v`'s mode macros), every 13-bit slice verified against its pad index, and the control block's reset shown to load from the defaults word verbatim. The power-up state: pads 0/1 (JTAG, SDO) are management-bidirectional with **output disabled** and strong drive mode selected; pad 3 (CSB) is a weak pull-up; the other 35 pads are management standard input, no pull. So **at power-up no pad actively drives** — settling L7/04's non-hazardous-defaults condition (i) by measurement: the UART TX pad is high-Z until software configures it. Two stale artifacts: `DM_INIT`/`OENB_INIT` exist in *both* repos' `defines.v` with **different** DM values (caravel `3'b001`, mgmt_soc `3'b110`) and are referenced by no pad RTL — the defaults blocks are the whole mechanism; and caravel `defines.v`'s comment claims pads default to *user* input when the measured defaults are all *management* input.

**The firmware anchor corpus** (`tools/fwanchors.py`; pinned by `check-l5.py`): the shipped interrupt-facing firmware, extracted as L6/01's working-software anchors — and it is consistent with every measured core fact. `crt0_vex.S` writes `mtvec` *before* setting `mie` (exactly the discipline the missing reset value forces — the firmware authors knew); the trap entry saves the 16 caller-saved registers and returns with `mret`; across the corpus the mask CSR (`0xBC0`) is read and written while the pending CSR (`0xFC0`) is **only ever read** — the write that would trap is never exercised. One stale expectation: `crt0` sets `mie = 0x880` (MTIE | MEIE), but MTIE is structurally dead on this SoC — the timer wire is tied to zero and the LiteX timer interrupts through external-array bit 0. Harmless, and exactly the drift the anchor corpus exists to surface.

**Flash is software-writable** (`check-l7.py` f-immutable): L7/04's immutability question is answered, negatively. Beside the read-only XIP window, CSR bank 3 exposes the LiteSPI **master** path: a write to `master_rxtx` pushes bytes into the TX FIFO, the crossbar arbitrates `{master, mmap}` and grants the master its own CSR-controlled chip select, and nothing gates it — no write-protect logic exists anywhere in `mgmt_core.v`. Software can clock WREN/page-program/erase sequences into the boot flash. Epoch independence therefore needs flash immutability as an *explicit hypothesis on the firmware* — a checkable property of a concrete image, like UB-freedom — not as a hardware fact; the flash part's own `WP#`/block-protect bits are board-level X4 territory.

**The core runs, and its bus discipline holds** (`tools/run-sim.sh`, `tools/sim/tb_core.v`; pinned by `check-l5.py`): the first execution of the design in this project. The shipped `VexRiscv_MinDebugCache` is wired to a two-region memory — flash at the XIP base the reset vector targets, RAM where the linker puts data and stack — loaded with the image built above, and run for 200,000 cycles under continuous assertion of L5/04's Wishbone clauses. It **executes**: 64 instruction fetches, 28 data transactions, of which **14 writes — exactly the 14 bytes the test payload stores**, which is how we know the program genuinely ran rather than the harness merely spinning. **Zero violations** of the clauses (`STB ⇒ CYC`; request address/`WE`/`SEL` stable until `ACK`; bounded termination; the instruction bus never writes). The monitor is *validated by a negative control* rather than trusted — `run-sim.sh --negative` stretches memory latency past the termination bound, and the clause duly fires; a monitor that cannot fail proves nothing.

**The retirement measure, measured — and it obeys the claimed law.** The same run records the gap between retirements at the writeBack commit point. Over ~50,000 retirements the distribution is dominated by **3-cycle** gaps (the taken-branch refill of the startup code's idle loop — L5/01's "pipeline refill at pipe depth" row), with a small tail at 4–7 for the store sequence and a handful of large gaps that are I-cache misses. Sweeping the memory's wait states then turns L5/01's `f(B)` from a shape into a **law**: the worst gap is exactly affine, **`gap_max = 24 + 8·B`**, and the slope is **8 — the cache line length in words**, measured independently in the configuration record (32 B lines). Each word of the burst refill pays the bus latency once. The measure's form and the cache geometry corroborate each other from different directions, which is the kind of agreement that makes a modelling claim credible. These are lower bounds on the true worst case — one execution, not a proof — but they establish that the table's *form* is right.

**A real flash image, built and checked UB-free** (`tools/build-firmware.sh`, `tools/imagecheck.py`; pinned by `check-l6.py`): L6/03's spec-UB clause is only tolerable because UB-freedom is a *checkable property of a concrete image* — and now it is checked rather than asserted. With the RV32 cross toolchain installed, an image is built from the shipped `crt0_vex.S` and the shipped `sections.lds` at `-march=rv32i_zicsr` (exactly the measured configuration record: RV32I, no M/A/C, plus the Zicsr instructions `crt0` needs for `mtvec`/`mie`), linking `.text` at `0x1000_0000` — the flash XIP base the reset vector targets — with the stack at the top of `dff2`. Every one of its **83 instruction words lies in the spec-legal set; zero reach the 4,292,609-word spec-UB set**. For this image the UB clause is unreachable and cannot weaken any theorem about it. The checker is validated against a deliberately-bad probe image rather than trusted: it flags `sret` and a LOAD `funct3=110` word as UB, and correctly classifies an RV32M `mul` as *trapping* — not-implemented is defined behaviour, and the distinction is exactly the one L6/03 draws.

**The RTL elaborates clean — no latches, no loops, two dangling wires** (`tools/rtlcheck.py`; pinned by `check-l4.py`): with yosys installed as a real Verilog front end, L4/02's two questions are answered instead of stubbed. Across the shipped core, the SoC fabric, `housekeeping` and the GPIO control block: **zero** inferred latches (`$dlatch`/`$adlatch`/`$sr`), so every combinational block assigns its outputs on every control path; and **zero** strongly-connected components, so the RTL is combinationally acyclic — the netlist-level W3 found only the PLL, and the RTL level is clean outright. The evidence comes from an *independent* implementation of Verilog elaboration, which is the point of L4/04: a disagreement between our reading and yosys's would surface as a finding rather than as silence. The elaboration also reports wires read but never driven, and the discriminator for whether that matters is whether the unit is a **closed hierarchy** — exactly one is. The shipped core instantiates nothing it does not also define, and it contains **two undriven wires**, both fed as inputs to the instruction cache: `io_cpu_fetch_isRemoved` (never read inside the cache) and `io_cpu_fetch_mmuRsp_bypassTranslation` (latched into a register nothing reads). Both are X-inert — but that is a fact that had to be established, not assumed, and they are genuine dangling signals in shipped RTL. The other three units' undriven wires all sit at the boundary of macros we do not have, which is the RTL-level echo of the gate-level W2 result.

**The SoC-side construct census** (`check-l4.py` soc-census): the RTL around the core pair is nearly construct-free. `caravel_core.v` and `mgmt_core_wrapper.v` contain *zero* always blocks — pure structural wiring; `housekeeping.v`'s 615 gate-level flops come from just **3** wide clocked blocks (two containing blocking assignments, extending L4's normal-form rewrite obligation there; one clocked on `csclk` — the SPI domain of the L2 synchroniser finding, now visible at RTL level); and `gpio_control_block.v` contributes the one genuinely new subset construct: a **falling-edge-clocked** serial-shift block (`negedge serial_clock`). No delays, casex, X-literals, or initial blocks anywhere in the SoC set.

## Management-core options

`caravel_mgmt_soc_litex/verilog/rtl`:

```
RAM128.v                4,826,924   generated
ibex_all.v                376,548   hand-written (lowRISC)
VexRiscv_LiteDebug.v      282,421   SpinalHDL output
mgmt_core.v               274,957   LiteX/Migen output
VexRiscv_MinDebug.v       219,377   SpinalHDL output
picorv32.v                 94,517   hand-written Verilog  ← the comparison core
VexRiscv_MinDebugCache.v  237,621   SpinalHDL output      ← SHIPPED (F7)
```

## Synthesis configuration

`openlane/caravel_core/config.tcl`:
```
SYNTH_STRATEGY  "DELAY 1"     ABC combinational restructuring
SYNTH_BUFFERING 0             no synthesis-stage buffering
SYNTH_MAX_FANOUT 12
SYNTH_READ_BLACKBOX_LIB 1
(no retiming setting)         ← retiming OFF: the biggest CEC-breaker is absent
```
`housekeeping` additionally enables `PL_RESIZER_*`, `GLB_RESIZER_TIMING_OPTIMIZATIONS`, `CLOCK_TREE_SYNTH`.

Assessment: ABC restructures combinational logic (CEC's home turf, registers intact); resizer sizing/buffering is logically neutral; CTS adds the clock tree post-synthesis; fill/tap/decap/diode are inserted in P&R. **The open risk is Yosys `opt_dff`/`opt_merge` removing or merging flops**, which breaks 1:1 register correspondence — and Yosys emits no SVF-equivalent guidance.

## We ran the pipeline

The whole point of retargeting to a core we can regenerate is that the rest of the flow becomes runnable too. It is: [`run-flow.sh`](https://github.com/digama0/thinking-sand/blob/master/tools/run-flow.sh) takes the target core through synthesis, floorplan, placement, clock-tree synthesis, routing, extraction, multi-corner STA, DRC and LVS, and produces **a GDS and a nine-corner signoff table we generated rather than fetched**. The engine is [librelane](https://github.com/librelane/librelane) 3.0.6 — the OpenLane 2 successor — shipped as a single self-contained AppImage carrying OpenROAD, yosys, magic, netgen and klayout, run under bubblewrap. `tools/install-toolchain.sh --only flow` installs it.

**The result, at the same level of detail as the shipped `signoff.rpt`:**

| | hold worst | setup worst | ours | 2021 |
|---|---|---|---|---|
| f-nom / f-min / f-max | +0.10 | +12.0 … +12.8 | PASS | Passed |
| t-nom / t-min / t-max | +0.30 | +7.2 … +8.8 | PASS | Passed |
| **s-nom / s-min / s-max** | **+0.81** | **−5.7 … −8.6** | **FAIL** | **FAILED (in2reg hold)** |

Physical verification is entirely clean: magic DRC 0, klayout DRC 0, routing DRC 0, LVS 0. The design is 20,604 standard cells and 2,623 flops in 369,021 µm² at 56% utilisation.

**The same three corners fail — for the opposite reason.** The 2021 signoff failed *hold* at the three slow corners with setup comfortable (+4.52). This run fixes hold at **every** corner (worst +0.100 ns, hold TNS exactly 0) by inserting **2,409 hold buffers**, and pays for it in setup (−8.56 ns at ss). Same design, opposite trade: the modern flow prioritises hold where the 2021 one left it failing. That is the honest shape of "replicate the results even if the precise details have changed" — the numbers do not match and were never going to, but they are now *commensurable*, produced by a flow we control, and the difference has an identifiable cause rather than being a mystery.

Caveats worth keeping attached to those numbers: the floorplan parameters (40% target utilisation) are ours, not the shipped run's; this is the core alone rather than `caravel_core` with its SoC and macros; and the PDK is librelane's own sky130A rather than the 2020 `open_pdks` build the chip used — that build predates configuration variables librelane 3.x requires, so pinning the 2026 core means pinning a 2026-compatible PDK with it.

**The flow's own checker found a generator regression.** Synthesis refused to proceed on four undriven signals. Two are the long-standing instruction-cache inputs, present in the 2021 core too. The other two are **new**: `CsrPlugin_mtvec_mode[1:0]`, which the 2021 core *drives* and the 2026 core does not — the generator now declares and reads that register without ever writing it. It is inert (the signal it feeds, `xtvec_mode`, is itself never read, and `mtvec` is write-only anyway), so the config disables the checker and the fact is recorded rather than the design being quietly patched. It also exposed a gap in our own [`rtlcheck.py`](https://github.com/digama0/thinking-sand/blob/master/tools/rtlcheck.py), which reports undriven *wires* and so missed an undriven *register*.

## The target is the regenerated core

**Decision.** The design this project reasons about is the **2026-regenerated core** (`data/mgmt/VexRiscv_target.v`, produced by [`regenerate-core.sh`](https://github.com/digama0/thinking-sand/blob/master/tools/regenerate-core.sh) from a pinned generator and the recovered invocation), not the 2021 artifact committed in the silicon repository. The reason is the one this chapter keeps running into: the 2021 file cannot be reproduced from anything public, and a target that cannot be regenerated cannot be re-derived when an input moves. The 2021 file stays fetched as the provenance comparison.

**What the retarget costs, measured.** Almost nothing, because the two cores are **configuration-identical**: the same nine decoded CSRs, the same 64 B / 2-line / 32 B / 28-bit-tag / single-way I-cache, the same interlock hazards, no M/A/C, WFI present. Re-running the whole suite against the target produced exactly three failures, and all three were the checkers doing their job:

- **The encoding partition changed, and hugely in our favour.** The 2021 decoder accepted **4,292,609** reserved words; the 2026 decoder accepts **one** — `sret`, still caught in `mret`'s slot by the same don't-care. The reserved LOAD (`funct3=110`) and shift-immediate accept-sets are gone. The spec-UB clause survives but is now **vestigial rather than load-bearing**: it quantifies over a single encoding instead of four million.
- **Two "changes" were cosmetic** and revealed brittle checkers, not moved facts: the interrupt funnel is emitted as a reduction-OR `(|x)` where 2021 emitted `x != 32'h0` (same predicate), and a generated line label renumbered inside a signal name the check had hardcoded. Both checks now match the predicate rather than the spelling.

**A correction the retarget surfaced.** Comparing the two cores' `mtvec` handling showed something true of *both*, which the earlier C5 row got wrong: **`mtvec` is write-only.** Its access legality is gated on `CSR_WRITE_OPCODE`, so a pure read (`csrr mtvec`) is an illegal access and traps. The earlier claim that its mode field "reads back as written" was therefore not merely incomplete but unobservable-in-principle. The 2026 generator additionally drops the mode-field write entirely, which changes nothing architecturally *because* the register cannot be read.

**One dangling pair, unfixed in five years.** The two undriven instruction-cache inputs are present in the 2026 core exactly as in the 2021 one.

**What the retarget does NOT move: everything below L4.** The GDS, the gate netlist, the SPEF and the STA reports are artifacts of the *fabricated 2021 chip*. Retargeting the RTL does not retarget those, so L3's netlist-versus-RTL equivalence now names two different designs, and closing it honestly requires either re-running synthesis and place-and-route on the target — the "generate silicon from the 2026 plans" path, of which only the synthesis half is reachable with the installed tools — or keeping L0–L3 explicitly scoped to the fabricated instance. This is recorded as an open scoping question rather than resolved by fiat, because the answer changes what the tower's bottom four layers are *about*.

## Replicating the generator

The management SoC's RTL is LiteX output, and the repository carries the generator (`litex/caravel.py`), its driver (`litex/Makefile`) and its dependency list — so the generation step can be *re-run* rather than trusted. It was (`tools/regenerate-mgmt-core.sh`, which builds a pinned virtualenv and drives the same two commands the shipped Makefile does). Three results, in increasing order of interest.

**The shipped RTL cannot be byte-reproduced from public inputs, and the reason is recorded in the file itself.** `mgmt_core.v`'s header reads `Auto-generated by Migen (9a0be7a) & LiteX (470fc6f) on 2022-10-14 12:53:55`. LiteX `470fc6f` **exists in no reachable repository** — not upstream, not in any fork the code search reaches. The migen revision does resolve, to **2021-11-12**: ten months before the file was committed. And that header *format* was retired from LiteX before January 2022, when the generator's vendored Verilog writer replaced it. All three facts point the same way: the artifact was produced by a **stale, partly-unpublished build environment** — consistent with `requirements.txt` installing migen as an editable checkout (`-e`) that was never updated. Re-running with the newest dependencies available at the file's commit date reproduces **78%** of its non-comment lines exactly; the rest is LiteX/LiteSPI version drift (signal renamings, mostly). This is ordinary practice and not a defect, but it is the honest provenance status of a shipped chip's RTL: *the generator is published, the generated artifact is pinned, and the path between them is not reproducible.*

**The committed generator does not produce the shipped core.** `caravel.py` requests `cpu_variant="minimal+debug"`, and LiteX's variant table maps that to **`VexRiscv_MinDebug`** — the *uncached* core. The regenerated build duly selects it. But the silicon carries `VexRiscv_MinDebugCache`, which the repository's own history shows being added by hand in a separate commit (2021-11-30, alongside debug-testbench changes) — it is not an output of this flow at all. This independently confirms **F7** from a direction the netlist archaeology could not reach: `IBusCachedPlugin` and the cache arrays (`banks_0`, `ways_0_tags`) appear in the cached variant and are wholly absent from the uncached one, while both share `LightShifter` and neither has `MulDivIterativePlugin`. The identification was right, and the flow that would contradict it is the flow nobody ran.

**The core half, and the invocation nobody wrote down.** `regenerate-mgmt-core.sh` reaches only the SoC; the core is SpinalHDL output, and — unlike every other variant — `VexRiscv_MinDebugCache` is **not a target of the upstream generator Makefile**. It was hand-added in a single 2021 commit, so the arguments that produced the silicon were never recorded. [`regenerate-core.sh`](https://github.com/digama0/thinking-sand/blob/master/tools/regenerate-core.sh) recovers them, using the same control-then-experiment structure as the STA rerun.

*The control*: `MinDebug`, whose invocation upstream **does** document, regenerates **byte-for-byte identical** to the committed file apart from one line — the git hash the generator stamps into its own header. SpinalHDL generation is deterministic and the toolchain is faithful, which is what makes the next step admissible.

*The experiment*: the same flags with the instruction cache enabled at the measured size. `-d --iCacheSize 64 --dCacheSize 0 --mulDiv false --singleCycleShift false --singleCycleMulDiv false --bypass false --prediction none` reproduces the shipped core on **every measured configuration fact**, including a cache geometry agreeing in all five dimensions (64 B total, 2 lines, 32 B lines, 28-bit tags, one way). The residual is dated rather than mysterious: the pinned 2026 generator emits counter and PMP CSRs (`mcountinhibit`, `pmpcfg0`, `pmpaddr0`, `mcycle`, `cycle`) that the 2021 silicon predates. Byte-exact reconstruction needs the era generator, whose Scala 2.11 build requires Java 8 — the one dependency this environment cannot supply.

Two generator *defaults* corroborate earlier findings from a direction that had nothing to do with them: `externalInterruptArray` defaults **true**, which is why the array residue of L6/01 exists at all; and `xtvecModeGen` defaults **false**, which is precisely why `mtvec`'s mode bits are writable storage the trap redirect ignores (L6/02's C5). Those were measured out of the Verilog months before anyone looked at the generator's argument list.

**Every fact the checkers extract survives regeneration.** `tools/replicate.py` re-derives, from the regenerated artifacts alone, the thirteen SoC-level facts the book rests on — the seven-window bus decode, the 20 CSR banks, the 10⁶-cycle interconnect timeout and its `0xFFFFFFFF` read, the external-interrupt array wiring, the 2FF synchroniser chains, the eight latched event blocks, the LiteSPI master path and the absence of write protection, the reset-vector register, the software/timer tie-offs, the construct census, and the CSR bank naming from the regenerated firmware header — and **all thirteen match**. Three initially did not, and the diagnosis is worth keeping: those extractors keyed on LiteX *instance names* (`multiregimpl131_regs0` vs `multiregimpl1310`, `gpioin0_pending_status` vs `mgmtsoc_gpioin0_status`) rather than on structure. The structures were identical; the regexes were brittle. They are now keyed on the shape of the assignment, which is what the findings actually claim — so replication did what it is supposed to do: it found a weakness in the measuring instrument rather than in the thing measured.
