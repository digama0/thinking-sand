# L1/01 — Topology preservation (the sandwich theorem)

## Why this one first

It is the only major L1 result that is *self-contained computational geometry* — no PDEs, no Sobolev spaces, no empirical models — and it is what licenses the entire geometric verification flow: **run LVS and DRC on the drawn layout, conclude about the fabricated one.** Every EDA flow relies on that inference and none states it.

Writing it precisely turned up a missing hypothesis. See [the island problem](#the-island-problem).

## Notation

Minkowski operations on `X ⊆ ℝ³`, with `B_r` the closed ball:

```
erosion    X ⊖ B_r = { x : B(x,r) ⊆ X }
dilation   X ⊕ B_r = ⋃_{x∈X} B(x,r)
```

Two facts do the work. **Dilation distributes over unions**, `(⋃Xᵢ) ⊕ B_r = ⋃(Xᵢ ⊕ B_r)` — this drives separation. **Erosion does not**; it distributes over intersections — which is exactly why connectivity is a hypothesis and not a consequence.

## The perturbation model

`D` drawn ([00](00-layout-object.md)), `A` as-fabricated. Per mask `m`: a rigid overlay displacement `d_m` and a radius `r_m = bias_m(density) + k·σ_m`.

```
(P)   ∀m:   (D_m ⊕ d_m) ⊖ B_{r_m}  ⊆  A_m  ⊆  (D_m ⊕ d_m) ⊕ B_{r_m}
```

Write `r = max_m r_m` and let `Cond(·)` be the conductive subset of the induced material distribution, so (P) lifts to `Cond(D) ⊖ B_r ⊆ Cond(A) ⊆ Cond(D) ⊕ B_r`.

## Theorem

> Let `N₁,…,N_k` be the connected components (nets) of `Cond(D)`. Assume
>
> - **(H1)** ∀i: `Nᵢ ⊖ B_r` is **nonempty and connected**
> - **(H2)** ∀i≠j: `dist(Nᵢ, Nⱼ) > rᵢ + rⱼ + |d_{m(i)} − d_{m(j)}|`
> - **(H3)** every connected component of `Cond(A)` meets `Cond(D) ⊖ B_r`
>
> Then for every `A` satisfying (P) there is a **bijection** `ν` from nets of `Cond(D)` to nets of `Cond(A)` with `Nᵢ ⊖ B_r ⊆ ν(Nᵢ) ⊆ Nᵢ ⊕ B_r`, and `ν` preserves incidence with device terminals.

### Proof

1. By (H2) the dilations `Nᵢ ⊕ B_r` are pairwise disjoint.
2. `Cond(A) ⊆ Cond(D) ⊕ B_r = ⋃ᵢ(Nᵢ ⊕ B_r)` by distributivity. Since the parts are disjoint, **every connected component of `Cond(A)` lies wholly inside exactly one** `Nᵢ ⊕ B_r`.
3. By (H1), `Nᵢ ⊖ B_r` is nonempty, connected, and contained in `Cond(A)`; so it lies in a single component, call it `ν(Nᵢ)`, and by 2 that component is inside `Nᵢ ⊕ B_r`.
4. *Injective*: distinct `i` give components in disjoint dilations.
5. *Surjective*: by (H3) each component of `Cond(A)` meets some `Nⱼ ⊖ B_r`; by 2 it lies in a unique `Nᵢ ⊕ B_r`; disjointness forces `i = j`; so it is `ν(Nⱼ)`. ∎

### The island problem

**Without (H3) the theorem is false.** Steps 1–4 go through and give an injection, but not a surjection: `A` may contain a component sitting inside `Nᵢ ⊕ B_r \ (Nᵢ ⊖ B_r)` — a sliver of spurious material — which is a *net that does not exist in the drawn layout*. The sandwich (P) does not forbid it, because it constrains only containment, not the boundary's shape.

Two ways to repair, and the choice matters:

- **(i) Assume (H3).** Clean, and honest about what it is: a claim that the process does not create spurious material. **It is not checkable** — it quantifies over `A`, which you do not have. So it belongs to **E7**, and this is a genuine sharpening of E7's content.
- **(ii) Strengthen (P) to an edge-displacement model** — `∂A` is a graph over `∂D`, each boundary point moved along the normal by ≤ r. This *implies* (H3) and is physically the right model (etch and litho move edges; they do not nucleate islands). Cost: it needs a normal field, hence regularity of `∂D`, which polygons with corners do not have without care.

Recommendation: take (i), and cite (ii) as the physical reason (i) is true.

**No dual hypothesis is needed for voids.** A spurious hole cannot disconnect `ν(Nᵢ)`, because `ν(Nᵢ) ⊇ Nᵢ ⊖ B_r`, which (H1) already makes connected. The asymmetry is real: extra material creates nets, missing material cannot destroy them.

## Which DRC rules are which hypothesis

Sharper than the README's earlier claim that "min-width and min-spacing are precisely (a) and (b)":

| hypothesis | rule | relationship |
|---|---|---|
| (H2) | min spacing, **colour-aware** | rules **⟺** hypothesis, essentially exactly |
| (H1) | min width | **necessary, not sufficient** |
| (H1) | notch / neck rules | supply the missing part |
| (H3) | — | **no rule; it is an assumption (E7)** |

**(H1) is not min-width.** Erosion of a connected set need not be connected — a dumbbell erodes to two blobs. Min-width `w > 2r` makes the erosion locally nonempty; it does *not* keep it connected across a neck. Notch and neck rules are exactly the missing content, and this is the precise sense in which they are load-bearing rather than cosmetic.

**(H2) explains colour-awareness for free.** The overlay term is `|d_{m(i)} − d_{m(j)}|`, which **vanishes when the two features share a mask** — same-mask features move together. Different-mask pairs need the full overlay budget. That is precisely why multiple-patterning decks carry colour-aware spacing rules, and here it falls out of the statement rather than being a separate convention.

## Checkability

| | on the drawn layout? | cost |
|---|---|---|
| (H1) | **yes** — erode per net, test connectivity | polygon morphology + union-find, near-linear with a scanline |
| (H2) | **yes** — min-distance between distinct nets, colour-aware | near-linear |
| (H3) | **no** — a claim about `A` | assumption → E7 |

So the theorem has two checkable hypotheses and one assumed one, and it is worth stating in exactly that form: *conditional on E7, geometric checking on `D` is sound for `A`.*

## Caveats

**Vias are not covered, and they are where the failures are.** The theorem is 3D so vias participate in `Cond`, but the perturbation model (P) is an *in-plane* edge displacement. A via failure is a fill/void phenomenon in `z` — not an edge moving — so it is outside (P) entirely. Incomplete via fill is the dominant open mechanism in real chips. **A separate model for vias is the largest gap in this document.**

**`r` is not a constant.** Etch bias depends on local pattern density (loading), so `r = r(x)`. The theorem is unaffected — take `r` pointwise and the containments still hold — but the *checks* must use the local value, which means the density computation feeds the DRC check rather than sitting beside it.

**Line-end pullback and corner rounding are systematic and directional**, not captured by an isotropic ball. They are why enclosure rules exist, and a faithful model needs a structuring element that is not a ball. The theorem generalises to any convex structuring element without change; the checks get more expensive.

## What it buys

Composed with [02](02-extraction-lvs.md):

```
LVS(D) ≅ intended    ∧    (H1) ∧ (H2) on D    ∧    E7 ⊨ (H3)
  ⟹   LVS(A) ≅ intended
```

That is the soundness of running LVS on drawn geometry — the inference the whole flow makes silently, now with its hypotheses named and two of the three mechanically checkable.

## First experiments

- Implement (H1) and (H2) on `data/pdk/inv_1.gds` with a plausible `r`. One cell, small, and it exercises the whole pipeline: flatten, derive, erode, component-test.
- Then a row of abutted cells, to exercise the merging lemma (L1/00 O1) — recall `inv_1`'s nwell and implants **overhang** the cell boundary by design, so a row's colouring is not the disjoint union of its cells'.
- Check whether SKY130's published notch/neck rules are strong enough to give (H1), or only min-width. If only min-width, (H1) has a gap in the deck itself — which would be a real finding.

## Effort

**The most tractable substantial result in L1**: months, not years, and it needs no analysis. If one piece of the layer is formalised first, this is it.

## Reading

Serra, *Image Analysis and Mathematical Morphology*, for the Minkowski calculus. [Grisvard](../BIBLIOGRAPHY.md#grisvard-1985) for what corner geometry does to the regularity that route (ii) would need.
