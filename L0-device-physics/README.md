# L0 — Device physics and the digital abstraction

> **Spec below:** `Field(A)` — trajectories of the transient field problem ([00](00-field-problem.md)). **Spec above:** `Contracts(N)` — the timed contract network ([MAIN](../MAIN.md#the-spec-tower)). **Kind: theorem** — within the envelope, every field trajectory refines the contract network, modulo E1.

## Statement

Two things, and they are different in kind:

1. **A transistor network implements its contract.** For each of the ~400 standard cells: geometry → devices → interval device model → a timed assume-guarantee contract (interval Liberty arc + regime classes, [03](03-cell-enclosures.md)/[05](05-digital-abstraction.md)), whose untimed shadow is the cell's Boolean function. Verified once per process, amortised over every design forever.
2. **The error model is Poisson, not Gaussian.** Continuous perturbations are suppressed below any threshold of interest and are *discharged*; discrete events are carried.

## The L0 / L1 boundary — resolved

There is **one** physical problem: Maxwell plus carrier transport over the whole die. The layer split is not "L0 = devices, L1 = wires" — it is a split by *abstraction target*, and both layers solve instances of the same PDE.

```
                 ONE field problem over the die
                              │
        ┌─────────────────────┴─────────────────────┐
   L0: on cell interiors                     L1: on the complement
   nonlinear (transport)                     linear (electrostatics)
   → terminal I-V → Boolean function         → per-net RC enclosures
        └─────────────────────┬─────────────────────┘
                              │
              L0/04: the LUMPING + COMPOSITION theorem
              "you may glue these two and get a circuit"
```

**L0 owns** well-posedness of the field problem, the quasi-static reduction, device models, per-cell enclosures, and — critically — **the composition theorem that licenses gluing**. **L1 owns** the geometry that *defines the domain* (the coloured image and its extrusion) and the linear interconnect enclosures.

## The four-step factoring

The proof plan, in order of logical dependence (which is not document order — notably it puts the envelope *before* the per-component work, as a precondition):

1. **Existence, circuit-independent.** The transient system has global-in-time solutions for any geometry, within the model's validity — established ([Gajewski–Gröger](../BIBLIOGRAPHY.md#gajewski-groger-1986)). Uniqueness is *not required*: every downstream claim is an enclosure **quantified over all solutions**, which converts stationary non-uniqueness (M1) from a blocking assumption into a reachability obligation — see [00](00-field-problem.md). "Within reasonable physical bounds" means *model validity*, not solution bounds: the theorem is unconditional for the model; the envelope justifies the model. [00, 01]
2. **Coarse invariance, near-circuit-independent.** Every solution stays in a broad safe set: bounded potentials (maximum principle) and carrier densities, no runaway — a theorem *within* the model, since the omitted terms (impact ionisation, electrothermal coupling) are exactly where the feedback dangers live. Excluding those is [07](07-operating-envelope.md)'s envelope, whose side conditions are computable but not all structural (thermal is workload-conditional). The safe set is honest-broad: it contains U, 0, 1, transitioning, metastable, **and the latched states** — which step 3 must show unreachable, not assume absent. [07, 00, 02]
3. **Fine regime decomposition, per component.** Pin regions "0" / "1" / "transitioning", with "transitioning" a family parameterised by slew — the component's behaviour is an **assume-guarantee contract on trajectory classes** (an interval Liberty arc with an explicit domain): guaranteed output class given input classes, load, and a bounded local disturbance budget. Established numerically with rigorous enclosures, once per library cell. The disturbance budget's discharge is nonlocal (L1's screening) and must cover Miller feedthrough *through* the component. [02, 03, 05]
4. **Composition = combinatorics + side conditions.** Components plug together by finite checking: each edge's load / slew / coupling within the contracts' domains (not vacuous — the shipped design fails these, F2). Cuts are licensed only at restoring, near-unidirectional boundaries (channel-connected components), so every bistable loop is internal to a component. Three globals do not factor through pins — supply, clock, temperature — and need their own aggregate arguments. Conclusion: the network emulates a state machine, **except** at Poisson fault events and unresolved synchroniser reads, which are carried as P1/P2, never proved away. [04, 06]

The overall deliverable, restated: **every solution of the field problem lies within the enclosure that the lumped semantics predicts**, established by component contracts + PDE bounds + an abstract composition argument.

## Subcomponents

| | | status |
|---|---|---|
| [00](00-field-problem.md) | The field problem and its well-posedness | **partly open** — see below |
| [01](01-quasistatic-reduction.md) | Maxwell → elliptic, with an error bound | settled maths, unformalised |
| [02](02-device-models.md) | Devices: the nonlinear part, and where uniqueness fails | **open** |
| [03](03-cell-enclosures.md) | Per-cell field bounds → terminal behaviour | hard, mechanical |
| [04](04-lumping-composition.md) | Distributed field → lumped network; **Kirchhoff as a theorem** | **the key one** |
| [05](05-digital-abstraction.md) | Restoration, noise margins → Boolean function | settled, unformalised |
| [06](06-error-model.md) | Thermal / SEU / metastability / the ECC interface | settled, unformalised |
| [07](07-operating-envelope.md) | The side conditions under which everything above is valid | mostly structural |
| [08](08-quantum-floor.md) | What lies below drift–diffusion; where the tower bottoms out | scope-fixing — no new axiom |
| [09](09-cut-discipline.md) | Where the network may be cut: CCCs, PUN/PDN duality, bistables internal | gated on cell extraction |

**On the existence question.** For the *linear electrostatic* problem it is classical — Lax–Milgram on H¹ with bounded measurable coefficients — and not open at all. For the *device* problem (drift–diffusion) existence is established but **uniqueness is not known in general**, and the non-uniqueness is physically real: latch-up and snapback are second solution branches. See [00](00-field-problem.md) and [02](02-device-models.md). The industry's answer is to not solve the PDE at all, which relocates the question into an empirical claim about compact models.

## Interfaces

**Consumes:** cell layouts and the material stack (L1's geometry), an interval device model (E1). **Exports:** per-cell **timed contracts** — interval Liberty arcs with explicit domains ([03](03-cell-enclosures.md)) — and their Boolean shadows ([05](05-digital-abstraction.md)); the composition licence ([04](04-lumping-composition.md), [09](09-cut-discipline.md)); a per-cycle upset rate λ and the noise margin NM ([06](06-error-model.md)). The timed contracts are what L2's STA composes; omitting them from this list was the seam mismatch the 2026-07 review caught.

## Axioms introduced

**E1** (the tower's one physical axiom) and **P2** (SEU). Formerly also E2, P3 and X2 — all discharged or rerouted in the reassessment ([AXIOMS](../AXIOMS.md#discharged-and-retired)): [03](03-cell-enclosures.md) is E2's discharge route, [06](06-error-model.md) P3's, and X2's check moved to L1's G2 with its empirical residue (the upset radius) into P2.

## Effort

2–4 years. Dominated by [03](03-cell-enclosures.md) and [04](04-lumping-composition.md). The Boolean-function-per-cell result is the load-bearing output; the error model is smaller but needs probabilistic machinery nothing else in the project requires.

## Reading

[von Neumann](../BIBLIOGRAPHY.md#von-neumann-1956), *Probabilistic Logics and the Synthesis of Reliable Organisms from Unreliable Components* (1956). [Bryant](../BIBLIOGRAPHY.md#bryant-1984) on switch-level (MOSSIM). [Melham](../BIBLIOGRAPHY.md#melham-1993), *Higher Order Logic and Hardware Verification*. [Markowich](../BIBLIOGRAPHY.md#markowich-1986), *The Stationary Semiconductor Device Equations*.
