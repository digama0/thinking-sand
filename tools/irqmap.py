#!/usr/bin/env python3
"""irqmap.py — the interrupt path, extracted end to end and diffed vs docs.

The path an external event takes to reach the core, measured from the shipped
RTL at every hop:

  pad/user project                          (chip wiring, rtl_caravel_core.v)
    -> mgmt_core_wrapper irq[5:0]           ({irq_spi[2:0], user_irq[2:0]})
    -> mgmt_core user_irq[5:0]
    -> 2FF MultiReg synchroniser            (multiregimpl*_regs0/regs1)
    -> gpioinN event block                  (configurable change/edge trigger,
                                             LATCHED pending, W1C, & enable)
    -> mgmtsoc_interrupt[2+N]  ------+
  timer0 event (pending & enable) -> bit 0  |  the 32-bit array into the core
  uart events  (pending & enable) -> bit 1  |
    -> VexRiscv externalInterruptArray      (ExternalInterruptArrayPlugin)
    -> CSR 0xBC0 mask (R/W), CSR 0xFC0 pending (READ-ONLY: a live view of
       mask & RegNext(lines) — NOT a latch; a write to 0xFC0 traps)
    -> externalInterrupt = (mask & lines) != 0  ->  mip.MEIP  (imported spec)

Persistence therefore lives in the SoC event blocks (L7/03's device models),
not in the core: the in-core "pending" CSR is a windowed view. The docs side
is the generated interrupts.rst table (assigned interrupt numbers).

Usage: irqmap.py            (prints the measured path and the docs diff)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MGMT_CORE = ROOT / "data/mgmt/mgmt_core.v"
WRAPPER = ROOT / "data/mgmt/mgmt_core_wrapper.v"
CHIP = ROOT / "data/caravel/rtl_caravel_core.v"
VEX = ROOT / "data/mgmt/VexRiscv_MinDebugCache.v"
DOC = ROOT / "data/mgmt/interrupts.rst"


def array_bits():
    """mgmt_core.v: which signal drives each externalInterruptArray bit."""
    txt = MGMT_CORE.read_text(errors="replace")
    return {int(i): sig for i, sig in re.findall(
        r"mgmtsoc_interrupt\[(\d+)\] = (\w+);", txt)}


def sync_chains():
    """mgmt_core.v: user_irq[N] -> 2FF MultiReg -> gpioinK; returns {N: K}.

    Keyed on the STRUCTURE (x <= user_irq[n]; y <= x; gpioinK_in_status = y),
    not on LiteX's MultiReg instance naming, which differs between generator
    versions (multiregimpl131_regs0/regs1 vs multiregimpl1310/1311) while
    denoting the same two flip-flops. See tools/replicate.py.
    """
    txt = MGMT_CORE.read_text(errors="replace")
    stage0 = {reg: int(n) for reg, n in re.findall(
        r"(\w+)\s*<=\s*user_irq\[(\d+)\];", txt)}
    stage1 = {}                                   # second FF: y <= x
    for y, x in re.findall(r"(\w+)\s*<=\s*(\w+);", txt):
        if x in stage0:
            stage1[x] = y
    sink = {reg: int(k) for k, reg in re.findall(
        r"assign gpioin(\d+)_in_status = (\w+);", txt)}
    out = {}
    for x, n in stage0.items():
        y = stage1.get(x)
        if y is None:
            raise AssertionError(f"user_irq[{n}] has no second synchroniser flop")
        if y in sink:
            out[n] = sink[y]
    return out


def event_blocks():
    """mgmt_core.v: every array source is (latched pending & enable).

    Structure-keyed: `irq = (<something>status & <something>storage)`, since
    the LiteX EventManager's signal prefixes move between versions
    (gpioin0_pending_status vs mgmtsoc_gpioin0_status).
    """
    txt = MGMT_CORE.read_text(errors="replace")
    latched = set()
    for k in range(6):
        if re.search(rf"assign gpioin{k}_gpioin{k}_irq = "
                     rf"\(\w*status\w* & \w*storage\w*\);", txt):
            latched.add(f"gpioin{k}")
    if re.search(r"assign mgmtsoc_irq = \(\w*status\w* & \w*storage\w*\);", txt):
        latched.add("timer0")
    if re.search(r"assign uart_irq = \(\(\w*status\w*\[0\] & \w*storage\w*\[0\]\)", txt):
        latched.add("uart")
    return latched


def outer_wiring():
    """wrapper + chip: how the 6 lines are fed."""
    wrap = WRAPPER.read_text(errors="replace")
    chip = CHIP.read_text(errors="replace")
    return {
        "wrapper_port": bool(re.search(r"input\s+\[5:0\] irq", wrap)),
        "wrapper_pass": bool(re.search(r"\.user_irq\(irq\)", wrap)),
        "chip_concat": bool(re.search(r"\.irq\(\{irq_spi, user_irq\}\)", chip)),
    }


def core_csrs():
    """VexRiscv: the array CSR pair's measured semantics."""
    txt = VEX.read_text(errors="replace")
    mask_dec = re.search(r"(\w+) <= \(decode_INSTRUCTION\[31 : 20\] == 12'hbc0\);", txt).group(1)
    pend_dec = re.search(r"(\w+) <= \(decode_INSTRUCTION\[31 : 20\] == 12'hfc0\);", txt).group(1)
    # mask is written under writeEnable; pending has NO write site
    mask_rw = bool(re.search(
        rf"if\({mask_dec}\) begin\s*\n\s*if\(execute_CsrPlugin_writeEnable\)", txt))
    pend_written = bool(re.search(
        rf"if\({pend_dec}\) begin\s*\n\s*if\(execute_CsrPlugin_writeEnable\)", txt))
    # pending's legality is gated on READ_OPCODE (write -> illegal access -> trap)
    pend_ro = bool(re.search(
        rf"if\({pend_dec}\) begin\s*\n\s*if\(execute_CSR_READ_OPCODE\)", txt))
    # the funnel: externalInterrupt = ((mask & RegNext(lines)) != 0)
    live_view = re.search(
        r"assign (\w+) = \((\w+) & externalInterruptArray_regNext\);", txt)
    funnel = live_view and bool(re.search(
        rf"assign externalInterrupt = \({live_view.group(1)} != 32'h0\);", txt))
    delayed = bool(re.search(
        r"externalInterruptArray_regNext <= externalInterruptArray;", txt))
    return {"mask_rw": mask_rw, "pending_read_only": pend_ro and not pend_written,
            "funnel_live_view": bool(funnel), "one_cycle_delay": delayed}


def doc_table():
    """interrupts.rst: assigned interrupt number -> module name."""
    return {int(n): name for n, name in re.findall(
        r"\|\s*(\d+)\s*\|\s*:doc:`(\w+)", DOC.read_text(errors="replace"))}


def main():
    bits = array_bits()
    chains = sync_chains()
    blocks = event_blocks()
    outer = outer_wiring()
    csrs = core_csrs()
    doc = doc_table()

    print("# The interrupt path, measured\n")
    print("## array bits (mgmt_core.v -> VexRiscv externalInterruptArray)")
    rename = {"mgmtsoc_irq": "TIMER0", "uart_irq": "UART",
              **{f"gpioin{k}_gpioin{k}_irq": f"USER_IRQ_{k}" for k in range(6)}}
    for i in sorted(bits):
        name = rename.get(bits[i], bits[i])
        agree = "== docs" if doc.get(i) == name else f"DOCS SAY {doc.get(i)}"
        print(f"  bit {i}: {bits[i]:<24} ({name})  {agree}")
    extra_doc = sorted(set(doc) - set(bits))
    print(f"  docs rows not in RTL: {extra_doc or 'none'}")

    print("\n## the six external lines")
    print(f"  chip: .irq({{irq_spi, user_irq}}) = {outer['chip_concat']}"
          f"  (bits 5:3 housekeeping, 2:0 user project)")
    print(f"  wrapper passes irq[5:0] -> user_irq: {outer['wrapper_port'] and outer['wrapper_pass']}")
    print(f"  2FF sync chains user_irq[N] -> gpioin[K]: {sync_chains()}")
    print(f"  latched event blocks (pending & enable): {sorted(blocks)}")

    print("\n## the core's array CSR pair (0xBC0 mask / 0xFC0 pending)")
    for k, v in csrs.items():
        print(f"  {k}: {v}")
    print("  => pending is a live view of (mask & lines), delayed one cycle;")
    print("     writes to 0xFC0 trap; persistence lives in the SoC event blocks")


if __name__ == "__main__":
    main()
