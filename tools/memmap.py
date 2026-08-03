#!/usr/bin/env python3
"""memmap.py — the L7 memory map, extracted from the shipped RTL and diffed.

Four independent artifacts describe the management SoC's address space, and
nothing upstream checks their agreement (L7/03). This tool extracts each and
diffs them:

  RTL        mgmt_core.v — the shipped decode: `slave_sel[i] = (shared_adr
             [29:L] == V)` gives window base V<<(L+2), size 1<<(L+2); the
             CSR bridge's `csrbankN_sel = (adr[13:9] == N)` gives the bank
             map inside the csr window (LiteX paging: 0x800 bytes per bank)
  generator  litex/caravel.py — the LiteX source: the vexriscv `mem_map`
             dict is the design intent for the bases; declared sizes from
             the register_mem/add_slave calls
  firmware   defs.h / csr-defs.h — the addresses software is written
             against: every LIVE (uncommented) literal pointer, classified
             into a window or flagged unmapped
  docs       memory_map.rst (caravel repo) — the housekeeping SPI-register
             table's memory-map column, all expected inside the hk window

An unmapped access does not trap: the shared Wishbone interconnect times out
after 1,000,000 cycles (`count = 20'd1000000`), acks with 0xFFFFFFFF, and
increments the `bus_errors` CSR. "Unmapped" therefore means a ~10^6-cycle
stall returning garbage, which is why firmware pointers into holes matter.

Usage: memmap.py            (prints the four-way map and every diff)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MGMT_CORE = ROOT / "data/mgmt/mgmt_core.v"
CARAVEL_PY = ROOT / "data/mgmt/caravel.py"
DEFS_H = ROOT / "data/mgmt/defs.h"
CSR_DEFS_H = ROOT / "data/mgmt/csr-defs.h"
DEFINES_V = ROOT / "data/mgmt/defines.v"
DOC_RST = ROOT / "data/caravel/memory_map.rst"
VEX = ROOT / "data/mgmt/VexRiscv_MinDebugCache.v"

# bus-signal prefix (in the slave_sel[i] -> *_cyc wiring) -> region name as
# caravel.py's mem_map spells it
BUS_TO_REGION = {
    "mgmtsoc_vexriscv_debug_bus": "vexriscv_debug",
    "dff_bus": "dff",
    "dff2_bus": "dff2",
    "mgmtsoc_litespimmap_bus": "flash",
    "mprj": "mprj",
    "hk": "hk",
    "mgmtsoc_wishbone": "csr",
}

CSR_PAGE = 0x800  # LiteX CSR paging: adr[13:9] selects the bank, 512 words


def rtl_windows():
    """The shipped decode: region -> (base, size) in byte addresses."""
    txt = MGMT_CORE.read_text(errors="replace")
    sels = {}   # index -> (base, size)
    for i, lo, val in re.findall(
            r"slave_sel\[(\d+)\] = \(shared_adr\[29:(\d+)\] == \d+'d(\d+)\);", txt):
        sels[int(i)] = (int(val) << (int(lo) + 2), 1 << (int(lo) + 2))
    names = {}  # index -> region name
    for bus, i in re.findall(
            r"assign (\w+?)_cyc = \(shared_cyc & slave_sel\[(\d+)\]\);", txt):
        names[int(i)] = BUS_TO_REGION[bus]
    assert sorted(sels) == sorted(names), "decode/wiring index mismatch"
    return {names[i]: sels[i] for i in sels}


def rtl_csr_banks():
    """The CSR bridge map: bank index -> sorted set of peripheral registers."""
    txt = MGMT_CORE.read_text(errors="replace")
    for n, cmp_ in re.findall(
            r"assign csrbank(\d+)_sel = \(interface\d+_bank_bus_adr\[13:9\] == \d+'d(\d+)\);",
            txt):
        assert n == cmp_, f"bank {n} decodes as {cmp_}"
    banks = {}
    for n, reg in re.findall(r"assign csrbank(\d+)_\w+_w = ([a-z0-9_]+)", txt):
        banks.setdefault(int(n), set()).add(
            re.sub(r"_(storage|status)\d*(\[.*)?$", "", reg))
    return {n: sorted(regs) for n, regs in sorted(banks.items())}


def gen_map():
    """caravel.py's intent: the vexriscv mem_map dict + declared sizes."""
    txt = CARAVEL_PY.read_text(errors="replace")
    # the live (uncommented) mem_map assignments; the vexriscv one is the one
    # that contains vexriscv_debug
    the_map = None
    for body in re.findall(r"self\.mem_map = \{(.*?)\}", txt, re.S):
        entries = {k: int(v, 16) for k, v in re.findall(
            r'^\s*"(\w+)": (0x[0-9a-fA-F]+),?', body, re.M)}
        if "vexriscv_debug" in entries:
            the_map = entries
    sizes = {
        "dff": int(re.search(r"dff_size = (\d+) \* (\d+)", txt).group(1))
               * int(re.search(r"dff_size = (\d+) \* (\d+)", txt).group(2)),
        "dff2": int(re.search(r"dff2_size = (\d+)", txt).group(1)),
        "mprj": int(re.search(r'name="mprj".*?size=(0x[0-9a-fA-F]+)', txt).group(1), 16),
        "hk": int(re.search(r'name="hk".*?size=(0x[0-9a-fA-F]+)', txt).group(1), 16),
        # flash: SoCRegion size = module.total_size; the module is W25Q128JV,
        # a 128 Mbit / 16 MiB part (litespi.modules)
        "flash": 16 * 1024 * 1024 if "W25Q128JV" in txt else None,
    }
    reset = int(re.search(r"cpu_reset_address=(0x[0-9a-fA-F]+)", txt).group(1), 16)
    return the_map, sizes, reset


CSR_H = ROOT / "data/mgmt/generated/csr.h"
MEM_H = ROOT / "data/mgmt/generated/mem.h"
REGIONS_LD = ROOT / "data/mgmt/generated/regions.ld"


def mem_h_regions(path=None):
    """The generated mem.h: region -> (base, size), as C sees the map."""
    txt = (path or MEM_H).read_text(errors="replace")
    base = {n.lower(): int(v, 16) for n, v in re.findall(
        r"#define (\w+)_BASE (0x[0-9a-fA-F]+)L", txt)}
    size = {n.lower(): int(v, 16) for n, v in re.findall(
        r"#define (\w+)_SIZE (0x[0-9a-fA-F]+)", txt)}
    return {n: (base[n], size[n]) for n in base if n in size}


def regions_ld(path=None):
    """The generated linker script: region -> (origin, length).

    The firmware's own linker script does `INCLUDE ../generated/regions.ld`,
    so this is the map the shipped software is actually LINKED against.
    """
    txt = (path or REGIONS_LD).read_text(errors="replace")
    return {n: (int(o, 16), int(l, 16)) for n, o, l in re.findall(
        r"(\w+)\s*:\s*ORIGIN = (0x[0-9a-fA-F]+), LENGTH = (0x[0-9a-fA-F]+)", txt)}


def csr_header(path=None):
    """The LiteX-generated csr.h: symbol -> offset from CSR_BASE.

    This is the *fourth* description of the map and the only one that names
    each CSR bank semantically; the RTL only exposes LiteX's internal signal
    prefixes (bank 10 is `mgmtsoc_en/load/value` in Verilog and `TIMER0` here).
    Generated by the same build as the shipped mgmt_core.v — its header records
    the same LiteX revision, one second earlier.
    """
    txt = (path or CSR_H).read_text(errors="replace")
    return {n: int(o, 16) for n, o in re.findall(
        r"#define (CSR_\w+?_ADDR) \(CSR_BASE \+ (0x[0-9a-fA-F]+)L\)", txt)}


def header_bank_names(path=None):
    """bank index -> the peripheral names csr.h assigns to it."""
    out = {}
    for sym, off in csr_header(path).items():
        out.setdefault(off // CSR_PAGE, set()).add(
            sym[len("CSR_"):-len("_ADDR")].split("_")[0])
    return {b: sorted(n) for b, n in sorted(out.items())}


def fw_symbolic_pointers():
    """defs.h's pointers written through csr.h symbols, resolved to addresses.

    Most of defs.h addresses the SoC symbolically; only a handful are literals
    (those are `fw_pointers`). Resolving them needs the generated header, so
    this is the check that covers the rest of the firmware's map usage.
    """
    hdr = csr_header()
    out, unresolved = {}, []
    live = "\n".join(l for l in DEFS_H.read_text(errors="replace").splitlines()
                     if not l.lstrip().startswith("//"))
    for name, expr in re.findall(
            r"#define (\w+)\s*\(\*\(volatile \w+ ?\w*\*\)\s*\(?\s*(CSR_\w+_ADDR(?:\s*\+\s*\d+)?)\s*\)?\)",
            live):
        sym, _, add = expr.partition("+")
        sym = sym.strip()
        if sym not in hdr:
            unresolved.append((name, sym))
            continue
        out[name] = hdr[sym] + (int(add.strip() or 0) if add else 0)
    return out, unresolved


def fw_pointers():
    """defs.h: every LIVE literal register pointer + the address constants."""
    ptrs, consts = [], {}
    for line in DEFS_H.read_text(errors="replace").splitlines():
        if line.lstrip().startswith("//"):
            continue
        m = re.search(r"#define (\w+)\s*\(\*\(volatile \w+ ?\w*\*\)\s*(0x[0-9a-fA-F]+)\)", line)
        if m:
            ptrs.append((m.group(1), int(m.group(2), 16)))
        m = re.search(r"#define (DFF\d_\w+|USER_SPACE_\w+) 0x([0-9a-fA-F]+)", line)
        if m:
            consts[m.group(1)] = int(m.group(2), 16)
    return ptrs, consts


def rtl_consts():
    """defines.v: the address constants the Verilog side shares."""
    txt = DEFINES_V.read_text(errors="replace")
    return {
        "USER_SPACE_ADDR": int(re.search(r"USER_SPACE_ADDR 32'h([0-9a-fA-F]+)", txt).group(1), 16),
        "USER_SPACE_SIZE": int(re.search(r"USER_SPACE_SIZE 'h([0-9a-fA-F]+)", txt).group(1), 16),
        "MEM_WORDS": int(re.search(r"MEM_WORDS (\d+)", txt).group(1)),
    }


def doc_addrs():
    """memory_map.rst: the housekeeping table's memory-map address column."""
    return sorted({int(a.replace("_", ""), 16) for a in re.findall(
        r"\b(2[66][0-9a-f]{2}_[0-9a-f]{4})\b",
        DOC_RST.read_text(errors="replace"))})


def locate(addr, windows):
    for name, (base, size) in windows.items():
        if base <= addr < base + size:
            return name
    return None


def custom_csrs():
    """The machine-CSR addresses the shipped core decodes vs csr-defs.h."""
    vex = set(re.findall(r"12'h([0-9a-f]{3})", VEX.read_text(errors="replace")))
    hdr = {name: int(v, 16) for name, v in re.findall(
        r"#define (CSR_\w+) 0x([0-9A-Fa-f]+)",
        CSR_DEFS_H.read_text(errors="replace")) if int(v, 16) > 0xFF}
    return vex, hdr


def main():
    win = rtl_windows()
    banks = rtl_csr_banks()
    gmap, gsizes, greset = gen_map()
    ptrs, consts = fw_pointers()

    print("# The memory map, four ways\n")
    print("## RTL (shipped decode)")
    for name, (base, size) in sorted(win.items(), key=lambda kv: kv[1]):
        print(f"  {base:08x}  +{size:>9x}  {name}")

    print("\n## generator (caravel.py mem_map) vs RTL")
    for name, base in sorted(gmap.items(), key=lambda kv: kv[1]):
        rb, rs = win[name]
        note = "base OK" if rb == base else f"BASE MISMATCH rtl={rb:08x}"
        ds = gsizes.get(name)
        if ds is not None and ds != rs:
            note += f"; declared size {ds:#x} != decoded {rs:#x} (power-of-2 rounding)"
        print(f"  {base:08x}  {name:<15} {note}")
    print(f"  reset vector {greset:08x} "
          f"({'== flash base' if greset == gmap['flash'] else 'NOT flash base!'})")

    print("\n## CSR banks (csr window, 0x800 bytes each)")
    csr_base = win["csr"][0]
    for n, regs in banks.items():
        print(f"  {csr_base + n * CSR_PAGE:08x}  bank {n:>2}  {', '.join(regs)}")

    print("\n## firmware (defs.h live pointers)")
    for name, addr in ptrs:
        region = locate(addr, win)
        print(f"  {addr:08x}  {name:<24} -> {region or 'UNMAPPED (10^6-cycle timeout, reads 0xFFFFFFFF)'}")

    print("\n## firmware/Verilog constants vs RTL decode")
    vc = rtl_consts()
    rows = [
        ("defs.h DFF1", (consts["DFF1_START_ADDR"], consts["DFF1_SIZE"]), win["dff"]),
        ("defs.h DFF2", (consts["DFF2_START_ADDR"], consts["DFF2_SIZE"]), win["dff2"]),
        ("defs.h USER_SPACE_ADDR", (consts["USER_SPACE_ADDR"],), (win["mprj"][0],)),
        ("defines.v USER_SPACE_ADDR", (vc["USER_SPACE_ADDR"],), (win["mprj"][0],)),
        ("defines.v MEM_WORDS*4", (vc["MEM_WORDS"] * 4,), (win["dff"][1],)),
    ]
    for label, got, want in rows:
        ok = "agrees" if got == want else f"MISMATCH rtl={tuple(hex(x) for x in want)}"
        print(f"  {label:<28} {' '.join(f'{x:#x}' for x in got):<20} {ok}")

    print("\n## docs (memory_map.rst housekeeping table)")
    doc = doc_addrs()
    outside = [a for a in doc if locate(a, win) != "hk"]
    print(f"  {len(doc)} distinct addresses, "
          f"{'all inside the hk window' if not outside else f'OUTSIDE hk: {[hex(a) for a in outside]}'}")

    vex, hdr = custom_csrs()
    print("\n## machine-CSR space (csr-defs.h vs the shipped core's decode)")
    for name, a in sorted(hdr.items(), key=lambda kv: kv[1]):
        print(f"  {a:03x}  {name:<20} {'decoded' if f'{a:x}' in vex else 'NOT DECODED by the shipped core'}")


if __name__ == "__main__":
    main()
