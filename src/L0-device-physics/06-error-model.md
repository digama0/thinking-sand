# L0/06 — The error model

## Statement

Determine what survives as a probabilistic term after the digital abstraction is established, and hand it upward in a form the rest of the project can consume.

**Result: exactly one *failure* term survives at the physical layer, and it is Poisson.** One *disturbance* also survives — clock phase diffusion — but it enters as a budget line, not a failure probability; see below.

## The central distinction

Two kinds of ε get confused, and they behave completely differently:

- **Probabilistic ε** — exponentially suppressed by a mechanism, multiply by scale freely, **discharge and forget**.
- **Additive-physical ε** (capacitance, IR drop, skew) — accumulate linearly, need a *convergent decay* argument, and the bound must be on the **aggregate**, not per element.

Confusing them is the most common modelling error in this area. Thermal noise is the first kind; coupling capacitance is the second (see L1/X3).

## Mechanisms sorted by functional form

| mechanism | form | scaling | verdict |
|---|---|---|---|
| thermal / kT/C | Gaussian tail, 40–125σ | area × time | **discharged** |
| oscillator phase drift | Wiener, σ² ∝ t | the one non-restoring mode | **carried** as jitter budget (X5 → P6) |
| timing variation (PVT) | distribution over dies | → *yield* | caught by test |
| metastability | exp(−t/τ) | localised to synchronisers | design-controlled |
| **particle strikes (SEU)** | **Poisson** | **linear in area × time** | **carried** |

## Thermal noise: discharge it, do not carry it

Kramers escape from a basin goes as `exp(−ΔE/kT)`. The barrier is

```
ΔE/kT = ½(ΔV/v_n)²,   v_n = √(kT/C) ≈ 2 mV at C ≈ 1 fF
ΔV ≈ 0.25 V  ⟹  ΔE ≈ 7,500 kT  ⟹  P ≈ exp(−7500) ≈ 10⁻³²⁵⁷
```

Ten trillion transistors at 10 GHz for the age of the universe is ~10⁴⁰ opportunities. Not close — and the exponent is *quadratic* in the margin while the scale factor is only linear in count, so no amount of scale reaches it.

**A formal model should prove the barrier exceeds N·kT and then delete the term**, not carry an epsilon around. Full rail-to-rail (½C·Vdd² at 1.8 V) is ~4×10⁵ kT.

### The one escape from the discharge: the oscillator's phase mode

The Kramers argument requires a restoring force — it bounds *escape from a basin*. There is exactly one deliberately non-restoring direction in the whole system: the phase of the clock oscillator. Time-translation symmetry of a limit cycle forces a zero Floquet exponent along it, so thermal noise projected onto phase is not suppressed at all — it accumulates as a Wiener process, variance linear in time ([Demir–Mehrotra–Roychowdhury](../BIBLIOGRAPHY.md#demir-mehrotra-roychowdhury-2000) is the standard theory). **Jitter is thermal noise made visible by the absence of restoration.** The PLL's feedback bounds the drift relative to its reference; the per-cycle residue is Gaussian with picosecond-scale σ against a much larger timing margin, so its *exceedance* is discharged like every other Gaussian tail — but the σ itself is a real, surviving, derivable quantity, and it is where X5's genuinely physical content lives (see M8). The discharge above is therefore correct for every regime-holding node and would be unsound applied to the clock generator.

## Why particles are different in kind

A 10 MeV neutron carries ~4×10⁸ kT against a 7,500 kT barrier — about 10⁵× the energy needed. It is **not a rare fluctuation of the thermal distribution**; it is an energy injection from outside the bath. So the probability is not `exp(−barrier/kT)` but simply (arrival rate) × (cross-section) × (fraction depositing more than Q_crit).

General lesson worth carrying to every layer: **in a well-designed restoring system, the tail of the distribution you modelled is never what kills it.** What kills it is events drawn from a different distribution.

Rates: [JEDEC](../BIBLIOGRAPHY.md#jesd89a)'s sea-level reference is ~13 neutrons/cm²/hr above 10 MeV; historical SRAM figures are ~10⁻³–10⁻⁴ FIT/bit. At 10⁹ bits that is ~10⁶ FIT ≈ one upset per thousand hours. Observable, which is why ECC exists.

## Metastability breaks the abstraction in time, not in value

Restoration guarantees the flop reaches a rail — there is no steady-state half-bit. But the *time* is unbounded: `P(unresolved after t) ≈ (T₀/T_c)·exp(−t/τ)`. During the unresolved window, **different downstream gates can read the same mid-rail voltage differently**. The signal is not a boolean, because observers disagree.

That is strictly worse than a random bit, and it is why P1 is permanent. The mitigation is to *localise* it: enumerate every asynchronous input and clock-domain crossing (L2), and make the theorem explicitly conditional on resolution.

Calibration note: the ~10⁻⁴³/cycle figures assume a *correctly designed* synchroniser with a full period of settling. A grossly violated path has percent-level rates.

## Masking is computable, not merely measurable

Not every upset becomes an error. Four derating layers, three of them derivable:

- **Electrical** — the induced pulse attenuates through gates (restoration working *for* you).
- **Logical** — the flipped node does not affect the output. A Boolean question about the netlist.
- **Temporal** — the glitch misses every setup/hold window. A timing question.
- **Architectural** — dead register, wrong-path instruction, predictor state. The "prove it irrelevant" category from L5.

Together these knock the raw rate down by one to two orders of magnitude (AVF commonly 10–30%). Industry *measures* this by fault injection. All four are in principle derivable from artifacts this project already formalises — **deriving derating factors rather than measuring them is a plausible novel contribution**, and it is unusually well-positioned because L3 gives the netlist, L2 the timing, and L5 the architectural irrelevance argument.

## The ECC interface

What L0 hands upward is a **discrete channel** — occasional bit flips at Poisson times. Everything above is coding theory, which is why ECC is a digital-regime object.

Two obligations of very different character:

- **Functional correctness** — encoder/decoder, minimum distance over GF(2): distance 3 suffices for correct-one ([Hamming 1950](../BIBLIOGRAPHY.md#hamming-1950)), but SECDED requires **distance 4** (the extended Hamming code) — the extra parity bit is what makes double errors *detected* rather than miscorrected. A finite algebraic fact, exhaustively checkable. Among the cheapest obligations in the project.
- **Sufficiency** — given λ, a scrub interval, and word size, bound P(uncorrectable). A renewal/Markov argument, and **the only place the project needs a probabilistic reasoning layer** alongside the deterministic refinement. The model is small enough for a probabilistic model checker ([PRISM](../BIBLIOGRAPHY.md#prism-2011), [Storm](../BIBLIOGRAPHY.md#storm-2017)) to compute the bound exactly, and the in-prover route exists too — [Hölzl](../BIBLIOGRAPHY.md#holzl-2017)'s Markov-chain formalisation in Isabelle, or Mathlib's probability library — so this layer is tooling choice, not research.

The payoff is structural: raw upsets give failure probability *linear* in λ·N·T; SECDED plus scrubbing means failure needs *two* errors in one word within a scrub interval, so the rate goes as (λ·T_scrub)² — **quadratic, with a tunable coefficient.** (Two errors is a *detected-uncorrectable* loss; silent miscorrection needs three. The sufficiency statement should distinguish the two, since they have different consequences upstream.) That is how the abstraction survives a real, nonzero, measurable upset rate.

## X2 — the sharpest cross-layer obligation in the project

ECC's independence assumption ("errors within a word are independent") is discharged by **bit interleaving in the layout** — physically adjacent cells assigned to different ECC words, because one particle can upset several neighbours. Multi-cell upsets are a measured, growing fraction of events as cells shrink ([Ibe et al.](../BIBLIOGRAPHY.md#ibe-2010) have tracked the scaling across nodes), so the required interleaving distance is node-dependent — the hypothesis has a number in it, not just a topology.

The netlist cannot see geometry. The code's algebra cannot see particles. **The obligation lives in the GDS and is invisible to every level one would naturally formalise.** It is the clearest example of a correctness argument spanning from geometry to coding theory with nothing in between able to see both ends.

## Open problems

1. The probabilistic reasoning layer and its interface to deterministic refinement.
2. Deriving AVF/derating from the formalised netlist and timing model.
3. Formalising X2 — stating an interleaving property over the layout and connecting it to the code's independence hypothesis.

## First experiments

- Write the four-mechanism model formally, with the thermal term explicitly **discharged**, and check the layering composes into a single statement of the form `P(T-cycle execution refines spec) ≥ 1 − (λ·A·T·AVF + N_sync·P_meta + …)`.
- Check whether the shipped design has ECC at all (`RAM128`), and if not, what the raw FIT budget is and whether it matters for the claim being made.
- Enumerate every asynchronous input and CDC in the design — this list *is* P1's scope, and L2 needs it anyway.

## Effort

Weeks for the formal model; the probabilistic reasoning layer it needs is machinery no other layer requires.

## Reading

[von Neumann](../BIBLIOGRAPHY.md#von-neumann-1956) (1956). [Hamming (1950)](../BIBLIOGRAPHY.md#hamming-1950) for the code. [Mukherjee et al.](../BIBLIOGRAPHY.md#mukherjee-2003) (MICRO 2003) on architectural vulnerability factor. [JEDEC JESD89A](../BIBLIOGRAPHY.md#jesd89a) for the standard terrestrial flux reference. [Ibe et al.](../BIBLIOGRAPHY.md#ibe-2010) on multi-cell upset scaling — the empirical content behind X2. [PRISM](../BIBLIOGRAPHY.md#prism-2011) / [Storm](../BIBLIOGRAPHY.md#storm-2017) for the renewal-model computation; [Hölzl](../BIBLIOGRAPHY.md#holzl-2017)'s Isabelle Markov chains for the in-prover version. [Demir, Mehrotra & Roychowdhury](../BIBLIOGRAPHY.md#demir-mehrotra-roychowdhury-2000), "Phase noise in oscillators: a unifying theory" (IEEE TCAS-I 2000) — the phase-diffusion structure behind the jitter exception.
