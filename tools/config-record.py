#!/usr/bin/env python3
"""config-record.py — extract the shipped configuration record from the pinned
RTL pair (L4/00's `Config`, L5/00 obligation 1).

Everything below is *measured* from `VexRiscv_MinDebugCache.v` (SpinalHDL
output) and `mgmt_core.v` (LiteX output); nothing is quoted from
documentation. The record is what decides which ISA subset L6 must cover,
what the invariant must describe, and which register-dependent hypotheses
(reset vector!) become reachability conditions.

Usage: config-record.py            (prints the record)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VEX = ROOT / "data/mgmt/VexRiscv_MinDebugCache.v"
LITEX = ROOT / "data/mgmt/mgmt_core.v"

# machine-mode CSR names for the addresses we may find
CSR_NAMES = {0x300: "mstatus", 0x301: "misa", 0x304: "mie", 0x305: "mtvec",
             0x340: "mscratch", 0x341: "mepc", 0x342: "mcause", 0x343: "mtval",
             0x344: "mip", 0xC00: "cycle", 0xC02: "instret",
             0xBC0: "custom-0xBC0 (LiteX external-IRQ mask)",
             0xFC0: "custom-0xFC0 (LiteX external-IRQ pending)"}


def record():
    vex = VEX.read_text(errors="replace")
    lit = LITEX.read_text(errors="replace")
    r = {}

    # ISA: no compressed decode, no mul/div state, no atomics
    r["compressed"] = bool(re.search(r"[Cc]ompress", vex))
    r["muldiv"] = "MulDivIterativePlugin" in vex
    r["atomics"] = bool(re.search(r"\bAMO|LRSC|lrsc", vex))
    r["wfi"] = "32'h10500073" in vex

    # CSR address set, from the generated decode's 12-bit literals
    csrs = sorted({int(h, 16) for h in re.findall(r"12'h([0-9a-fA-F]+)", vex)} - {0})
    r["csrs"] = csrs

    # I-cache geometry from the memory array declarations
    m = re.search(r"reg \[(\d+):0\] banks_0 \[0:(\d+)\]", vex)
    t = re.search(r"reg \[(\d+):0\] ways_0_tags \[0:(\d+)\]", vex)
    words, lines = int(m.group(2)) + 1, int(t.group(2)) + 1
    r["icache"] = {"bytes": 4 * words, "lines": lines,
                   "line_bytes": 4 * words // lines, "tag_bits": int(t.group(1)) + 1,
                   "ways": 1 + len(re.findall(r"ways_1_tags", vex))}

    # hazard style: does a writeBackBuffer address match STALL (interlock) or forward?
    stall = re.search(r"if\(HazardSimplePlugin_addr0Match\) begin\s*\n\s*"
                      r"HazardSimplePlugin_src0Hazard = 1'b1;", vex)
    r["hazards"] = "interlock (match => stall)" if stall else "UNRECOGNISED - inspect"

    # LiteX side: reset vector register, interrupt wiring
    rv = re.search(r"reg \[31:0\] mgmtsoc_vexriscv = 32'd(\d+);", lit)
    r["reset_vector"] = {"register": "mgmtsoc_vexriscv (CSR-writable)",
                         "init": hex(int(rv.group(1))) if rv else "NOT FOUND"}
    r["sw_timer_irq_tied_0"] = bool(
        re.search(r"\.softwareInterrupt\(1'd0\)", lit)
        and re.search(r"\.timerInterrupt\(1'd0\)", lit))
    ia = re.search(r"reg \[(\d+):0\] mgmtsoc_interrupt", lit)
    r["ext_irq_array_bits"] = int(ia.group(1)) + 1 if ia else None
    r["buses"] = {"iBus": "Wishbone (+CTI/BTE burst)" if ".iBusWishbone_CTI" in lit else "?",
                  "dBus": "Wishbone (+CTI/BTE burst)" if ".dBusWishbone_CTI" in lit else "?"}
    return r


def main():
    r = record()
    print("# The shipped configuration record (measured)\n")
    print(f"ISA            : RV32I — compressed={r['compressed']}, "
          f"hardware mul/div={r['muldiv']}, atomics={r['atomics']}, wfi={r['wfi']}")
    print("CSRs           : " + ", ".join(
        f"0x{a:03X} ({CSR_NAMES.get(a, 'UNKNOWN')})" for a in r["csrs"]))
    absent = [f"0x{a:03X} ({n})" for a, n in CSR_NAMES.items()
              if a not in r["csrs"] and a not in (0xBC0, 0xFC0)]
    print("  notably absent: " + ", ".join(absent))
    ic = r["icache"]
    print(f"I-cache        : {ic['bytes']} B total — {ic['lines']} lines x "
          f"{ic['line_bytes']} B, {ic['ways']} way (direct-mapped), tag {ic['tag_bits']} bits")
    print(f"hazards        : {r['hazards']}")
    print(f"reset vector   : {r['reset_vector']['register']} = {r['reset_vector']['init']}")
    print(f"interrupts     : software/timer tied to 0 = {r['sw_timer_irq_tied_0']}; "
          f"external array width {r['ext_irq_array_bits']}")
    print(f"buses          : iBus {r['buses']['iBus']}; dBus {r['buses']['dBus']}")


if __name__ == "__main__":
    main()
