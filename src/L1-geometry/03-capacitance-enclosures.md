# L1/03 — Capacitance enclosures

## Background

Timing needs numbers out of the geometry: every wire's delay is set by its resistance and its **capacitance** — the amount of charge that must be moved to swing its voltage, determined by the wire's shape and its proximity to every neighbouring conductor. Computing capacitance is a problem in electrostatics: the electric potential in the insulating material between conductors obeys a partial differential equation (Laplace's, generalised for varying dielectrics), with the conductors imposing boundary values, and the capacitance matrix is read off from the resulting field's energy. Industrial extraction tools do not solve this PDE per wire — they pattern-match against a precomputed library of solved geometries — and their accuracy target is a few percent. This chapter asks for something different in kind: not better accuracy, but *certified bounds* — numbers with a proof that the truth lies between them — and its opening observation is that the accuracy bar for certified bounds is unusually low here, because the timing flow already tolerates 10–20% margins. Crude-but-rigorous is enough, which is rarely true in verified numerics.

The classical route to two-sided bounds is a pair of **variational principles**, and the intuition is worth having. The true potential field is the *laziest* one — among all fields matching the boundary voltages, it minimises stored energy (the **Dirichlet principle**). So take *any* trial field satisfying the boundary conditions, compute its energy, and you have provably overshot: an upper bound, no PDE solved. The complementary (**Thomson**) principle runs the same trick from the dual side — any divergence-free trial *flux* gives a provable undershoot. Squeeze the truth between a decent trial of each kind, and the gap between your bounds even tells you how good your trials were. The trials in practice come from the **finite element method** (FEM — carve the domain into small cells, approximate the field by simple polynomials per cell, solve the resulting linear system), run once and post-processed into both a valid trial field and a valid trial flux; the machinery for the second half ("equilibrated flux reconstruction") exists off the shelf in the numerical-analysis literature, with computable constants.

Two honest difficulties shape the rest of the chapter. Where a conductor has a sharp corner, the true field *diverges* (integrably — like `r^(−1/3)` at a right angle), and rigorous integration must handle that known singularity rather than stepping in it. And the object actually needed is not the capacitance of *the* geometry but bounds valid across the whole family of geometries the fab might print — [01](01-topology-preservation.md)'s sandwich — which turns out to cost nothing extra, by choosing the trial fields once for the whole family. The heavy cost sits elsewhere, and the chapter is frank about it: the functional-analysis machinery (Sobolev spaces, the well-posedness theory) that everything rests on is beyond what today's proof-assistant libraries provide, and formalising it is the single largest cost in L1.

## Statement

Replace the pattern-matched extraction deck (E3) with **rigorous two-sided bounds** on the capacitance matrix, valid over the whole as-fabricated geometry family.

The viability argument, stated up front because it is unusual: the accuracy requirement is **soft**. Industrial extraction targets ~5% against a field solver, and the flow already carries 10–20% in derates and OCV margin. So *crude but rigorous* bounds are enough — unlike most verified-numerics applications, where loose bounds are useless.

## Setup

`Ω ⊆ ℝ³` bounded; disjoint closed conductors `K₀` (ground), `K₁,…,K_n`; dielectric `Ω_d = Ω ∖ ⋃Kᵢ`; permittivity `ε ∈ L^∞`, `0 < ε_min ≤ ε ≤ ε_max` (bounded measurable — dielectric jumps are fine).

For `V ∈ ℝⁿ`, let `φ_V ∈ H¹(Ω_d)` solve

```
∇·(ε∇φ) = 0  in Ω_d,     φ = Vᵢ on ∂Kᵢ,     φ = 0 on ∂K₀
```

Existence and uniqueness are Lax–Milgram — classical, see [L0/00](../L0-device-physics/00-field-problem.md). The energy `E(V) = ½∫_{Ω_d} ε|∇φ_V|²` is a positive quadratic form, and

```
E(V) = ½ Vᵀ C V     defines the capacitance matrix C.
```

**The existence theorem is what makes `C` a well-defined object at all** — no well-posedness, no capacitance matrix, no RC enclosures, nothing above.

## Theorem (two-sided enclosure)

> For any **admissible potential** `u ∈ H¹(Ω_d)` with `u = Vᵢ` on `∂Kᵢ`, `u = 0` on `∂K₀`, and any **admissible flux** `j ∈ H(div, Ω_d)` with `∇·j = 0`, writing `Qᵢ(j) = ∮_{∂Kᵢ} j·n`:
>
> ```
> Σᵢ Vᵢ Qᵢ(j) − ½∫ |j|²/ε   ≤   E(V)   ≤   ½∫ ε|∇u|²
> ```
>
> Both bounds are attained simultaneously iff `j = ε∇φ_V` and `u = φ_V`.

Evaluating at a basis of `V` and polarising gives a bracket on `C` in the **Loewner order**: `C_lo ⪯ C ⪯ C_hi`.

### Proof hints

Convex duality. The upper bound is the **Dirichlet principle**: `φ_V` minimises the energy over the admissible affine set, so any trial `u` overestimates. The lower bound is the **complementary (Thomson) principle**, the Fenchel dual, with `∇·j = 0` as the constraint dualising the Dirichlet condition. The gap between the two *is* the duality gap, which is zero at the solution — so the bracket tightens automatically as the trial fields improve, with no separate convergence argument.

### The practical route: one FEM solve gives both sides

The upper bound is easy — any conforming FEM solution is an admissible `u`. The lower bound needs a *divergence-free* `j`, which a raw FEM gradient is not.

**Equilibrated flux reconstruction** ([Ern–Vohralík](../BIBLIOGRAPHY.md#ern-vohralik-2015)) is built for exactly this: it post-processes a FEM solution into a certified `H(div)`-conforming, divergence-free flux, with fully computable constants and no unknown interpolation factors. So a single solve yields both an admissible `u` and an admissible `j`, hence the bracket.

This is the concrete answer to "how would this actually be computed", and it is why the lower bound — usually the hard half — is not an obstacle.

## Corollary: bounds over the geometry family

The theorem is for one geometry; what is needed is a bracket valid for **every** `A` in [01](01-topology-preservation.md)'s sandwich. Both trial fields can be chosen family-uniformly:

- **`u`**: set `u ≡ Vᵢ` on the *dilated* conductor `Kᵢ ⊕ B_r`. Since `Aᵢ ⊆ Kᵢ ⊕ B_r`, this `u` satisfies the boundary condition for every member of the family. Well-defined precisely because the dilations are **disjoint — which is hypothesis (H2)**.
- **`j`**: `∇·j = 0` means the flux through any surface enclosing `Kᵢ(A)` is the same, so `Qᵢ(j)` is independent of which `A` in the family is meant, provided `j` is divergence-free throughout the annulus `(Kᵢ ⊕ B_r) ∖ (Kᵢ ⊖ B_r)`.

So the enclosure over the family costs nothing extra, and **(H2) is doing double duty** — it separates nets in 01 and it makes the uniform trial potential constructible here. Worth noting as a real dependency between the two documents rather than a coincidence.

This also means the right object was never a point geometry: "∀ geometries within tolerance, `C ∈ [lo,hi]`" is *more* faithful to the physics than the point-geometry field solve it replaces, since as-fabricated ≠ drawn regardless.

## The obstacle: corner singularities

`∇φ` diverges like `r^(−1/3)` at a right-angle conductor corner — precisely where the capacitance concentrates. Consequences:

- Total energy is **finite** (`|∇φ|² ~ r^(−2/3)`, and `∫r^(−2/3)·r dr` converges near an edge), so the variational framework is intact; `φ ∈ H¹` regardless.
- But convergence *rates* degrade, and verified quadrature must handle **integrable singularities of known exponent**. The exponents are analytic ([Grisvard](../BIBLIOGRAPHY.md#grisvard-1985)), so graded meshes or singular enrichment work. Engineering, not research — but it must be done, because the naive quadrature bound is infinite exactly where the answer lives.

## A cheaper decomposition: 2D may be exact

Much of extraction reduces to 2D cross-sections with 3D corrections. For 2D multiconductor configurations with piecewise-linear boundaries, **Schwarz–Christoffel mapping** gives closed-form capacitance in terms of elliptic integrals. The SC parameter problem is finite-dimensional root-finding, where validated numerics is routine.

That suggests attacking the layer as *(exact 2D) + (verified 3D correction)* rather than as one 3D PDE — a materially better decomposition, and one that puts the hard verified-numerics work only on the correction term.

## Obligations

1. Formalise the two variational principles. **Sobolev-space machinery, well beyond current prover-library scale** — this is the single largest formalisation cost in L1.
2. Verified quadrature with `r^(−1/3)` singularities.
3. The family-uniform trial construction above (small, given 01).
4. Whether multi-conductor capacitance is monotone under conductor inclusion — would give the family bound directly by evaluating at erode and dilate. True for single-conductor capacity; **the multi-conductor case needs checking rather than assuming**.

## First experiments

- Two parallel plates, then two parallel wires over a ground plane: compute both bounds by hand, confirm the bracket contains the analytic answer, and measure how loose a trial pair can be while still landing inside a 20% budget.
- Run Ern–Vohralík reconstruction on a small FEM solve and check the certified gap.
- Compare a Schwarz–Christoffel 2D result against a field solver on one SKY130 cross-section.

## Effort

Years, dominated by obligation 1. But the accuracy requirement being soft means the *numerical* side is unusually forgiving; the cost is formalisation, not computation.

## Reading

[Pólya & Szegő](../BIBLIOGRAPHY.md#polya-szego-1951), *Isoperimetric Inequalities in Mathematical Physics* — rigorous capacity bounds by exactly this method. [Nakao, Plum, Watanabe](../BIBLIOGRAPHY.md#nakao-plum-watanabe-2019) for verified elliptic numerics. [Ern–Vohralík](../BIBLIOGRAPHY.md#ern-vohralik-2015) for the equilibrated flux.
