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

Caravel has been fabricated repeatedly and works, so these are presumably waived for good reasons (the `in2reg` paths are GPIO inputs with no meaningful external timing spec — hence the 112 false paths). "Presumably" is doing all the work.

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

275,705 instances, 187 distinct cell types. Classification is heuristic on cell names.

| class | count | share | fate |
|---|---|---|---|
| PHYSICAL (decap/tap/fill/diode) | 235,566 | **85.4%** | delete (inertness check) |
| LOGIC | 15,853 | 5.7% | **keep** |
| CLOCK | 15,306 | 5.6% | delete (after L2) |
| SEQ (flops) | **5,774** | 2.1% | **keep — the state** |
| BUF/INV | 3,109 | 1.1% | collapse |
| macros | 97 | — | holes |

Reduction 275,705 → ~21,627 (≈13×). |S| = 2^5774 at this level alone, so **model checking is not on the table** — refinement plus induction only.

Macro holes: `RAM128`×3, `housekeeping`, `gpio_control_block`×38, `spare_logic_block`×4, `digital_pll`, `simple_por`, `caravel_clocking`.

## Structural checks on the gate netlist (L3)

`tools/netgraph.py data/caravel/gl_caravel_core.v` — 7.5 s. 275,608 `sky130_*` instances (+97 macro instances = 275,705, reconciling with the looser count above), 48 top-level ports, 43 distinct pin names all classified explicitly (the tool exits non-zero on an unknown pin rather than guessing a direction).

| check | result |
|---|---|
| **W1** nets with >1 driver | **26** — all tri-state, all in `pll.ringosc`; **0 static contention** |
| **W2** read nets with no driver | 1,609 — all at hierarchy/macro boundaries |
| **W3** combinational cycles | **exactly 1 SCC, 64 nets, entirely in `pll.ringosc`** |
| **W4** physical cells with signal pins | **0** |
| | physical 235,566 (85.5%) · sequential 5,774 · nets 42,084 (DEF says 42,304, difference is power/special nets) |

**W1 discharges structurally.** The contended nets are `einvp`/`einvn` pairs with the *same* enable net on `TE` and `TE_B` — complementary polarity, so exactly one conducts. It is the oscillator's delay-trim multiplexer (`pll.itrim[k]` selects tapped path vs bypass). No functional reasoning required. Note this is idiom-dependent: a *decoded* tri-state bus would need a reachability proof instead.

**W3 makes X5's excision provably minimal.** Excise `pll.ringosc` and the netlist is contention-free and acyclic. The ring oscillator is *exactly* the set of structural violations — both the only cycle and the only contention, with the same cause. The prediction that the PLL cannot live inside the synchronous abstraction was right, and nothing else violates it.

**W2 is a hierarchy artifact**, localising to `mgmt_buffers` 631, `gpio_control_in_*` 462, `soc.core` 69, `RAM256` 64, `user_io_*` 76 — black-box macro outputs and hierarchical ports. Needs the macro interface list to reduce to genuine floats; expect ~0 residue.

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

## picorv32 Verilog tameness

3,044 lines. The semantics obligation is **finite and enumerable**:

| construct | count | consequence |
|---|---|---|
| `#` delays | **0** | no scheduling games |
| X literals (`'bx`) | **0** | no X-optimism |
| `casex` | **0** | — |
| `force`/`release`/`deassign` | **0** | — |
| `always @*` | 15 | latch-inference risk — check complete assignment |
| posedge blocks with blocking `=` | 2 of 25 | order-dependent within block |
| `casez` | 1 | wildcard/don't-care pattern |
| `initial` | 1 | power-up value; part of the reset story |

**19 specific spots**, each individually inspectable. Not "formalise Verilog".

## Management-core options

`caravel_mgmt_soc_litex/verilog/rtl`:

```
RAM128.v                4,826,924   generated
ibex_all.v                376,548   hand-written (lowRISC)
VexRiscv_LiteDebug.v      282,421   SpinalHDL output
mgmt_core.v               274,957   LiteX/Migen output
VexRiscv_MinDebug.v       219,377   SpinalHDL output
picorv32.v                 94,517   hand-written Verilog  ← chosen
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
