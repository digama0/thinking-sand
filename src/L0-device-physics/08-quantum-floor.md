# L0/08 — The quantum floor

## Background

Every layer so far has rested on the one below it; this chapter asks what the *bottom* layer rests on, and the answer requires a tour of the physics tower beneath drift–diffusion. Reading upward: the deepest available description of electrons and light is **QED** (quantum electrodynamics), a *quantum field theory* — the framework in which particles are excitations of fields and can be created and destroyed. Above it sits ordinary **many-body quantum mechanics**: a fixed roster of electrons and nuclei interacting by Coulomb attraction, no creation or annihilation — the description in which chemistry lives. Above that, **band structure**: in a crystal's periodic potential, the electron energy levels organise into bands, and the material's electronic character (metal, insulator, semiconductor) is read off from how the bands fill — the single most important organising idea in solid-state physics. Above that, **semiclassical transport**: treat carriers as classical particles with band-modified properties, colliding randomly with lattice vibrations, governed by the **Boltzmann equation** of kinetic theory. And its slow-scale limit is drift–diffusion, where L0/00 came in.

The chapter's question is whether this tower can be made into an unbroken chain of *theorems* — and the honest answer needs a distinction the reader may not have met: between a physical theory's *predictive success* and its *mathematical existence*. QED is the most precisely confirmed theory in science; it is *also*, as mathematics, not known to exist — its calculations are manipulations of divergent series about which no one has constructed the underlying object. ("Constructive quantum field theory," the discipline that builds QFTs rigorously, has succeeded only for simplified models in reduced dimensions; for the full theories the construction problem is worth a Clay million, and for QED specifically the expectation is that no construction exists — the theory is meaningful only as an approximation with a built-in cutoff.) A chain of theorems cannot be anchored to an object that does not mathematically exist, so the chain must be *cut* somewhere, and the chapter's argument is about where: one level up, at the many-body Coulomb Hamiltonian, which **is** a theorem-grade object — its good behaviour (the "stability of matter": why bulk material doesn't collapse, why energy is proportional to particle count) is celebrated rigorous mathematics.

Two more pieces of vocabulary for the middle rungs. The reductions between levels are **scaling limits** — theorems of the form "in the limit of weak coupling / long times / many particles, the finer description converges to the coarser one" — and several of the tower's rungs have genuine theorems of this type, with the honest caveat that they are asymptotic statements in idealised settings, not effective bounds on real silicon. And **decoherence** is the mechanism by which quantum superposition becomes irrelevant at chip scale: a node's charge state is coupled to a hot, messy environment of lattice vibrations that continuously "measures" it, destroying any superposition of logic states in femtoseconds. It is the reason the chapter can answer "what about quantum weirdness in the logic?" with a bounded argument rather than a shrug.

## Statement

Fix what the bottom row of [00](00-field-problem.md)'s hierarchy rests on, and answer a question the factoring invites: *can one prove that a QFT solution exists whose divergence from the statistical approximation is negligible at this scale?*

**Answer: no — and the structure of the "no" is the content of this document.** No new axiom is introduced. The document exists to justify *where* the tower's one empirical axiom sits (inside E1), and to preempt "but what about quantum effects" with a precise scope statement.

## Why the question is not well-posed at the bottom

QED in 3+1 dimensions has **no nonperturbative construction**. Constructive QFT stops at superrenormalisable models; Yang–Mills existence is a Clay problem; and for QED the expectation is worse than "hard" — the Landau pole suggests it exists only as an effective theory with a cutoff, and the [Aizenman–Duminil-Copin](../bibliography.md#aizenman-duminil-copin-2021) triviality theorem for `φ⁴` in exactly four dimensions (2021) is the rigorous version of that suspicion for the simplest analogous theory. So "a QFT solution of the chip" is not currently a mathematical object one could prove things about. This is not a gap this project could close or should try to.

## The rigorous anchor is one level up

The **nonrelativistic many-body Coulomb Hamiltonian** — every electron and nucleus in the die, pairwise Coulomb interaction — *is* a well-defined mathematical object: self-adjoint ([Kato](../bibliography.md#kato-1951) 1951), bounded below with the right extensivity (**stability of matter**, [Dyson–Lenard](../bibliography.md#dyson-lenard-1967), then [Lieb–Thirring](../bibliography.md#lieb-thirring-1975); book treatment in [Lieb & Seiringer](../bibliography.md#lieb-seiringer-2010)). Everything in this project could in principle be anchored there.

Below the anchor, the QM ↔ QED gap is an effective-field-theory power-counting statement, validated by the most precisely tested predictions in science (electron g−2 agrees with experiment to parts in 10¹²). That is an empirical claim, not a theorem, and it can never become one from above.

**The structural consequence, in this project's terms:** the physics tower contributes exactly one empirical axiom *no matter how deep you dig* — digging deeper only relocates it. So the position of the axiom is a free choice, and the rational choice is the level where the empirical validation is strongest and the mathematics above it is theorem-dense. That is the many-body / semiclassical boundary — i.e. essentially where E1 already sits. Pushing E1 downward buys epistemically nothing and costs open mathematics.

## What is a theorem above the anchor

The reductions between the anchor and drift–diffusion, with status:

| reduction | status | who |
|---|---|---|
| many-body → band structure / one-particle | **mean-field settings only** | [Catto–Le Bris–Lions](../bibliography.md#catto-lebris-lions-1998) (crystals); [Cancès–Deleurence–Lewin](../bibliography.md#cances-deleurence-lewin-2008) (defects) |
| one-particle in random medium → **linear** Boltzmann | **theorem** (weak-coupling limit) | [Erdős–Yau](../bibliography.md#erdos-yau-2000) 2000; beyond kinetic time [Erdős–Salmhofer–Yau](../bibliography.md#erdos-salmhofer-yau-2008) |
| semiclassical limit machinery | **theorem** (Wigner measures) | [Gérard–Markowich–Mauser–Poupaud](../bibliography.md#gerard-markowich-mauser-poupaud-1997) |
| Boltzmann → drift–diffusion | **theorem** (diffusion limit) | [Poupaud](../bibliography.md#poupaud-1991); [Golse–Poupaud](../bibliography.md#golse-poupaud-1992); [Ben Abdallah–Degond](../bibliography.md#ben-abdallah-degond-1996) (energy-transport) |
| nonlinear collision terms (e–e, Pauli exclusion; phonons in full) | open | — |

Two honest caveats. Every "theorem" above is an asymptotic scaling limit over idealised settings with non-explicit constants — the same status as M6, the quasi-static constant. And the two open rows mean there is no unbroken theorem-chain from the anchor to van Roosbroeck; the chain is theorem-dense, not theorem-complete.

## The ideal theorem could not say "negligible" anyway

Suppose every link were proved. The statement still could not be "the physical behaviour diverges negligibly from the drift–diffusion (DD) solution," pointwise, for a physical reason: **the statistical approximation's fluctuations are observable at this node.**

A logic `1` at 1.8 V on ~1 fF is ~10⁴ electrons. Central-limit-theorem-scale fluctuations around the mean field are therefore ~1%, and they have names: **shot noise** (carrier granularity), **random telegraph noise** (single trapped charges modulating a transistor's current — individually visible; [Kirton & Uren](../bibliography.md#kirton-uren-1989)), **discrete dopant fluctuation** (a channel holds thousands, not 10²³, dopant atoms; [Asenov](../bibliography.md#asenov-1998)'s atomistic simulations quantify the resulting threshold scatter). None of these is negligible pointwise; all are bounded by margins and corners (E4) — the correct theorem has the **P3 shape**: `P(deviation > margin)` bounded by something astronomically small, then discharged. Fluctuations are bounded against margins, never proved absent.

## Quantum effects already inside E1

At 130 nm, quantum mechanics is not a correction waiting to be bounded — parts of it are **first-order device physics already folded into the compact model**:

- **Gate tunnelling.** BSIM4 carries explicit gate-current models. At SKY130's ~4 nm oxide direct tunnelling is still small (it becomes first-order below ~3 nm), but the model content is there and the leakage budget should cite it rather than ignore it.
- **Quantum confinement in the inversion layer** shifts the threshold voltage ([Ando–Fowler–Stern](../bibliography.md#ando-fowler-stern-1982) is the classic treatment); BSIM4 has the correction terms.
- **Band-to-band tunnelling / GIDL** — likewise modelled.

So the E1 clause added in [00](00-field-problem.md) — "the PDE being dodged would itself have been adequate" — should be read as: adequate *with these quantum channels routed around the PDE and into the fit*. The semiclassical transport picture itself is comfortable here: the thermal de Broglie wavelength in silicon is ~8 nm against a ≥150 nm channel.

## Why the digital state is classical at all

Two things a physicist should say once, then discharge:

**Decoherence.** A node voltage is a collective coordinate of ~10⁴ electrons coupled to a dissipative lattice at 300 K; superpositions of logic states decohere on femtosecond scales ([Zurek](../bibliography.md#zurek-2003)'s einselection — the charge on a node is about as robust a pointer observable as exists). There is no coherent-superposition failure mode to model; whatever quantum noise survives is already inside the thermal and RTN terms.

**Macroscopic quantum tunnelling of a logic state.** The quantum analogue of the thermal Kramers term: rate `~exp(−S/ħ)` with `S` the action of a collective many-electron tunnelling path — larger-than-astronomically suppressed, far beyond even P3's `exp(−7500)`. (MQT is real physics, observed in Josephson junctions at millikelvin — [Caldeira–Leggett](../bibliography.md#caldeira-leggett-1981) theory, [Devoret–Martinis–Clarke](../bibliography.md#devoret-martinis-clarke-1985) experiments — which is exactly the regime a logic node is not in.) Same verdict as P3: **prove the exponent is enormous, delete the term.**

## Conclusion

- No additional axiom. The quantum floor is absorbed into E1, and this document is the argument that E1 is the *right place* for the tower to bottom out.
- "Prove a QFT solution exists and diverges negligibly" fails three ways: the object does not exist mathematically (QED), the reduction chain has open links (band structure beyond mean field, nonlinear collisions), and the true statement is probabilistic with observable fluctuations bounded by margins, not negligible divergence.
- What *is* available, and matches the project's pattern everywhere else: a rigorous anchor (stability of matter), a theorem-dense chain of scaling limits above it, and P3-style discharge of the residual quantum terms.
- The data-side consequence (axioms.md, "Empirical inputs"): the practical data floor is **bulk material data, not fundamental constants** — ab initio methods reach percent accuracy at best on the quantities that matter, so material parameters remain measured even if the whole reduction chain were proved. Fundamental constants themselves are exact (2019 SI) or known to ~10⁻¹⁰, and enter L0's arguments directly only through kT, e, and ε₀.

## Open problems

None blocking. Optional, in descending value:

1. Explicit-constant versions of the kinetic and diffusion limits (parallel to M6) — contributions to mathematical physics independent of this project.
2. A stated numeric bound, from the SKY130 model cards, on gate leakage + RTN + discrete- dopant scatter against the noise-margin budget — turning "inside E1" into a checked number.
3. Model hygiene: verify DD-with-BSIM4-corrections does not double-count any quantum channel (the corrections were fitted, not derived, so overlap is possible in principle).

## First experiments

- Pull the gate-current and threshold-correction parameters from the SKY130 BSIM4 model cards and compare their contribution against the noise margin — this is open problem 2 and is an afternoon, not a year.
- Estimate discrete-dopant σ(V_t) for the SKY130 device geometry from [Asenov](../bibliography.md#asenov-1998)-style scaling and check it is comfortably inside the corner spread (E4) — i.e. that variability corners already carry the granularity of the statistical approximation.

## Effort

Days to state — this file exists to prevent effort, not to consume it.

## Reading

[Lieb & Seiringer](../bibliography.md#lieb-seiringer-2010), *The Stability of Matter in Quantum Mechanics* (2010); [Kato](../bibliography.md#kato-1951) (1951) for self-adjointness. [Glimm & Jaffe](../bibliography.md#glimm-jaffe-1987), *Quantum Physics*, for what constructive QFT can and cannot do; [Aizenman & Duminil-Copin](../bibliography.md#aizenman-duminil-copin-2021) (Ann. of Math. 2021) for `φ⁴₄` triviality. [Erdős & Yau](../bibliography.md#erdos-yau-2000) (CPAM 2000) — linear Boltzmann from random Schrödinger; [Erdős–Salmhofer–Yau](../bibliography.md#erdos-salmhofer-yau-2008) (Acta Math. 2008). [Gérard–Markowich–Mauser–Poupaud](../bibliography.md#gerard-markowich-mauser-poupaud-1997) (CPAM 1997) on Wigner measures. [Poupaud](../bibliography.md#poupaud-1991) (1991) and [Ben Abdallah & Degond](../bibliography.md#ben-abdallah-degond-1996) on diffusion and energy-transport limits; [Markowich–Ringhofer– Schmeiser](../bibliography.md#markowich-ringhofer-schmeiser-1990), *Semiconductor Equations*, ties the chain together. [Ando, Fowler & Stern](../bibliography.md#ando-fowler-stern-1982) (Rev. Mod. Phys. 1982) on inversion-layer quantisation. [Kirton & Uren](../bibliography.md#kirton-uren-1989) (Adv. Phys. 1989) on RTN; [Asenov](../bibliography.md#asenov-1998) (IEEE Trans. Electron Devices, 1998 onward) on random dopant fluctuation. [Zurek](../bibliography.md#zurek-2003) (Rev. Mod. Phys. 2003) on decoherence and einselection. [Caldeira & Leggett](../bibliography.md#caldeira-leggett-1981) on dissipative MQT; [Devoret, Martinis & Clarke](../bibliography.md#devoret-martinis-clarke-1985) for the experiments.
