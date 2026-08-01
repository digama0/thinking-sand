# L7/01 — The boundary decision

## Background

"Verify the processor" is ambiguous in a way that matters enormously, because the thing you might mean by "the processor" comes in at least three sizes, and each size is a different theorem about a different object.

The smallest object is the **core**: picorv32 itself, a few thousand lines of Verilog describing a CPU. A core is not a chip — it is a module with named ports (a clock input, a reset input, a memory request bus), the hardware analogue of a function that has parameters but has not been called. It cannot run anything on its own; it must be instantiated inside a larger design that connects its ports to actual memory and actual pins. The middle object is the **SoC** (system-on-chip): the full Caravel design, which wraps the core together with on-chip RAM, the SPI-flash controller, the UART, the housekeeping logic, and the **pad ring** — the ring of large driver circuits around the die's edge that turn feeble internal signals into ones strong enough to drive the outside world, and protect the die from it. The SoC is the thing that was actually fabricated. The largest object is the **device**: the packaged chip soldered to a board, next to a flash chip holding the program, a voltage regulator, and a reset supervisor. Only the device is a thing you can hold, and only claims about the device are claims about a computer rather than about a description of one.

Each step outward drags more of the world into the theorem. A claim about the core can assume its memory port behaves (someone else's problem). A claim about the SoC must prove that the surrounding fabric actually delivers that behaviour — but may still assume the external flash chip works. A claim about the device must model the flash chip, the power supply, and the reset circuitry too — and for those parts, which are other people's silicon, no proof is possible even in principle: the best available model is the manufacturer's **datasheet**, the document stating what the part promises under what conditions. Datasheet-backed models are assumptions, and they are tracked in the axiom ledger under X4. The discipline this chapter establishes is that "the devices meet their datasheets" is never assumed as one blanket axiom, but in per-claim batches: each theorem names exactly which datasheets it stands on.

## Statement

The defining scoping choice of the layer: which system the claim is *about*. Three candidate statements, strictly increasing in strength and in what they drag in:

| | claim | needs | character |
|---|---|---|---|
| **B1 core** | the core module refines `ISA` at its bus interface | the bus contract only ([02](02-bus-contract.md)) | strongest per unit effort; not about a device |
| **B2 SoC** | `caravel_core` refines `ISA ⊕ memory map` | + RAM model, XIP model, housekeeping ([03](03-memory-map-devices.md)) | about the netlist that was fabricated |
| **B3 device** | *"the chip, with flash image F, produces UART output O"* | + X4 in full: flash datasheet, pad ring, POR, supervisor ([04](04-power-epochs.md)) | about a thing you can hold |

B3 is the honest end statement and the reason this project is about a computer rather than a core. The plan is **B1 → B2 → B3 as successive theorems**, each conditional on exactly its batch of X4 models — not one monolithic claim.

## X4 as a dial, not a monolith

Each B-level's theorem is conditional on precisely its batch: B1 none; B2 the on-die models (DFFRAM — openable, per L3/02 — housekeeping, the XIP controller's RTL side); B3 the off-die world (flash chip datasheet, pad-ring IO cells, `simple_por`, the board supervisor). This batching is what keeps X4 honest in Axioms: "the devices meet their datasheets" is never assumed wholesale, only per claim.

## What each step buys and costs

**B1** is where L5 lands naturally — it is the refinement theorem re-stated at the core's ports, and needs nothing from this layer except the contract. **B2** is the first statement about the *fabricated netlist*: it discharges the bus contract's assume-half against the actual fabric (the contract stops being an assumption), opens the RAM hole, and pulls in the memory map. It also inherits the partial-power-cycling obligation (`mgmt_protect` containment, [04](04-power-epochs.md)) because the user domain neighbours the management core on the die. **B3** adds the world: pads, flash, power epochs, the supervisor — and is the only level at which `obs` (physical pad traces) rather than an internal interface is the observation.

The mid-level irony worth recording: **B2 is about the artifact that was verified, B3 about the artifact that was bought.** The gap between them is exactly X4's off-die batch plus the pad ring — the part of the world no proof reaches, only datasheets and bench tests.

## Obligations

1. Fix the B-level for each publishable claim; never let a theorem's statement straddle levels implicitly.
2. The B1→B2 discharge plan for the bus contract ([02](02-bus-contract.md)).
3. The B3 instance experiment: one hello-world `F`, the claim stated fully formally ([00](00-sys-and-obs.md)'s derivation stack exercised end to end), even unproven — it will surface every missing definition in the layer.

## Effort

The decision: immediate. The B3 instance statement: days, and the highest-value definitional smoke test available.
