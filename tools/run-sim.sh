#!/usr/bin/env bash
# run-sim.sh — execute the SHIPPED core on a REAL firmware image and check the
# L5/04 Wishbone guarantee clauses on the trace.
#
# This is the project's first execution of the design. The testbench
# (tools/sim/tb_core.v) wires the core to a two-region memory — flash at the
# XIP base the reset vector targets, RAM where the linker puts data and stack —
# and asserts the bus clauses continuously. See that file for the clause list.
#
# The monitor is validated by construction: `--negative` re-runs with a memory
# latency past the clause's own bound, and the run is only trusted if that
# FAILS. A monitor that cannot fail proves nothing.
#
# Usage: tools/run-sim.sh [--negative]     (needs iverilog + a built image)
set -euo pipefail
cd "$(dirname "$0")/.."
NEG=0; [ "${1:-}" = "--negative" ] && NEG=1
OUT=build-sim
CORE=data/mgmt/VexRiscv_MinDebugCache.v
IMG=build-fw/fw.bin

command -v iverilog >/dev/null || {
  echo "iverilog not found — tools/install-toolchain.sh --only cad" >&2; exit 1; }
[ -s "$IMG" ] || { echo "no image — run tools/build-firmware.sh first" >&2; exit 1; }
[ -s "$CORE" ] || { echo "missing $CORE — tools/fetch-data.sh mgmt" >&2; exit 1; }

mkdir -p "$OUT"
python3 - "$IMG" "$OUT/fw.hex" <<'PY'
import pathlib, struct, sys
d = pathlib.Path(sys.argv[1]).read_bytes()
d += b"\x00" * ((-len(d)) % 4)
pathlib.Path(sys.argv[2]).write_text(
    "\n".join("%08x" % struct.unpack("<I", d[i:i+4])[0] for i in range(0, len(d), 4)) + "\n")
PY

if [ "$NEG" = 1 ]; then
  echo "== NEGATIVE control: memory latency past the G3 bound (violations EXPECTED)"
  iverilog -g2012 -P tb_core.MEM_LAT=100 -o "$OUT/sim.vvp" tools/sim/tb_core.v "$CORE"
else
  echo "== running the shipped core on $IMG"
  iverilog -g2012 -o "$OUT/sim.vvp" tools/sim/tb_core.v "$CORE"
fi
( cd "$OUT" && vvp sim.vvp ) 2>&1 | grep -vE "^WARNING.*readmemh" | tee "$OUT/sim.log" | grep -E "VIOLATION|SUMMARY" | head -5
echo
grep -q "violations=0" "$OUT/sim.log" && V=clean || V=violations
if [ "$NEG" = 1 ]; then
  [ "$V" = violations ] && { echo "negative control OK: the monitor fires when the clause is broken"; exit 0; }
  echo "NEGATIVE CONTROL FAILED: the monitor stayed silent — it proves nothing" >&2; exit 1
fi
[ "$V" = clean ] && echo "no bus-guarantee violation in the run" || { echo "VIOLATIONS — see $OUT/sim.log" >&2; exit 1; }
