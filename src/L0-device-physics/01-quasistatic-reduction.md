# L0/01 — Quasi-static reduction

## Statement

Maxwell's equations reduce to a sequence of elliptic problems, with an error bound. This is the first abstraction step and it is where "the circuit" becomes a meaningful concept at all — before it, there are only fields.

## Why it is needed

Every downstream statement (RC enclosures, delay, Kirchhoff's laws) presupposes that propagation can be ignored and that charge and current are instantaneously related to potential. That is an *approximation*, and nobody in the flow states its error.

## The content

**The criterion is scale separation:** feature size `L ≪ λ = c/(f√ε_r)`.

At 130 nm in SiO₂ (`ε_r ≈ 3.9`), λ is roughly 1.5 m at 100 MHz and 15 mm at 10 GHz. The die is ~5 mm. So at Caravel's tens-of-MHz operating frequency the separation is five orders of magnitude and the approximation is excellent; at multi-GHz on global nets it starts to bind, which is exactly when on-chip inductance became an industry concern.

**Two sub-regimes, and only one matters here:**

- **Electroquasistatic (EQS)** — `∇×E ≈ 0`, capacitance dominates. This is the interconnect regime and the one L1 solves.
- **Magnetoquasistatic (MQS)** — inductance, current loops. Relevant for long global nets and clock distribution at high frequency. **Not local**: there is no screening argument for inductance because return paths can be distant, which is why inductance extraction is much harder than capacitance extraction — the engineering response is the *partial inductance* formalism ([Ruehli](../BIBLIOGRAPHY.md#ruehli-1974)'s PEEC; [FastHenry](../BIBLIOGRAPHY.md#kamon-tsuk-white-1994) is the reference extractor), which assigns loop-free per-segment values and recovers physical loop inductance only in closed sums. At Caravel's frequency it is negligible; that should be a stated and checked condition, not an assumption.

**What the error bound should look like.** Expand in the small parameter `L/λ` (equivalently `ωL/c`). The leading correction to the EQS solution is `O((L/λ)²)`, so a rigorous statement has the form

```
‖φ_Maxwell − φ_EQS‖ ≤ C · (L/λ)² · ‖source‖
```

with `C` depending on the geometry. **Theorems of exactly this shape exist**, on the MQS side: [Ammari–Buffa–Nédélec](../BIBLIOGRAPHY.md#ammari-buffa-nedelec-2000) justified the eddy-current approximation of Maxwell with error bounds in powers of the small parameter (SIAM J. Appl. Math. 2000), and [Raviart–Sonnendrücker](../BIBLIOGRAPHY.md#raviart-sonnendrucker-1996) did the same programme for the Darwin model (the combined EQS+MQS, radiation-free intermediate). The EQS analogue is easier and essentially folklore. What does *not* exist is the version this project needs: an **explicit, computable `C`** over realistic multi-material Lipschitz geometry, stated as a verification hypothesis rather than an asymptotic order. So the open problem is sharpening constants in a known theorem, not inventing the theorem.

**Kirchhoff's laws are consequences of this reduction, not axioms.** KCL is `∇·J = 0` integrated over a surface enclosing a node; KVL is `∇×E = 0` integrated around a loop. Both are *exact* in the quasi-static limit and carry the `O((L/λ)²)` error otherwise. This is worth stating explicitly because circuit theory is normally introduced axiomatically, and here it needs to be derived — see [04](04-lumping-composition.md).

## Status

Settled physics, standard asymptotic analysis, entirely unformalised in this context. The mathematics is a regular perturbation expansion; the work is stating it with explicit constants over realistic domains.

## Open problems

1. An explicit, geometry-dependent constant in the `O((L/λ)²)` bound — i.e. the [Ammari–Buffa–Nédélec](../BIBLIOGRAPHY.md#ammari-buffa-nedelec-2000)-style result with the constants made computable. Without it the reduction is qualitative and the error cannot be folded into the margin budget.
2. A checkable side condition for when MQS may be dropped — i.e. a bound on the inductive contribution to delay, given the design's frequency and net lengths.
3. Whether the expansion is uniform near the corner singularities of [00](00-field-problem.md), where `‖source‖` in the bound above is itself unbounded.

## First experiments

- Compute `L/λ` for the actual design: die size, longest net, clock frequency, `ε_r`. Confirm the separation is as comfortable as it appears, and record it as a checked side condition rather than folklore.
- Estimate the inductive contribution on the longest global net and the clock spine, to justify dropping MQS.

## Effort

Weeks for the statement; M6's explicit constant is the open-ended part.

## Reading

[Haus & Melcher](../BIBLIOGRAPHY.md#haus-melcher-1989), *Electromagnetic Fields and Energy* — the standard careful treatment of the EQS/MQS split. [Ammari, Buffa & Nédélec](../BIBLIOGRAPHY.md#ammari-buffa-nedelec-2000), "A justification of eddy currents model for the Maxwell equations" (SIAM J. Appl. Math. 2000). [Raviart & Sonnendrücker](../BIBLIOGRAPHY.md#raviart-sonnendrucker-1996) on the Darwin model. [Alonso Rodríguez & Valli](../BIBLIOGRAPHY.md#alonso-rodriguez-valli-2010), *Eddy Current Approximation of Maxwell Equations* — book-length treatment of the MQS side. [Ruehli](../BIBLIOGRAPHY.md#ruehli-1974) on PEEC / partial inductance; [Kamon–Tsuk–White](../BIBLIOGRAPHY.md#kamon-tsuk-white-1994) ([FastHenry](../BIBLIOGRAPHY.md#kamon-tsuk-white-1994)) for what inductance extraction actually computes. Any asymptotic-analysis text for the regular perturbation structure.
