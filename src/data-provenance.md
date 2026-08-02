# Data provenance — the fetched design artifacts

**Not committed.** The repo-root `data/` directory is gitignored: ~490 MB, all reproducible from upstream. Regenerate with `tools/fetch-data.sh [all|small|caravel|checks|mgmt|pdk]`.

## Provenance — pinned, deliberately

| repo | commit | date |
|---|---|---|
| `efabless/caravel` | `27cbe49c90ba5362ad52c9968dd98e035c30c74f` | 2024-11-04 |
| `efabless/caravel_mgmt_soc_litex` | `503eda0790085712ffef7f4ad8934c7daed3237f` | 2024-01-03 |
| `google/skywater-pdk-libs-sky130_fd_sc_hd` | `ac7fb61f06e6470b94e8afdf7c25268f62fbd7b1` | 2020-11-10 |

Refs are commit SHAs, not branches. `findings.md` quotes exact byte counts, instance counts, and Liberty table values from these files, and `L0/09` quotes structural-check results. A floating ref would silently invalidate all of it. **If you move to newer upstream: bump the SHA in `tools/fetch-data.sh`, re-run, and re-derive Findings — never one without the other.**

The design's own toolchain pins are recorded separately, inside the fetched artifacts: `data/caravel/OPENLANE_VERSION` and `data/caravel/PDK_SOURCES`.

## Contents

```
caravel/
  rtl_caravel_core.v       44 KB    RTL top level (instantiates mgmt_core_wrapper)
  gl_caravel_core.v        33 MB    gate-level netlist — the L0/09 and L3 subject
  caravel_core.def[.gz]   118 MB    placement + routing
  caravel.gds[.gz]        291 MB    full-chip layout
  caravel.sdc              26 KB    112 false paths, 45 case analyses — the L2 subject
  signoff.rpt             413 B     the STA verdict; 3 of 9 corners fail hold (F1/F2)
  cmds.log                 33 KB    170 literal timestamped commands — the flow "spec"
  config.tcl               14 KB    synthesis configuration
  metrics.csv, warnings.log, OPENLANE_VERSION, PDK_SOURCES
mgmt/
  picorv32.v               95 KB    the chosen core: hand-written, 3,044 lines, 19 flagged
                                    Verilog sites (L4). RV32IMC — there is no picorv64;
                                    the other mgmt-core options are Ibex and VexRiscv.
  mgmt_core_wrapper.v, defines.v
pdk/
  inv_1.gds, nand2_1.gds, dfxtp_1.gds          sample cell layouts
  inv_1__{tt_025C_1v80,ss_100C_1v60,ff_n40C_1v95_ccsnoise}.lib.json
                                    three corners of one cell — the L0/03 and L2 subject
```

The fast corner exists only as the `_ccsnoise` variant at this SHA, and carries more data (composite-current-source noise models) than the plain file would.

## Tools that consume this

| tool | input | produces |
|---|---|---|
| `tools/netgraph.py` | `gl_caravel_core.v` | W1–W4 structural checks (L0/09). 7.5 s. |
| `tools/gdsdump.py` | any `.gds` | record/layer/element census |
| `tools/bbox.py` | any `.gds` | per-layer bounding boxes in µm |

`netgraph.py` exits non-zero on an unrecognised pin name rather than guessing a direction, so re-running it against a different library is a deliberate act.
