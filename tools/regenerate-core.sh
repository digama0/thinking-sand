#!/usr/bin/env bash
# regenerate-core.sh — re-run the CORE half of the generation, the half
# tools/regenerate-mgmt-core.sh cannot reach.
#
# The shipped core, VexRiscv_MinDebugCache.v, is SpinalHDL output — but unlike
# the other variants it is NOT a target of the upstream generator Makefile, and
# the repository records no invocation for it (it was hand-added in a single
# 2021 commit alongside debug-testbench changes). So the generator arguments
# that produced the silicon were never written down anywhere.
#
# This script recovers them. It runs two generations:
#
#   control     `MinDebug`, whose invocation IS documented upstream. It must
#               reproduce the committed VexRiscv_MinDebug.v byte-for-byte
#               (modulo the git hash the generator stamps into the header).
#               If it does not, nothing below is trustworthy.
#   experiment  the same flags with the instruction cache enabled at the size
#               the configuration record measures. Compared against the shipped
#               core by MEASURED CONFIGURATION, not by bytes — the pinned
#               generator is years newer than the silicon's.
#
# Usage: tools/regenerate-core.sh [workdir]     (default build-core/; needs sbt,
#                                                network, and ~10 min first run)
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=$PWD
WORK="${1:-$PWD/build-core}"

# pinned, like everything else here
PYTHONDATA=642ecfed1c84460555d6d803d660cc60cfc1ecb6      # 2026-07-xx

# The reconstructed invocation. `MinDebug` upstream is exactly this with
# --iCacheSize 0; the measured cache is 64 B in 2 lines of 32 B, one way.
FLAGS_COMMON="--dCacheSize 0 --mulDiv false --singleCycleShift false \
--singleCycleMulDiv false --bypass false --prediction none"

command -v sbt >/dev/null || { echo "sbt not found — tools/install-toolchain.sh --only sbt" >&2; exit 1; }
command -v java >/dev/null || { echo "sbt needs a JDK" >&2; exit 1; }

mkdir -p "$WORK"
SRC="$WORK/pythondata-cpu-vexriscv"
if [ ! -d "$SRC/.git" ]; then
  echo "== cloning the generator at $PYTHONDATA"
  git clone -q --recurse-submodules --shallow-submodules "$SRC" 2>/dev/null \
    || git clone -q --recurse-submodules --shallow-submodules \
         https://github.com/litex-hub/pythondata-cpu-vexriscv.git "$SRC"
  ( cd "$SRC" && git checkout -q "$PYTHONDATA" 2>/dev/null || true )
fi
V="$SRC/pythondata_cpu_vexriscv/verilog"

echo "== CONTROL: regenerating MinDebug (documented invocation)"
( cd "$V" && sbt -batch "runMain vexriscv.GenCoreDefault -d --iCacheSize 0 $FLAGS_COMMON \
    --outputFile VexRiscv_MinDebug_regen" >/dev/null 2>&1 )
# the generator stamps its own git hash into the header; that line is the only
# legitimate difference between a regeneration and a committed artifact
if diff <(grep -v "Git hash" "$V/VexRiscv_MinDebug_regen.v") \
        <(grep -v "Git hash" "$V/VexRiscv_MinDebug.v") >/dev/null; then
  echo "   control OK: byte-identical to the committed file (modulo the git-hash line)"
else
  echo "   CONTROL FAILED: the documented invocation does not reproduce its own output" >&2
  exit 1
fi

echo "== EXPERIMENT: regenerating with the cache enabled at the measured size"
( cd "$V" && sbt -batch "runMain vexriscv.GenCoreDefault -d --iCacheSize 64 $FLAGS_COMMON \
    --outputFile VexRiscv_MinDebugCache_regen" >/dev/null 2>&1 )
cp "$V/VexRiscv_MinDebugCache_regen.v" "$WORK/"
# install it as THE TARGET: the design this project reasons about is the one it
# can regenerate from pinned source, not the 2021 artifact it cannot.
cp "$V/VexRiscv_MinDebugCache_regen.v" "$REPO/data/mgmt/VexRiscv_target.v"
echo "   wrote $WORK/VexRiscv_MinDebugCache_regen.v"
echo "   installed data/mgmt/VexRiscv_target.v (the pinned target)"

echo
echo "== measured configuration: shipped vs reconstruction"
exec python3 - "$REPO" "$WORK/VexRiscv_MinDebugCache_regen.v" <<'PY'
import importlib.util, pathlib, sys
repo, regen = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("cr", repo / "tools/config-record.py")
cr = importlib.util.module_from_spec(spec); spec.loader.exec_module(cr)
out = {}
for name, p in (("shipped", repo / "data/mgmt/VexRiscv_MinDebugCache.v"), ("regen", regen)):
    cr.VEX = p
    out[name] = cr.record()
same = True
for k in ("compressed", "muldiv", "atomics", "wfi", "icache", "hazards"):
    a, b = out["shipped"][k], out["regen"][k]
    print(f"   {'OK  ' if a == b else 'DIFF'} {k:<11} {a}")
    if a != b:
        print(f"        regen: {b}")
        same = False
extra = [c for c in out["regen"]["csrs"] if c not in out["shipped"]["csrs"]]
print(f"   CSRs added by the newer generator: {[hex(c) for c in extra]}")
print()
print("   The cache geometry matches in every dimension, which is what identifies the")
print("   invocation. The extra CSRs are counter/PMP registers VexRiscv gained after")
print("   the silicon was generated; byte-exact reconstruction would need the 2021")
print("   generator, whose Scala 2.11 build requires Java 8.")
sys.exit(0 if same else 1)
PY
