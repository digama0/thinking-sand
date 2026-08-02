#!/usr/bin/env python3
"""fwanchors.py — the interrupt-facing firmware paths, as spec anchors.

L6/01's authoring methodology needs evidence about intended behaviour that is
independent of the RTL; the shipped firmware is the working-software corpus.
This tool extracts the interrupt-facing facts from the pinned firmware tree
and checks them for consistency with the measured core semantics:

  crt0_vex.S    the startup discipline: mtvec is written BEFORE mie is set
                (forced by the measured fact that mtvec has no reset value),
                the trap entry saves caller-saved registers and ends in mret
  irq_vex.h     the CSR usage: the mask (0xBC0) is read AND written; the
                pending view (0xFC0) is only ever READ - consistent with the
                measured read-only/trap-on-write semantics
  isr.c         the handler exists and uses the mask/pending idiom

One stale expectation is pinned: crt0 sets mie = 0x880 (MTIE | MEIE), but on
this SoC the timer interrupt wire is tied to zero - the LiteX timer arrives
through the external array (bit 0), so MTIE is set-but-dead. Harmless, and
exactly the kind of drift the anchor corpus exists to surface.

Usage: fwanchors.py            (prints the extracted anchor facts)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FW = ROOT / "data/mgmt/firmware"


def crt0():
    txt = (FW / "crt0_vex.S").read_text(errors="replace")
    mtvec = txt.find("csrw mtvec")
    mie = txt.find("csrw mie")
    m = re.search(r"li a0, (0x[0-9a-fA-F]+)\s*//.*\n\s*csrw mie", txt)
    return {
        "mtvec_written": mtvec != -1,
        "mtvec_before_mie": -1 < mtvec < mie,
        "mie_value": int(m.group(1), 16) if m else None,
        "trap_entry_mret": bool(re.search(r"trap_entry:.*?\bmret\b", txt, re.S)),
        "saves_caller_saved": len(re.findall(r"sw x\d+,", txt)),
    }


def csr_usage():
    """Across the firmware corpus: how 0xBC0 (mask) and 0xFC0 (pending) are used."""
    reads, writes = set(), set()
    for f in FW.glob("*"):
        txt = f.read_text(errors="replace")
        for m in re.finditer(r'csrr %0, %1" : "=r"\(\w+\) : "i"\((CSR_IRQ_\w+)\)', txt):
            reads.add(m.group(1))
        for m in re.finditer(r'csrw %0, %1" :: "i"\((CSR_IRQ_\w+)\)', txt):
            writes.add(m.group(1))
        # any direct literal use of the pending address in a write position
        if re.search(r'csrw.*0xFC0|csrw.*4032', txt, re.I):
            writes.add("LITERAL_0xFC0")
    return {"reads": sorted(reads), "writes": sorted(writes)}


def isr():
    txt = (FW / "isr.c").read_text(errors="replace")
    live = "\n".join(l for l in txt.splitlines() if not l.lstrip().startswith("//"))
    return {
        "defined": "void isr(void)" in live,
        "uses_setmask": "irq_setmask" in live,
    }


def main():
    print("# The firmware anchor corpus (interrupt-facing)\n")
    c = crt0()
    print("crt0_vex.S:")
    for k, v in c.items():
        print(f"  {k}: {hex(v) if k == 'mie_value' else v}")
    u = csr_usage()
    print(f"\ncustom-CSR usage across the corpus:")
    print(f"  read : {u['reads']}")
    print(f"  write: {u['writes']}   (0xFC0 in a write position would trap - "
          f"{'CLEAN' if 'CSR_IRQ_PENDING' not in u['writes'] and 'LITERAL_0xFC0' not in u['writes'] else 'VIOLATION'})")
    i = isr()
    print(f"\nisr.c: defined={i['defined']}, uses irq_setmask={i['uses_setmask']}")
    if c["mie_value"] is not None:
        mtie, meie = bool(c["mie_value"] & 0x80), bool(c["mie_value"] & 0x800)
        print(f"\nmie = {c['mie_value']:#x}: MTIE={mtie} (structurally dead - timer wire "
              f"tied 0, the LiteX timer uses array bit 0), MEIE={meie}")


if __name__ == "__main__":
    main()
