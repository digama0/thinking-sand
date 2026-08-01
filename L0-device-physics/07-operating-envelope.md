# L0/07 — The operating envelope

## Statement

Collect the conditions under which every bound in L0 and L1 is valid, and establish that the design and its environment stay inside them.

These are the **disturbance bounds of [05](05-digital-abstraction.md)'s robust invariance claim**. Without them (I) and (P) are unconditional statements that are simply false: every one of these mechanisms *does* leave the invariant set, and the design's job is to make them unreachable.

## The pattern

Each entry has the same shape, and it recurs enough to be worth naming:

> A real physical instability, prevented by a design rule, which is therefore secretly a hypothesis of a well-posedness or boundedness claim rather than a manufacturing constraint.

This is the third time this pattern has appeared in the project. L1's min-width and min-spacing rules are the hypotheses of a topology-preservation theorem. Tap-coverage rules are the hypothesis that kills latch-up's second solution branch. And now the whole envelope. **Several DRC and design rules are the side conditions of theorems nobody has written.**

## The envelope

| # | condition | prevents | how established |
|---|---|---|---|
| V1 | No low-resistance Vdd→GND path in steady state | short-circuit current, melting | *structural* — CMOS complementary logic guarantees it by construction; contention is a netlist property |
| V2 | Transient crowbar current bounded | excess dynamic power | timing/slew limits (L2's `max_transition`) |
| V3 | Terminal voltages below avalanche | impact-ionisation runaway | voltage rating; supply bound (P6) |
| V4 | Junction temperature within range | thermal runaway, second breakdown | thermal design; corner range (E4) |
| V5 | Every device within *d* of a well tap | **latch-up** — the second PDE solution branch | tap-coverage rule (L1 geometry) |
| V6 | Current density below electromigration limits | wearout opens | EM design rules (L1) |
| V7 | No manufacturing short or open | arbitrary behaviour | LVS + DRC + test (P5) |
| V8 | Supply ramps follow the specified sequencing and rate | **latch-up during power transitions** — wrong rail order forward-biases junctions in a multi-rail bring-up (vddio 3.3 / vccd 1.8 / vdda, switchable user rails), reaching M1's second branch *during the ramp*, when the wells are not yet at their rails and tap coverage does not yet protect | board design + POR (`simple_por`, X4-class); a **trajectory** condition (type D) on the transitions between U and powered operation — V1–V7 constrain powered states, V8 the paths between them |

## Notes on the interesting ones

**V1 is structural and cheap.** Static CMOS is *designed* so that no conducting path from Vdd to GND exists in any steady state — that is what complementary logic means. So V1 is a property of the netlist, checkable by the same machinery L3 already needs. The failure modes are bus contention (two drivers fighting) and pass-gate paths, both of which are netlist properties, not physics.

**V2 is why the transient version is separate.** During switching both devices are momentarily partly on, so there genuinely *is* a Vdd→GND path — the crowbar or short-circuit current, a real and non-trivial fraction of dynamic power. It does not threaten the abstraction because it is brief and bounded, and what bounds it is the **input slew**. So `max_transition` is doing double duty: it keeps you inside the Liberty table's domain (L0/03) *and* it bounds crowbar current. A slow input violates both.

**V3 and V4 are the genuine runaway mechanisms**, and they are the reason the answer to "can the chip destroy itself" is yes-but-only-outside-the-envelope. Both are positive feedback loops:

```
V3:  field ↑ → impact ionisation ↑ → carriers ↑ → current ↑ → (field ↑)
V4:  power ↑ → temperature ↑ → leakage ↑ → power ↑
```

Neither is spontaneous. Both require the operating point to leave the envelope first, which is why they are side conditions rather than open problems. Note that adding impact-ionisation terms is exactly what can destroy the global-existence results in [00](00-field-problem.md) — so V3 is not merely a device-reliability condition, it is what keeps the *mathematics* in the well-behaved regime.

**V5 is uniqueness, wearing a layout rule's clothing.** Latch-up is a second solution branch of the stationary device PDE (M1). Tap coverage destroys the parasitic thyristor, hence destroys the branch. So a rule normally filed under reliability is the side condition that makes "the transistor's I-V characteristic" well-defined at all.

**V4 also couples layers unpleasantly.** Thermal behaviour depends on power, which depends on switching activity, which depends on the *workload* — so strictly the envelope is workload-dependent. At 130 nm with a small core this is comfortable; it is one of the things that gets much worse at advanced nodes, where self-heating enters the functional path.

## The shape of the boundary

Worth working out, because the constraints are not all the same kind of object and a naive "bound the field and its derivatives" formulation is **not satisfiable**.

### What is free and what is not

`|φ| ≤ Vdd` everywhere is **free** — it is the maximum principle ([00](00-field-problem.md)), a theorem rather than a constraint.

`|∇φ|` is **not** free, and is genuinely unbounded: the `r^(−1/3)` singularity at reentrant conductor corners. Note however that the *total* energy is finite — energy density goes as `r^(−2/3)`, and near an edge `∫ r^(−2/3)·r dr` converges. So:

> The solution lives in `H¹` automatically. The safe region needs `W^{1,∞}`-type control, which the idealised geometry does not provide.

**Consequence: every constraint below must be stated on a mollified quantity.** Pointwise field values at geometric singularities are not physical — real corners are rounded at the atomic scale, and every breakdown criterion involves a finite volume and time scale anyway. So the right form is

```
‖ G_δ * ∇φ ‖_∞  <  E_crit
```

with δ a physical length (oxide thickness, mean free path). Mollified constraints are satisfiable; the idealised pointwise ones are not. **This is a modelling decision that has to be made explicitly, and getting δ wrong is the difference between a vacuous constraint and a false one.**

### Five shapes

| type | constraint | functional form | convex? |
|---|---|---|---|
| **A** pointwise | oxide breakdown: `‖∇φ‖_∞ < E_ox` on oxide regions | L^∞ ball on ∇φ, restricted to a subdomain | **yes** |
| **B** nonlinear line integral | avalanche: `∫ α(|∇φ|) ds < 1` along field lines, α = A·exp(−B/E) | sublevel set of a monotone nonlinear functional | no, but **monotone** |
| **C** smoothed quadratic | thermal: `(G_th * σ|∇φ|²) < T_max` | quadratic in ∇φ, convolved with the thermal Green's function | **yes** |
| **D** time-integrated | electromigration: `∫|J|ⁿ dt < threshold` ([Black](../BIBLIOGRAPHY.md#black-1969), n≈2) | a condition on *trajectories*, not states | — |
| **E** structural | latch-up (V5), rail contention (V1) | property of the **operator/domain**, not of any solution | — |

Three observations:

**Avalanche is not a pointwise field bound.** The ionisation coefficient is exponential in 1/E, and the criterion is that the *integral* along a field line reaches unity. Sharper and weaker than `|∇φ| < E_crit`: a brief high-field region is tolerable, a sustained moderate one may not be.

**Thermal is not local.** The temperature is a *nonlocal* response — the power density `σ|∇φ|²` convolved with a thermal Green's function. So a small hot spot is tolerable while a diffuse but large dissipation is not. The constraint is on a smoothed quantity, and the smoothing length is set by the thermal diffusion length, not by anything electrical.

**D and E are not state constraints at all.** Electromigration is a wearout criterion over a trajectory; latch-up and contention are properties of the *operator* (does a second solution branch exist, is there a conducting rail-to-rail path). Neither can be phrased as "the field is in this set", which is why they need combinatorial rather than analytic treatment.

So your conjecture — field bounded, derivatives bounded, energy density bounded — captures A and C. Energy *density* bounded is equivalent to `|∇φ|` bounded, so it is A restated. B, D and E are genuinely different.

### Structural properties of the safe set

Two facts that make it tractable:

**It is star-shaped about the unpowered state.** Scale `φ → λφ` for `λ ∈ [0,1]`: the field scales by λ, power density by λ², and the ionisation integral decreases monotonically. Every constraint is preserved. So **you can always retreat to safety by lowering the supply** — which is exactly what thermal throttling and dynamic voltage scaling do, and it means the safe set is connected and contains a path to the origin from any interior point.

**Convexity is inherited through the linear map, for A and C.** For the electrostatic part the map from applied boundary voltages to the field is *linear*, so a convex constraint in field space pulls back to a convex constraint in input space. A and C are convex; hence the safe operating region **in applied-voltage space is convex apart from the avalanche term**.

That matches engineering practice — safe operating areas are specified as boxes and trapezoids in (V, I, T) space — and it explains why: the box is a conservative inner approximation of a convex set, and the corner cuts are the non-convex avalanche term.

Both structural facts share the same caveat: the star-shapedness argument scales the *field configuration*, and the retreat-to-safety reading ("lower the supply") transfers to applied-voltage space only through linearity of the input-to-field map. For the nonlinear device problem that map is not linear, so there both convexity *and* the supply-scaling argument degrade from theorem to physically-motivated heuristic (lowering Vdd does shrink the fields, but not proportionally, and the safe set in supply space inherits neither property automatically). So the clean statement holds for interconnect and degrades at devices.

### What this means for verification

The envelope should be stated as an **intersection of mollified sublevel sets**, with δ explicit for each, plus two combinatorial side conditions (E) that live outside the analytic framework entirely. Star-shapedness gives a cheap sufficient check — verify at the worst corner of the operating box and scale down — and convexity means the A and C constraints can be checked at box vertices rather than swept.

## What this buys

With the envelope in hand, the chain of statements is honest:

```
design + environment ∈ envelope          [this document]
  ⟹ single solution branch, bounded fields, no runaway     [00, 02]
  ⟹ robust invariance (I) and progress (P) hold            [05]
  ⟹ the Boolean/Mealy abstraction is sound                 [05, L2]
```

Without it, [05](05-digital-abstraction.md)'s claims are false as stated, because the disturbance set is unbounded.

## Open problems

1. **Formalise V1** as a netlist property and prove static CMOS satisfies it. Should be easy, and it is a genuine precondition rather than an assumption.
2. **Turn V5 into a proved sufficient condition** for single-branch operation, rather than an empirical distance rule. This is the concrete form of attacking M1 from the engineering side rather than the analysis side.
3. Bound crowbar current from the slew limit (V2), and check the shipped design's `max_transition` violations (finding F2) do not breach it — currently these are treated as a timing issue only.
4. A workload-independent thermal bound, or an explicit statement that the envelope is workload-conditional.

## First experiments

- **Check V1 structurally on the shipped netlist.** Enumerate every net with more than one driver and every pass-gate/tri-state structure. Cheap, mechanical, and it either confirms the assumption or finds something interesting. L3 needs the same analysis for one-driver-per-net well-formedness, so it is shared work.
- Confirm the design's operating voltage sits comfortably below the process's avalanche rating, and record the margin.
- Check whether any net violating `max_transition` (F2) is in a high-activity region, where the crowbar-current consequence would actually matter.

## Reading

[Sze & Ng](../BIBLIOGRAPHY.md#sze-ng-2007), *Physics of Semiconductor Devices* — avalanche breakdown, the ionisation-integral criterion, and [Chynoweth](../BIBLIOGRAPHY.md#chynoweth-1958)'s `α(E) = A·exp(−B/E)`; also second breakdown. [Troutman](../BIBLIOGRAPHY.md#troutman-1986), *Latchup in CMOS Technology: The Problem and Its Cure* (1986) — the standard monograph on the thyristor structure and the role of taps and guard rings. [Black](../BIBLIOGRAPHY.md#black-1969) (1969) for the electromigration law behind V6. Note that these are normally presented as reliability engineering, and the reframing as side conditions of well-posedness is this project's angle rather than the field's.
