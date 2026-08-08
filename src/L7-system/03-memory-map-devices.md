# L7/03 — The memory map and device models

## Background

A CPU core has no instructions for "print a character" or "read a pin." It has loads and stores, and nothing else — so systems are built on a convention called **memory-mapped I/O**: regions of the address space are wired not to memory but to devices, and a store to such an address flips wires in a peripheral rather than writing a byte to RAM. A store to the UART's data register starts a byte transmitting; a load from the CLINT's `mtime` registers reads the running timer; a store to the tile-reset setter holds the processor in reset. The **memory map** is the table saying which address ranges mean what — and since the CPU's view of the entire world is filtered through it, a verification effort that gets the memory map wrong is proving theorems about a different machine.

The devices behind those addresses each need a formal model — a small transition system saying how register writes translate into behaviour. For the UART that means the **divisor register** (the programmable number that sets the baud rate by dividing the bus clock) and the framing sequence: on a write to the transmit register, the TX wire emits start bit, eight data bits, stop bit, each lasting `divisor` clock cycles. **Interrupts** are the other direction of device communication: rather than the CPU polling devices in a loop, a device raises a dedicated wire when it wants attention, and the CPU suspends the program to run a handler. In this design the wiring is the RISC-V standard shape: the **CLINT** drives the core's software and timer interrupt lines, and the **PLIC** funnels device interrupts (here just the UART) into the external-interrupt line, with a claim/complete protocol replacing ad-hoc pending registers.

There is also a fact about *where this information lives* that deserves a newcomer's attention: the map is **generated**. The SoC is elaborated from parameterised Chisel generators, and the address assignments come out of the elaboration (the framework's *diplomacy* layer negotiates them); the same run emits the decode logic in the RTL, a **device tree** describing every device and its range, and per-device **register-map JSON** files. Agreement among these artifacts is claimed *by construction* — they are renderings of one elaboration — and that is precisely the kind of claim this book checks rather than assumes: the diff of the RTL's actual decode against the emitted metadata is this chapter's first deliverable, and any drift is an elaboration bug worth a finding.

## Statement

The remaining components of `Sys`: what each address means, what each device does, and which pad carries what — consolidated from the generated sources into one formal object, **diffed against the RTL** rather than trusted.

## Where the information lives today

| content | authoritative source | rendered in |
|---|---|---|
| memory map | the elaboration (diplomacy) — realised as decode logic in the generated SystemVerilog | the generated device tree (`.dts`); per-device `regmap.json` files |
| IRQ map | the elaboration — CLINT→(msip, mtip), PLIC→meip, PLIC source 1 = UART | `interrupts-extended` / `interrupt-parent` annotations in the device tree |
| pad list | `ChipTop`'s port list — 18 signals: UART pair, `custom_boot`, JTAG ×5, reset, clock in, clock tap, serial TileLink (32-bit phits + link clock) | the generated top-level module |
| pad electrical behaviour | `sky130_fd_io` (PDK) — black-box IO macros | PDK io documentation |
| boot devices | boot ROM (with its baked-in contents), boot-address register, `custom_boot` pin semantics | generated RTL + ROM image |
| serial TileLink | the bridge RTL (phit serialisation); **the far agent is outside the chip** (X4 proper) | testchipip documentation |
| UART, CLINT, PLIC | generated RTL | device tree + `regmap.json` |
| electrical envelope | — | PDK operating conditions — P6/Envelope material as prose |

The concrete map, from the generated device tree of this configuration:

| base | size | device |
|---|---|---|
| `0x0000_0000` | 4 KiB | debug module (JTAG-reached) |
| `0x0000_1000` | 4 KiB | boot-address register |
| `0x0000_3000` | 4 KiB | **error device** |
| `0x0001_0000` | 64 KiB | boot ROM |
| `0x0010_0000` | 4 KiB | clock gater |
| `0x0011_0000` | 4 KiB | tile-reset setter |
| `0x0200_0000` | 64 KiB | CLINT |
| `0x0C00_0000` | 64 MiB | PLIC |
| `0x1002_0000` | 4 KiB | UART |
| `0x8000_0000` | 16 KiB | data memory (DTIM) |

The hole semantics matter to [02](02-bus-contract.md)'s contract and are *better-behaved than most systems*: the fabric routes accesses to unmapped space to the **error device**, which answers with a TileLink denied response, and a denied response to a load raises an access fault in the core — so a stray pointer produces a precise architectural exception, not a hang or a silent `0xFFFF_FFFF`. The address-decode model must say so, and the error device is thereby a spec component, not scenery.

## The models to write

**Memory map**: an address-decode function `addr → (region, device, offset)` — extracted from the RTL's decode logic and diffed three ways against the device tree and the register maps; then cast as the formal decode component, including the error-device routing on holes, exported to [02](02-bus-contract.md)'s A5 and to L5's load/store lemmas.

**The IRQ map**: which physical event drives which line of L6/01's interrupt array — the system half of interrupts, deliberately *not* in the portable spec. The shape is standard RISC-V: CLINT compare drives `mtip`, CLINT software-interrupt register drives `msip`, and the PLIC drives `meip`, with the UART as PLIC source 1. Where an interrupt *persists* is the PLIC's gateway-and-pending machinery (level-triggered gateways, claim/complete, priority threshold) — L6/01's pending CSR is a live view — so the PLIC model is a required component of `Sys`, carrying the no-lost-interrupts half of L5/05's delivery obligation.

**UART**: the observable channel — divisor register semantics, bit-cell generation against the bus clock, transmit/receive FIFOs and watermark interrupts, the TX trace feeding [00](00-sys-and-obs.md)'s derivation stack; RX's synchroniser is L2/06's business, its byte semantics here.

**Boot machinery**: the ROM's contents as data, the boot-address register, and the `custom_boot` pin — together they determine the first fetch address and hence what "with image F" means in every end-to-end statement; the load paths (resident ROM, debug-module writes, serial-link writes) are each a spec-level way for F to arrive.

**Serial TileLink bridge**: phit serialisation and clock crossing on the chip side — the piece that turns [02](02-bus-contract.md)'s `B(config)` into a function of the link clock ratio; the far side is X4.

## Obligations

1. The RTL-vs-metadata diff for map, IRQ wiring, and the port list — re-anchoring the layer's checker to the generated artifacts; agreement is expected, and drift is a finding about the generator.
2. The five models above as components of `Sys`'s composition ([00](00-sys-and-obs.md) obligation 3) — for the map, that is the extracted table plus the error-device semantics on holes, as a formal decode function.
3. Track the elaboration-emitted map against the *hardened* netlist's decode — the elaboration is authoritative for intent, the netlist for the artifact; synthesis must not have changed the table.

## Effort

Months, wide and mechanical; the models are small individually and the consolidation *is* the deliverable.
