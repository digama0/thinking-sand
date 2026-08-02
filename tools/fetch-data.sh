#!/usr/bin/env bash
# Fetch the design artifacts the scoping documents refer to.
#
# Everything lands in data/, which is gitignored: these files total ~350 MB and are
# reproducible from upstream, so they are deliberately not committed.
#
# Refs are PINNED to commit SHAs, not branches. findings.md quotes exact byte counts,
# instance counts and table values from these files; a floating ref would silently
# invalidate those numbers. If you deliberately move to a newer upstream, bump the SHA
# here, re-run, and re-derive findings.md — do not do one without the other.
#
# Usage:  tools/fetch-data.sh [all|caravel|mgmt|pdk|small]
#         small  = everything except the two large binaries (~1 MB total)

set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/{caravel,mgmt,pdk}

CARAVEL=efabless/caravel@27cbe49c90ba5362ad52c9968dd98e035c30c74f          # 2024-11-04
MGMT=efabless/caravel_mgmt_soc_litex@503eda0790085712ffef7f4ad8934c7daed3237f  # 2024-01-03
PDK=google/skywater-pdk-libs-sky130_fd_sc_hd@ac7fb61f06e6470b94e8afdf7c25268f62fbd7b1  # 2020-11-10
OPCODES=riscv/riscv-opcodes@62a06d2b4a228a9b157ed9149bd99dd3912a5ba8       # 2026-07-30

get() {  # get <repo@sha> <path-in-repo> <dest>
  local repo="${1%@*}" sha="${1#*@}" src="$2" dst="$3"
  if [ -s "$dst" ]; then printf '  = %s\n' "$dst"; return; fi
  mkdir -p "$(dirname "$dst")"
  if curl -fsSL --max-time 300 -o "$dst" \
      "https://raw.githubusercontent.com/$repo/$sha/$src"; then
    printf '  + %-46s %10s B\n' "$dst" "$(wc -c < "$dst")"
  else
    printf '  ! FAILED %s\n' "$src" >&2; rm -f "$dst"; return 1
  fi
}

fetch_small_caravel() {
  echo "caravel (text artifacts)"
  get $CARAVEL verilog/rtl/caravel_core.v            data/caravel/rtl_caravel_core.v
  get $CARAVEL signoff/caravel/caravel.sdc           data/caravel/caravel.sdc
  get $CARAVEL signoff/caravel_core/signoff.rpt      data/caravel/signoff.rpt
  get $CARAVEL signoff/caravel_core/cmds.log         data/caravel/cmds.log
  get $CARAVEL signoff/caravel_core/OPENLANE_VERSION data/caravel/OPENLANE_VERSION
  get $CARAVEL signoff/caravel_core/PDK_SOURCES      data/caravel/PDK_SOURCES
  get $CARAVEL signoff/caravel_core/metrics.csv      data/caravel/metrics.csv
  get $CARAVEL signoff/caravel_core/warnings.log     data/caravel/warnings.log
  get $CARAVEL openlane/caravel_core/config.tcl      data/caravel/config.tcl
  get $CARAVEL openlane/Makefile                     data/caravel/openlane-Makefile
  # housekeeping is a macro inside caravel_core; its own gate netlist is needed to
  # trace async inputs to their synchronisers (synccheck.py / F1, F3)
  get $CARAVEL verilog/gl/housekeeping.v             data/caravel/gl_housekeeping.v
  # the caravel_core run's OWN sdc (distinct from signoff/caravel/caravel.sdc!)
  # and its per-path STA reports — the raw material for closing F1
  get $CARAVEL signoff/caravel_core/caravel_core.sdc                     data/caravel/caravel_core.sdc
  get $CARAVEL signoff/caravel_core/openlane-signoff/42-rcx_sta.min.rpt data/caravel/sta.min.rpt
  get $CARAVEL signoff/caravel_core/openlane-signoff/42-rcx_sta.max.rpt data/caravel/sta.max.rpt
  get $CARAVEL signoff/caravel_core/openlane-signoff/42-rcx_sta.worst_slack.rpt data/caravel/sta.worst_slack.rpt
  get $CARAVEL signoff/caravel_core/openlane-signoff/42-rcx_sta.wns.rpt data/caravel/sta.wns.rpt
  # the human-written memory-map documentation (the docs side of memmap.py)
  get $CARAVEL docs/rst/memory_map.rst           data/caravel/memory_map.rst
}

fetch_big_caravel() {
  echo "caravel (large binaries — ~90 MB compressed, ~400 MB expanded)"
  get $CARAVEL verilog/gl/caravel_core.v             data/caravel/gl_caravel_core.v
  get $CARAVEL def/caravel_core.def.gz               data/caravel/caravel_core.def.gz
  get $CARAVEL gds/caravel.gds.gz                    data/caravel/caravel.gds.gz
  for f in data/caravel/caravel_core.def data/caravel/caravel.gds; do
    [ -s "$f" ] || { echo "  … gunzip $(basename "$f")"; gunzip -c "$f.gz" > "$f"; }
  done
}

fetch_mgmt() {
  echo "management core RTL"
  # picorv32 is the hand-written option and the one the scoping targets (RV32IMC — there
  # is no picorv64; the RV64 variants of the mgmt core are Ibex/VexRiscv, both generated
  # or third-party, see L4).
  get $MGMT verilog/rtl/picorv32.v          data/mgmt/picorv32.v
  get $MGMT verilog/rtl/mgmt_core_wrapper.v data/mgmt/mgmt_core_wrapper.v
  get $MGMT verilog/rtl/defines.v           data/mgmt/defines.v
  # the SHIPPED management core (F7 resolution 2026-08-02): LiteX-generated SoC
  # around VexRiscv in its MinDebugCache configuration (identified by matching
  # the GL netlist's plugin register names against the three shipped variants)
  get $MGMT verilog/rtl/mgmt_core.v              data/mgmt/mgmt_core.v
  get $MGMT verilog/rtl/VexRiscv_MinDebugCache.v data/mgmt/VexRiscv_MinDebugCache.v
  # the other three descriptions of the memory map (memmap.py diffs all four):
  # the LiteX generator source and the firmware's address headers
  get $MGMT litex/caravel.py                     data/mgmt/caravel.py
  get $MGMT verilog/dv/firmware/defs.h           data/mgmt/defs.h
  get $MGMT verilog/dv/firmware/csr-defs.h       data/mgmt/csr-defs.h
  # the generated interrupt-assignment documentation (the docs side of irqmap.py)
  get $MGMT docs/generated/interrupts.rst        data/mgmt/interrupts.rst
}

fetch_opcodes() {
  echo "riscv-opcodes (official encoding tables — validates partition.py's SPEC)"
  for f in rv_i rv32_i rv_zifencei rv_zicsr rv_system rv_s; do
    get $OPCODES extensions/$f data/opcodes/$f
  done
}

fetch_pdk() {
  echo "SKY130 HD library samples"
  get $PDK cells/inv/sky130_fd_sc_hd__inv_1.gds                 data/pdk/inv_1.gds
  get $PDK cells/dfxtp/sky130_fd_sc_hd__dfxtp_1.gds             data/pdk/dfxtp_1.gds
  get $PDK cells/nand2/sky130_fd_sc_hd__nand2_1.gds             data/pdk/nand2_1.gds
  get $PDK cells/inv/sky130_fd_sc_hd__inv_1__tt_025C_1v80.lib.json data/pdk/inv_1__tt_025C_1v80.lib.json
  get $PDK cells/inv/sky130_fd_sc_hd__inv_1__ss_100C_1v60.lib.json data/pdk/inv_1__ss_100C_1v60.lib.json
  # Fast corner exists only in the _ccsnoise variant at this SHA (and carries more data).
  get $PDK cells/inv/sky130_fd_sc_hd__inv_1__ff_n40C_1v95_ccsnoise.lib.json data/pdk/inv_1__ff_n40C_1v95_ccsnoise.lib.json
}

fetch_checks() {
  # exactly what the layer scoreboards (check-l*.py) consume: the text artifacts,
  # the two gate netlists, and the mgmt RTL — no GDS/DEF (~40 MB instead of ~490)
  fetch_small_caravel
  fetch_mgmt
  fetch_opcodes
  get $CARAVEL verilog/gl/caravel_core.v data/caravel/gl_caravel_core.v
}

mkdir -p data/opcodes
case "${1:-all}" in
  small)   fetch_small_caravel; fetch_mgmt; fetch_opcodes; fetch_pdk ;;
  caravel) fetch_small_caravel; fetch_big_caravel ;;
  checks)  fetch_checks ;;
  mgmt)    fetch_mgmt ;;
  pdk)     fetch_pdk ;;
  all)     fetch_small_caravel; fetch_big_caravel; fetch_mgmt; fetch_opcodes; fetch_pdk ;;
  *) echo "usage: $0 [all|small|caravel|checks|mgmt|pdk]" >&2; exit 2 ;;
esac

echo
echo "data/ is $(du -sh data 2>/dev/null | cut -f1); see src/data-provenance.md"
