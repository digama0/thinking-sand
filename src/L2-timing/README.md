# L2 — Timing and the synchronous abstraction

> **Spec below:** `Contracts(N)` — the timed contract network (L0 + L1). **Spec above:** `Mealy(N)` — the discrete machine ([MAIN](../MAIN.md#the-spec-tower)). **Kind: theorem** (M5), carrying one of the two † conditioning marks in MAIN's chain.

## Statement

**The bridge theorem.** If every cell stays inside its contract's domain, STA certifies setup and hold at every flop at every corner, every excluded path carries a justified exception, and no fault event or unresolved synchroniser read occurs in `[0,T]` — then over `[0,T]` the physical circuit implements `Mealy(N)`. Full statement and proof sketch in [01](01-bridge-theorem.md); hypotheses (1) and (2) are **currently false for the shipped design** (F2, F1) and hypothesis (3) is unverified (F3, F4).

Everything above L2 presupposes this and nobody has written it down. It is the highest value-per-effort novel contribution in the project.

## Subcomponents

| | | status |
|---|---|---|
| [00](00-timed-model.md) | The timed model — bounded-delay semantics of `Contracts(N)`, the flop window rule, the metastability escape hatch | scaffolding; everything types against it |
| [01](01-bridge-theorem.md) | **The bridge theorem (M5)** — statement, per-cycle induction, where the shape breaks | the centrepiece; a paper, not a decade |
| [02](02-verified-sta.md) | Verified STA — the soundness statement, and three places standard practice is subtly unsound | ordinary verified-algorithm work |
| [03](03-corners.md) | Corners and correlation (**M4**) — when finitely many parameter assignments bound the continuum | open: production data violates the premise |
| [04](04-sdc-exceptions.md) | SDC exceptions — four claim classes, four discharge methods; F1–F4 live here | **the project's entry point — weeks** |
| [05](05-clock.md) | The clock — X5's minimal excision, jitter (M8), CTS as an active participant, the arrival function | checks are weeks; the contract proof is L0's |
| [06](06-boundaries.md) | Boundaries — the ladder of clock relationships; synchronisers; multi-domain composition; the P1 ledger | records what was previously only discussed |
| [07](07-crosstalk-power.md) | Crosstalk and the power grid — both absorbed at this layer, and the red line that keeps them absorbed | design-conditional; feasible at 130 nm |

## Interfaces

**Consumes:** `Contracts(N)` — RC enclosures + coupling graph (L1), interval Liberty contracts (L0/03; the shipped `.lib` is a cross-check oracle after E2's discharge), the netlist with registers/clock identified (L3), SDC. **Exports:** *the licence to reason discretely* — for the multi-domain design, a network of Mealy machines with gadget-bounded channels ([06](06-boundaries.md)) that collapses to nearly one machine here. Nothing numeric propagates upward, plus one outward artifact: the derived AC-timing table handed to L7.

## Axioms introduced

**P1** (synchronisers resolve — the per-boundary ledger is [06](06-boundaries.md)'s), **P6** (environment), **X5** (PLL limit cycle — [05](05-clock.md)). Formerly also E4 (split: empirical half → P4, mathematical half → M4) and E5 (subsumed by E2's and E3's discharge routes); see [AXIOMS](../AXIOMS.md#discharged-and-retired). Findings F1–F4 are *unestablished hypotheses of the bridge theorem*, not axioms.

## The recurring structure, seen from this layer

Three of the project's global patterns surface here in their sharpest forms. The clock edge is a **restoration point in time** — the induction invariant is fully re-established every cycle, so nothing accumulates ([01](01-bridge-theorem.md)). The boundary gadgets are **phase restorers** — the window hypothesis is manufactured on-die, never imposed on the world ([06](06-boundaries.md)). And the analog residue is confined to **single entry points**: the power grid enters once as an impedance bound, coupling enters once as an interval widening plus a geometric rule ([07](07-crosstalk-power.md)) — with the red line that any net needing a *functional* coupling constraint is a layout bug, because it would entangle the noise argument with L5's invariant.

## Open problems

1. **Write the bridge theorem** ([01](01-bridge-theorem.md)) — bounded-delay model, window rule, per-cycle induction, multi-domain composition ([06](06-boundaries.md)).
2. **A verified STA engine** with the three soundness deviations ([02](02-verified-sta.md)): four-corner interpolation, slew intervals, in-pass domain checks.
3. **Prove the 159 SDC exceptions** rather than asserting them ([04](04-sdc-exceptions.md)).
4. **The monotonicity census and the tier model** ([03](03-corners.md)) — decides whether M4 is a footnote or a project.

## First experiments

**This layer holds the whole project's tractable entry point** — [04](04-sdc-exceptions.md)'s work plan: elaborate the Tcl, classify the 159, discharge per class, and close F1 by mapping every failing hold path to a justified exception. Weeks to months, needs only artifacts already in `data/`, and either outcome is worth having.

Alongside it, two mechanical censuses that other files consume: library-wide table monotonicity ([02](02-verified-sta.md)/[03](03-corners.md)) and the clock-network cleanliness check ([05](05-clock.md)).

## Effort

1–1.5 years for the layer; the entry-point experiments are weeks. The theory is concentrated in 01 + 06; the rest is verified-algorithm work and measurement.

## Reading

[Lööw](../BIBLIOGRAPHY.md#loow-2021)'s HOL4 Verilog semantics and the Silver/Lutsig stack — closest prior art for a verified path from RTL to netlist; note it stops short of the bridge statement. Standard STA texts for the algorithm — none state the soundness bridge. McGeer & Brayton for the false-path/viability criterion ([04](04-sdc-exceptions.md)). [Zgliczyński](../BIBLIOGRAPHY.md#zgliczynski-1997), [Galias](../BIBLIOGRAPHY.md#galias-2001), [Demir–Mehrotra–Roychowdhury](../BIBLIOGRAPHY.md#demir-mehrotra-roychowdhury-2000) for [05](05-clock.md)'s oscillator contract; [Marino](../BIBLIOGRAPHY.md#marino-1981) for why [06](06-boundaries.md)'s ε is irreducible.
