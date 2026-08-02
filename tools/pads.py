#!/usr/bin/env python3
"""pads.py — the 38 per-pad power-up defaults, extracted and decoded.

Each GPIO pad's configuration at power-up comes from a `gpio_defaults_block`
— a 13-bit via-programmed constant wired into the adjacent control block,
whose reset state loads from it verbatim (gpio_control_block.v: "Initial
state on reset depends on applied defaults"). The values live in two places
in the caravel repo:

  rtl_caravel_core.v   pads 0-4: literal parameters (the management-interface
                       pads - JTAG, SDO, SDI, CSB, SCK)
  user_defines.v       pads 5-37: `USER_CONFIG_GPIO_N_INIT macros, named via
                       the GPIO_MODE_* catalogue in the same file

The legacy `DM_INIT`/`OENB_INIT` defines (present in BOTH repos' defines.v,
with DIFFERENT values: caravel 3'b001, mgmt_soc 3'b110) are referenced
nowhere in the pad-control RTL - the defaults blocks are the whole story.

Field positions per gpio_control_block.v's localparams (identical to the
firmware's documented bit masks): 0 MGMT_EN, 1 OEB, 2 HLDH, 3 INP_DIS,
4 MOD_SEL, 5 AN_EN, 6 AN_SEL, 7 AN_POL, 8 SLOW, 9 TRIP, 12:10 DM.

Usage: pads.py            (prints the per-pad table and the checks)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "data/caravel/rtl_caravel_core.v"
USER_DEF = ROOT / "data/caravel/user_defines.v"
CTRL = ROOT / "data/caravel/gpio_control_block.v"
DEFS_CARAVEL = ROOT / "data/caravel/defines.v"
DEFS_MGMT = ROOT / "data/mgmt/defines.v"

FIELDS = [("MGMT_EN", 0, 1), ("OEB", 1, 1), ("HLDH", 2, 1), ("INP_DIS", 3, 1),
          ("MOD_SEL", 4, 1), ("AN_EN", 5, 1), ("AN_SEL", 6, 1), ("AN_POL", 7, 1),
          ("SLOW", 8, 1), ("TRIP", 9, 1), ("DM", 10, 3)]


def mode_catalogue():
    """user_defines.v: GPIO_MODE_* name -> 13-bit value, and the reverse."""
    txt = USER_DEF.read_text(errors="replace")
    cat = {n: int(v, 16) for n, v in re.findall(
        r"`define (GPIO_MODE_\w+)\s+13'h([0-9a-fA-F]+)", txt)}
    return cat, {v: n for n, v in cat.items()}


def user_configs():
    """user_defines.v: pad index -> 13-bit value (via the mode macros)."""
    txt = USER_DEF.read_text(errors="replace")
    cat, _ = mode_catalogue()
    return {int(n): cat[m] for n, m in re.findall(
        r"`define USER_CONFIG_GPIO_(\d+)_INIT\s+`(GPIO_MODE_\w+)", txt)}


def pad_defaults():
    """rtl_caravel_core.v: pad index -> (value, (hi, lo) slice)."""
    txt = CORE.read_text(errors="replace")
    user = user_configs()
    pads = {}
    for m in re.finditer(
            r"gpio_defaults_block #\(\s*\n\s*\.GPIO_CONFIG_INIT\("
            r"(?:13'h([0-9a-fA-F]+)|`USER_CONFIG_GPIO_(\d+)_INIT)\)"
            r"\s*\n\s*\) gpio_defaults_block_(\d+) \(.*?"
            r"\.gpio_defaults\(gpio_defaults\[(\d+):(\d+)\]\)",
            txt, re.S):
        lit, uref, idx, hi, lo = m.groups()
        idx = int(idx)
        val = int(lit, 16) if lit else user[int(uref)]
        if uref is not None and int(uref) != idx:
            raise AssertionError(f"pad {idx} wired to USER_CONFIG_GPIO_{uref}")
        pads[idx] = (val, (int(hi), int(lo)))
    return pads


def ctrl_block_positions():
    """gpio_control_block.v: the localparam bit positions, verified."""
    txt = CTRL.read_text(errors="replace")
    pos = {n: int(v) for n, v in re.findall(r"localparam (\w+) = (\d+);", txt)}
    reset_from_defaults = bool(re.search(
        r"mgmt_ena <= gpio_defaults\[MGMT_EN\];", txt))
    return pos, reset_from_defaults


def legacy_defines():
    """Both repos' defines.v DM_INIT/OENB_INIT + whether the pad RTL uses them."""
    out = {}
    for name, p in (("caravel", DEFS_CARAVEL), ("mgmt_soc", DEFS_MGMT)):
        txt = p.read_text(errors="replace")
        out[name] = {
            "DM_INIT": re.search(r"`define DM_INIT 3'b(\d+)", txt).group(1),
            "OENB_INIT": re.search(r"`define OENB_INIT 1'b(\d)", txt).group(1),
        }
    rtl = CORE.read_text(errors="replace") + CTRL.read_text(errors="replace")
    out["referenced_by_pad_rtl"] = "DM_INIT" in rtl or "OENB_INIT" in rtl
    return out


def decode(val):
    parts = []
    for name, lo, width in FIELDS:
        v = (val >> lo) & ((1 << width) - 1)
        if v:
            parts.append(f"{name}={v:0{width}b}" if width > 1 else name)
    return " ".join(parts) or "(all zero)"


def main():
    pads = pad_defaults()
    _, rev = mode_catalogue()
    pos, reset_ok = ctrl_block_positions()

    print("# The 38 per-pad power-up defaults, decoded\n")
    print(f"control-block reset loads from the defaults word: {reset_ok}")
    print(f"field positions: {sorted(pos.items(), key=lambda kv: kv[1])}\n")
    for i in sorted(pads):
        val, (hi, lo) = pads[i]
        slice_ok = (hi, lo) == (13 * i + 12, 13 * i)
        print(f"  pad {i:>2}: 13'h{val:04x}  {rev.get(val, decode(val)):<38}"
              f"{'' if slice_ok else '  SLICE MISWIRED'}")

    print("\n# The legacy DM_INIT/OENB_INIT defines")
    for k, v in legacy_defines().items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
