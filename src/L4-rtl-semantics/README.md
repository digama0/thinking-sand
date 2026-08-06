# L4 — RTL semantics

> **Supplies:** `⟦RTL⟧` — the word-level transition system used on *both* sides of the tower: L3's right-hand side and L5's left-hand side ([the overview](../overview.md#the-spec-tower)). **Kind: definition.** Its obligations are well-definedness and adequacy — there is no refinement theorem here, and the risk profile is inverted accordingly: a wrong definition yields a true theorem about the wrong object.

## Background

Before anything can be proved about the RTL, the RTL must *mean* something. Verilog's official semantics is an event-driven simulator with deliberately loose scheduling — unusable as a proof object — so this layer defines the design's meaning directly, as a clean synchronous transition system, for exactly the subset of the language this design occupies, with membership mechanically checked rather than assumed ([00](00-elaborated-object.md), [01](01-subset.md)). The two conditions that make combinational logic actually combinational are checked in [02](02-comb-blocks.md); the treatment of unknown values and reset in [03](03-x-and-reset.md); and the question no proof can answer — whether the definition captures what the artifact really means — is made *detectable*, since it cannot be made provable, in [04](04-adequacy.md).

## Statement

A semantics for **the synthesisable subset this design actually uses** — not for Verilog: the simple synchronous semantics (two-phase non-blocking commit over an acyclic combinational pass), with the relationship to the LRM's event scheduler isolated as the scheduler-independence claim — probed by adequacy checks, stateable as a theorem. The subset is measured over the emitted design: one level-sensitive block (the clock-gate primitive), one X-idiom (23 memory-read don't-care sites), one initializer idiom, and the worst of the language's categories absent by construction.

## Subcomponents

| | | status |
|---|---|---|
| [00](00-elaborated-object.md) | `⟦·⟧ : Config → RTL → TransitionSystem`; the simple semantics; **scheduler independence** stated; the shipped configuration as part of the object | weeks |
| [01](01-subset.md) | The construct census of the emitted design; the admissible-subset move (third instance); the enforced boundary | census measured |
| [02](02-comb-blocks.md) | Completeness (latch inference — the check that *changes the circuit* if missed); RTL-level acyclicity; the clock-gate primitive carved out | days |
| [03](03-x-and-reset.md) | The two-valued strengthening, split three ways: X-elimination where the spec claims definiteness, refinement into spec nondeterminism where it doesn't, value-independence for the residue | weeks |
| [04](04-adequacy.md) | Differential simulation; **the CEC cross-check** (disagreement with Yosys is detected, not silent); the FIRRTL anchor | weeks; mostly inherited |

## Interfaces

**Consumes:** the emitted SystemVerilog design cone (~230 modules) and its FIRRTL ancestor; the elaborated configuration. **Exports:** `⟦RTL⟧` to L3 and L5; the configuration record to L6 (ISA subset) and L5; the reset/X story to L7's epoch model.

## Axioms introduced

None — a definition layer. (It once mirrored the netlist-semantics axiom S1, but S1 is now *derived* by the stack below; `⟦RTL⟧` has no such derivation, which is exactly why [04](04-adequacy.md)'s checks matter.) The mitigations: the failure mode is *detected* by the CEC cross-check and differential simulation rather than silent.

## The layer's shape

Everything here is the admissible-subset move plus its receipts. [01](01-subset.md) fixes the boundary and proves the awful constructs absent; [00](00-elaborated-object.md) gives the clean semantics that is *correct for that subset* — with scheduler independence as the honest statement of why the LRM can be ignored; [02](02-comb-blocks.md) checks the two conditions without which the semantics is undefined; [03](03-x-and-reset.md) reconciles the two-valued idealisation with physical power-up by splitting the obligation along what the spec actually claims; [04](04-adequacy.md) makes definitional error detectable. The layer stays small *because* the subset is small — which was the target-selection decision, and the census is its receipt.

## Open problems

1. Prove scheduler independence for the subset ([00](00-elaborated-object.md)) — bounded, genuine, severable from the critical path.
2. The census as an enforced regression over the synthesis file list ([01](01-subset.md)).
3. The register power-up story against the hardened netlist ([03](03-x-and-reset.md)).

## First experiments

- Extract and record the elaborated configuration (gates three other layers' scoping — cheapest high-value item in the layer).
- The completeness and RTL SCC checks ([02](02-comb-blocks.md)) — an afternoon each, and both are hard failures the front end should enforce thereafter.
- The differential harness on the design's own testbenches ([04](04-adequacy.md)).

## Effort

3–6 months. The smallest layer, and unusually well-bounded because the scope was measured rather than assumed; the only cost beyond the subcomponent sum is the elaborator front end, shared with X1's parser work.

## Reading

[Lööw](../bibliography.md#loow-2021)'s HOL4 Verilog semantics — the existing deep embedding, and the reference point for how much of the language one actually needs. The FIRRTL spec — the IR the design actually descends through, and the layer's long-term anchor ([04](04-adequacy.md)).
