# Data provenance — the fetched design artifacts

**Not committed.** The repo-root `data/` directory is gitignored: ~490 MB, all reproducible from upstream. Regenerate with `tools/fetch-data.sh [all|small|caravel|checks|mgmt|pdk]`.

## Provenance — pinned, deliberately

| repo | commit | date |
|---|---|---|
| `efabless/caravel` | `27cbe49c90ba5362ad52c9968dd98e035c30c74f` | 2024-11-04 |
| `efabless/caravel_mgmt_soc_litex` | `503eda0790085712ffef7f4ad8934c7daed3237f` | 2024-01-03 |
| `google/skywater-pdk-libs-sky130_fd_sc_hd` | `ac7fb61f06e6470b94e8afdf7c25268f62fbd7b1` | 2020-11-10 |
| `riscv/riscv-opcodes` | `62a06d2b4a228a9b157ed9149bd99dd3912a5ba8` | 2026-07-30 |

Refs are commit SHAs, not branches. `findings.md` quotes exact byte counts, instance counts, and Liberty table values from these files, and `L0/09` quotes structural-check results. A floating ref would silently invalidate all of it. **If you move to newer upstream: bump the SHA in `tools/fetch-data.sh`, re-run, and re-derive Findings — never one without the other.**

The design's own toolchain pins are recorded separately, inside the fetched artifacts: `data/caravel/OPENLANE_VERSION` and `data/caravel/PDK_SOURCES`.

## Contents

```
caravel/
  rtl_caravel_core.v       44 KB    RTL top level (instantiates mgmt_core_wrapper)
  gl_caravel_core.v        33 MB    gate-level netlist — the L0/09 and L3 subject
  gl_housekeeping.v       3.8 MB    housekeeping macro's own gate netlist (synchroniser audit)
  caravel_core.def[.gz]   118 MB    placement + routing
  caravel.gds[.gz]        291 MB    full-chip layout
  caravel.sdc              26 KB    the chip-level 8-mode SDC — the L2 subject
  caravel_core.sdc        2.6 KB    the caravel_core run's own single-mode SDC (F1)
  sta.{min,max,worst_slack,wns}.rpt per-corner STA reports from the shipped signoff (F1)
  signoff.rpt             413 B     the STA verdict; 3 of 9 corners fail hold (F1/F2)
  cmds.log                 33 KB    170 literal timestamped commands — the flow "spec"
  config.tcl               14 KB    synthesis configuration
  memory_map.rst           11 KB    the housekeeping memory-map documentation (memmap.py)
  user_defines.v, gpio_control_block.v, defines.v
                                    the pad power-up defaults + their loader (pads.py)
  metrics.csv, warnings.log, OPENLANE_VERSION, PDK_SOURCES
mgmt/
  mgmt_core.v             275 KB    the SHIPPED SoC fabric: LiteX/Migen output — bus decode,
                                    CSR banks, peripherals, interconnect (L5/L7 subject)
  VexRiscv_MinDebugCache.v 238 KB   the SHIPPED core: SpinalHDL output, pipelined RV32I (F7)
  caravel.py               16 KB    the LiteX generator source — the memory map's intent side
  defs.h, csr-defs.h       12 KB    the firmware's address headers — the map's software side
  interrupts.rst          1.3 KB    generated interrupt-assignment docs (irqmap.py)
  firmware/                18 KB    crt0_vex.S, isr.c, irq_vex.h + friends — the
                                    interrupt-facing anchor corpus (fwanchors.py)
  picorv32.v               95 KB    the comparison core: hand-written, 3,044 lines (L4 census)
  mgmt_core_wrapper.v, defines.v
opcodes/
  rv_i, rv32_i, rv_zifencei, rv_zicsr, rv_system, rv_s
                                    the official encoding tables — validates the
                                    partition's hand-tabulated spec side (L6/03)
pdk/
  inv_1.gds, nand2_1.gds, dfxtp_1.gds          sample cell layouts
  inv_1__{tt_025C_1v80,ss_100C_1v60,ff_n40C_1v95_ccsnoise}.lib.json
                                    three corners of one cell — the L0/03 and L2 subject
```

The fast corner exists only as the `_ccsnoise` variant at this SHA, and carries more data (composite-current-source noise models) than the plain file would.

## Tools that consume this

The per-layer scoreboards `tools/check-l0.py` … `check-l7.py` (run all via `tools/check-all.py`; rendered into the book as the [scoreboard](scoreboard.md)) drive the extractors:

| tool | input | produces |
|---|---|---|
| `tools/netgraph.py` | `gl_caravel_core.v` | W1–W4 structural checks (L0/09) |
| `tools/synccheck.py` | gate netlists | 2FF-synchroniser audit of async inputs (L2/06) |
| `tools/clockcheck.py` | gate netlists | clock-network root/gate census (L2/05) |
| `tools/sdc-audit.py` + `sdc-elaborate.tcl` | both SDCs | mode elaboration, exception classes (L2/04) |
| `tools/config-record.py` | `VexRiscv_MinDebugCache.v`, `mgmt_core.v` | the configuration record (L5) |
| `tools/partition.py` | `VexRiscv_MinDebugCache.v`, `opcodes/*` | the encoding partition + UB set, spec side validated (L6/03) |
| `tools/memmap.py` | `mgmt_core.v`, `caravel.py`, `defs.h`, `memory_map.rst` | the four-way memory-map diff (L7/03) |
| `tools/irqmap.py` | `mgmt_core.v`, wrapper, chip RTL, `interrupts.rst` | the end-to-end interrupt-path diff (L7/03) |
| `tools/pads.py` | `rtl_caravel_core.v`, `user_defines.v`, `gpio_control_block.v` | the 38 pad power-up defaults, decoded (L7/04) |
| `tools/fwanchors.py` | `firmware/*` | the interrupt-facing firmware anchor corpus (L5/05, L6/01) |
| `tools/gdsdump.py`, `tools/bbox.py` | any `.gds` | record/layer census, per-layer bounding boxes |

`netgraph.py` exits non-zero on an unrecognised pin name rather than guessing a direction, so re-running it against a different library is a deliberate act.
