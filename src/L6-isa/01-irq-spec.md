# L6/01 — The authored residue (S3)

## Background

Almost everything the core does is covered by the ratified formal model: the base instructions, the M/A/C extensions, the machine-mode CSRs, trap entry and `mret` are all *imported* spec ([00](00-sail-base.md)). But no real chip sits entirely inside a standard, and the parts that poke out must have their specification **authored** — written here, by this project, with no external document to defer to. Authoring a spec for hardware you can inspect carries a well-known trap: the natural move — read the RTL, write down what it does — produces a spec that agrees with the implementation *by construction*, and a refinement proof between them verifies nothing at all; bugs get transcribed into the spec and then formally certified. The field calls this "verifying the implementation against itself," and the defence is discipline about *evidence*: gather every description of intended behaviour that is independent of the RTL — generator sources, documentation, conventions, software written against them — formalise those first, and treat every point where the RTL disagrees as a finding to adjudicate deliberately, never a detail to silently copy.

For this core the residue is smaller than a custom design would carry, and its members are declared rather than hidden: the ISA string the elaboration emits — `rv32imac_zicsr_zifencei_zihpm_xrocket` — ends with a **custom extension marker**, and that `x` is precisely where the authored spec lives. Around it, the residue inventory:

- **The `xrocket` fragment.** The generated core carries implementation-control state outside any ratified document — custom CSRs of the "chicken bit" family (feature-disable and implementation-control registers) and any custom instructions the generator emits. The first obligation is an *enumeration*: diff the RTL's CSR and instruction decode against the ratified set; every hit is residue to author, from the generator source first.
- **The performance-counter event space (Zihpm).** The counters themselves are ratified; *which event each selector value counts* is implementation-defined by the standard — an authored table, extracted from the generator's event wiring.
- **The debug module** (RISC-V Debug specification, v0.13 family) can reach architectural state out of band. Its own register model is imported from the debug spec — a de-facto-standard document rather than the ISA manuals — and it is excluded from `ISA` proper by the debug-inactive conditionality (L5/04) rather than specified here.
- **Interrupt sources are *not* residue** — a genuine simplification worth recording. The software, timer, and external interrupt pending bits are all live and all standard; what drives them (CLINT compare, CLINT software-interrupt register, PLIC claim/complete) is device behaviour behind the memory map, specified as L7/03's models. The core-side interrupt spec is imported intact, and dispatch beyond `mcause`'s external-interrupt code is software's business via the PLIC.
- **The reset vector is a constant** (the boot ROM's entry), matching the standard's platform-constant expectation — the software-visible "boot address" indirection is an ordinary device register (L7/03), not a parameterisation of the spec's reset section.

The `⊕`-extension mechanism must still support **override**, not just extension: wherever measurement shows the implementation deviating from the imported model's ratified behaviour, the spec must either record the deviation explicitly as an override (making it S3-authored content with its own evidence trail) or treat it as a bug to fix upstream. No such deviations are currently pinned for this core — the ratified trap surface (access faults from denied bus responses included, misaligned loads and stores trapping, `ebreak` raising cause 3) is the *expected* answer — but "expected" is exactly what the diff exists to check, and the deviation log starts empty rather than assumed empty.

## Statement

Author the residue: the spec fragments for exactly the behaviours outside the ratified model, composed with the Sail import as `⊕`-extensions (with override capability). **S3** is the axiom that this authored fragment is what was intended — unfalsifiable in the same sense as any specification-fidelity claim, and priced in the [register](../axioms.md).

**State.** The custom-CSR file of the `xrocket` fragment (enumerated, then specified register by register) and the Zihpm event-selector table.

**Steps / invariants** — the discipline the RTL diff must settle rather than assume:

- Custom CSR accesses obey the standard CSR access rules (privilege, read/write legality) with the authored per-register semantics.
- Implementation-control CSRs may change *performance*, never *architecture*: the authored spec must say explicitly that every reachable setting preserves the refinement (or name the settings that do not, which then become operating-conditions rows — L7/05).
- The event-selector table is total over the selector values software can write, with unmapped selectors counting nothing.

## Authoring methodology: breaking the circularity

The spec and the implementation cannot share their evidence. The anchors, in order of independence:

1. **The generator source**: the Chisel CSR file and decode are the design intent — formalise the custom fragment from them first, then diff the formalisation against the emitted SystemVerilog's behaviour (a generator bug would surface as exactly that diff).
2. **The ecosystem's software**: the standard test suites and the framework's own bring-up code are written against the intended semantics; the spec must make observed, working behaviour correct.
3. **RVFI-style retirement checking** ([riscv-formal](https://github.com/YosysHQ/riscv-formal)'s discipline): prior art for what "an instruction retired correctly" observably means at a trace interface, applicable to the custom fragment as much as the base.

Discrepancies between anchors and RTL are *results*; choices the anchors leave open go to [02](02-underspecification.md)'s register, not improvised here.

## Obligations

1. The enumeration: every CSR address and instruction encoding the decode accepts beyond the ratified set, from the RTL, mechanically.
2. The generator-first draft of the custom fragment, the RTL diff, and the discrepancy log (each entry an S3-fidelity data point).
3. The Zihpm event table, extracted and stated.
4. The deviation log for the imported model — expected empty, checked not assumed.

## Effort

Weeks, thinking-dominated — and less than a custom interrupt scheme would cost: the trap machinery, all three standard interrupts, and the debug register model are imported; what is left is an enumeration, a table, and however many custom control registers the enumeration finds. The fidelity risk is priced in [axioms](../axioms.md) as S3 and cannot be engineered away, only anchored.
