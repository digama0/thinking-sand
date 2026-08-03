#!/usr/bin/env python3
"""replicate.py — re-run the SoC extractors against an INDEPENDENTLY REGENERATED
`mgmt_core.v` and check that the book's conclusions are properties of the design
rather than of one build.

The shipped `mgmt_core.v` is LiteX output. Its provenance is recoverable (the
repo carries `litex/caravel.py`, `litex/Makefile` and `requirements.txt`), so the
generation step can be re-run from public inputs. It does NOT reproduce
byte-for-byte — see `replicate-notes` below and src/findings.md — but that is the
uninteresting kind of difference. What matters is whether the *facts the
checkers extract* come out the same. This tool answers that.

Give it the path to a regenerated mgmt_core.v:

    tools/replicate.py <path-to-regenerated-mgmt_core.v>

It re-derives, against that file alone: the seven-window bus decode, the CSR
bank count, the interconnect timeout, the external-interrupt array wiring, the
LiteSPI master path (flash writability), and the SoC construct census — and
diffs each against the shipped-derived answer.
"""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHIPPED = ROOT / "data/mgmt/mgmt_core.v"


def load(name):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), Path(__file__).resolve().parent / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def facts(path):
    """Every SoC-level fact the book rests on, derived from one file."""
    mm, im = load("memmap"), load("irqmap")
    mm.MGMT_CORE = im.MGMT_CORE = path
    txt = path.read_text(errors="replace")
    f = {}
    f["windows"] = mm.rtl_windows()
    f["csr_banks"] = len(mm.rtl_csr_banks())
    f["timeout"] = int(re.search(r"reg \[19:0\] count = 20'd(\d+);", txt).group(1))
    f["timeout_reads"] = "shared_dat_r = 32'd4294967295;" in txt
    f["irq_bits"] = {i: s for i, s in im.array_bits().items()}
    f["irq_sync_2ff"] = im.sync_chains()
    f["event_blocks"] = sorted(im.event_blocks())
    # structure-keyed (see the sync_chains note): CSR-written bytes reach the
    # flash TX FIFO, and the crossbar grants the master its own chip select
    f["flash_master_path"] = bool(
        re.search(r"assign \w*master_tx_fifo_sink(?:_sink)?_payload_data = \w*master_rxtx_r;", txt)
        and re.search(r"\w*crossbar_cs = \w*master_cs;", txt))
    f["write_protect"] = bool(re.search(r"wrprot|write_protect|flash_lock", txt, re.I))
    f["reset_vector"] = re.search(r"reg \[31:0\] mgmtsoc_vexriscv = 32'd(\d+);", txt).group(1)
    f["sw_timer_irq_tied_0"] = bool(
        re.search(r"\.softwareInterrupt\(1'd0\)", txt)
        and re.search(r"\.timerInterrupt\(1'd0\)", txt))
    c4 = load("check-l4")
    cen = c4.census(path)
    f["census"] = {k: cen[k] for k in
                   ("# delays", "casex", "initial", "x literals", "force/release/deassign")}
    # the same build emits the firmware's CSR header; when a regenerated one sits
    # beside the regenerated RTL, compare the bank naming too
    hdr = (path.parent.parent / "software/include/generated/csr.h"
           if path.name.startswith("mgmt_core") and (
               path.parent.parent / "software/include/generated/csr.h").is_file()
           else mm.CSR_H)
    f["csr_bank_names"] = mm.header_bank_names(hdr)
    return f


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    regen = Path(sys.argv[1])
    a, b = facts(SHIPPED), facts(regen)
    print(f"# Replication check\n\n  shipped     {SHIPPED}")
    print(f"  regenerated {regen}\n")
    same, diff = [], []
    for k in a:
        (same if a[k] == b[k] else diff).append(k)
    for k in same:
        v = a[k]
        s = str(v)
        print(f"  [SAME] {k:<20} {s if len(s) < 90 else s[:87] + '...'}")
    for k in diff:
        print(f"  [DIFF] {k:<20}\n         shipped     {a[k]}\n         regenerated {b[k]}")
    print(f"\n{len(same)} facts reproduced, {len(diff)} differ")
    return 1 if diff else 0


if __name__ == "__main__":
    sys.exit(main())
