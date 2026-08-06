#!/usr/bin/env bash
# build-rocket-hammer.sh — set up and run the upstream (Hammer) physical flow.
#
# This is the flow the book's physical artifacts come from: Chipyard's own
# sky130 + OpenROAD path, driven by Hammer, with the SRAM22 macros. The
# front half (RTL generation) is tools/build-rocket.sh; this script covers
# hammer installation, the compatibility patches, the macro collateral, and
# the syn/par invocations.
#
# Hammer 1.2.0 does not run as shipped against current components — ten
# interface breakages, all catalogued in flow/rocket-hammer/NOTES.md and the
# findings appendix. The fixes live in one reviewable patch file:
#   flow/rocket-hammer/hammer-1.2.0-compat.patch
# applied here against a fresh pip install, so the venv is reproducible.
#
# Usage:
#   tools/build-rocket-hammer.sh setup     # venv + patch + macros
#   tools/build-rocket-hammer.sh syn       # synthesis
#   tools/build-rocket-hammer.sh par       # place-and-route through GDS
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=$(pwd)
ROOT="${TS_TOOLS:-/project/thinking-sand-tools}"
CHIPYARD="$ROOT/chipyard"
VENV="$ROOT/hammer-venv"
SRAMS="$ROOT/sram22_sky130_macros"
SRAM22_SHA=75cbe961e18ee00d5a6c73fa455505f0bcdf4c05   # master 2026-05-06
PDK=$(ls -d "$ROOT"/pdks/pdk2/ciel/sky130/versions/*/sky130A /tmp/pdk2/ciel/sky130/versions/*/sky130A 2>/dev/null | head -1)

setup() {
  # hammer, patched
  [ -d "$VENV" ] || python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q hammer-vlsi==1.2.0
  ( cd "$VENV"/lib/python3*/site-packages && \
    patch -p1 --forward -r - < "$REPO/flow/rocket-hammer/hammer-1.2.0-compat.patch" ) || true

  # the SRAM22 macro collateral, pinned; gunzip the GDS the plugin expects raw
  if [ ! -d "$SRAMS" ]; then
    git clone -q https://github.com/rahulk29/sram22_sky130_macros "$SRAMS"
  fi
  git -C "$SRAMS" checkout -q "$SRAM22_SHA"
  ( cd "$SRAMS" && for f in */*.gds.gz; do [ -f "${f%.gz}" ] || gunzip -k "$f"; done )

  # the tech config with real paths (the example ships /path/to placeholders)
  [ -n "$PDK" ] || { echo "no sky130A PDK found" >&2; exit 1; }
  sed -e "s|\"/path/to/sky130A\"|\"$PDK\"|" \
      -e "s|\"/path/to/sram22_sky130_macros\"|\"$SRAMS\"|" \
      -e "/sky130_nda/d" "$CHIPYARD/vlsi/example-sky130.yml" > "$CHIPYARD/vlsi/ts-sky130.yml"
  printf 'vlsi.core.max_threads: 12\n' > "$CHIPYARD/vlsi/ts-env.yml"
  # timing-driven GP is documented-optional and OOMs a contended 32 GB machine
  printf 'par.openroad:\n  global_placement.timing_driven: false\n  global_placement.routability_driven: true\n' \
    > "$CHIPYARD/vlsi/ts-lite.yml"
  echo "setup complete"
}

run() {
  export JAVA_HOME="${JAVA_HOME_11:-/usr/lib/jvm/java-11-openjdk-amd64}"
  export PATH="$VENV/bin:$JAVA_HOME/bin:$ROOT/firtool-1.75.0/bin:$ROOT/dtc:$PATH"
  export XDG_CONFIG_HOME="$ROOT/xdg"
  make -C "$CHIPYARD/vlsi" tutorial=sky130-openroad \
    TECH_CONF=ts-sky130.yml ENV_YML="$CHIPYARD/vlsi/ts-env.yml" \
    DESIGN_CONFS="example-designs/sky130-openroad.yml ts-lite.yml" "$1"
}

case "${1:-}" in
  setup) setup ;;
  syn|par) run "$1" ;;
  *) echo "usage: $0 {setup|syn|par}" >&2; exit 2 ;;
esac
