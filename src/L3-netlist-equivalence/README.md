# L3 — Netlist ↔ RTL equivalence

> **Spec below:** `Mealy(N)` — the hardened netlist's discrete machine. **Spec above:** `⟦RTL⟧` — L4's transition system. **Kind: theorem.** Note the proof-order inversion: this theorem *consumes* L4's object, so it is proved after L4 despite sitting below it in the tower — numbering is artifact altitude, not logical dependency. (The book's top-down reading order happens to agree: L4's chapters precede these.)

## Background

Synthesis compiled the emitted RTL into the netlist the flow hardens: 51,359 standard-cell instances (drawn from 96 cell types) with mangled names and aggressively restructured logic, growing further in place-and-route as clock trees, hold buffers, and physical cells are inserted. This layer proves the compilation preserved meaning — not by trusting the tool, but by checking certificates the tool's run can be made to emit. The route: define the netlist's semantics ([00](00-netlist-object.md)), check it is electrically sane ([01](01-well-formedness.md)), delete the instances that compute nothing under explicitly licensed theorems ([02](02-licensed-deletions.md)), extract the register correspondence from the flow's own run ([03](03-register-correspondence.md)), and prove per-register-boundary equivalence by certificate, with exploratory SAT confined to where no certificate exists ([04](04-equivalence-certificates.md), [05](05-hard-cones.md)).

## Statement

There is a register correspondence `ρ` — a bijection between RTL state elements and netlist flops, up to `opt_dff`-eliminated constants and resizer cloning (its existence is exactly **F5**) — such that, after the three licensed deletions,

```
Mealy(N) / (delete PHYSICAL · collapse clock to the global tick · collapse buffers)
    is bisimilar under ρ to   ⟦RTL⟧,   from matched reset states.
```

Established by **certificates**, with exploratory SAT confined to where no certificate exists. The `N` here is the shared object of [the overview's tower](../overview.md#the-spec-tower): one parse of `ChipTop.mapped.v` (and its post-P&R successor) serves L1's LVS target, L2's STA subject, and this theorem's left-hand side.

## Subcomponents

| | | status |
|---|---|---|
| [00](00-netlist-object.md) | `N` and `Mealy(N)` — ~20-production format, ~30-line semantics, S1 derived not posited | weeks; build first |
| [01](01-well-formedness.md) | **W1–W4** — the semantics' preconditions, measured on the hardened netlist | checker to re-run |
| [02](02-licensed-deletions.md) | The physical/clock/buffer deletions, each with its licence; the SRAM macros as holes with open collateral | weeks |
| [03](03-register-correspondence.md) | ρ and **F5**; reproduce-the-synthesis as the decision procedure | **the project's first experiment** |
| [04](04-equivalence-certificates.md) | CEC by certificate: ABC's trail instrumented, NPN library verified once, LRAT residue | months |
| [05](05-hard-cones.md) | Arithmetic by width-generic template theorems, PAC demoted to trail-loss fallback; the contingency table → certificate-of-absence | template inductions: weeks |

## Interfaces

**Consumes:** the hardened netlist, RTL, `⟦·⟧` (L4), the synthesis flow, per-cell Boolean functions (L0). **Exports:** to L2, `N` with identified registers/clock/reset; to L5, the licence to reason about `⟦RTL⟧` instead of the netlist.

## Axioms introduced

**None surviving.** S1 (netlist semantics) is *derived* — per-cell Boolean shadows (L0/05) + the bridge theorem (M5) + LVS (L1) yield it as a conclusion ([00](00-netlist-object.md)) — and X1 (parser fidelity) is an ordinary verified-parser obligation; both are in [Axioms' Discharged table](../axioms.md#discharged-and-retired). **F5** (does ρ exist?) is the layer's load-bearing unknown, decidable by [03](03-register-correspondence.md)'s experiment.

## The layer's shape

Everything reduces to the register boundary. Only ports and state elements need correspondence — internal restructuring is exactly what CEC absorbs — so the RTL-to-netlist gap *is* the question "do the flops correspond?" (F5), and every other file supports answering or exploiting it: 00–01 make the two sides comparable objects, 02 shrinks the problem 13×, 04 checks the cones between corresponded registers, 05 handles the cones where checking needs a different calculus. The methodological corollary: **never reconstruct word structure from bits** — words live on the RTL side of ρ; and never compare against an independently-written model — structural similarity is what makes any of this tractable.

## Open problems

1. **F5** — run [03](03-register-correspondence.md)'s reproduction; both outcomes are results.
2. The ABC trail patch and checker ([04](04-equivalence-certificates.md)) — the cheapest site anywhere in the project for the congruence-certificate architecture.
3. The mul/div parameter check ([05](05-hard-cones.md)) — confirms the multiplier stays iterative, keeping the hard problem class away.

## First experiments

**Instrument the synthesis** ([03](03-register-correspondence.md)) — the flow is ours to re-run, so ρ is logged, not excavated. Alongside: promote W1–W4 to lemmas ([01](01-well-formedness.md)), and state the SRAM macro contracts ([02](02-licensed-deletions.md)).

## Effort

6–9 months; the most likely place for an early concrete result after L2's SDC work. Cost scales with the certificate *trail length*, not the design size.

## Reading

[Kuehlmann](../bibliography.md#kuehlmann-2002)/[Brand](../bibliography.md#brand-1993) lineage on SAT sweeping; ABC's `rewrite`/`refactor`/`resub`. [Kaufmann & Biere](../bibliography.md#kaufmann-biere-2019) on PAC certificates for multipliers. [CompCert](../bibliography.md#compcert-2009) for the verified-pass vs validated-pass calculus — they *validated* register allocation for exactly the reasons [04](04-equivalence-certificates.md) validates the rewrite trail.
