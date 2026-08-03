#!/usr/bin/env bash
# build-firmware.sh — build a flash image from the SHIPPED firmware sources,
# using the SHIPPED linker script, so the image can be checked for spec-UB
# freedom (tools/imagecheck.py) against the measured encoding partition.
#
# What is shipped and what is not: `verilog/dv/firmware/` carries the startup
# code (crt0_vex.S) and the ISR, but the DV programs themselves pull in LiteX
# BIOS headers that are not in the tree. So this builds crt0 + the shipped isr
# entry + a small main that exercises the CSR window — enough to produce a
# REAL image laid out exactly as the flow lays one out, which is what the
# UB-freedom property is about.
#
# The linker script is the one the DV makefiles actually select — `sections.lds`
# (note `sections_vexriscv.lds` is commented out in verilog/dv/make/cpu.makefile).
# It hardcodes its own copy of the memory map rather than including the
# generated regions.ld; see findings for where that copy disagrees.
#
# -march=rv32i_zicsr matches the measured configuration record exactly: RV32I,
# no M/A/C, with the Zicsr instructions crt0 needs for mtvec/mie.
#
# Usage: tools/build-firmware.sh [outdir]      (default build-fw/)
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-build-fw}"
FW=data/mgmt/firmware
GEN=data/mgmt/generated

command -v riscv-none-elf-gcc >/dev/null || {
  echo "riscv-none-elf-gcc not found — tools/install-toolchain.sh --only riscv" >&2; exit 1; }
for f in "$FW/crt0_vex.S" "$FW/sections.lds"; do
  [ -s "$f" ] || { echo "missing $f — run tools/fetch-data.sh mgmt" >&2; exit 1; }
done

rm -rf "$OUT"; mkdir -p "$OUT"
cp "$FW"/* "$OUT"/ 2>/dev/null || true
mkdir -p "$OUT/generated" && cp "$GEN"/* "$OUT/generated/" 2>/dev/null || true

# A minimal payload: touch the UART CSR (bank 11, from the generated csr.h) and
# supply the `isr` symbol crt0's trap_entry calls. Deliberately plain RV32I.
cat > "$OUT/main.c" <<'EOF'
#include <stdint.h>
#define CSR_UART_RXTX (*(volatile uint32_t *)0xf0005800)
void isr(void) { }
int main(void) {
    for (const char *p = "thinking-sand\n"; *p; p++)
        CSR_UART_RXTX = (uint32_t)*p;
    return 0;
}
EOF

ARCH="-march=rv32i_zicsr -mabi=ilp32"
( cd "$OUT"
  riscv-none-elf-gcc $ARCH -nostdlib -ffreestanding -c crt0_vex.S -o crt0.o
  riscv-none-elf-gcc $ARCH -nostdlib -ffreestanding -O2 -c main.c -o main.o
  riscv-none-elf-gcc $ARCH -nostdlib -T sections.lds crt0.o main.o -o fw.elf 2>&1 \
    | grep -v "LOAD segment with RWX" || true
  riscv-none-elf-objcopy -O binary fw.elf fw.bin )

echo "== built $OUT/fw.elf"
riscv-none-elf-readelf -S "$OUT/fw.elf" | grep -E "\.text|\.data" || true
echo "== stack pointer:"; riscv-none-elf-nm "$OUT/fw.elf" | grep _fstack || true
echo
exec python3 tools/imagecheck.py "$OUT/fw.elf"
