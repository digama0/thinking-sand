# L0/00 — The field problem and its well-posedness

## Statement

Identify the PDE that the chip actually satisfies, and establish that it has a solution — so that "the field" in every downstream enclosure statement denotes something.

This is prior to every other document in L0 and L1. If the solution does not exist or is not unique, "the RC of net *n*" is not a well-defined quantity and the enclosures bound nothing.

## The hierarchy of problems

From most faithful to most used:

| level | system | existence | uniqueness |
|---|---|---|---|
| full | Maxwell + van Roosbroeck transport | hard | not known |
| **transient** quasi-static + transport | Poisson + 2 **parabolic** continuity eqns | **established** ([Gajewski–Gröger](../BIBLIOGRAPHY.md#gajewski-groger-1986)) | limited |
| **stationary** quasi-static + transport | Poisson + 2 continuity eqns | **established** | **NOT in general** |
| quasi-static, linear | `∇·(ε∇φ) = 0`, Dirichlet on conductors | **classical** | **classical** |
| lumped | RC network / compact models | trivially | trivially |

**The transient row is the one the digital abstraction actually needs.** Electrons flow; the circuit is a dynamical system, not a sequence of static solutions. The stationary rows characterise the *invariant sets*; the transient row is what makes "you stay in the regime and move according to the abstraction" a statement at all. See [05](05-digital-abstraction.md), which is built on it.

The transient system is elliptic–parabolic — Poisson as an algebraic constraint coupled to two parabolic transport equations, so a PDAE rather than a PDE. Global existence is established, and the proof route is worth knowing about: the system carries a **free-energy functional that decreases along trajectories**, which is exactly the Lyapunov structure the regime-decomposition argument needs. It decreases toward *thermal equilibrium*, though, so adapting it to a boundary-driven steady state is the open piece.

Each row is an abstraction of the one above with an error that ought to be bounded. L0/01 handles row 1→2, this document handles row 2 and row 3, L0/02 handles the device side of row 2, and L0/04 handles row 3→4.

**The top row is already a model.** Drift–diffusion is not first principles: it is the diffusion limit of semiclassical Boltzmann transport, which in turn coarse-grains quantum transport — the hierarchy continues upward through energy-transport and hydrodynamic models ([Markowich–Ringhofer–Schmeiser](../BIBLIOGRAPHY.md#markowich-ringhofer-schmeiser-1990); [Jüngel](../BIBLIOGRAPHY.md#jungel-2009)). The upward error terms are asymptotic, not bounded. At 130 nm drift–diffusion sits comfortably inside its validity window — channel lengths well above the carrier mean free path, quasi-ballistic corrections negligible — but that is an *empirical adequacy claim about the node*, and it should be recorded as part of E1's content: E1 asserts both "the fit matches the device" and, implicitly, "the PDE the fit dodges would itself have been adequate." There is no row you can point to and say *this one is physics all the way down*; there is only a row whose error is negligible for the question asked. [08](08-quantum-floor.md) works out where the tower actually bottoms out and why E1 is the right place to cut it.

## Row 3: the interconnect problem is settled

For `∇·(ε∇φ) = 0` with Dirichlet conditions on conductors, take the bilinear form

```
a(u,v) = ∫ ε ∇u · ∇v
```

If `0 < ε_min ≤ ε ≤ ε_max` (bounded measurable — dielectric jumps are fine), then `a` is bounded and, by Poincaré–Friedrichs, coercive on the subspace of `H¹` vanishing on the Dirichlet part of the boundary — which requires that part to have positive measure, true here since the rails are everywhere. **Lax–Milgram gives existence and uniqueness of the weak solution.** Equivalently by the direct method: the Dirichlet energy is coercive and weakly lower semicontinuous so a minimiser exists, and strict convexity gives uniqueness — which is also exactly the variational characterisation L1 uses for its two-sided capacitance bounds.

So **this is not an open problem**. It is classical, and the work is formalisation, not mathematics.

What *does* bite is **regularity, not existence**:

- Bounded measurable coefficients give only De Giorgi–Nash–Moser Hölder continuity. Higher regularity needs smoother coefficients, which dielectric interfaces do not provide. The sharp results for piecewise-constant ε are the transmission-problem estimates going back to [Kellogg](../BIBLIOGRAPHY.md#kellogg-1974) (1974).
- **Reentrant corners**: ∇φ blows up. Charge density diverges like `r^(−1/3)` at a right-angle conducting corner — precisely where the capacitance concentrates.
- **Mixed boundary conditions** (Dirichlet on conductors, Neumann on symmetry planes) are worse at corners than either alone. The right regularity framework here is [Gröger](../BIBLIOGRAPHY.md#groger-1989)'s `W^{1,p}` theory for mixed problems on nonsmooth domains (1989).
- **Unbounded domain**: the die is finite but the field is not. Needs a decay condition at infinity, or a truncation with a bound — which is L1's screening argument again, from the other side.

The weak solution exists in `H¹` on Lipschitz domains regardless. But numerics converge at degraded rates near singularities, so **verified quadrature must handle integrable singularities of known exponent**. Since the exponents are analytically known, graded meshes work; it is engineering, not research. The relevant machinery exists in pieces: Arb-style ball arithmetic for rigorous quadrature ([Johansson](../BIBLIOGRAPHY.md#johansson-2017)), and — more to the point for enclosures — **guaranteed a posteriori FEM error bounds** with fully computable constants via equilibrated flux reconstruction ([Ern–Vohralík](../BIBLIOGRAPHY.md#ern-vohralik-2015)). The latter is the natural route to "the true field is within δ of this computed one" as a machine-checkable statement rather than an asymptotic convergence rate.

## Row 2: the device problem is genuinely open

The van Roosbroeck system — Poisson coupled to continuity equations for electrons and holes with Einstein relations — is nonlinear elliptic/parabolic.

- **Existence** for the stationary system is established ([Mock](../BIBLIOGRAPHY.md#mock-1983), [Gajewski](../BIBLIOGRAPHY.md#gajewski-1985), [Markowich](../BIBLIOGRAPHY.md#markowich-1986)).
- **Uniqueness is known only under near-equilibrium / smallness conditions**, and in general it is not known and *does not hold*.

The non-uniqueness is not a mathematical artifact. **Latch-up and snapback are real physical second solution branches** — a parasitic thyristor in the CMOS well structure has a genuinely bistable I-V characteristic. Which is why tap cells and guard rings exist: they are there to *destroy the second branch*, not merely to bias the wells.

So the honest statement is:

> The device-level PDE does not have a uniqueness theorem, and "the transistor's I-V characteristic" is therefore not obviously well-defined from first principles. Where it fails, the failure is a real device phenomenon that designers actively engineer against.

**This is the sharpest genuinely-open mathematical question in the project.**

## Enclosures quantify over solutions — uniqueness may be bypassable

Every downstream statement has the form "the behaviour lies within this set." Stated universally — *every* weak solution from the given initial data remains in the enclosure — no statement ever selects "the" solution, and stationary non-uniqueness stops being a blocking assumption. What replaces it is a **reachability obligation**: from the unpowered initial state, under tap coverage, show that no solution enters the latch branch's basin.

The dynamics make this the physically correct formulation anyway: the transient initial-value problem is deterministic in a way the stationary problem is not — latch-up in real silicon is a *triggered* event (an injection transient kicks the state across a basin boundary), not an ambiguity about which I-V curve the device "has." The bistability lives in the stationary picture; the trajectory picture sees one history per disturbance signal.

The method also fails safe: if the second basin *is* reachable by some weak solution, the universal enclosure is forced to include it, the per-cell contract of [03](03-cell-enclosures.md) cannot be established, and verification stops — it does not silently certify the good branch. Uniqueness for the transient problem (known in 2D, partial in 3D — [Gajewski](../BIBLIOGRAPHY.md#gajewski-1985)) then becomes an optimisation that tightens enclosures, not a foundation the argument stands on.

## Genericity: existence does not depend on the layout being sensible

For the linear problem, **Lax–Milgram does not care about the geometry.** Coercivity comes from Poincaré and boundedness of ε; neither mentions the shape. So the weak solution exists for essentially any measurable die drawing, sensible or not.

What degrades with bad geometry is **regularity and the constants**, not existence: a thin neck gives a large resistance, a sharp corner a stronger singularity, a bad aspect ratio a worse Poincaré constant. The solution is still there.

So the honest summary is: **existence is generic in the geometry; uniqueness and useful bounds are not.** Which is convenient, because it means well-posedness is not something to re-establish per design — it is a once-and-for-all theorem about the class.

## No blowup — and this is where the Navier–Stokes analogy breaks

**Linear electrostatics cannot blow up, by the maximum principle.** Solutions of divergence-form elliptic equations attain their extrema on the boundary, so

```
|φ(x)| ≤ max |boundary data| = Vdd
```

everywhere, always. There is no mechanism for spontaneous energy concentration: superposition holds, and focusing requires either nonlinearity or wave propagation. Quasi-static ([01](01-quasistatic-reduction.md)) has removed the waves, and the equation has no nonlinearity. **The field is bounded by the applied voltages, full stop.**

The only singularities are **geometric** — `r^(−1/3)` field crowding at reentrant conductor corners. These are static, integrable, analytically characterised, and engineered against (they matter for oxide breakdown and electromigration). They are not spontaneous and they are not blowup.

**Drift–diffusion has global existence**, so no finite-time blowup there either. The reason is structural and better than the Navier–Stokes situation: the free energy is a genuine Lyapunov functional, and the dissipative structure gives *a priori* bounds strong enough to continue solutions globally. Navier–Stokes lacks exactly this — its energy does not control enough to prevent vortex-stretching concentration.

So there is no analogue here of the NS regularity problem. The nonlinearity is dissipative rather than energy-concentrating.

**The two genuine runaway mechanisms are physical, not mathematical**, and both are engineered against rather than proved away — see [07](07-operating-envelope.md):

- **Avalanche / impact ionisation.** High field → carriers gain energy → create pairs → more current. Real positive feedback, and adding impact-ionisation terms is precisely what can destroy the global existence results above.
- **Thermal runaway.** Dissipation heats the die; leakage rises with temperature; more leakage means more dissipation. Real, and it destroys real chips (second breakdown).

Neither is spontaneous: both require the operating point to leave a design envelope, which is why they become *side conditions* rather than open problems.

## How the industry dodges it

By not solving the PDE. Compact models (BSIM, PSP) are *fitted algebraic relations* between terminal voltages and currents — hundreds of parameters calibrated against measured silicon. The existence/uniqueness question never arises because no PDE is solved.

That relocates rather than removes the problem: it becomes the empirical claim E1, "the compact model adequately describes the device," which is unfalsifiable in principle and validated by measurement in practice.

Two consequences worth stating plainly:

1. **A verified switch-level cell model rests on a fitted device model.** L0/05's clean restoration argument bottoms out in E1. There is no first-principles route to a Boolean function that does not pass through either drift–diffusion (no uniqueness) or a fitted model (no derivation).
2. **The tap-coverage rule is a hypothesis about uniqueness.** "Every device within *d* of a tap" is what makes the single-branch assumption valid. It is normally filed as a layout rule; it is really the side condition on a well-posedness claim.

## Open problems

1. **Uniqueness for the stationary drift–diffusion system under operating conditions**, or a characterisation of when the second branch is reachable. Genuinely open; a solution would be a contribution to semiconductor mathematics independent of this project. Note the enclosure formulation above may sidestep the uniqueness half entirely — what it needs is the reachability half: unreachability of the second basin from the unpowered state.
2. Formalise Lax–Milgram / the direct method over `H¹` with bounded measurable coefficients. Settled mathematics, substantial Sobolev-space infrastructure, well beyond what current prover libraries support.
3. Rigorous treatment of the unbounded-domain truncation, shared with L1's screening bound.
4. Whether tap-coverage rules can be turned into a *proved* sufficient condition for single-branch operation rather than an empirical design rule.

## First experiments

- Write the four-row abstraction hierarchy as formal statements with explicit error terms between rows, before attempting any of them. This alone will reveal which rows have bounds and which currently have only folklore.
- Survey what Mathlib-scale libraries actually have: weak solutions, `H¹`, Lax–Milgram, Poincaré. Determines whether row 3 is a year or five. The prior art to calibrate against: [Boldo–Clément–Filliâtre–Mayero–Melquiond–Weis](../BIBLIOGRAPHY.md#boldo-2013) verified a full numerical wave-equation solver in Coq (method error + rounding error, end to end); [Immler](../BIBLIOGRAPHY.md#immler-2018)'s HOL-ODE-Numerics in Isabelle does rigorous ODE enclosures inside the prover (used to check [Tucker](../BIBLIOGRAPHY.md#tucker-2002)'s Lorenz computation). Nothing comparable exists for elliptic problems, which is exactly the gap.

## Effort

Statement work: weeks. The row-3 formalisation (Lax–Milgram over H¹) is Sobolev-library-scale, shared with L1/03's obligation 1 rather than owned here.

## Reading

[Markowich](../BIBLIOGRAPHY.md#markowich-1986), *The Stationary Semiconductor Device Equations* (1986). [Mock](../BIBLIOGRAPHY.md#mock-1983), *Analysis of Mathematical Models of Semiconductor Devices* (1983) — stationary existence. [Gajewski & Gröger](../BIBLIOGRAPHY.md#gajewski-groger-1986), "On the basic equations for carrier transport in semiconductors" (J. Math. Anal. Appl. 1986) — transient existence and the free-energy structure. [Markowich–Ringhofer– Schmeiser](../BIBLIOGRAPHY.md#markowich-ringhofer-schmeiser-1990), *Semiconductor Equations* (1990) and [Jüngel](../BIBLIOGRAPHY.md#jungel-2009), *Transport Equations for Semiconductors* (2009) — the model hierarchy above drift–diffusion. [Grisvard](../BIBLIOGRAPHY.md#grisvard-1985), *Elliptic Problems in Nonsmooth Domains* — corner singularity exponents. [Kellogg](../BIBLIOGRAPHY.md#kellogg-1974) (1974) on interface regularity; [Gröger](../BIBLIOGRAPHY.md#groger-1989) (1989) on mixed boundary conditions. [Ern & Vohralík](../BIBLIOGRAPHY.md#ern-vohralik-2015) on guaranteed a posteriori bounds. Any graduate elliptic PDE text for Lax–Milgram and De Giorgi–Nash–Moser.
