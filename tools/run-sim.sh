#!/usr/bin/env bash
# run-sim.sh — build and drive the Verilator simulation of the design.
#
# The functional half of the flow: Chipyard's own TestHarness (SimTSI loads an
# ELF over the serial-TileLink port — L7/03's load path — and watches the
# riscv-tests tohost protocol; the UART adapter echoes TX to stdout).
#
# Usage:
#   tools/run-sim.sh build              # build the simulator binary (~10 min)
#   tools/run-sim.sh run <prog.riscv>   # run an ELF; exit 0 = tohost pass
#   tools/run-sim.sh hello              # build + run the smoke test program
#
# Requirements (see NOTES): Spike installed at $ROOT/riscv (for libriscv —
# tools/../flow/rocket-sram22/NOTES.md records the v1.1.0 build recipe incl.
# the -include cstdint fix and the manual libriscv.a install); the radiance
# generator's chipyard.mk hook disabled (its GPU submodules are not checked
# out and TinyRocket does not use them).
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=$(pwd)
ROOT="${TS_TOOLS:-/project/thinking-sand-tools}"
CHIPYARD="$ROOT/chipyard"
SIMDIR="$CHIPYARD/sims/verilator"
SIM="$SIMDIR/simulator-chipyard.harness-TinyRocketConfig"
L="$ROOT/librelane-root"

env_run() {
  ulimit -v 16777216
  export JAVA_HOME="${JAVA_HOME_11:-/usr/lib/jvm/java-11-openjdk-amd64}"
  export RISCV="$ROOT/riscv"
  export PATH="$JAVA_HOME/bin:$ROOT/firtool-1.75.0/bin:$ROOT/dtc:$PATH"
  bwrap --dev-bind / / --bind "$L/nix" /nix -- "$L/entrypoint" "$@"
}

build() {
  [ -f "$CHIPYARD/generators/radiance/chipyard.mk" ] && \
    mv "$CHIPYARD/generators/radiance/chipyard.mk" "$CHIPYARD/generators/radiance/chipyard.mk.disabled"
  env_run make -C "$SIMDIR" CONFIG=TinyRocketConfig VERILATOR_THREADS=1 -j6
}

run() {
  [ -x "$SIM" ] || { echo "simulator missing — run: $0 build" >&2; exit 1; }
  env_run "$SIM" "$1"
}

cc() {  # cc <src.c> <out.riscv> — build a bare-metal RV32IMAC image with stock clang
  local d="$REPO/flow/rocket-sram22/sim"
  ( cd "$d" && clang --target=riscv32-unknown-elf -march=rv32imac_zicsr -mabi=ilp32 \
      -O2 -nostdlib -ffreestanding -fuse-ld=lld -T link.ld crt0.S "$1" -o "$2" )
}

hello() {
  cc hello.c hello.riscv
  run "$REPO/flow/rocket-sram22/sim/hello.riscv"
}

# cosim — the L5 trace-oracle: build CospikeTinyRocketConfig (trace port +
# DebugROB + spike attached) and run a pure-compute image, every committed
# instruction checked against the golden ISA model. The cospike C++ needs the
# RV32 portability patch (flow/rocket-sram22/cospike-rv32.patch) applied to the
# testchipip submodule first; see NOTES. ELF *before* the +verilator plusarg so
# htif takes the ELF as target while Verilator parses the reset-init flag.
COSIM_SIM="$SIMDIR/simulator-chipyard.harness-CospikeTinyRocketConfig"
cosim() {
  [ -x "$COSIM_SIM" ] || { echo "cosim simulator missing — run: $0 cosim-build" >&2; exit 1; }
  local elf="${1:-$REPO/flow/rocket-sram22/sim/cotest.riscv}"
  [ -f "$elf" ] || cc cotest.c cotest.riscv
  env_run "$COSIM_SIM" "$elf" +verilator+rand+reset+0
}
cosim_build() { env_run make -C "$SIMDIR" CONFIG=CospikeTinyRocketConfig VERILATOR_THREADS=1 -j6; }

case "${1:-}" in
  build) build ;;
  run) shift; run "$1" ;;
  hello) hello ;;
  cosim-build) cosim_build ;;
  cosim) shift; cosim "${1:-}" ;;
  *) echo "usage: $0 {build|run <elf>|hello|cosim-build|cosim [elf]}" >&2; exit 2 ;;
esac
