# L6/01 — The authored residue (S3)

## Background

Almost everything the shipped core does is covered by the ratified formal model: the base instructions, the machine-mode CSRs, trap entry and `mret` are all *imported* spec ([00](00-sail-base.md)). But no real chip sits entirely inside a standard, and the parts that poke out must have their specification **authored** — written here, by this project, with no external document to defer to. Authoring a spec for hardware you can inspect carries a well-known trap: the natural move — read the RTL, write down what it does — produces a spec that agrees with the implementation *by construction*, and a refinement proof between them verifies nothing at all; bugs get transcribed into the spec and then formally certified. The field calls this "verifying the implementation against itself," and the defence is discipline about *evidence*: gather every description of intended behaviour that is independent of the RTL — generator sources, documentation, conventions, software written against them — formalise those first, and treat every point where the RTL disagrees as a finding to adjudicate deliberately, never a detail to silently copy.

For this core the residue is mercifully small, and every piece of it is a measured fact of the [configuration record](../tools/config-record.py). The centrepiece is the **external-interrupt array**: 32 interrupt lines with a mask register and a pending register exposed as two custom CSRs (`0xBC0`/`0xFC0`), whose OR funnels into the standard external-interrupt pending bit — machinery from the [`ExternalInterruptArrayPlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/ExternalInterruptArrayPlugin.scala), outside any ratified document. Around it, three smaller residues: the standard software and timer interrupts are **never pending** (their wires are tied to zero at [instantiation](https://github.com/efabless/caravel_mgmt_soc_litex/blob/503eda0790085712ffef7f4ad8934c7daed3237f/verilog/rtl/mgmt_core.v) — a fact the spec must state, since the imported model would otherwise permit them); the **reset vector arrives from a register** (LiteX's CSR-writable reset address) rather than a constant, so the spec's reset section is parameterised where the standard expects a platform constant; and the **debug unit** ([`DebugPlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/DebugPlugin.scala)) can reach architectural state out of band — excluded from the spec by the debug-inactive conditionality (L5/04) rather than specified. One more residue arrived by measurement (F8, [03](03-coverage.md)): the decoder **accepts 4,292,609 reserved encodings** — reserved loads, reserved shift immediates, `sret` — whose execution semantics the ratified model does not cover; each family needs an authored alias row (what the word actually executes as, extracted from the decode control signals) or the refinement is false on those words.

## Statement

Author the residue: the spec fragments for exactly the behaviours outside the ratified model, composed with the Sail import as `⊕`-extensions. **S3** is the axiom that this authored fragment is what was intended — unfalsifiable in the same sense as any specification-fidelity claim, and priced in the [register](../axioms.md).

**State.** The 32-bit array-pending register and array-mask register (the two custom CSRs), read/written by the standard `csrr*` instructions like any CSR.

**Steps / invariants.**

- **Capture**: an asserted external line sets its pending bit; pending bits persist until cleared by software (the capture/clear discipline — level vs. latched — is exactly the kind of detail the RTL diff must settle, not assume).
- **The funnel**: the machine-mode external-interrupt pending bit equals `(pending ∧ mask) ≠ 0`. Interrupt *taking* is then entirely the imported spec's business (`mstatus.MIE`, `mie`, trap entry).
- **Never-pending**: the software-interrupt and timer-interrupt pending bits are constant zero.
- **Dispatch is software's problem**: all 32 lines share the one external-interrupt trap cause; the handler reads `0xFC0` to find the source. (Which device drives which line is system wiring — L7/03's map, not this spec.)

## Authoring methodology: breaking the circularity

The spec and the implementation cannot share their evidence. The anchors, in order of independence:

1. **The generator source**: the [plugin](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/ExternalInterruptArrayPlugin.scala) is ~60 lines of SpinalHDL and *is* the design intent — formalise it first, then diff the formalisation against the emitted Verilog's behaviour (a generator bug would surface as exactly that diff).
2. **The [LiteX](https://github.com/enjoy-digital/litex) interrupt conventions** and the shipped BIOS/firmware: software written against the intended semantics; the spec must make observed, working interrupt handling correct.
3. **[riscv-formal](https://github.com/YosysHQ/riscv-formal)'s VexRiscv checks**: prior art for what "an interrupt retired correctly" observably means at the RVFI boundary.

Discrepancies between anchors and RTL are *results*; choices the anchors leave open go to [02](02-underspecification.md)'s register, not improvised here.

## Obligations

1. The state + step formalisation above, as a `⊕`-extension of the Sail import.
2. The plugin-first draft, the RTL diff, and the discrepancy log (each entry an S3-fidelity data point).
3. The firmware anchor corpus (shared with L5/05).
4. The never-pending and register-reset-vector clauses, stated in the spec rather than assumed.

## Effort

Weeks, thinking-dominated — but a fraction of what a fully custom interrupt scheme would cost: the trap machinery itself is imported, and the residue is two registers, a funnel, and two tie-offs. The fidelity risk is priced in [axioms](../axioms.md) as S3 and cannot be engineered away, only anchored.
