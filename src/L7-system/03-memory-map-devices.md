# L7/03 — The memory map and device models

## Background

A CPU core has no instructions for "print a character" or "read a pin." It has loads and stores, and nothing else — so systems are built on a convention called **memory-mapped I/O**: regions of the address space are wired not to memory but to devices, and a store to such an address flips wires in a peripheral rather than writing a byte to RAM. A store to `0x3000_0000` lands in the user area; a store to the UART's data register starts a byte transmitting; a load from a GPIO register reads the current pin voltages. The **memory map** is the table saying which address ranges mean what — and since the CPU's view of the entire world is filtered through it, a verification effort that gets the memory map wrong is proving theorems about a different machine.

The devices behind those addresses each need a formal model — a small transition system saying how register writes translate into behaviour. For the UART that means the **divisor register** (the programmable number that sets the baud rate by dividing the core clock) and the framing sequence: on a write to the data register, the TX wire emits start bit, eight data bits, stop bit, each lasting `divisor` clock cycles. **Interrupts** are the other direction of device communication: rather than the CPU polling devices in a loop, a device raises a dedicated wire when it wants attention, and the CPU suspends the program to run a handler. Six such wires reach this core; which physical event drives which wire is system wiring, not part of any portable spec, and lives here. And the 38 GPIO pads each carry a configuration block, loaded through a serial daisy-chain, that determines the pad's direction and function — configuration state that three different chapters' definitions index on.

There is also a fact about *where this information lives* that a newcomer would not guess: nowhere checkable. The memory map's authoritative source is a **Python program**. Caravel's management SoC is built with LiteX, a framework in which hardware is described by Python code that *generates* Verilog — so the map exists as generator source, as generated RTL, as `#define`s in firmware headers, and as human-written documentation, four artifacts with no tool upstream checking their agreement. This is normal practice, not a Caravel quirk — which is why this chapter's first deliverable is a diff of all four ([`memmap.py`](../tools/memmap.py)), and why that diff finds real disagreements in shipped artifacts ([findings](../findings.md)).

## Statement

The remaining components of `Sys`: what each address means, what each device does, and which pad carries what — consolidated from five scattered sources into one formal object, **diffed against the RTL** rather than trusted.

## Where the information lives today

Documentation-of-record and generator source, not machine-checked artifacts:

| content | authoritative source | documented in |
|---|---|---|
| memory map | **generated** — [`litex/caravel.py`](https://github.com/efabless/caravel_mgmt_soc_litex/blob/503eda0790085712ffef7f4ad8934c7daed3237f/litex/caravel.py) (LiteX source); realised in generated [`mgmt_core.v`](https://github.com/efabless/caravel_mgmt_soc_litex/blob/503eda0790085712ffef7f4ad8934c7daed3237f/verilog/rtl/mgmt_core.v); fragments in `defines.v` (`USER_SPACE_ADDR 32'h3000_0000`, `MEM_WORDS 256`) and the firmware's [`defs.h`](https://github.com/efabless/caravel_mgmt_soc_litex/blob/503eda0790085712ffef7f4ad8934c7daed3237f/verilog/dv/firmware/defs.h)/[`csr-defs.h`](https://github.com/efabless/caravel_mgmt_soc_litex/blob/503eda0790085712ffef7f4ad8934c7daed3237f/verilog/dv/firmware/csr-defs.h) | [`memory_map.rst`](https://github.com/efabless/caravel/blob/27cbe49c90ba5362ad52c9968dd98e035c30c74f/docs/rst/memory_map.rst) (the housekeeping table) |
| IRQ map | `irq[5:0]` wiring in `mgmt_core_wrapper.v` | `irq.rst` |
| pad frame | `chip_io.v`, `ef_io.list`; power-up defaults are the 38 `gpio_defaults_block` constants — pads 0–4 literal in `caravel_core.v`, 5–37 via [`user_defines.v`](https://github.com/efabless/caravel/blob/27cbe49c90ba5362ad52c9968dd98e035c30c74f/verilog/rtl/user_defines.v) — extracted and decoded by [`pads.py`](../tools/pads.py) (the `DM_INIT`/`OENB_INIT` defines are vestigial: present in both repos with *different* values, referenced by no pad RTL) | `pinout.rst`, `gpio.rst` |
| pad electrical behaviour | `sky130_fd_io` (PDK) — black-box IO macros | PDK io documentation |
| per-pad configuration | the `gpio_control_block` ×38 serial chain (clocks `hk_serial_clk`/`hk_serial_load` in the SDC) | `gpio.rst`, `housekeeping-spi.rst` |
| flash / XIP | housekeeping SPI + QSPI controller RTL; **the flash datasheet is outside every repo** (X4 proper) | `qspi-flash.rst` |
| UART, timers | RTL | `counter-timers.rst` |
| electrical envelope | — | `maximum-ratings.rst`, `external-clock.rst` — P6/Envelope material as prose |

Two standing observations. First, the memory map's authoritative source is a **Python generator** — spec-by-generator, so read `caravel.py`, not the RST. Second, [`memmap.py`](../tools/memmap.py) extracts the shipped decode (seven windows from `mgmt_core.v`'s `slave_sel` comparisons, plus the 20 LiteX CSR banks inside the `csr` window) and diffs it against the other three artifacts — and drift is exactly what it finds ([findings](../findings.md)): the `hk` window is declared 3 MB but decoded as 4 MB (LiteX rounds decode windows to powers of two), four live `defs.h` pointers target unmapped space, and `csr-defs.h` names a machine CSR (`CSR_DCACHE_INFO`, 0xCC0) the shipped core does not decode. The unmapped-space semantics matter to [02](02-bus-contract.md)'s contract: an access to a hole does not trap — the shared interconnect **times out after 10⁶ cycles**, acks with `0xFFFF_FFFF`, and counts a `bus_errors` CSR — so a stray firmware pointer costs a ~100 ms stall at 10 MHz, and the address-decode model must say so.

## The models to write

**Memory map**: an address-decode function `addr → (region, device, offset)` — the extraction and the four-way diff exist ([`memmap.py`](../tools/memmap.py)); what remains is casting the extracted table as the formal decode component, including the timeout behaviour on holes, exported to [02](02-bus-contract.md)'s A5 and to L5's load/store lemmas.

**The IRQ map**: which physical event drives which line of L6/01's external-interrupt array — the system half of interrupts, deliberately *not* in the portable spec. The whole path is measured and diffed against the generated documentation ([`irqmap.py`](../tools/irqmap.py), which agrees exactly): array bit 0 = timer, bit 1 = UART, bits 2–7 = `user_irq[0:5]` (chip-level: the low three from the user project, the high three from housekeeping), bits 8–31 unused. Each external line crosses into the core clock domain through a 2FF synchroniser and then a **latched event block** (configurable change/edge trigger, pending ∧ enable, write-one-to-clear) — these blocks, not the core, are where an interrupt *persists* (L6/01's pending CSR is a live view), so their model is a required component of `Sys`, carrying the no-lost-interrupts half of L5/05's delivery obligation.

**UART**: the observable channel — divisor register semantics, bit-cell generation against the core clock, the TX trace feeding [00](00-sys-and-obs.md)'s derivation stack; RX's synchroniser is L2/06's business, its byte semantics here.

**GPIO/pad configuration**: the ×38 serial-chain state as spec-level configuration — the same object F4's timing modes and [00](00-sys-and-obs.md)'s per-pad `obs` indexing consume; one definition, three users.

**XIP controller**: wait-state behaviour per mode bits — the piece "nobody ever writes down," and the source of `B(config)` in [02](02-bus-contract.md).

## Obligations

1. The RTL-vs-docs diff for map, IRQ wiring, and pad defaults — the map's four-way diff runs in [`memmap.py`](../tools/memmap.py) (three discrepancies found and pinned); the IRQ-wiring and pad-defaults diffs remain ([`check-l7.py`](../tools/check-l7.py)).
2. The five models above as components of `Sys`'s composition ([00](00-sys-and-obs.md) obligation 3) — for the map, that is the extracted seven-window table plus the 10⁶-cycle timeout semantics on holes, as a formal decode function.
3. Track the `caravel.py`-generated map against the *shipped* `mgmt_core.v` — the generator is authoritative for intent, the RTL for the artifact; the one mismatch (the `hk` window's power-of-two rounding) is a real result of exactly this kind.

## Effort

Months, wide and mechanical; the models are small individually and the consolidation *is* the deliverable.
