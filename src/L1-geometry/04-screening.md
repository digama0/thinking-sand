# L1/04 — Screening and locality (M2)

## Background

Electrostatics has no built-in locality: *every* pair of conductors in the universe has a nonzero capacitance between them, however far apart. Yet every extraction tool, when computing a wire's couplings, looks only a few wire-pitches away and ignores the other forty thousand nets on the die. What makes that truncation sound cannot be "distant couplings are individually small" — the chapter's opening computation shows the sum over all distant conductors *diverges* if nothing intervenes, because the count of conductors grows faster with distance than pairwise coupling shrinks. The truncation is sound, if it is, for a different reason: **screening** — grounded metal in between *blocks* the field.

The physics is the Faraday-cage principle. A conductor held at a fixed potential terminates electric field lines: whatever field arrives on one side induces surface charge that exactly cancels its influence on the other side. A wire fully enclosed in grounded metal couples to the outside world not weakly but *not at all* — and a chip's power-distribution grid, a dense mesh of supply metal on every routing layer held at fixed voltage (that "held at" being the decap army's job, a hypothesis to be tracked, not assumed), approximates exactly such an enclosure around every signal wire. Approximates: a mesh has holes, and field leaks through them. The chapter's mathematical task is to quantify the leakage, and the tools are two classical pillars of potential theory. The **maximum principle** says a harmonic function (which the potential is, away from charges) attains its extremes on the boundary — no interior bumps — so bounding a potential on a surrounding surface bounds it everywhere beyond. **Harmonic measure** refines this into an accounting of *where* the boundary's influence comes from: the potential at a point is a weighted average over the boundary, and the weight of the holes-in-the-mesh portion is exactly the factor by which one layer of mesh attenuates the field.

The structure of the conjectured answer explains why a mesh works where a single barrier would not: one layer of holes attenuates by some fixed factor α < 1, and a distant net sits behind *many* layers in series, so the attenuation compounds **exponentially** in the number of grid cells crossed — which beats the polynomial growth in the number of distant conductors and makes the discarded sum genuinely negligible. Every capacitance number in this book — and in every industrial flow — rests on this argument existing; it is the widest-error-bar open problem in the layer, and nobody has written it down.

## Why this is the load-bearing open problem

Every practical extraction truncates: only conductors within a few tracks are considered. The justification is *not* "distant things are small". **Without screening the far-field sum diverges.**

The count of conductors at distance `d` grows polynomially (`~d` in a quasi-2D die), while unscreened coupling between two thin parallel wires decays only **logarithmically**, `C ~ 1/ln(d/a)`. So `Σ_d count(d)·C(d)` has no chance of converging. Local extraction is sound only because intervening grounded metal *screens*, and quantifying that is this document.

Everything in [03](03-capacitance-enclosures.md) is computed on a truncated window. If M2 is false, those numbers bound nothing.

## The conjecture

> Let `n` be a net, `W_d(n)` the conductors within distance `d`, and `C_d` the capacitance matrix computed with all conductors outside `W_d(n)` **grounded**. Suppose the power grid is a mesh of pitch `p` with aperture parameter `a`, held at a fixed potential, and every intervening conductor is either grounded or driven with impedance bounded by `Z_max` over the band of interest. Then there exist `K` and `α < 1`, depending only on `(p, a, ε_max/ε_min)`, with
>
> ```
> Σ_{m ∉ W_d(n)} |C(n,m) − C_d(n,m)|   ≤   K · α^{d/p}
> ```

Two features of the statement are deliberate.

**The bound is on the aggregate, not per pair.** There are ~42,000 nets; a per-pair bound `|C(n,m)| ≤ ε` would give `42000·ε`, which is not small. The sum is the object that must be controlled.

**The decay is exponential in `d/p`** — cells traversed, not distance. That is what beats the polynomial count and makes the series converge. A power law would leave convergence marginal and dependent on the exponent.

## Proof route

### Step 1 — the exact case is topological

> If a grounded conductor `G` **separates** `n` from `m` — every path from one to the other meets `G` — then `C(n,m) = 0` **exactly**.

Proof: the boundary value problem decouples. Solve inside and outside `G` independently with `G`'s Dirichlet condition; neither solution sees the other's data.

This is worth isolating because the hypothesis is **topological, not metric**, hence *combinatorially checkable* — and because it is what deliberate shielding (grounded wires alongside a critical net) buys: exactly zero, not a bound. It also gives the base case for what follows.

### Step 2 — one-cell attenuation via harmonic measure

Real grids are meshes, not solid planes, so the field leaks through apertures. Take a closed surface `S` of grounded conductor plus apertures; let `φ` be the potential from `n` with all else grounded, `φ ≤ M` on the apertures, `φ = 0` on the conductor. By the **maximum principle**, for `x` beyond `S`:

```
φ(x) ≤ M · ω(apertures, x)
```

where `ω` is the **harmonic measure** of the aperture set seen from `x`. Complete enclosure gives `ω = 0`, recovering Step 1.

**The lemma to prove is the one-cell bound**: for a periodic aperture array of pitch `p` and aperture size `a`, `ω ≤ α(a/p) < 1` at distance `≳ p` beyond the barrier. Explicit for simple geometries; the general estimate is the technical core.

### Step 3 — cascade

Between `n` and a net at distance `d` lie roughly `d/p` mesh cells **in series**. Iterating Step 2 multiplies the attenuation:

```
φ beyond k barriers ≤ α^k · φ at the source
```

by induction on `k`, each step an application of the maximum principle to the region between consecutive barriers. Converting a potential bound to a capacitance bound is then a surface integral of `ε∇φ` over the far conductor.

**Cascaded apertures are the whole mechanism.** A single aperture gives only a power law; the exponential comes from having many in series, which is exactly what a dense power mesh provides.

## Hypotheses that must be stated, not assumed

**The grid must be an equipotential over the band of interest.** The maximum-principle argument needs `φ = 0` on the shield. A wobbling shield is a *source*, not a boundary condition. This is exactly what L2's ~225,000 decaps establish — a frequency-domain impedance bound, discharged once. **So the decaps do double duty: supply integrity and shield quality**, and removing them degrades this theorem, not just the power delivery.

**Floating conductors relay rather than screen.** A conductor not held at a potential does not terminate field lines — it couples in and out, shortcutting an aperture chain and destroying the cascade. Consequence: **metal fill must be tied, not floating.** This should be a *requirement* on the design, not an option; a design with floating fill has no valid locality argument at all.

**Driven signal nets screen only partially.** A driven net is low-impedance through its driver's output resistance, which rises with frequency; digital edges carry content well above where the drivers are stiff. So "grounded" is an idealisation and the honest hypothesis carries `Z_max` over the band, which is why the conjecture states it that way.

## What follows if it holds

- The coupling graph has **support bounded by the truncation radius** — each net has O(10) neighbours instead of O(42,000). That sparsity is what makes L2's crosstalk treatment and [03](03-capacitance-enclosures.md)'s per-window solves possible at all.
- **X3 stops being an axiom.** It is currently the assumption standing in for this theorem.
- Truncation radius becomes a *derived* quantity: choose `d` so that `K·α^{d/p}` fits the margin, rather than choosing 2–3 tracks by convention.

## What follows if it fails

Local extraction is unsound, and every capacitance number in the flow — industrial as well as verified — bounds nothing. This is not a hedge: the divergence of the unscreened sum is elementary, so *something* must supply convergence, and screening is the only candidate.

## Obligations

1. **The one-cell harmonic-measure bound** — the technical core, and the piece I would treat as genuine analysis rather than engineering.
2. The cascade lemma: iterated maximum principle across successive barriers.
3. Potential bound → capacitance bound (surface integral; routine given 1–2).
4. A checkable *shielding-coverage* predicate on the layout: the design-side hypothesis that there really is grid metal interposed. Combinatorial, and it belongs with [05](05-geometric-checks.md).

## First experiments

- **Numerically test the cascade before committing.** A 2D mesh of grounded strips with a source on one side: measure attenuation per cell, check it is geometric in the number of cells, and extract an empirical `α(a/p)`. Cheap, and it either supports the exponential form or kills it early.
- Compute the shielding coverage actually present in the flow's layout between representative net pairs — is there grid metal interposed, or are there sparsely-gridded regions where the hypothesis fails locally?
- Check whether the flow's metal fill is tied or floating. If floating, the locality argument needs the harder version.

## Effort

Unknown, and the widest error bars in the project — obligation 1 could be six months or a thesis. It is also the highest-leverage single result in L1, since **everything in local extraction depends on it**.

## Reading

[Pólya & Szegő](../bibliography.md#polya-szego-1951) for capacity comparison methods. Standard potential-theory texts for harmonic measure and the maximum principle; Garnett & Marshall, *Harmonic Measure*, for the estimates Step 2 needs.
