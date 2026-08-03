#!/usr/bin/env python3
"""check-l7 — L7 (the system): obligations as an executable scoreboard.

The layer's deliverables are definitions and consolidations; the checker-shaped
work is the diffs (docs vs RTL vs generator) and the numeric epoch inequalities,
each stubbed with its missing input named.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import Layer, PASS, FAIL, FINDING

L = Layer("L7", "the system specification")

@L.check("memmap", "the memory map four ways: shipped decode vs generator vs firmware headers vs docs",
         doc="src/L7-system/03-memory-map-devices.md")
def _(ctx):
    from checklib import load, DATA, need
    for f in ("mgmt/mgmt_core.v", "mgmt/caravel.py", "mgmt/defs.h",
              "mgmt/csr-defs.h", "mgmt/defines.v", "caravel/memory_map.rst"):
        if m := need(DATA / f):
            return FAIL, f"missing {m} (run tools/fetch-data.sh checks)"
    mm = load("memmap")
    win = mm.rtl_windows()
    expect_win = {
        "dff": (0x00000000, 0x400), "dff2": (0x00000400, 0x200),
        "flash": (0x10000000, 0x1000000), "hk": (0x26000000, 0x400000),
        "mprj": (0x30000000, 0x10000000), "csr": (0xF0000000, 0x10000),
        "vexriscv_debug": (0xF00F0000, 0x100),
    }
    if win != expect_win:
        return FAIL, f"shipped decode changed: {win}"
    gmap, gsizes, greset = mm.gen_map()
    if any(gmap[n] != win[n][0] for n in gmap) or greset != gmap["flash"]:
        return FAIL, f"generator disagrees on a base or the reset vector: {gmap}, reset {greset:#x}"
    size_diffs = {n: (s, win[n][1]) for n, s in gsizes.items()
                  if s is not None and s != win[n][1]}
    if size_diffs != {"hk": (0x300000, 0x400000)}:
        return FAIL, f"declared-vs-decoded size diffs changed: {size_diffs}"
    banks = mm.rtl_csr_banks()
    sentinels = {0: "mgmtsoc_reset", 5: "gpio_out", 10: "mgmtsoc_load",
                 11: "uart_enable", 13: "gpioin0_enable", 19: "user_irq_ena"}
    if sorted(banks) != list(range(20)) or any(r not in banks[n] for n, r in sentinels.items()):
        return FAIL, f"CSR bank map changed: {len(banks)} banks, {banks}"
    ptrs, consts = mm.fw_pointers()
    unmapped = sorted(name for name, a in ptrs if mm.locate(a, win) is None)
    if unmapped != ["reg_la_sample", "reg_ro_block0", "reg_rw_block0", "reg_rw_block1"]:
        return FAIL, f"unmapped firmware pointers changed: {unmapped}"
    vc = mm.rtl_consts()
    if (consts["DFF1_START_ADDR"], consts["DFF1_SIZE"]) != win["dff"] or \
       (consts["DFF2_START_ADDR"], consts["DFF2_SIZE"]) != win["dff2"] or \
       consts["USER_SPACE_ADDR"] != win["mprj"][0] or \
       vc["USER_SPACE_ADDR"] != win["mprj"][0] or vc["MEM_WORDS"] * 4 != win["dff"][1]:
        return FAIL, "an address constant in defs.h/defines.v disagrees with the decode"
    doc = mm.doc_addrs()
    if len(doc) != 112 or any(mm.locate(a, win) != "hk" for a in doc):
        return FAIL, f"housekeeping doc table changed: {len(doc)} addresses"
    vex, hdr = mm.custom_csrs()
    undecoded = sorted(n for n, a in hdr.items() if f"{a:x}" not in vex)
    if undecoded != ["CSR_DCACHE_INFO"]:
        return FAIL, f"csr-defs.h vs decoded machine CSRs changed: {undecoded}"
    return FINDING, ("all 7 window bases agree across RTL, generator, firmware headers and "
                     "defines.v; reset vector = flash base; the 20 CSR banks enumerated; all "
                     "112 documented housekeeping addresses inside the hk window. Three real "
                     "diffs, pinned: (1) hk is declared 3 MB but the shipped decode rounds to "
                     "4 MB - 0x26300000..0x263FFFFF also selects housekeeping; (2) four live "
                     "defs.h pointers (reg_rw_block0/1, reg_ro_block0, reg_la_sample) target "
                     "unmapped space, where an access stalls the bus for the 10^6-cycle "
                     "interconnect timeout and reads 0xFFFFFFFF; (3) csr-defs.h's "
                     "CSR_DCACHE_INFO (0xCC0) is not decoded by the shipped core (0xBC0/0xFC0 "
                     "are) - reading it traps")
@L.check("irq-map", "the interrupt path end to end: chip wiring -> sync -> event blocks -> array -> CSRs, vs docs",
         doc="src/L7-system/03-memory-map-devices.md")
def _(ctx):
    from checklib import load, DATA, need
    for f in ("mgmt/mgmt_core.v", "mgmt/mgmt_core_wrapper.v", "mgmt/interrupts.rst",
              "mgmt/VexRiscv_MinDebugCache.v", "caravel/rtl_caravel_core.v"):
        if m := need(DATA / f):
            return FAIL, f"missing {m} (run tools/fetch-data.sh checks)"
    im = load("irqmap")
    bits = im.array_bits()
    rename = {"mgmtsoc_irq": "TIMER0", "uart_irq": "UART",
              **{f"gpioin{k}_gpioin{k}_irq": f"USER_IRQ_{k}" for k in range(6)}}
    rtl = {i: rename.get(s, s) for i, s in bits.items()}
    doc = im.doc_table()
    if rtl != doc:
        return FAIL, f"array wiring vs docs diverged: rtl={rtl}, docs={doc}"
    if im.sync_chains() != {n: n for n in range(6)}:
        return FAIL, f"user_irq sync chains changed: {im.sync_chains()}"
    if len(im.event_blocks()) != 8:
        return FAIL, f"latched event blocks changed: {sorted(im.event_blocks())}"
    if not all(im.outer_wiring().values()):
        return FAIL, f"outer wiring changed: {im.outer_wiring()}"
    csrs = im.core_csrs()
    if not all(csrs.values()):
        return FAIL, f"array CSR semantics changed: {csrs}"
    return PASS, ("the generated interrupt docs agree with the RTL exactly: array bit 0 = "
                  "timer0, 1 = uart, 2-7 = user_irq[0:5]; chip level feeds "
                  "{irq_spi[2:0], user_irq[2:0]} (housekeeping high, user project low). "
                  "Every external line is 2FF-synchronised then latched in a LiteX event "
                  "block (pending & enable, W1C). In the core, mask 0xBC0 is R/W and "
                  "pending 0xFC0 is READ-ONLY - a live view of mask & RegNext(lines), "
                  "not a latch; a write to 0xFC0 traps. This settles L6/01's deferred "
                  "level-vs-latched question: persistence lives in the SoC event blocks, "
                  "not the core")
@L.check("pad-defaults", "the 38 per-pad power-up defaults, extracted and decoded",
         doc="src/L7-system/04-power-epochs.md")
def _(ctx):
    from checklib import load, DATA, need
    for f in ("caravel/rtl_caravel_core.v", "caravel/user_defines.v",
              "caravel/gpio_control_block.v", "caravel/defines.v", "mgmt/defines.v"):
        if m := need(DATA / f):
            return FAIL, f"missing {m} (run tools/fetch-data.sh checks)"
    pd = load("pads")
    pads = pd.pad_defaults()
    pos, reset_ok = pd.ctrl_block_positions()
    if sorted(pads) != list(range(38)) or not reset_ok:
        return FAIL, f"pad set changed: {len(pads)} pads, reset-from-defaults {reset_ok}"
    if any((hi, lo) != (13 * i + 12, 13 * i) for i, (_, (hi, lo)) in pads.items()):
        return FAIL, "a defaults-block slice is miswired"
    vals = {i: v for i, (v, _) in pads.items()}
    expect = {0: 0x1803, 1: 0x1803, 2: 0x0403, 3: 0x0801, 4: 0x0403,
              **{i: 0x0403 for i in range(5, 38)}}
    if vals != expect:
        diff = {i: (hex(vals[i]), hex(expect[i])) for i in vals if vals[i] != expect[i]}
        return FAIL, f"pad defaults changed: {diff}"
    exp_pos = {"MGMT_EN": 0, "OEB": 1, "HLDH": 2, "INP_DIS": 3, "MOD_SEL": 4,
               "AN_EN": 5, "AN_SEL": 6, "AN_POL": 7, "SLOW": 8, "TRIP": 9, "DM": 10}
    if {k: pos.get(k) for k in exp_pos} != exp_pos:
        return FAIL, f"control-block field positions changed: {pos}"
    legacy = pd.legacy_defines()
    if legacy["referenced_by_pad_rtl"] or \
       (legacy["caravel"]["DM_INIT"], legacy["mgmt_soc"]["DM_INIT"]) != ("001", "110"):
        return FAIL, f"legacy-defines situation changed: {legacy}"
    return FINDING, ("all 38 defaults blocks extracted, slices verified, and the control "
                     "block's reset state provably loads from them. Power-up state: pads "
                     "0/1 (JTAG, SDO) management-bidirectional with output DISABLED and "
                     "strong drive mode; pad 3 (CSB) weak pull-up; the other 35 pads "
                     "management standard input, no pull. So at power-up NO pad actively "
                     "drives - answering L7/04's non-hazardous-defaults question. Two "
                     "stale artifacts pinned: DM_INIT/OENB_INIT exist in BOTH repos' "
                     "defines.v with DIFFERENT DM values (caravel 001, mgmt_soc 110) and "
                     "are referenced by no pad RTL - the defaults blocks are the whole "
                     "story; and caravel defines.v's comment says pads default to USER "
                     "input when they are in fact MANAGEMENT input")
L.todo("b-config", "tabulate B(config): worst-case bus latency per XIP configuration",
       doc="src/L7-system/02-bus-contract.md",
       note="the XIP path on the shipped SoC is LiteSPI inside the fetched mgmt_core.v "
            "(litespimmap + phy, W25Q128JV read 0x03 at 1x) - the remaining work is the "
            "latency analysis of the litespi FSM plus the flash part's timing")
L.todo("f-immutable", "the flash-immutability check: can software reach flash write commands?",
       doc="src/L7-system/04-power-epochs.md",
       note="the fetched mgmt_core.v exposes a LiteSPI MASTER path (CSR bank 3: master_cs/"
            "phyconfig/rxtx) beside the read-only XIP map - software plausibly CAN issue "
            "arbitrary SPI commands incl. writes; the check is tracing that path and any gates")
L.todo("holdup-ineq", "the supervisor/hold-up inequalities with datasheet + decap numbers",
       doc="src/L7-system/04-power-epochs.md",
       blocked_on="L5/wcet-table for t_epilogue, the decap census (done: 125k) times per-cell C from the PDK, and a chosen supervisor part")
L.todo("oc-rows", "the operating-conditions clause rows (F4, F6, B(config)) as one audited table",
       doc="src/L7-system/05-operating-conditions.md",
       note="the F4 rows sharpened by the SDC audit land here; F6 needs L2/f6-pll-range")
L.extern("X4", "external devices meet their datasheets (per B-level batch)",
         doc="src/axioms.md",
         note="other people's silicon; modelled from datasheets, never checked from shipped data")

if __name__ == "__main__":
    sys.exit(L.main())
