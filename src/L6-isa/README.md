# L6 — The ISA specification

> **Supplies:** `ISA = Sail-RV32(config, incl. machine mode) ⊕ authored residue ⊕ S4-choices` — the transition system L5 proves refinement against, and the core of [L7](../L7-system/README.md)'s `Sys(F)`. **Consumes:** the RISC-V standard, the [configuration record](../tools/config-record.py) (L4/L5). **Kind: definition** — specification authoring, not proof; the layer where being wrong is least detectable.

## Background

An ISA — instruction set architecture — is the contract between hardware and software: the instructions, their encodings, and their exact effects on architectural state. This layer fixes that contract as a mathematical object, because L5's refinement theorem is only as meaningful as the spec it refines against. The object has three components with three different levels of trust: RISC-V's official formal model is *imported* — the base ISA and, because the shipped core implements the standard machine-mode trap machinery, the ratified machine-mode subset of the privileged architecture with it ([00](00-sail-base.md)); the small pieces of behaviour that live *outside* the ratified model — the core's custom external-interrupt CSRs, chiefly — must be *authored* ([01](01-irq-spec.md)); and where the standard is deliberately loose, the choices this implementation embodies are *recorded* rather than silently assumed ([02](02-underspecification.md)). A totality sweep ([03](03-coverage.md)) then makes the spec answer for all 2³² instruction words, not just the meaningful ones.

## Statement

What L5's theorem is *stated against*: `Sail-RV32(config) ⊕ authored residue ⊕ S4-choices`, its three components carrying the three fidelity axioms — **S2** (the official model's small residue, now covering the machine-mode subset as well as the base), **S3** (the authored residue: the external-interrupt array and anything else outside the ratified model), **S4** (the recorded choices). It is *not* the top of the tower — the pad-level system spec is L7's — and the boundary test is portability: the same core in a different SoC keeps this layer's spec while L7's is replaced wholesale.

## Subcomponents

| | | status |
|---|---|---|
| [00](00-sail-base.md) | **How RISC-V is structured** (volumes, base + extension letters, formats, encoding space) and how Sail specifies it — with `addi`/`beq` worked; the machine-mode subset; S2 and the import path | weeks |
| [01](01-irq-spec.md) | **S3** — the authored residue: the external-interrupt array CSRs, the never-pending standard interrupts, the debug exclusion; the anchor methodology against circularity | weeks; the thinking |
| [02](02-underspecification.md) | **S4** — the choice register: pick, record, flow down; mid-proof stalls become filing operations | days to seed; discipline thereafter |
| [03](03-coverage.md) | The encoding sweep: implemented ↔ Sail clauses, everything else ⟹ traps-correctly — for RV32I-only, "everything else" is most of the space | months of mechanised typing |

## Interfaces

**Consumes:** the standard, [`sail-riscv`](https://github.com/riscv/sail-riscv), the [configuration record](../tools/config-record.py) (which *derives* the subset boundary), the RTL + plugin sources + firmware as S3's anchors. **Exports:** `ISA` to L5 (refinement target) and L7 (core of `Sys`); the partition of the encoding space to L5/03; the choice register to L5's lemmas.

## Axioms introduced

**S2** (Sail faithful — small: the model is the standard's official golden model; residue is fidelity to the ratified manuals plus the pinned translation path — now covering the machine-mode subset too), **S3** (the authored residue is what was intended — unfalsifiable, anchored), **S4** (the recorded choices are acceptable — legislative by nature). X4 lives in L7.

## The layer's shape

Entropy sorted by kind: [00](00-sail-base.md) receives the bulk for free (official golden model, structured encoding space — and, for this core, the trap machinery too), [03](03-coverage.md) turns the remaining width into independent SAT-shaped typing, and the *thinking* is deliberately concentrated into two small artifacts — [01](01-irq-spec.md)'s authored residue and [02](02-underspecification.md)'s choices — because those are the two places an error is invisible downstream. The honest end statement this layer serves: not "the core is correct" but *the device refines **this** specification, modulo **these** axioms* — with unbounded proof capacity the axiom list is the achievement, which is why [axioms.md](../axioms.md) precedes any proof.

**The ISA is rightly silent about power**: its reset section is the power-on hook (X ⊑ reset nondeterminism), prefix-closed small-step refinement is the power-off hook; everything else power-shaped is L7's epoch model. Resist adding power events here — the layering is doing its job.

## Open problems

1. **Author the residue** ([01](01-irq-spec.md)) — gates L5/05; the highest-risk specification work left in the layer.
2. Seed and enforce the S4 register ([02](02-underspecification.md)) *before* L5's proofs start.
3. The Sail→prover translation's trust status, pinned and stated ([00](00-sail-base.md)) — now including the privileged-subset clauses.

## First experiments

- Import [`sail-riscv`](https://github.com/riscv/sail-riscv) at a pinned commit, carve the configuration's subset, and run the [architectural compliance suite](https://github.com/riscv-non-isa/riscv-arch-test) against the imported model ([00](00-sail-base.md)) — the only handle on S2.
- Draft the array residue from the [plugin source](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/ExternalInterruptArrayPlugin.scala) and [LiteX](https://github.com/enjoy-digital/litex) conventions *first*, then diff against RTL behaviour; log every discrepancy ([01](01-irq-spec.md)).
- Generate the encoding partition from the [configuration record](../tools/config-record.py) ([03](03-coverage.md)).

## Effort

6–9 months. Small in proof content, disproportionate in consequence: an error here is invisible to every layer below and produces a true theorem about the wrong machine.

## Reading

[`sail-riscv`](https://github.com/riscv/sail-riscv) and the [Sail language papers](../bibliography.md#sail-2019). The RISC-V unprivileged spec (Volume I) and the machine-mode chapters of the privileged spec (Volume II) — both short and readable, and [00](00-sail-base.md)'s tour is a map into them. ARM's [CHERI/Morello](../bibliography.md#morello-2022) work — the best existing example of an ISA-level property proved against a *shipping* architecture spec.
