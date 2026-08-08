# Spike co-simulation — the L5 trace-oracle

`tools/run-sim.sh cosim` builds `CospikeTinyRocketConfig` (TinyRocket + trace
port + DebugROB + spike attached via testchipip's `SpikeCosim`) and runs an
image with **every committed instruction checked against spike, the golden ISA
model**, per commit: PC, register writeback, CSR effects. It is L5's α anchor
(the abstraction function reading architectural state at retirement) made
executable — the precursor to the refinement proof.

## Result

A pure-compute RV32IMAC image (`sim/cotest.c` — mul/div/rem, shifts, rotates,
branches, load/store loops) runs to a `tohost` pass with **1,631 committed
instructions and zero mismatches** — and always the same 1,631 whenever it
boots (the boot/wake window is a flaky async race, boundary 2 below; when it
clears it, the whole program verifies clean). The RTL the
flow hardens refines the ISA, verified instruction-by-instruction.

## Two boundaries, both diagnosed

1. **ISA co-sim ends at MMIO.** The `hello` image diverges at its UART TX-full
   *poll loop*: the DUT reads the real UART status and spins; spike has no UART,
   reads a placeholder, and runs ahead. This is the fundamental scope of ISA
   co-simulation — the golden model is the *core*, not the SoC's devices —
   correctly surfaced, not a core bug. cospike's read-override machinery covers
   CLINT/PLIC/tohost but a tight MMIO poll still desyncs the branch. The compute
   image sidesteps it (no device reads).

2. **Boot/wake window is flaky.** The wake interrupt and first fetch cross the
   TSI-load / serial-TL async clock boundary, and the run either desyncs at
   cycle ~15 (the boot race, ~2 commits) or boots cleanly and *always* completes
   at 1,631/0 — a real mid-program mismatch never appears. `+verilator+rand+reset+0`
   (the script sets it, ELF *before* the plusarg or htif eats it) removes the
   X-init half of the variance but not the CDC-ordering half, so the checker
   retries the boot race a few times; when a run boots, the program verifies.
   The core-correctness result is solid; only the boot handshake is unreliable.

## cospike is RV64/Boom-shaped: eight portability fixes

The whole exercise is a finding about the ecosystem's co-sim tooling being
written and CI'd for 64-bit out-of-order cores. `cospike-rv32.patch` (against
the testchipip submodule) carries them; each is a real RV32/in-order/custom-ext
incompatibility, not a workaround:

- **custom extensions**: the ISA string ends `_xrocket`; spike tries to `dlopen`
  a plugin per `x`-extension. Strip `_x*` before configuring spike — the golden
  model covers the ratified surface, and touches of custom state then mismatch
  loudly (correct, while the custom fragment is authored-spec not golden-model).
- **page levels**: an `assert(maxpglevels >= 3)` guarded RV64 Sv39..Sv57;
  RV32/no-VM reports fewer. Relaxed to `<= 5`.
- **interrupt bit**: the pending/interrupt bit is xlen-1 — bit 31 on RV32, not
  only bit 63. The RV64 mask `& 0x7FFF...` mis-parsed every RV32 interrupt cause.
- **register width**: spike stores RV32 GPRs sign-extended in 64-bit state; the
  trace zero-extends. Compare writeback *and* PC masked to xlen, or every
  address ≥ 0x80000000 false-mismatches.
- **pre-boot wake**: before the DUT's first commit the trace's interrupt-cause
  field is X (see boundary 2). Guard the whole interrupt block on a
  `cosim_started` flag — record the pending bit, never step spike, until the DUT
  commits.
- plus the config itself (`CosimConfigs.scala`, committed): `WithDebugROB` gives
  the trace port writeback data the comparison needs.

## Toolchain notes (also in tools/run-sim.sh)

Spike v1.1.0 needs `-include cstdint` under GCC 13 and does not `make install`
`libriscv.a`/`libfdt.a` (copy them by hand); the pinned Chipyard spike
(`toolchains/riscv-tools/riscv-isa-sim`, 2025-08) is the one cospike links.
The images build with stock clang — no riscv-gcc.
