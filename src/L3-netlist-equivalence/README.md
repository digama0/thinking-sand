# L3 — Netlist ↔ RTL equivalence

> **Spec below:** `Mealy(N)` — the shipped netlist's discrete machine. **Spec above:** `⟦RTL⟧` — L4's transition system. **Kind: theorem.** Note the proof-order inversion: this theorem *consumes* L4's object, so it is proved after L4 despite sitting below it in the tower — numbering is artifact altitude, not logical dependency. (The book's top-down reading order happens to agree: L4's chapters precede these.)

## Statement

There is a register correspondence `ρ` — a bijection between RTL state elements and netlist flops, up to `opt_dff`-eliminated constants and resizer cloning (its existence is exactly **F5**) — such that, after the three licensed deletions,

```
Mealy(N) / (delete PHYSICAL · collapse clock to the global tick · collapse buffers)
    is bisimilar under ρ to   ⟦RTL⟧,   from matched reset states.
```

Established by **certificates**, with exploratory SAT confined to where no certificate exists. The `N` here is the shared object of [MAIN's tower](../MAIN.md#the-spec-tower): one parse of `gl_caravel_core.v` serves L1's LVS target, L2's STA subject, and this theorem's left-hand side.

## Subcomponents

| | | status |
|---|---|---|
| [00](00-netlist-object.md) | `N` and `Mealy(N)` — ~20-production format, ~30-line semantics, S1 derived not posited | weeks; build first |
| [01](01-well-formedness.md) | **W1–W4** — the semantics' preconditions, measured on the shipped netlist | **done** at tool level |
| [02](02-licensed-deletions.md) | The 85.5% + 5.6% + 1.1% deletions, each with its licence; macros as holes — **DFFRAM can be opened** | weeks |
| [03](03-register-correspondence.md) | ρ and **F5**; reproduce-the-synthesis as the decision procedure | **the project's first experiment** |
| [04](04-equivalence-certificates.md) | CEC by certificate: ABC's trail instrumented, NPN library verified once, LRAT residue | months |
| [05](05-hard-cones.md) | Arithmetic by width-generic template theorems, PAC demoted to trail-loss fallback; the contingency table → certificate-of-absence | template inductions: weeks |

## Interfaces

**Consumes:** shipped netlist, RTL, `⟦·⟧` (L4), the synthesis flow, per-cell Boolean functions (L0). **Exports:** to L2, `N` with identified registers/clock/reset; to L5, the licence to reason about `⟦RTL⟧` instead of the netlist.

## Axioms introduced

**None surviving.** S1 (netlist semantics) is *derived* — per-cell Boolean shadows (L0/05) + the bridge theorem (M5) + LVS (L1) yield it as a conclusion ([00](00-netlist-object.md)) — and X1 (parser fidelity) is an ordinary verified-parser obligation; both are in [AXIOMS' Discharged table](../AXIOMS.md#discharged-and-retired). **F5** (does ρ exist?) is the layer's load-bearing unknown, decidable by [03](03-register-correspondence.md)'s experiment.

## The layer's shape

Everything reduces to the register boundary. Only ports and state elements need correspondence — internal restructuring is exactly what CEC absorbs — so the RTL-to-netlist gap *is* the question "do the flops correspond?" (F5), and every other file supports answering or exploiting it: 00–01 make the two sides comparable objects, 02 shrinks the problem 13×, 04 checks the cones between corresponded registers, 05 handles the cones where checking needs a different calculus. The methodological corollary: **never reconstruct word structure from bits** — words live on the RTL side of ρ; and never compare against an independently-written model — structural similarity is what makes any of this tractable.

## Open problems

1. **F5** — run [03](03-register-correspondence.md)'s reproduction; both outcomes are results.
2. The ABC trail patch and checker ([04](04-equivalence-certificates.md)) — the cheapest site anywhere in the project for the congruence-certificate architecture.
3. The PCPI configuration check ([05](05-hard-cones.md)) — decides whether the multiplier problem class exists here at all.

## First experiments

**Reproduce the synthesis** ([03](03-register-correspondence.md)) — before anything else in the project. Alongside: promote W1–W4 to lemmas ([01](01-well-formedness.md)), and open the DFFRAM hole ([02](02-licensed-deletions.md)) as the first test of the certificate machinery on a regular structure.

## Effort

1–2 years; the most likely place for an early concrete result after L2's SDC work. Cost scales with the certificate *trail length*, not the design size.

## Reading

[Kuehlmann](../BIBLIOGRAPHY.md#kuehlmann-2002)/[Brand](../BIBLIOGRAPHY.md#brand-1993) lineage on SAT sweeping; ABC's `rewrite`/`refactor`/`resub`. [Kaufmann & Biere](../BIBLIOGRAPHY.md#kaufmann-biere-2019) on PAC certificates for multipliers. [CompCert](../BIBLIOGRAPHY.md#compcert-2009) for the verified-pass vs validated-pass calculus — they *validated* register allocation for exactly the reasons [04](04-equivalence-certificates.md) validates the rewrite trail.
