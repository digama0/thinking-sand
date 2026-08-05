#!/usr/bin/env bash
# build-rocket.sh — regenerate the Rocket SoC RTL that flow/rocket-tiny hardens.
#
# This is the front half of the replacement chain described in
# src/platform-assessment.md: Chisel -> FIRRTL -> (CIRCT/firtool) -> SystemVerilog.
# The back half is tools/run-rocket-flow.sh, which takes the output to GDS.
#
# Everything is pinned. Chipyard is a shallow clone at a fixed SHA with only the
# submodules the build actually reaches; firtool is a fixed CIRCT release, taken
# as a release binary rather than built, because CIRCT is an LLVM tree.
#
# Three environment facts that are not obvious and cost time to rediscover:
#
#   * Java 11.  Chipyard's sbt line does not run on Java 21 — sbt's parser class
#     fails to load. The JDK is selected explicitly rather than inherited.
#   * XDG_CONFIG_HOME.  sbt's jgit writes ~/.config/jgit/config.lock; if $HOME is
#     read-only the build dies late, after the long Scala compile. Point it
#     somewhere writable up front.
#   * sims/firesim.  A plain Rocket build still needs it. Chipyard's build
#     aggregates every generator in the tree, so FireSim's `midas` is on the
#     compile path even when no FireSim target is requested.
#
# Usage: build-rocket.sh [CONFIG]     (default TinyRocketConfig)

set -euo pipefail

CONFIG="${1:-TinyRocketConfig}"
ROOT="${TS_TOOLS:-/project/thinking-sand-tools}"
CHIPYARD="$ROOT/chipyard"
DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/flow/rocket-tiny"

CHIPYARD_SHA=e27c6561c0066c1f60bf4eb4885a38391c850ac0   # 2026-07-27
FIRTOOL_VER=1.75.0
FIRTOOL_SHA=547a5181a47f805cbf5b7f666bff381bf1068cd3449b24b628267205ca56a0e7

# the submodules this build reaches; the full set is ~40 and most are unused
SUBMODULES=(
  generators/rocket-chip generators/rocket-chip-blocks
  generators/rocket-chip-inclusive-cache generators/testchipip
  generators/diplomacy generators/hardfloat generators/constellation
  tools/cde tools/dsptools tools/rocket-dsp-utils tools/firrtl2 tools/fixedpoint
  sims/firesim
)

say() { printf '\n=== %s\n' "$*"; }

# --- chipyard, at the pin -----------------------------------------------------
if [ ! -d "$CHIPYARD/.git" ]; then
  say "cloning chipyard @ ${CHIPYARD_SHA:0:12}"
  git clone --filter=blob:none https://github.com/ucb-bar/chipyard "$CHIPYARD"
  git -C "$CHIPYARD" checkout "$CHIPYARD_SHA"
fi
[ "$(git -C "$CHIPYARD" rev-parse HEAD)" = "$CHIPYARD_SHA" ] ||
  { echo "chipyard is not at the pinned SHA — refusing to build" >&2; exit 1; }

say "submodules"
# --force: a shallow clone can register a submodule without populating it, and
# a plain `update --init` then silently leaves the directory empty.
git -C "$CHIPYARD" submodule update --init --force "${SUBMODULES[@]}"

# --- firtool: the Chisel -> SystemVerilog compiler ----------------------------
FIRTOOL_DIR="$ROOT/firtool-$FIRTOOL_VER"
if [ ! -x "$FIRTOOL_DIR/bin/firtool" ]; then
  say "fetching firtool $FIRTOOL_VER"
  tmp=$(mktemp -d)
  curl -fL --progress-bar -o "$tmp/circt.tgz" \
    "https://github.com/llvm/circt/releases/download/firtool-$FIRTOOL_VER/circt-full-shared-linux-x64.tar.gz"
  tar -xzf "$tmp/circt.tgz" -C "$ROOT" && rm -rf "$tmp"
fi
echo "$FIRTOOL_SHA  $FIRTOOL_DIR/bin/firtool" | sha256sum -c - >/dev/null ||
  { echo "firtool checksum mismatch" >&2; exit 1; }

# --- dtc: chipyard emits a device tree and then compiles it -------------------
if [ ! -x "$ROOT/dtc/dtc" ]; then
  say "building dtc"
  git clone --depth 1 https://github.com/dgibson/dtc "$ROOT/dtc"
  make -C "$ROOT/dtc" -j"$(nproc)" NO_PYTHON=1 NO_YAML=1 dtc
fi

# --- the generate step --------------------------------------------------------
JAVA_HOME="${JAVA_HOME_11:-/usr/lib/jvm/java-11-openjdk-amd64}"
[ -x "$JAVA_HOME/bin/java" ] ||
  { echo "need a Java 11 JDK; set JAVA_HOME_11" >&2; exit 1; }
export JAVA_HOME
export XDG_CONFIG_HOME="$ROOT/xdg"          # jgit writes here, not into $HOME
mkdir -p "$XDG_CONFIG_HOME"
export PATH="$JAVA_HOME/bin:$FIRTOOL_DIR/bin:$ROOT/dtc:$PATH"

say "elaborating $CONFIG (Chisel -> FIRRTL -> SystemVerilog; tens of minutes)"
make -C "$CHIPYARD/sims/verilator" verilog \
  CONFIG="$CONFIG" JAVA_HEAP_SIZE=5G FIRTOOL_BIN="$(command -v firtool)"

GEN="$CHIPYARD/sims/verilator/generated-src/chipyard.harness.TestHarness.$CONFIG"

# --- stage the hardening inputs ----------------------------------------------
# The generated tree carries simulation-only collateral alongside the design;
# only the SystemVerilog is wanted, and the memory arrays are replaced wholesale
# by srams/rocket_srams.v (see its header for why).
say "staging into $DEST/src"
rm -rf "$DEST/src"; mkdir -p "$DEST/src"
cp "$GEN"/*.sv "$DEST/src/" 2>/dev/null || true
cp "$GEN"/*.v  "$DEST/src/" 2>/dev/null || true
# these are behavioural memory models; srams/ supplies the macro-backed versions
rm -f "$DEST/src"/*_ext.sv "$DEST/src"/*_ext.v

# the macro views come from the PDK itself, so there is nothing to pin separately
PDK_ROOT="${PDK_ROOT:-/tmp/pdk2}"
SRAM_SRC=$(find "$PDK_ROOT" -type d -name sky130_sram_macros -path "*sky130A*" | head -1)
[ -n "$SRAM_SRC" ] ||
  { echo "no sky130_sram_macros under $PDK_ROOT — is the PDK installed?" >&2; exit 1; }
mkdir -p "$DEST/macros"
M=sky130_sram_1kbyte_1rw1r_32x256_8
cp "$SRAM_SRC/lef/$M.lef" "$SRAM_SRC/gds/$M.gds" "$DEST/macros/"
cp "$SRAM_SRC/lib/${M}_TT_1p8V_25C.lib" "$DEST/macros/"

say "done"
printf '  RTL      %s files, %s\n' \
  "$(ls "$DEST/src" | wc -l)" "$(du -sh "$DEST/src" | cut -f1)"
printf '  memories %s (macro-backed, srams/rocket_srams.v)\n' \
  "$(grep -c '^module' "$DEST/srams/rocket_srams.v")"
printf '\n  next: tools/run-rocket-flow.sh\n'
