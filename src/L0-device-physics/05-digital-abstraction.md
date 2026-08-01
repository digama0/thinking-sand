# L0/05 — The digital abstraction as a regime decomposition

## Statement

The physical state is a *field configuration evolving in time* — potentials and carrier densities over the domain, driven by environmental inputs. The digital abstraction is a **decomposition of that state space into regimes**, plus three claims:

```
regimes:   U           unpowered / at rest
           Z₀ⁿ, Z₁ⁿ    node n denotes 0 / denotes 1
           Tⁿ          node n transitioning

(I)  INVARIANCE   starting in a valid regime with bounded inputs, you stay in the
                  union of valid regimes — you never escape to "undefined"
(P)  PROGRESS     from Tⁿ you reach the appropriate Z regime within bounded time
(A)  ABSTRACTION  the induced discrete transitions are exactly the Boolean/Mealy semantics
```

The digital state is a *tuple* over nodes, so the regime structure is a product; the decomposition is a covering of an infinite-dimensional state space, not a partition of a scalar.

`Tⁿ` is not a single set but a **family parameterised by transition time**: delay and crowbar current depend on the input trajectory, not its endpoints, so "transitioning" carries its slew with it. This is why the per-component contract ([03](03-cell-enclosures.md), [04](04-lumping-composition.md)) is stated on trajectory classes rather than voltage regions — a static region cannot support the composition.

## Why the static story was wrong

The textbook argument — DC transfer characteristic, gain > 1 in transition, rails as attracting fixed points, `V_OL < V_IL` — establishes only that the **steady states** are attracting. It says nothing about trajectories, and a circuit spends much of its life not at a steady state.

The static picture is the **equilibrium slice** of (I): it characterises the invariant sets but not the invariance, and not (P) at all.

## What the correct framing buys

Several things I had scattered across documents turn out to be the same object:

- **Noise margin is not a static gap.** It is the *robustness radius* of the invariant set — how large a disturbance the region tolerates while (I) still holds.
- **Restoration is the contraction that makes the invariant set attracting**, i.e. it is what proves (I) and (P), not a separate phenomenon.
- **Metastability is exactly the failure of (P).** From `Tⁿ` you may not reach a `Z` regime within bounded time; the exponential tail `exp(−t/τ)` *is* the reachability-time distribution. It is not a separate pathology bolted onto the model — it is the one place the model's progress claim has no bound. And this is a **theorem, not an engineering observation**: [Marino](../BIBLIOGRAPHY.md#marino-1981) (IEEE Trans. Computers 1981) proved by a connectedness/continuity argument that *any* bistable device with continuous dynamics admits inputs driving it to arbitrarily long settling — no clever circuit escapes it. So (P) provably cannot be made unconditional, which is the formal justification for carrying P1 as an axiom rather than filing it as an open problem.
- **The setup/hold window is the condition under which (P) holds for a flop.** Which is precisely why L2's bridge theorem needs it as a hypothesis.
- **The switching window is where no `Z` regime holds** — so it is unsurprising that disturbances get amplified there rather than attenuated.

## The mathematics

This is a **robust invariance** problem for a controlled dynamical system with bounded disturbances. Standard tools apply:

- **Barrier certificates** for (I): find `B(state)` with `B ≤ 0` on the initial set, `B > 0` on the bad set, and `Ḃ ≤ 0` on `{B = 0}`. Constructive and checkable, and the standard method in hybrid-systems verification ([Prajna & Jadbabaie](../BIBLIOGRAPHY.md#prajna-jadbabaie-2004)).
- **Lyapunov functions** for (P): a functional decreasing along trajectories toward the target regime, with a decrease rate giving the time bound.

Both are found in practice by sum-of-squares programming ([Parrilo](../BIBLIOGRAPHY.md#parrilo-2003); [SOSTOOLS](../BIBLIOGRAPHY.md#sostools-2002) as the front-end, an SDP solver underneath), and — importantly for this project — the *checking* side is already formalised: a numeric SOS certificate can be rounded to a rational identity and verified in a prover, which is exactly what [Harrison](../BIBLIOGRAPHY.md#harrison-2007)'s HOL Light SOS procedure and [Martin-Dorel & Roux](../BIBLIOGRAPHY.md#martin-dorel-roux-2017)'s ValidSDP (Coq) do. So the pipeline "search numerically, certify formally" exists end to end for polynomial dynamics; the work is getting an interval-valued device model into polynomial (or polynomial-envelope) form.

**There is a natural candidate at the field level.** The van Roosbroeck system has a **free-energy functional that decreases along trajectories** — this is the structure [Gajewski and Gröger](../BIBLIOGRAPHY.md#gajewski-groger-1986) used to prove global existence and asymptotic behaviour for the transient system. That is exactly a Lyapunov functional, and it is the physical basis for "the circuit settles."

Caveat: the free energy decreases toward *thermal equilibrium*, i.e. toward the unpowered regime `U`. For a driven circuit the relevant statement is convergence to a **boundary-driven steady state**, so the working functional is a relative free energy with respect to that steady state rather than the equilibrium one. That adaptation is where I would expect the real work to be.

## Environmental bounds are hypotheses, and you named the right ones

(I) and (P) are conditional on the inputs staying in range. Concretely:

| input | bound | axiom |
|---|---|---|
| supply voltage | Vdd within spec, droop bounded | P6 |
| temperature | within corner range | E4 |
| clock | present, frequency/jitter bounded | P6, X5 |
| primary inputs | stable outside their windows | L2 |
| radiation | Poisson, rate λ | P2 |

So the theorem is *robust* invariance: invariance under all disturbance signals within these bounds. The unbounded ones (P2's particle strikes) are exactly the ones that **can** kick you out of the invariant set — which is the correct formal statement of why SEU is the only surviving probabilistic term.

## Finite-dimensional reduction

Doing this in the infinite-dimensional field setting is PDE stability theory. Doing it on the lumped model is finite-dimensional and tractable — barrier certificates over a few state variables per cell.

**[L0/04](04-lumping-composition.md) is what licenses the reduction**, so the dependency is: well-posedness (00) → quasi-static reduction (01) → lumping (04) → this document in the lumped world, with (04)'s error term entering as a disturbance the invariance must be robust against. That last point is worth stating explicitly: the lumping error is not a separate approximation to be apologised for, it is a *disturbance signal*, and robust invariance already has the machinery to absorb it.

## Handoff

L0/05 establishes that transitions **complete**. It does not say how fast — that is L2, which quantifies the time bound (delay), checks it against the clock period, and turns (P) into the setup/hold constraints. So:

```
L0/05 : (P) holds with SOME bound
L2    : the bound is ≤ T_clk − setup − skew, and the design meets it
```

The bridge theorem is the composition of the two.

## Reading off the Boolean function

Given (I), (A) reduces to a finite check per cell: for each of the 2ⁿ input regime combinations, the output's invariant regime is `f(inputs)`. Standard cells have few inputs, so this is exhaustive and cheap **once the invariant sets exist** — the work is all in (I).

Note this needs only a *coarse* device model: you need the regimes to be separated, not accurate currents. That materially weakens what E1 must assert.

## Where the abstraction is not in force

- **During switching** — no `Z` regime holds; this is (P)'s domain and metastability's home.
- **Tri-state / pass-transistor nodes** — a floating node has no driver, so there is no attracting invariant set; the value is held by charge and decays. Needs separate treatment, and L3's one-driver-per-net well-formedness condition is the structural counterpart.
- **Below the design point** — `ΔE/kT = ½C(ΔV)²/kT` is not scale-invariant. At the 1.8 V design point the noise-margin barrier (ΔV ≈ 0.25 V, C ≈ 1 fF) is ~7,500 kT; near-threshold it falls to ~10³ kT. Still uncrossable, but 2,800 orders of magnitude vanish quietly. **The abstraction is robust because designers keep it robust**, so the noise margin must be a *checked* quantity, not an assumed one.

## Open problems

1. **State (I), (P), (A) formally** for the lumped model, with the regime sets explicit. This is the honest form of "the digital abstraction", and I do not know of it being written down anywhere for real CMOS.
2. **Construct barrier certificates** for a standard cell from an interval-valued device model. If this works for `inv_1` it plausibly works for the library.
3. **Adapt the free-energy Lyapunov functional to the boundary-driven steady state.** The equilibrium version is established; the driven version is what circuits need.
4. Time bounds from the Lyapunov decrease rate, and their relationship to the Liberty tables — these ought to be the same quantity derived two ways, which is a strong consistency check on L0/03.
5. Tri-state and pass-transistor cells: does the shipped configuration use any?

## First experiments

- **Write (I)/(P)/(A) for a single inverter** in the lumped model, with explicit regime sets and disturbance bounds. Small, concrete, and it will immediately show whether the framing survives contact with a real device model.
- Attempt a barrier certificate for that inverter (SOS programming is the standard route).
- Check whether the Lyapunov time bound and the Liberty delay agree in order of magnitude.

## Effort

The single-inverter (I)/(P)/(A) instance: weeks. The driven-steady-state Lyapunov adaptation (M7) is the open-ended piece.

## Reading

[Gajewski & Gröger](../BIBLIOGRAPHY.md#gajewski-groger-1986) on existence and asymptotics for van Roosbroeck, and the free-energy functional. [Prajna & Jadbabaie](../BIBLIOGRAPHY.md#prajna-jadbabaie-2004) on barrier certificates; [Parrilo](../BIBLIOGRAPHY.md#parrilo-2003) on SOS relaxations; [Harrison](../BIBLIOGRAPHY.md#harrison-2007) and [Martin-Dorel & Roux](../BIBLIOGRAPHY.md#martin-dorel-roux-2017) (ValidSDP) for prover-checked certificates. [Blanchini](../BIBLIOGRAPHY.md#blanchini-1999) on set invariance in control; [Lohmiller & Slotine](../BIBLIOGRAPHY.md#lohmiller-slotine-1998) for contraction. [Marino](../BIBLIOGRAPHY.md#marino-1981), "General theory of metastable operation" (IEEE Trans. Computers 1981) — the unavoidability theorem; [Kinniment](../BIBLIOGRAPHY.md#kinniment-2007), *Synchronization and Arbitration in Digital Systems*, for the engineering side. Standard hybrid-systems abstraction literature for the (I)/(P)/(A) pattern — this is a well-worn shape, just not usually applied this far down.
