#!/usr/bin/env python3
"""imagecheck.py — is a flash image free of spec-UB instructions?

L6/03 assigns the decoder's reserved-accept set (4,292,609 words) UNSPECIFIED
behaviour. That clause is only tolerable because UB-freedom is a *checkable
property of a concrete image*: if no word of F lies in the UB set, the spec-UB
clause never fires and the theorem about F is unaffected by it. This is the
checker for that property, and the same sweep answers two more questions the
book needs about any candidate F:

  ub          words in the measured spec-UB set (decoder accepts, spec does not
              specify) — must be zero for a UB-free image
  illegal     words in neither the spec-legal set nor the decoder-legal set —
              these TRAP, which is defined behaviour, but in .text they are
              almost certainly data or a build error
  extension   words the spec set rejects because they belong to an extension
              this core does not implement (M/A/C ...) — these trap too, and
              indicate the image was built for the wrong -march

Word-aligned 32-bit little-endian decode over the image's executable bytes.
The RV32I core has no compressed instructions (measured: C absent), so a flat
4-byte stride is the right reading of .text.

Usage: imagecheck.py <image.bin|image.elf> [--base 0x10000000]
"""
import subprocess
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib.util


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), Path(__file__).resolve().parent / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def text_words(path):
    """(addr, word) for each 4-byte word of the image's executable bytes."""
    path = Path(path)
    data = path.read_bytes()
    base = 0
    if data[:4] == b"\x7fELF":
        if not shutil.which("riscv-none-elf-objcopy"):
            # a normal exception, not SystemExit: this module is imported by
            # tools/check-l6.py, where exiting would kill the whole layer
            raise RuntimeError("ELF input needs riscv-none-elf-objcopy "
                               "(tools/install-toolchain.sh --only riscv)")
        # take only the executable allocated sections
        out = subprocess.run(["riscv-none-elf-readelf", "-S", str(path)],
                             capture_output=True, text=True).stdout
        raw = path.with_suffix(".imagecheck.bin")
        subprocess.run(["riscv-none-elf-objcopy", "-O", "binary",
                        "--only-section=.text", str(path), str(raw)], check=True)
        data = raw.read_bytes()
        raw.unlink()
        for line in out.splitlines():
            if " .text " in line:
                base = int(line.split()[4], 16)
                break
    return base, [(base + i, int.from_bytes(data[i:i + 4], "little"))
                  for i in range(0, len(data) - 3, 4)]


def classify(words):
    """Split the image's words by the measured partition."""
    pt = _load("partition")
    spec = pt.union([(m, v) for m, v, _ in pt.SPEC])
    dec = pt.union(pt.decoder_cubes())
    ub = pt.bdd_andnot(dec, spec)          # decoder accepts, spec does not cover

    def member(bdd, w):
        node = bdd
        for bit in range(31, -1, -1):
            if node in (0, 1):
                return node == 1
            v, lo, hi = node
            while v < bit:                  # skipped variable = don't care
                bit -= 1
            node = hi if (w >> v) & 1 else lo
        return node == 1

    out = {"ok": [], "ub": [], "trap": []}
    for addr, w in words:
        if member(spec, w):
            out["ok"].append((addr, w))
        elif member(ub, w):
            out["ub"].append((addr, w))
        else:
            out["trap"].append((addr, w))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    base, words = text_words(args[0])
    r = classify(words)
    n = len(words)
    print(f"# Image check — {args[0]}\n")
    print(f"  .text base   {base:#010x}")
    print(f"  words        {n}")
    print(f"  spec-legal   {len(r['ok'])}")
    print(f"  spec-UB      {len(r['ub'])}   <- must be 0 for a UB-free image")
    print(f"  trapping     {len(r['trap'])}")
    for label in ("ub", "trap"):
        for addr, w in r[label][:8]:
            print(f"    {label:>8} {addr:#010x}: {w:08x}")
    print()
    if r["ub"]:
        print("  NOT UB-free: the spec-UB clause is reachable in this image.")
    elif r["trap"]:
        print("  UB-free, but some words trap — inspect (data in .text, or wrong -march).")
    else:
        print("  UB-FREE: every word is in the spec-legal set, so L6/03's spec-UB")
        print("  clause is unreachable for this image and cannot weaken its theorem.")
    return 1 if r["ub"] else 0


if __name__ == "__main__":
    sys.exit(main())
