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

hello() {
  local d="$REPO/flow/rocket-sram22/sim"
  ( cd "$d" && clang --target=riscv32-unknown-elf -march=rv32imac_zicsr -mabi=ilp32 \
      -O2 -nostdlib -ffreestanding -fuse-ld=lld -T link.ld crt0.S hello.c -o hello.riscv )
  run "$d/hello.riscv"
}

case "${1:-}" in
  build) build ;;
  run) shift; run "$1" ;;
  hello) hello ;;
  *) echo "usage: $0 {build|run <elf>|hello}" >&2; exit 2 ;;
esac
