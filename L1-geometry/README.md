# L1 — Geometry, manufacturing, and extraction

> **Spec below:** the drawn layout `D` (GDS) and the as-fabricated family `A` it stands for ([00](00-layout-object.md)). **Spec above:** the netlist `N` with per-net RC enclosures — the geometric half of `Contracts(N)` ([MAIN](../MAIN.md#the-spec-tower)). **Kind: theorem** — for *every* `A` in the E7 tolerance family, the geometry realises exactly `N` and its RC lies in the exported intervals.

## Statement

One theorem with three faces, decomposed in the subcomponents:

1. **The layout implements the netlist.** `Ext(M(A)) ≅ N` for all `A` in the family — the sandwich theorem ([01](01-topology-preservation.md)) plus extraction/LVS ([02](02-extraction-lvs.md)).
2. **The layout determines RC enclosures**, valid over the whole family ([03](03-capacitance-enclosures.md), [04](04-screening.md)).
3. **DRC rules are the hypotheses**, not an unstructured pile of manufacturing constraints — (H1)(H2), (D1)–(D3), G1–G6.

This is the largest and least-charted layer. On the FPGA alternative it disappears entirely.

## Interfaces

**Consumes:** GDS, process stack, DRC deck. **Exports:** the netlist `N` (the shared object of [MAIN's tower](../MAIN.md#the-spec-tower) — the same `N` that L2 times and L3 compares), per-net RC enclosures and a sparse coupling graph plus one aggregate ε (into `Contracts(N)`).

## Axioms introduced

**E7** (as-fabricated geometry within the tolerance family — now also carrying the sandwich's (H3)), **P4** (variation within corners), **P5** (defect coverage), **X3** (T→theorem: retires when M2 lands). Formerly also E3 (discharged — [03](03-capacitance-enclosures.md)'s enclosures are its route) and E6 (retired: yield, not per-die correctness); see [AXIOMS](../AXIOMS.md#discharged-and-retired).

## Subcomponents

| | | status |
|---|---|---|
| [00](00-layout-object.md) | The layout as a formal object; admissible GDS | small, prerequisite |
| [01](01-topology-preservation.md) | **The sandwich theorem** — stated precisely | months; **the most tractable substantial result in L1** |
| [02](02-extraction-lvs.md) | Extraction and LVS; devices as rectangle intersections | small |
| [03](03-capacitance-enclosures.md) | Two-sided variational bounds on `C` | years — Sobolev formalisation dominates |
| [04](04-screening.md) | Screening and locality (**M2**) | unknown — **the load-bearing open problem** |
| [05](05-geometric-checks.md) | G1–G6: the finite, decidable obligations | weeks each |

### Two things precisification turned up

**The sandwich theorem needs a third hypothesis.** With only "erosion connected" and "dilations disjoint" it is **false**: the fabricated set may contain a spurious island inside `N ⊕ B_r` that meets no eroded net, i.e. a net that does not exist in the drawn layout. The missing hypothesis (H3) — *every component of `Cond(A)` meets `Cond(D) ⊖ B_r`* — is **not checkable**, since it quantifies over `A`. It is an assumption about the process and belongs to **E7**. (No dual hypothesis is needed for voids: extra material creates nets, missing material cannot destroy them, because the eroded net is already connected.)

**01's conclusion overclaims.** Its statement says the net bijection preserves device-terminal incidence, but its proof handles only nets. Devices are components of `poly ∩ active` and perturb under their own sandwich; the missing device-level hypotheses (D1)–(D3) are stated in [02](02-extraction-lvs.md). (D3) — terminals stay attached — is exactly where **line-end pullback** bites, so the enclosure rules are its hypotheses, not the net-level theorem's.

## Established during scoping

**The right model of a layout is a coloured image plus a fixed z-extrusion.**

```
d = F(L)                          derived layers; F = booleans + morphology
c : ℝ² → 2^Layer                  pointwise colour
M : ℝ³ → Material,  M(x,y,z) = Z(c(x,y), z)
```

This is literally what DRC/extraction decks compute (`gate = poly AND diff`). Two refinements: the algebra is booleans **plus morphology** (grow/shrink), because self-alignment and diffusion mean the doped extent is the boolean *then sized*; and the vertical stack is a **process constant**, which is exactly why a finite extraction pattern library is possible at all. If z varied per design, no library would exist.

**The model is exact for interconnect, lossy for devices.** BEOL is conductors and dielectrics in fixed geometry — R and C are functionals of M via Laplace, nothing lost. FEOL doping is a *continuous 3D concentration profile*; the colour only identifies *that* there is an NMOS here, and (W,L) come from geometry while behaviour comes from a fitted compact model. So verified extraction is available for interconnect and not for devices.

**The morphological sandwich, and why DRC is a theorem's hypotheses.**

```
∀ mask m:  erode(D_m + d_m, r_m) ⊆ A_m ⊆ dilate(D_m + d_m, r_m),  |d_m| ≤ overlay_m
           r_m = bias_m(density) + k·σ_m

(a) ∀ nets n: erode(D_n, r) connected              [min width, neck/notch rules]
(b) ∀ n≠n':  dist(D_n,D_n') ≥ r + r' + overlay     [colour-aware spacing rules]
(c) ∀ vias:  enclosure ≥ pullback + overlay        [enclosure rules]
⟹ connectivity_graph(A) = connectivity_graph(D)
```

Proof is one line each way (erosion spans the net ⟹ connected; dilations disjoint ⟹ no shorts). **Min-width and min-spacing rules are precisely (a) and (b).** This is self-contained computational geometry — no PDEs, no Sobolev spaces — and converts a large fraction of a DRC deck from folklore into hypotheses. *If one piece of L1 is formalised first, it should be this.*

Caveats: bias is density-dependent so r = r(x); line-end pullback and corner rounding are systematic and are why (c) exists; **vias are the dominant open mechanism** and are not bounded in-plane at all; multiple patterning makes overlay a *rigid per-mask displacement*, a different perturbation class, hence colour-aware spacing.

**Sub-resolution mask features do not transmit — lithography is a low-pass filter.** A gap much smaller than the resolution limit prints as a slight narrowing or nothing. Proof that this is real: sub-resolution assist features work precisely by not printing. So the geometry family to propagate is *band-limited*, not arbitrary polygon perturbation. Another restoration-like property.

**LER does not sever wires; defects do.** Severing requires roughness to consume the full width — Gaussian-tail suppressed. The sandwich with r = bias + 4σ is effectively deterministic. Topology changes are Poisson defects handled by test (P5). *Same continuous/discrete split as L0.*

**Extraction is pattern matching against a field-solver-characterised library** — template matching on cross-sectional images, with the rule deck as a trained model. The replacement is **rigorous enclosures**: Dirichlet principle gives upper bounds from any trial potential, Thomson's principle gives lower bounds from any trial flux field, so any pair of trial fields yields a two-sided bracket. Verified-numerics machinery for elliptic BVPs is mature ([Nakao, Plum, Watanabe](../BIBLIOGRAPHY.md#nakao-plum-watanabe-2019)). And the accuracy requirement is *soft*: ~5% vs field solver, against 10–20% derates already carried — so crude-but-rigorous bounds suffice, which is unusual and makes this viable.

**2D may be exactly solvable.** Schwarz–Christoffel mapping gives closed-form multiconductor capacitance for piecewise-linear 2D cross-sections in terms of elliptic integrals; verified numerics then only handles the 3D corrections. Better decomposition than treating everything as a 3D PDE.

**Corner singularities are the real obstacle.** Charge density diverges like r^(−1/3) at a right-angle conductor corner, exactly where the capacitance concentrates. Exponents are analytically known, so graded meshes work — but verified quadrature must handle integrable singularities.

**You want enclosures over a geometry *family* anyway.** As-fabricated ≠ drawn (etch bias, LER, CMP). So the right object is "∀ geometries within tolerance, C ∈ [lo,hi]" — which interval methods give naturally and which is arguably *more* faithful than the point-geometry field solve it replaces.

**Below extraction it becomes image processing for real:** DRC is polygon booleans; LVS is extraction + graph isomorphism; **OPC is literal inverse imaging** (simulate partially-coherent image formation, iteratively adjust mask polygons); fracturing is rasterisation, and multi-beam mask writers take a bitmap. Note E7 sits *between* LVS and the fab: the mask is deliberately not the drawn layout, so LVS-verified geometry is not what prints.

**GDS is a clean formal object with dirty corners.** A finite set of layer-tagged integer-coordinate polygons plus a hierarchy — far cleaner than Verilog. But: layer numbers are *semantically empty* (need an external layer map); PATH endcap type 1 is a *semicircle* so the format isn't purely polygonal; self-intersecting polygons and same-layer overlap semantics are unspecified. Restrict to a well-formed subset. Encouragingly, Caravel's routing uses **zero PATH records** — all BOUNDARY — so production output lives in a much cleaner subset than the format permits.

### The geometric combinatorial obligations

L1 owns a set of *finite, decidable* checks — the discharge points for conditions L0's operating envelope only **states** ([L0/09](../L0-device-physics/09-cut-discipline.md) has the dispatch table). Stated precisely as G1–G6 in [05](05-geometric-checks.md): tap coverage, ECC interleaving, antenna ratio, width/spacing/enclosure, shielding coverage, and tied fill.

Two of the six are **not properties of the geometry alone** — interleaving needs the ECC word structure from L3/L5, and the antenna check quantifies over *prefixes of the process order* rather than over the finished layout. That is worth carrying as a general caution: some geometric obligations need inputs a layout tool does not record.

## Open problems

1. **The screening exponent — the load-bearing open problem of this layer.** The far-field coupling sum does **not** obviously converge: the count of nets at distance d grows polynomially while unscreened coupling decays only logarithmically. Truncation is justified *not* by "distant things are small" but by screening making the decay fast enough. The mechanism is a **mesh of apertures in series**, giving multiplicative attenuation and hence `C_far(d) ≲ C_adj · α^(d/p)` — exponential in grid cells traversed. The rigorous object is **harmonic measure of the aperture set**, bounded via the maximum principle (complete enclosure ⟹ exactly zero; this case is *topological*, not metric, and so combinatorially checkable). **Deriving α is a genuine analysis problem and everything in local extraction depends on it.**
2. Formalising the variational characterisations of capacity — Sobolev machinery, well outside current Mathlib-scale infrastructure.
3. Verified quadrature with r^(−1/3) singularities.
4. Whether metal fill must be *tied* rather than floating: floating conductors do not screen, they **relay**, shortcutting an aperture chain. Should be a requirement, not an option.

## First experiments

- **Formalise the sandwich theorem.** Self-contained, no analysis, converts DRC into hypotheses. Highest value per effort in this layer by a wide margin.
- Run `magic`/`netgen` LVS on `inv_1` and check the extracted netlist against the intended one; measure what a per-cell LVS obligation costs.
- Sanity-check the screening claim numerically on a toy 2D mesh before committing to (1).

## Effort

4–6 years, and the widest error bars in the project. (1) could be six months or could be a thesis. **The FPGA alternative deletes this entire layer.**

## Reading

[Pólya & Szegő](../BIBLIOGRAPHY.md#polya-szego-1951), *Isoperimetric Inequalities in Mathematical Physics* (1951) — rigorous capacity bounds. [Nakao, Plum, Watanabe](../BIBLIOGRAPHY.md#nakao-plum-watanabe-2019), *Numerical Verification Methods and Computer-Assisted Proofs for PDEs*. [Driscoll](../BIBLIOGRAPHY.md#driscoll-trefethen-2002) on Schwarz–Christoffel.
