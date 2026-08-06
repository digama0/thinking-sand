# Upstream's own flow — Chipyard + Hammer + OpenROAD on sky130

`flow/rocket-tiny/` hardens Rocket with a librelane config written by hand. That
was a mistake worth recording: **Chipyard already ships a physical flow for this
exact configuration** — `docs/VLSI/Sky130-OpenROAD-Tutorial.rst`, driven by
Hammer, `CONFIG=TinyRocketConfig`, sky130 + OpenROAD, entirely open tools. Every
decision made by hand in `rocket-tiny` is already made there, and better:

| | upstream | our librelane config |
|---|---|---|
| die | 3588 × 2992 µm = **10.7 mm²** | 4200 × 4200 = 17.64 mm² |
| SRAM macros | **3 kinds, 6 instances** (SRAM22) | 20 instances (PDK OpenRAM) |
| macro placement | explicit coordinates **and orientations** (`r90`, `mx90`) | hand-placed, axis-aligned only |
| hold margin | `clock_tree_resize.hold_margin: 0.20`, `global_route_resize.hold_margin: 0.60` | flow defaults (we failed hold by 40–90 ps) |
| congestion | `global_route.routing_adjustment: 0.3`, `macro_placement.halo: [50,50]` | discovered by trial |
| clock | 30 ns tile / 50 ns SoC, commented "relax … to meet timing" | 10 ns, unexamined |

The SRAM difference is structural rather than cosmetic. SRAM22 provides a
2048×32 macro, so the dcache scratchpad is *one* instance; the PDK's OpenRAM
macro is only 256 deep, which is why `rocket-tiny` banks eight of them behind a
hand-written mux (`srams/rocket_srams.v`). Upstream also puts the icache tag
array in a macro; we left it as flops.

## But it does not run as shipped

The tutorial warns "may break with different tool versions." That undersells it.
Its two pinned halves — Hammer's plugins and the components they drive — have
drifted apart, and **ten** distinct breakages sit between `make par` and a
result. None is a configuration mistake; each is a genuine interface change.

Against: Hammer 1.2.0, `sram22_sky130_macros` master (2026-05-06), open_pdks
sky130A via ciel, yosys 0.62, OpenROAD `dcf36133`, KLayout 0.30.7, Magic 8.3.623
— versus the tutorial's pins of yosys 0.27, OpenROAD `0264023b6`, KLayout
0.28.5, Magic 8.3.376, open_pdks 1.0.457.

**PDK skew**

1. `sky130/__init__.py: setup_io_lefs()` unconditionally patches a known
   `sky130_ef_io.lef` bug (a macro closed by the wrong `END` name). On a PDK
   build where that bug is *fixed*, the search returns nothing and an unguarded
   `[0]` raises `IndexError`. The workaround cannot survive its own fix landing.

**SRAM macro skew** — the tutorial's macro repo has moved on without the plugin

2. `sram_compiler` looks for `_tt_025C_1v80.{rcc,rc,c}.lib` extraction-fidelity
   variants; current master ships a plain NLDM `.lib`. It also logs an error and
   then uses the missing path anyway, so the failure surfaces far downstream.
3. It expects `{name}.gds`; the repo ships `{name}.gds.gz`.
4. **Six of thirteen** `sram-cache.json` entries name macros absent from that
   repo (`sram22_64x24m4w24`, `sram22_512x32m4w32`, `4096x*`, …). Removing the
   dead entries makes barstools re-map to macros that exist — but note the
   mapping is baked into generated Verilog, so `gen-collateral/*.top.mems.v`
   must be deleted to force it; deleting the `.mems.hammer.json` alone does
   nothing, because its make rule has **no recipe**.

**yosys skew**

5. The plugin emits `dfflibmap -map-only` per liberty file. `-map-only` forbids
   yosys from synthesising flop types the library lacks, and sky130 has neither
   a synchronous-reset nor an enable flop. yosys 0.62 infers `$_SDFFE_*` /
   `$_SDFFCE_*` far more eagerly than 0.27, so ~2,300 unmapped cells reach the
   netlist and P&R dies on `LEF master $_DFF_PP0_ not found`. Fix: full
   `dfflibmap` for the standard-cell library; IO pad libraries keep `-map-only`
   (they carry no flops).

**OpenROAD skew** — four separate interface changes

6. `source -verbose` → `wrong # args`. Current OpenROAD uses stock Tcl `source`.
7. `source -echo -verbose` — the same, elsewhere.
8. `place_cell -inst_name X -orient O` → `place_inst -name X -orientation O`.
9. `place_pins -random` → `PPL-0113 -random and -random_seed are obsolete.
   Skipping random pin placement.` It **warns and places nothing**, so global
   placement then fails with `GPL-0326 <port> toplevel port is not placed`. The
   most dangerous of the ten: a warning, not an error, three steps upstream of
   where it bites.

**Genuine design/tech mismatch**

10. `PDN-0233 Failed to generate full power grid`. Hammer builds each macro's
    power grid from that macro's *topmost* layer plus one. SRAM22's sky130 SRAMs
    route up to met3 but expose `vdd`/`vss` on **met2**, so the generated
    met3→met4 grid never touches a power shape. Compounding it,
    `example-sky130.yml` restricts straps to met4/met5, so met3 carries nothing
    to connect *to*. The plugin carries a `TODO: should restrict layers to those
    specified by power straps` at exactly this spot. Fix: include the macro pin
    layers and connect each to the lowest layer above it that actually has
    straps, giving met2→met4.

## What this means

This is a different finding from the Caravel one, and the difference matters.
Caravel shipped a *complete* recipe — 170 timestamped commands — that did not
reproduce its own signoff. Chipyard ships a *maintained* flow that is better
engineered than anything we would write, and it does not run against current
versions of the components it names. Neither platform has a build you can simply
execute.

The encouraging half: all ten are small, local, and open — six-line patches to
Python that generates Tcl, in a tree we can modify. That is exactly the property
[the platform assessment](../../src/platform-assessment.md) argued for when it
chose modern-and-patchable over pinned-and-frozen. The pinned-container route
would have hidden every one of these behind a working binary, and hidden with
them the fact that the flow's assumptions are now wrong.
