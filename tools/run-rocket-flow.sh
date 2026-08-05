#!/usr/bin/env bash
# run-rocket-flow.sh — harden the Chipyard Rocket SoC: RTL -> GDS -> signoff.
#
# The back half of the replacement chain (front half: tools/build-rocket.sh).
# Same librelane installation and same PDK as tools/run-flow.sh; what differs is
# that this design has SRAM macros in it, and macros change the flow's shape.
#
# Four things this config does that the VexRiscv one does not, each forced:
#
#   USE_SLANG.  Chipyard emits SystemVerilog, which yosys's default Verilog front
#     end will not read. slang does. It needs --single-unit (the design relies on
#     macros crossing file boundaries, which separate compilation units hide) and
#     --ignore-timing (generated delay controls are simulation-only).
#
#   MACROS with explicit `instances`.  librelane will not place macros for you;
#     without locations, PDN generation fails (PDN-0235) with every macro at the
#     origin. The layout below is two banks pinned to opposite die edges with a
#     clear band of logic between them. A packed block in the middle routes into
#     congestion failure (GRT-0116) — the channels matter more than the density.
#
#   ERROR_ON_DISCONNECTED_PINS off.  The checker reports 20 critical disconnected
#     pins. Querying the ODB directly shows *zero* unconnected inputs: all 680
#     are the SRAM macros' unused second-port `dout1` outputs, which the Rocket
#     arrays are single-ported and never read. Verified before disabling, not
#     disabled to make a message go away.
#
#   Low PL_TARGET_DENSITY_PCT.  The die is sized by SRAM, not by logic — 0.68 mm²
#     of standard cells in a 17.6 mm² die — so the placer must be told to spread
#     out rather than pack into one corner far from the macros it feeds.
#
# Disk: a full run is ~4 GB and the flow does not clean up after itself. Check
# free space before starting; a mid-run ENOSPC loses the placement and routing.
#
# Usage: tools/run-rocket-flow.sh [run-tag] [pdk-root]      (hours, not minutes)
set -euo pipefail
cd "$(dirname "$0")/.."
RUN="${1:-rtl2gds}"
PDK_ROOT="${2:-/tmp/pdk2}"
D=flow/rocket-tiny

command -v librelane-shell >/dev/null || {
  echo "librelane-shell not found — tools/install-toolchain.sh --only flow" >&2; exit 1; }
[ -d "$D/src" ] && [ -d "$D/macros" ] || {
  echo "no staged RTL — run tools/build-rocket.sh first" >&2; exit 1; }

free_gb=$(df -BG --output=avail . | tail -1 | tr -dc 0-9)
[ "$free_gb" -ge 6 ] || {
  echo "only ${free_gb}G free; a run needs ~4G and dies badly on ENOSPC" >&2; exit 1; }

rm -rf "$D/runs/$RUN"
echo "== hardening $(ls $D/src | wc -l) source files + $(ls $D/macros/*.gds | wc -l) SRAM macro"
librelane-shell librelane --pdk-root "$PDK_ROOT" --pdk sky130A \
  --run-tag "$RUN" "$D/config.json"

exec python3 tools/flowreport.py "$D/runs/$RUN"
