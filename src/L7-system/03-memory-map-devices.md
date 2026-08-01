# L7/03 — The memory map and device models

## Statement

The remaining components of `Sys`: what each address means, what each device does, and which pad carries what — consolidated from five scattered sources into one formal object, **diffed against the RTL** rather than trusted.

## Where the information lives today

Documentation-of-record and generator source, not machine-checked artifacts:

| content | authoritative source | documented in |
|---|---|---|
| memory map | **generated** — `caravel_mgmt_soc_litex/litex/caravel.py` (LiteX source); realised in generated `mgmt_core.v`; fragments in `defines.v` (`USER_SPACE_ADDR 32'h3000_0000`, `MEM_WORDS 256`, 2 DFFRAM blocks) | `memory-mapped-io-summary.rst` |
| IRQ map | `irq[5:0]` wiring in `mgmt_core_wrapper.v` | `irq.rst` |
| pad frame | `chip_io.v`, `ef_io.list`; power-up defaults `DM_INIT 3'b110`, `OENB_INIT` in `defines.v` | `pinout.rst`, `gpio.rst` |
| pad electrical behaviour | `sky130_fd_io` (PDK) — black-box IO macros | PDK io documentation |
| per-pad configuration | the `gpio_control_block` ×38 serial chain (clocks `hk_serial_clk`/`hk_serial_load` in the SDC) | `gpio.rst`, `housekeeping-spi.rst` |
| flash / XIP | housekeeping SPI + QSPI controller RTL; **the flash datasheet is outside every repo** (X4 proper) | `qspi-flash.rst` |
| UART, timers | RTL | `counter-timers.rst` |
| electrical envelope | — | `maximum-ratings.rst`, `external-clock.rst` — P6/Envelope material as prose |

Two standing observations: the memory map's authoritative source is a **Python generator** — spec-by-generator, so read `caravel.py`, not the RST — and nothing checks the documentation against the RTL; the diff is this file's first experiment because drift is the expected finding.

## The models to write

**Memory map**: an address-decode function `addr → (region, device, offset)`, extracted from RTL, diffed against docs, exported to [02](02-bus-contract.md)'s A5 and to L5's load/store lemmas.

**The IRQ map**: which physical event drives which of the 6 wired lines — the system half of interrupts, deliberately *not* in L6/01's portable spec. Includes the timer and the UART's line.

**UART**: the observable channel — divisor register semantics, bit-cell generation against the core clock, the TX trace feeding [00](00-sys-and-obs.md)'s derivation stack; RX's synchroniser is L2/06's business, its byte semantics here.

**GPIO/pad configuration**: the ×38 serial-chain state as spec-level configuration — the same object F4's timing modes and [00](00-sys-and-obs.md)'s per-pad `obs` indexing consume; one definition, three users.

**XIP controller**: wait-state behaviour per mode bits — the piece "nobody ever writes down," and the source of `B(config)` in [02](02-bus-contract.md).

## Obligations

1. The RTL-vs-docs diff for map, IRQ wiring, and pad defaults — cheap, and any discrepancy is a finding about shipped documentation.
2. The five models above as components of `Sys`'s composition ([00](00-sys-and-obs.md) obligation 3).
3. Track the `caravel.py`-generated map against the *shipped* `mgmt_core.v` — the generator is authoritative for intent, the RTL for the artifact; a mismatch is a real result either way.

## Effort

Months, wide and mechanical; the models are small individually and the consolidation *is* the deliverable.
