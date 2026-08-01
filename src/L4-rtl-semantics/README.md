# L4 — RTL semantics

> **Supplies:** `⟦RTL⟧` — the word-level transition system used on *both* sides of the tower: L3's right-hand side and L5's left-hand side ([MAIN](../MAIN.md#the-spec-tower)). **Kind: definition.** Its obligations are well-definedness and adequacy — there is no refinement theorem here, and the risk profile is inverted accordingly: a wrong definition yields a true theorem about the wrong object.

## Statement

A semantics for **the synthesisable subset this design actually uses** — not for Verilog. Defined directly as a simple synchronous semantics (two-phase non-blocking commit over an acyclic combinational pass), *not* via the LRM's event scheduler; the relationship to the LRM is the scheduler-independence claim, probed by adequacy checks and stateable as a theorem. The subset is measured: 19 sites needing care, and the categories that make Verilog semantics awful are absent.

## Subcomponents

| | | status |
|---|---|---|
| [00](00-elaborated-object.md) | `⟦·⟧ : Config → RTL → TransitionSystem`; the simple semantics; **scheduler independence** stated; the shipped configuration as part of the object | weeks |
| [01](01-subset.md) | The 19-site census; the admissible-subset move (third instance); the enforced boundary | days — census done |
| [02](02-comb-blocks.md) | Completeness of the 15 `always @*` blocks (latch inference — the check that *changes the circuit* if missed); RTL-level acyclicity; the 2-block blocking-assignment rewrite | days |
| [03](03-x-and-reset.md) | The two-valued strengthening, split three ways: X-elimination where the spec claims definiteness, refinement into spec nondeterminism where it doesn't, value-independence for the residue | weeks |
| [04](04-adequacy.md) | Differential simulation; **the CEC cross-check** (disagreement with Yosys is detected, not silent); the FIRRTL counterfactual | weeks; mostly inherited |

## Interfaces

**Consumes:** `picorv32.v` (3,044 lines) and the surrounding SoC RTL; the shipped configuration. **Exports:** `⟦RTL⟧` to L3 and L5; the configuration record to L3/05 (PCPI existence), L6 (ISA subset), and L5; the reset/X story to L7's epoch model.

## Axioms introduced

None — a definition layer. (It once mirrored the netlist-semantics axiom S1, but S1 is now *derived* by the stack below; `⟦RTL⟧` has no such derivation, which is exactly why [04](04-adequacy.md)'s checks matter.) The mitigations: the failure mode is *detected* by the CEC cross-check and differential simulation rather than silent.

## The layer's shape

Everything here is the admissible-subset move plus its receipts. [01](01-subset.md) fixes the boundary and proves the awful constructs absent; [00](00-elaborated-object.md) gives the clean semantics that is *correct for that subset* — with scheduler independence as the honest statement of why the LRM can be ignored; [02](02-comb-blocks.md) checks the two conditions without which the semantics is undefined; [03](03-x-and-reset.md) reconciles the two-valued idealisation with physical power-up by splitting the obligation along what the spec actually claims; [04](04-adequacy.md) makes definitional error detectable. The layer stays small *because* the subset is small — which was the target-selection decision, and the census is its receipt.

## Open problems

1. Prove scheduler independence for the subset ([00](00-elaborated-object.md)) — bounded, genuine, severable from the critical path.
2. The SoC-level census sweep ([01](01-subset.md)) — the 19-site figure is core-only.
3. Resolve the one `initial` site against the shipped netlist ([03](03-x-and-reset.md)).

## First experiments

- Extract and record the shipped configuration (gates three other layers' scoping — cheapest high-value item in the layer).
- The 15 completeness checks and the RTL SCC check ([02](02-comb-blocks.md)) — an afternoon each, and both are hard failures the front end should enforce thereafter.
- The differential harness on the design's own testbenches ([04](04-adequacy.md)).

## Effort

~1 year. The smallest layer, and unusually well-bounded because the scope was measured rather than assumed.

## Reading

[Lööw](../BIBLIOGRAPHY.md#loow-2021)'s HOL4 Verilog semantics — the existing deep embedding, and the reference point for how much of the language one actually needs. The FIRRTL spec, for what the alternative architecture would have looked like ([04](04-adequacy.md)).
