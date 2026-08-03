#!/usr/bin/env bash
# sta-rerun.sh — re-run the shipped signoff timing analysis and record the result.
#
# This is the F1 experiment. The shipped signoff.rpt records three SLOW corners
# failing hold, but the per-path evidence for those corners was never committed;
# the reports that WERE committed are the nominal corner. So the question is
# simply: fed the committed inputs, does OpenSTA say what signoff.rpt says?
#
# Inputs, all pinned, nothing improvised:
#   netlist  data/caravel/gl_caravel_core.v  (minus 3 physical-cell instance
#            arrays OpenSTA's Verilog reader rejects — decap/fill only, which
#            L3's W4 check proved carry no signal pins, so timing is unaffected)
#   sdc      data/caravel/caravel_core.sdc   (the caravel_core run's OWN sdc)
#   spef     data/caravel/spef/caravel_core.nom.spef  (the RCX extraction)
#   liberty  the macro libs config.tcl's EXTRA_LIBS names, plus sky130_fd_sc_hd
#            from the open_pdks build the chip was signed off with (12df12e2,
#            fetched by volare — see src/data-provenance.md)
#
# Needs: tools/install-toolchain.sh --only sta, and the PDK:
#   pip install volare && volare enable --pdk sky130 --pdk-root <dir> 12df12e2...
#
# Usage: tools/sta-rerun.sh [pdk-root]        (default /tmp/pdk; ~5 min)
set -euo pipefail
cd "$(dirname "$0")/.."
PDK="${1:-/tmp/pdk}"
OUT=build-sta
NET=data/caravel/gl_caravel_core.v
STANET=data/caravel/gl_caravel_core.sta.v

command -v sta >/dev/null || { echo "OpenSTA not found — tools/install-toolchain.sh --only sta" >&2; exit 1; }
[ -d "$PDK/sky130A/libs.ref/sky130_fd_sc_hd/lib" ] || { echo "sky130A not at $PDK — see header" >&2; exit 1; }
for f in "$NET" data/caravel/caravel_core.sdc data/caravel/spef/caravel_core.nom.spef \
         data/caravel/lib/housekeeping.lib data/caravel/lib/RAM128.nom.lib; do
  [ -s "$f" ] || { echo "missing $f — run tools/fetch-data.sh sta" >&2; exit 1; }
done
mkdir -p "$OUT"

# OpenSTA's Verilog reader rejects instance ARRAYS (`cell name[65364:0] (...)`).
# The only three in this netlist are decap/fill — physical cells that W4 proved
# have no signal pins, so dropping them cannot change a timing path.
if [ ! -s "$STANET" ] || [ "$NET" -nt "$STANET" ]; then
  echo "== preparing netlist (dropping physical-cell instance arrays)"
  python3 - "$NET" "$STANET" <<'PY'
import re, sys, pathlib
src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
txt = src.read_text()
pat = re.compile(r"^ *(sky130_ef_sc_hd__(?:decap_12|fill_4|fill_8)) +\w+\[\d+:\d+\] \([^;]*?\);\s*$",
                 re.M | re.S)
dropped = pat.findall(txt)
assert all(("decap" in d or "fill" in d) for d in dropped), f"non-physical array: {dropped}"
dst.write_text(pat.sub("", txt))
print(f"   dropped {len(dropped)} arrays: {', '.join(dropped)}")
PY
fi

# Each corner takes ~2 min; keep completed logs so re-summarising is free.
# FORCE=1 tools/sta-rerun.sh re-runs them.
for corner in tt_025C_1v80 ss_100C_1v60; do
  if [ -s "$OUT/sta-$corner.log" ] && [ "${FORCE:-0}" != 1 ] \
     && grep -q "WORST SLACK" "$OUT/sta-$corner.log"; then
    echo "== STA at $corner (cached; FORCE=1 to re-run)"
    continue
  fi
  echo "== STA at $corner"
  STA_CORNER=$corner STA_PDK=$PDK sta -no_init -exit tools/sta-rerun.tcl \
    > "$OUT/sta-$corner.log" 2>&1 || true
done

# --- summarise: the numbers, and how much of the SPEF actually attached -------
{
  echo "# STA rerun — F1"
  echo "pdk           $PDK"
  echo "spef          data/caravel/spef/caravel_core.nom.spef"
  for corner in tt_025C_1v80 ss_100C_1v60; do
    log="$OUT/sta-$corner.log"
    echo "corner        $corner"
    echo "  hold_worst  $(grep -oP '(?<=worst slack min )\S+' "$log" | tail -1)"
    echo "  setup_worst $(grep -oP '(?<=worst slack max )\S+' "$log" | tail -1)"
    echo "  wns         $(grep -oP '(?<=^wns max )\S+' "$log" | tail -1)"
    echo "  hold_viol   $(grep -c 'Path Type: min' "$log" || true)"
    echo "  spef_nets_missing $(grep -oE 'net [A-Za-z_0-9]+ not found' "$log" | sort -u | wc -l)"
  done
  echo "spef_d_nets   $(grep -c '^\*D_NET' data/caravel/spef/caravel_core.nom.spef)"
  echo "committed_reference_hold  $(grep -A3 'report_worst_slack -min' data/caravel/sta.worst_slack.rpt | grep -oP '(?<=worst slack )\S+')"
  echo "committed_reference_setup $(grep -A3 'report_worst_slack -max' data/caravel/sta.worst_slack.rpt | grep -oP '(?<=worst slack )\S+')"
} > "$OUT/summary.txt"

cat "$OUT/summary.txt"
echo
echo "wrote $OUT/summary.txt — tools/check-l2.py f1-match reads it"
