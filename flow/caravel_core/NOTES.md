# caravel_core through the modern flow — the obstacle chain

The VexRiscv core alone goes end to end (`flow/vexriscv/`, GDS + nine-corner
signoff). The full `caravel_core` does not, and the reasons are worth recording
because each is a concrete portability finding about the shipped RTL, not a
configuration mistake. In order of discovery, all now resolved except the last:

1. **Missing includes.** `digital_pll.v` includes `digital_pll_controller.v` and
   `ring_osc2x13.v`, which the shipped `VERILOG_FILES` list does not name — the
   2021 flow found them by include path.
2. **Implicit net declarations.** librelane reads Verilog with `-noautowire`;
   `caravel_core.v` relies on implicit wires (`qspi_enabled` and friends) while
   `defines.v` has left `` `default_nettype none `` in force, its own reset being
   gated behind `` `ifdef SIM ``. Yosys's message names `default_nettype`, but the
   cause is the flag. Fixed by `USE_SLANG` (the slang front end does not pass it).
3. **Compilation units.** slang follows SystemVerilog rules, so `` `define ``s in
   `defines.v` do not reach `caravel_core.v`. Fixed by `--single-unit`.
4. **Hard-macro models.** Fourteen macro modules (`gpio_defaults_block`,
   `housekeeping`, `caravel_clocking`, …) must be supplied as Verilog; the 2021
   flow blackboxed them from `.lib` via `SYNTH_READ_BLACKBOX_LIB`.
5. **Power pins.** librelane defines `USE_POWER_PINS` by default, which makes
   `mgmt_core.v` connect `.vccd1`/`.vssd1` on the VexRiscv instance — ports the
   core does not have. The 2021 flow evidently did not define it at synthesis.
6. **The PLL is unsynthesizable**, and the tool says so independently: slang
   rejects `ring_osc2x13`'s delay controls as "unsynthesizable timing control".
   This is X5 / L0-09's W3 finding arriving from the opposite direction — the
   ring oscillator is exactly the part that cannot live inside the synchronous
   abstraction. Suppressed here with `--ignore-timing`.
7. **`inout` on a macro boundary.** Reading the gate-level `user_project_wrapper`
   stub as RTL trips yosys-slang issue #143. Correct fix: it is a MACRO, and
   belongs in `EXTRA_LIBS`, not `VERILOG_FILES`.
8. **UNRESOLVED — conflicting initial values.** Inside synthesis proper, yosys
   rejects `soc.core.mgmtsoc_litespisdrphycore_dq_i[0]`: the LiteX SoC declares
   `reg [1:0] ... = 2'd0` and drives only bit 1, so bit 0 carries both an `x`
   and a `0` initial value. 27 such conflicts. This is an RTL property of the
   generated SoC, not a flow setting.

Reproduce with: `librelane --pdk-root <dir> --pdk sky130A --to Yosys.Synthesis
flow/caravel_core/config.json` inside `librelane-shell`.
