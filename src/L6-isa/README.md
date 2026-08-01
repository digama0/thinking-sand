# L6 — The ISA specification

> **Supplies:** `ISA = Sail-RV32I(config) ⊕ authored-IRQ ⊕ S4-choices` — the transition system L5 proves refinement against, and the core of [L7](../L7-system/README.md)'s `Sys(F)`. **Consumes:** the RISC-V standard, the shipped configuration (L4). **Kind: definition** — specification authoring, not proof; the layer where being wrong is least detectable.

## Background

An ISA — instruction set architecture — is the contract between hardware and software: the instructions, their encodings, and their exact effects on architectural state. This layer fixes that contract as a mathematical object, because L5's refinement theorem is only as meaningful as the spec it refines against. The object has three components with three different levels of trust: the officially ratified formal model of RISC-V is *imported* ([00](00-sail-base.md)); the custom interrupt machinery picorv32 substitutes for the standard's — which has no specification anywhere — must be *authored*, the most error-prone artifact in the project ([01](01-irq-spec.md)); and where the standard is deliberately loose, the choices this implementation embodies are *recorded* rather than silently assumed ([02](02-underspecification.md)). A totality sweep ([03](03-coverage.md)) then makes the spec answer for all 2³² instruction words, not just the meaningful ones.

## Statement

What L5's theorem is *stated against*: `Sail-RV32I(config) ⊕ authored-IRQ ⊕ S4-choices`, its three components carrying the three fidelity axioms — **S2** (the ratified import's small residue), **S3** (the authored IRQ spec, the sharpest surviving specification axiom), **S4** (the recorded choices). It is *not* the top of the tower — the pad-level system spec is L7's — and the boundary test is portability: **move the core to the iCEBreaker and L6 survives byte-for-byte while L7 is replaced wholesale.**

## Subcomponents

| | | status |
|---|---|---|
| [00](00-sail-base.md) | **How RISC-V is structured** (volumes, base + extension letters, formats, encoding space) and how Sail specifies it — with `addi`/`beq` worked; S2 and the import path | weeks |
| [01](01-irq-spec.md) | **S3** — the authored IRQ spec: state (incl. the spec-visible `waitirq` state L5's measure demanded), entry/return steps, the six custom instructions; the anchor methodology against circularity | months; the thinking |
| [02](02-underspecification.md) | **S4** — the choice register C1–C7: pick, record, flow down; mid-proof stalls become filing operations | days to seed; discipline thereafter |
| [03](03-coverage.md) | The encoding sweep: implemented ↔ Sail clauses, unimplemented ⟹ traps-correctly; the custom-0 and PCPI-timeout edges | months of mechanised typing |

## Interfaces

**Consumes:** the standard, `sail-riscv`, L4's configuration record (which *derives* the subset boundary), the RTL + docs + firmware as S3's anchors. **Exports:** `ISA` to L5 (refinement target) and L7 (core of `Sys`); the partition of the encoding space to L5/03; the choice register to L5's lemmas.

## Axioms introduced

**S2** (Sail faithful — small: the model is ratified; residue is community-intent plus the pinned translation path), **S3** (the authored IRQ spec is what was intended — unfalsifiable, anchored), **S4** (the recorded choices are acceptable — legislative by nature). X4 lives in L7.

## The layer's shape

Entropy sorted by kind: [00](00-sail-base.md) receives the bulk for free (ratified model, structured encoding space), [03](03-coverage.md) turns the remaining width into independent SAT-shaped typing, and the *thinking* is deliberately concentrated into two small artifacts — [01](01-irq-spec.md)'s authored spec and [02](02-underspecification.md)'s choices — because those are the two places an error is invisible downstream. The honest end statement this layer serves: not "picorv32 is correct" but *the device refines **this** specification, modulo **these** axioms* — with unbounded proof capacity the axiom list is the achievement, which is why axioms.md precedes any proof.

**The ISA is rightly silent about power**: its reset section is the power-on hook (X ⊑ reset nondeterminism), prefix-closed small-step refinement is the power-off hook; everything else power-shaped is L7's epoch model. Resist adding power events here — the layering is doing its job.

## Open problems

1. **Author S3** ([01](01-irq-spec.md)) — gates L5/05; highest-risk specification work in the project.
2. Seed and enforce the S4 register ([02](02-underspecification.md)) *before* L5's proofs start.
3. The Sail→prover translation's trust status, pinned and stated ([00](00-sail-base.md)).

## First experiments

- Import `sail-riscv`, run the compliance suite against the imported model ([00](00-sail-base.md)) — the only handle on S2.
- Draft S3 from the documentation *first*, then diff against the RTL; log every discrepancy ([01](01-irq-spec.md)).
- Generate the encoding partition from L4's record ([03](03-coverage.md)).

## Effort

6–9 months. Small in proof content, disproportionate in consequence: an error here is invisible to every layer below and produces a true theorem about the wrong machine.

## Reading

`sail-riscv` and the [Sail language papers](../bibliography.md#sail-2019). The RISC-V unprivileged spec itself — Volume I is short and readable, and [00](00-sail-base.md)'s tour is a map into it. ARM's [CHERI/Morello](../bibliography.md#morello-2022) work — the best existing example of an ISA-level property proved against a *shipping* architecture spec. picorv32's README for the custom-instruction prose S3 formalises.
