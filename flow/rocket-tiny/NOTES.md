# Rocket through the modern flow — how far the chain closes

The replacement target from [the platform assessment](../../src/platform-assessment.md):
a Chipyard `TinyRocketConfig` SoC, generated from Chisel and hardened by our own
flow, at one pinned era. This records what the chain actually produces, because
the interesting content is not "it worked" — it is exactly where it stops.

Reproduce with `tools/build-rocket.sh` then `tools/run-rocket-flow.sh`.

## The chain, end to end

Chisel → FIRRTL → CIRCT (`firtool` 1.75.0) → SystemVerilog → yosys/slang →
OpenROAD → Magic/KLayout/netgen. Every stage runs. **A GDS exists.**

| | |
|---|---|
| die | 4200 × 4200 µm = **17.64 mm²** |
| standard cells | 271,473 |
| SRAM macros | 20 × `sky130_sram_1kbyte_1rw1r_32x256_8` = 3.81 mm² |
| flip-flops | 12,276 |
| hold buffers inserted | 9,291 |
| fill cells | 3,293,356 (total instances 3,564,849) |
| utilisation | 29.0% |
| routed wirelength | 7,037,345 µm ≈ **7.0 m** |
| vias | 631,900 |

Synthesis alone gives 55,093 cells; CTS and hold repair take it to 269,458.
The growth is the flow buying hold margin, and it is most of the design.

## Signoff, and what fails

**Magic DRC: 0.** Clean on the streamed layout.

**Routing: 14 unresolved violations, all on met4 — 9 metal-spacing, 5 shorts.**
The router ran 64 iterations, oscillating between 5 and 247, and settled at 14.
met4 carries the PDN straps, so these are signal-versus-power-strap collisions.

**LVS: fails, on exactly one net.** Devices match exactly (84,051 each); nets
differ by one (84,585 extracted vs 84,586 in the netlist). 0 unmatched devices,
0 unmatched pins, 0 property failures, 0 illegal overlaps. The one net is
`net9497`, and it is *the same defect as the shorts above* seen from the other
side — in the extracted layout its driver's output and both loads' inputs all
sit on `VPWR`:

```
Xwire9492       VPWR VGND VGND VPWR VPWR wire9492/X   buf_4   <- input A on VPWR
Xwire9493       VPWR VGND VGND VPWR VPWR wire9493/X   buf_4   <- input A on VPWR
Xload_slew9497  wire9496/A VGND VGND VPWR VPWR VPWR   buf_4   <- output X on VPWR
```

It is a slew-repair buffer chain feeding an SRAM macro's input bus. So the
design is **not** clean: it has a real short to the power rail, the router knew
it, and LVS caught it independently. Worth stating plainly, because "Magic DRC
0" on its own reads like success — DRC checks geometry, not connectivity.

**Timing: setup passes everywhere, hold fails at six of nine corners.**

| corner | hold ws | setup ws | |
|---|---|---|---|
| ff (fast) ×3 | −0.072 … −0.091 | +9.70 … +10.36 | FAIL (hold) |
| tt (typical) ×3 | −0.046 … −0.081 | +7.78 … +8.51 | FAIL (hold) |
| ss (slow) ×3 | +0.024 … +0.113 | +3.00 … +3.80 | PASS |

This is the mirror image of both earlier results. The 2021 Caravel signoff fails
hold at the three *slow* corners; our VexRiscv run fixes hold at every corner
and pays in setup; this one fails hold at the six *fast and typical* corners
with 3–10 ns of setup margin to spare. Three flows, three different shapes of
the same trade — which is itself the argument for producing the numbers rather
than citing them.

**Design-rule checks: 6,186 max-slew, 526 max-cap, 185 max-fanout violations.**
Under-buffered long nets. This is the loose floorplan's bill, and it is a direct
trade against the routing violations — see below.

## The floorplan trade

The macros are two banks pinned to opposite die edges with a clear logic band
between them, not a packed block. A packed 5×4 block in the middle fails global
routing outright (GRT-0116).

Then, within the edge-banked layout, channel width trades one failure for
another. At 130 µm channels on a 3800 µm die, routing left **16** violations. At
200 µm on a 4200 µm die it leaves **14** — but the extra spread stretches nets
and buys the 6,186 slew violations. Neither setting closes; the die is sized by
SRAM rather than by logic (3.81 mm² of macro against 0.68 mm² of standard
cells), so the logic is spread thin across a die it does not need.

The lever that actually helps is not geometric: **shrink the scratchpad.** It is
a config parameter, it removes macros rather than rearranging them, and it takes
the die back under OpenFrame's ~15 mm² at the same time. 17.64 mm² does not fit
the harness the assessment picked.

## Tool findings worth keeping

**Magic's stream-out orphans macro subcells.** The GDS Magic writes has **13 top
cells**: `ChipTop` plus the SRAM macro's twelve internal subcells
(`..._bank`, `..._control_logic_rw`, `..._col_addr_dff`, …). KLayout's
stream-out of the same design has exactly one. This breaks any downstream
consumer that resolves a single top — it is what fails `KLayout.Render` and
`KLayout.DRC`, both of which librelane points at the *Magic* GDS by default.
Run KLayout DRC against `ChipTop.klayout.gds` instead.

**Fill insertion is what makes the back end unaffordable.** It multiplies the
instance count by 13× (271k → 3.56M). Post-PnR STA then runs nine corners *in
parallel* against that, and `-j 1` does not gate the step's internal fan-out:
two corners peak past 31 GB and the OOM killer takes the flow out with a bare
`SIGKILL` and no error message. IR-drop analysis dies the same way. Both are
avoidable by running the corners yourself; all nine complete individually.

**A run is ~4 GB and the flow does not clean up.** An ENOSPC mid-flow loses
placement and routing. Worse, pruning a run directory afterwards breaks
`--run-tag <tag>` resume, because that reloads the whole step chain rather than
the step you name — resume instead with a *fresh* tag plus
`--with-initial-state <step>/state_out.json`, and keep every file that state
references.

## Status

The chain closes structurally and fails physically. Nothing here is a dead end
of the kind the Caravel assessment found — no missing provenance, no
unreachable revision, no unbuildable dependency. It is one congested metal
layer and one oversized scratchpad, both parameters we control.
