#!/usr/bin/env bash
# Re-run the SHIPPED SoC's own generation step from public inputs, so the
# extracted facts can be checked against an independently produced artifact
# (tools/replicate.py). See src/findings.md, "Replicating the generator".
#
# This does NOT reproduce data/mgmt/mgmt_core.v byte-for-byte, and cannot:
# the shipped file records LiteX revision 470fc6f, which exists in no
# reachable repository, and its header format was retired from LiteX before
# 2022-01 although the file was committed 2022-10-14 (the build environment
# was stale — the recorded migen 9a0be7a is from 2021-11-12). The versions
# below are the earliest-reachable approximation: LiteX/LiteSPI at the file's
# commit date. What IS reproduced is every fact the checkers extract.
#
# Usage: tools/regenerate-mgmt-core.sh [workdir]   (default: ./build-regen)
set -euo pipefail
cd "$(dirname "$0")/.."
WORK="${1:-$PWD/build-regen}"

# pinned as everywhere else in this repo: SHAs, never branches
LITEX=b990b90c0e733def030597ce1fba732c809ea36a          # 2022-10-14
LITESPI=69d13319cd389d9b88dfad9d5dbd19c9c95438b2        # 2022-10-14
MIGEN=639e66f4f453438e83d86dc13491b9403bbd8ec6          # 2022-09-02
VEXDATA=e75700dff2ab9662f3e26dd89ab59a5f6da65687        # 2022-08-29
PICOLIBC=228a2adfe0402a3c2691d62797085263997e82ef       # 2022-10-12
COMPILERRT=fcb03245613ccf3079cc833a701f13d0beaae09d     # 2022-10-12

[ -s data/mgmt/litex/caravel.py ] || { echo "run tools/fetch-data.sh checks first" >&2; exit 1; }

mkdir -p "$WORK"
if [ ! -x "$WORK/venv/bin/python" ]; then
  echo "== creating venv"
  python3 -m venv "$WORK/venv"
  "$WORK/venv/bin/pip" -q install \
    "git+https://github.com/m-labs/migen.git@$MIGEN" \
    "git+https://github.com/enjoy-digital/litex.git@$LITEX" \
    "git+https://github.com/litex-hub/litespi.git@$LITESPI" \
    "git+https://github.com/litex-hub/pythondata-cpu-vexriscv.git@$VEXDATA" \
    "git+https://github.com/litex-hub/pythondata-software-picolibc.git@$PICOLIBC" \
    "git+https://github.com/litex-hub/pythondata-software-compiler_rt.git@$COMPILERRT"
fi

echo "== generating"
rm -rf "$WORK/src"; mkdir -p "$WORK/src"
cp data/mgmt/litex/*.py data/mgmt/litex/debug_reset.v "$WORK/src/"
# `SpiFlash` was removed from litex.soc.cores.spi_flash; caravel.py imports it
# but never uses it (the flash goes through LiteSPI). Guard the dead import.
python3 - "$WORK/src/caravel.py" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text()
old = "from litex.soc.cores.spi_flash import SpiFlash"
if old in s:
    p.write_text(s.replace(old, "try:\n    " + old + "\nexcept ImportError:\n    SpiFlash = None"))
PY
( cd "$WORK/src" && "$WORK/venv/bin/python" caravel.py >/dev/null 2>&1 \
                && "$WORK/venv/bin/python" modify_verilog.py )

OUT="$WORK/src/build/caravel_platform/gateware/mgmt_core_modified.v"
echo "== regenerated: $OUT ($(wc -l < "$OUT") lines)"
echo "== checking the extracted facts against it"
exec python3 tools/replicate.py "$OUT"
