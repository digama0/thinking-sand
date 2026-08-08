#!/usr/bin/env python3
"""check-l7 — L7 (the system specification): obligations as an executable scoreboard.

Re-anchored to the Chipyard target. Implemented: the memory-map diff (device
tree vs per-device register maps vs the boundary), the ChipTop port-list check,
and the interrupt-wiring extraction from the device tree. The models themselves
are the layer's authored deliverables and stay TODO.
"""
import re
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer, PASS, FAIL, FINDING, DTS, GENSRC, GEN_COLLATERAL, RTL_SRC, need

L = Layer("L7", "the system specification")

# The boundary the book states (L7/00): 18 signals.
EXPECTED_PORTS = {
    "uart_0_txd", "uart_0_rxd", "custom_boot",
    "jtag_TCK", "jtag_TMS", "jtag_TDI", "jtag_TDO", "jtag_reset",
    "reset_io", "clock_uncore", "clock_tap",
    "serial_tl_0_in_ready", "serial_tl_0_in_valid", "serial_tl_0_in_bits_phit",
    "serial_tl_0_out_ready", "serial_tl_0_out_valid", "serial_tl_0_out_bits_phit",
    "serial_tl_0_clock_in",
}


def dts_regions():
    """Parse `reg = <base size>` regions with their node names from the dts."""
    txt = DTS.read_text(errors="replace")
    out = {}
    for m in re.finditer(r"(\w[\w-]*)@([0-9a-f]+)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", txt, re.S):
        name, addr, body = m.group(1), int(m.group(2), 16), m.group(3)
        rm = re.search(r"reg\s*=\s*<\s*0x([0-9a-f]+)\s+0x([0-9a-f]+)\s*>", body)
        if rm:
            out[name] = (int(rm.group(1), 16), int(rm.group(2), 16))
    return out


@L.check("memmap", "the memory map: device tree vs per-device register maps", doc="src/L7-system/03-memory-map-devices.md")
def _(ctx):
    if need(DTS):
        return FINDING, f"device tree absent (regenerate: tools/build-rocket.sh): {DTS}"
    regions = dts_regions()
    if not regions:
        return FAIL, "no reg regions parsed from the dts"
    # cross artifact: every regmap.json's baseAddress must be a dts region base
    regmaps = sorted(GENSRC.glob("*.regmap.json"))
    mism = []
    for rm in regmaps:
        d = json.loads(rm.read_text())
        base = int(d["peripheral"]["baseAddress"], 16)
        if not any(b <= base < b + sz for b, sz in regions.values()):
            mism.append(f"{rm.name}: base {base:#x} inside no dts region")
    # overlap check over the dts regions
    spans = sorted((b, b + s, n) for n, (b, s) in regions.items())
    overlaps = [(a[2], b[2]) for a, b in zip(spans, spans[1:]) if a[1] > b[0]]
    if mism or overlaps:
        return FAIL, "; ".join(mism + [f"overlap {x}/{y}" for x, y in overlaps])
    named = ", ".join(f"{n}@{b:#x}" for n, (b, s) in sorted(regions.items(), key=lambda kv: kv[1][0]))
    return PASS, (f"{len(regions)} dts regions, non-overlapping; all {len(regmaps)} register-map bases "
                  f"land on dts regions. Map: {named}")


@L.check("boundary", "the ChipTop port list is the book's 18-signal boundary", doc="src/L7-system/00-sys-and-obs.md")
def _(ctx):
    top = RTL_SRC / "ChipTop.sv"
    if need(top):
        return FINDING, f"ChipTop.sv absent (regenerate: tools/build-rocket.sh)"
    txt = top.read_text(errors="replace")
    m = re.search(r"module\s+ChipTop\s*\((.*?)\);", txt, re.S)
    ports = set(re.findall(r"(?:input|output)\s+(?:\[[^\]]*\]\s*)?(\w+)", m.group(1)))
    extra, missing = ports - EXPECTED_PORTS, EXPECTED_PORTS - ports
    if extra or missing:
        return FAIL, f"boundary drift: extra {sorted(extra)}, missing {sorted(missing)}"
    return PASS, f"exactly the documented boundary: {len(ports)} named ports (UART, JTAG x5, custom_boot, reset, clock in/tap, serial-TL x6)"


@L.check("irq-map", "the interrupt wiring from the device tree", doc="src/L7-system/03-memory-map-devices.md")
def _(ctx):
    if need(DTS):
        return FINDING, "device tree absent"
    txt = DTS.read_text(errors="replace")
    clint = re.search(r"clint@\w+\s*\{[^}]*interrupts-extended\s*=\s*<([^>]*)>", txt, re.S)
    plic = re.search(r"interrupt-controller@\w+\s*\{[^}]*interrupts-extended\s*=\s*<([^>]*)>", txt, re.S)
    uart_irq = re.search(r"serial@\w+\s*\{[^}]*interrupts\s*=\s*<(\d+)>", txt, re.S)
    ndev = re.search(r"riscv,ndev\s*=\s*<(\d+)>", txt)
    if not (clint and plic and uart_irq and ndev):
        return FAIL, "could not extract the CLINT/PLIC/UART wiring from the dts"
    clint_ints = re.findall(r"\b(\d+)\b", clint.group(1))
    plic_ints = re.findall(r"\b(\d+)\b", plic.group(1))
    ok = clint_ints == ["3", "7"] and plic_ints == ["11"] and uart_irq.group(1) == "1"
    msg = (f"CLINT → ints {clint_ints} (msip, mtip); PLIC → int {plic_ints} (meip), "
           f"ndev {ndev.group(1)}; UART = PLIC source {uart_irq.group(1)}")
    if not ok:
        return FINDING, msg + " — differs from the standard shape the book states; adjudicate"
    return PASS, msg + " — the standard RISC-V shape, all three lines live (no residue at the core, L6/01)"


L.todo("rtl-decode-diff", "the RTL's actual address decode diffed against the dts",
       doc="src/L7-system/03-memory-map-devices.md",
       blocked_on="a decode extractor over the TL fabric modules (the third leg of the diff)")
L.todo("pad-defaults", "the reset drive state of every output pad",
       doc="src/L7-system/04-power-epochs.md",
       blocked_on="reset-state extraction from the IOCell/serializer RTL")
L.todo("b-config", "the latency bound B per configuration",
       doc="src/L7-system/02-bus-contract.md",
       blocked_on="the serializer FSM analysis + link-clock ratio")
L.todo("sys-models", "the device models (UART, CLINT, PLIC, boot, serial-TL) as Sys components",
       doc="src/L7-system/00-sys-and-obs.md", blocked_on="spec-phase authoring")
L.extern("X4", "external devices meet their datasheets (per B-level batch)",
         doc="axioms.md",
         note="the board oscillator, the serial-link far end, the pad-ring cells, the POR arrangement — modelled from datasheets, never checked from artifacts")

if __name__ == "__main__":
    sys.exit(L.main())
