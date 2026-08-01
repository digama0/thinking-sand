# L7 — The system specification

> **Supplies:** `Sys(F)` and `obs` — the two objects [MAIN](../MAIN.md)'s top-level statement quantifies over. **Consumes:** `ISA` (L6), device datasheet models (X4). **Kind: definition** — specification authoring, not proof.

## Statement

The ISA is not the top: MAIN's statement is about **pad-level traces**, and the map from architecture to observable behaviour goes through everything the SoC wraps around the core. This layer owns that map — `Sys(F) = ISA ⊕ memory map ⊕ XIP ⊕ UART ⊕ pad configuration`, rendered as timed pad traces, and `obs` as the physical observation ([00](00-sys-and-obs.md)). The boundary test with L6: **move the core to the iCEBreaker and L6 survives byte-for-byte while this layer is replaced wholesale** — L7 is *this chip*.

## Subcomponents

| | | status |
|---|---|---|
| [00](00-sys-and-obs.md) | The two definitions; the **physical trace alphabet** (forced by epoch composition) with byte views derived | weeks; everything plugs in here |
| [01](01-boundary.md) | **B1 core → B2 SoC → B3 device** as successive theorems; X4 as a per-level dial | decision + the B3 smoke test |
| [02](02-bus-contract.md) | The bus contract: five assume-clauses and the load-bearing latency bound `B(config)`; discharged at B2 | days to author |
| [03](03-memory-map-devices.md) | Memory map, IRQ map, UART, GPIO chain, XIP wait states — five sources consolidated, **diffed against the RTL** | months, wide |
| [04](04-power-epochs.md) | Epoch composition: V8, POR, X-elimination, boot promise, F-immutability, brown-out + supervisor | composition: weeks |
| [05](05-operating-conditions.md) | The recommended-operating-conditions clause: register-reachable knobs (F6, F4, `B(config)`), X-flood semantics of "unspecified" | days; the slot matters |

## Interfaces

**Consumes:** `ISA` (L6), L4's configuration record, the SoC RTL and Caravel docs (as [03](03-memory-map-devices.md)'s raw material), X4's models per B-level. **Exports:** `Sys(F)` and `obs` to MAIN; the bus contract and `B` to L5; the configuration objects to F4/F6's resolution; the epoch requirements to the board (supervisor, sequencing).

## Axioms introduced

**X4** (device datasheet models) — a scoping dial, not a monolith: B1 needs none, B2 the on-die batch, B3 all of it; each theorem conditional on exactly its batch ([01](01-boundary.md)).

## The layer's shape

Two definitions and four consequences. [00](00-sys-and-obs.md) fixes the objects, with the alphabet choice forced from below (epochs need prefix closure, which only the physical level has). [01](01-boundary.md) fixes what the claim is about, in three widening rings. The remaining files are the composition's components: the interface half ([02](02-bus-contract.md)), the address-and-device half ([03](03-memory-map-devices.md)), time's outer structure ([04](04-power-epochs.md)), and the domain clause ([05](05-operating-conditions.md)). The recurring find of the layer: **census macro families keep receiving their formal jobs here** — `gpio_defaults_block` (boot promise), `simple_por` (epoch base), `mgmt_protect` (partial-cycling containment) — continuing the pattern that nothing on this die is decorative.

## Open problems

1. **Author the bus contract** ([02](02-bus-contract.md)) — gates L5's refinement statement; days.
2. The RTL-vs-docs diffs ([03](03-memory-map-devices.md)) — drift is the expected finding.
3. The UART framing-error decision and the rest of [00](00-sys-and-obs.md)'s derivation stack.
4. The F-immutability check and the supervisor inequalities ([04](04-power-epochs.md)).
5. Whether `simple_por` and the pad ring get behavioural models (B3) or the claim stops at B2 ([01](01-boundary.md)).

## First experiments

- Write the B1 bus contract and check it against picorv32's testbench transactions ([02](02-bus-contract.md)) — unblocks L5.
- Extract the memory map from the RTL, diff against `caravel.py` and the docs ([03](03-memory-map-devices.md)).
- **State B3 for one hello-world image** — *"with F = this 200-byte image, the UART emits 'hello' at 9600 baud"* — fully formally, even unproven: it exercises every definition in the layer and will surface each one that is missing ([01](01-boundary.md)).

## Effort

~1 year, definitional. The risk profile matches L6: errors here are invisible to every layer below and produce a true theorem about the wrong system.

## Reading

The picorv32 README's memory-interface section — the native handshake [02](02-bus-contract.md) formalises. The Caravel documentation tree ([03](03-memory-map-devices.md)'s provenance table maps it). The flash vendor datasheet for XIP mode and wait states — X4's concrete content.
