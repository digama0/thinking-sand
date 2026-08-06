# L2/03 — Corners and correlation (M4)

## Background

No two copies of this chip are identical. Fabrication is a statistical process — dopant counts, oxide thicknesses, and etch widths all vary — so transistors on one die are a few percent faster or slower than on another, and even neighbouring transistors on the *same* die differ slightly. On top of manufacturing variation, delay depends on operating conditions: a gate at 1.6 V and 100 °C is markedly slower than the same gate at 1.9 V and −40 °C. A timing verdict must therefore hold not for one circuit but for a whole *family* of circuits, indexed by a parameter space: the process outcome, the supply voltage, the temperature — **P, V, T** in the trade's abbreviation.

Industry's answer to "how do you check a continuum?" is the **corner**: a small set of consistent worst-case parameter assignments. The library ships each cell's timing characterised at points like `ss_1.60_100` — **s**low-NMOS/**s**low-PMOS process, 1.60 V, 100 °C — and its mirror `ff` (fast/fast) at high voltage and low temperature; run STA at every corner, and if all pass, declare the whole box covered. Note the structure of the move: rather than treating every gate's delay as independently uncertain (which double-counts the shared physics and compounds into hopeless pessimism — a die where alternate gates came out fast and slow is not a thing fabrication produces), corners evaluate *correlated* extremes, all gates slow together or fast together. Setup is checked where everything is slow, hold where everything is fast.

The logical leap in this practice is the reason this chapter exists. Checking the box's *vertices* covers its *interior* only if delay responds **monotonically** to each parameter — a function that peaked somewhere in the middle of the voltage range would evade every corner. Monotonicity is physically plausible, universally assumed, and never stated as the hypothesis it is; this book files it as open mathematics (M4). And the plot thickens on contact with data: the measured library tables are *not* monotone (the census below found genuine sign changes), for a reason that turns out to be an artifact of how "delay" is defined rather than of the physics — the resolution, which involves distinguishing the monotone waveform-level truth from its non-monotone tabulated shadow, is the heart of the chapter.

The remaining vocabulary of the trade, in one breath: **OCV** ("on-chip variation") is the per-cell random component left after die-wide correlation is accounted for — it accumulates down a path as √n, not n, because independent random errors partially cancel; a **derate** is the industry's flat percentage margin approximating that effect; and **CPPR** ("common path pessimism removal") is the correction that stops a shared clock-distribution prefix from being counted as slow for the launching flop and simultaneously fast for the capturing flop — the same physical wire cannot be both.

## Statement

Delays are not numbers but functions of process, voltage and temperature parameters. The question this file owns: **when is it sound to check finitely many parameter assignments?** Corner methodology — the entire industry's answer — assumes yes; the assumption is M4, and production data already violates its usual justification.

## The problem naive intervals have

Propagating per-cell delay intervals independently is sound and useless: the same physical uncertainty is counted independently at every use site, admitting assignments no die realises — this cell slow, its neighbour fast, the first slow again. The pessimism compounds along paths and closure becomes impossible at any frequency.

Corners fix this by evaluating **consistent assignments**: all cells slow together (`ss`), one voltage, one temperature. The library ships 17 of them. But finitely many consistent points bound the continuum only under a monotonicity premise:

> **(M4)** If the response (path delay, slack) is monotone in each parameter over the box, its extremes over the box are attained at vertices — so checking the corners is checking the box.

## Status: the premise is not free

`cell_fall(inv_1)` is **non-monotone in input slew** at two grid points (measured). Slew is not itself a corner parameter, but it is the composition variable through which corner parameters act on downstream delays — so the clean argument "everything is monotone in P/V/T, therefore corners suffice" has a hole in its transfer step.

### Where the non-monotonicity comes from — the physics is monotone, the abstraction is not

The derivative of `cell_fall` in slew across the load columns runs **−15.0, −6.2, +15.0, +53.5, +118.5, +226.9, +335.5 ps** (measured, slew step 0.65→1.5 ns) — a smooth zero crossing between 1.3 and 3.6 fF, i.e. two competing deterministic terms, not noise. The mechanism: delay is anchored at the input's **50% crossing**, but the NMOS conducts from V_th ≈ 25–30% VDD, so a slow ramp gives the output a *head start* proportional to slew; at light load the discharge is nearly instantaneous and the head start wins (delay decreases, eventually going negative — real Liberty tables contain negative delays); at heavier load the slew-degraded discharge time dominates and the usual sign returns.

At the **waveform level there is a genuine monotonicity theorem** by scalar ODE comparison: with `C·dV/dt = −I(V_in(t),V)` and `I` increasing in `V_in` (a property E1's interval model must state), pointwise-ordered input waveforms give pointwise-ordered outputs, hence monotone crossing times for *every* threshold. The non-monotonicity is manufactured by the quotient to `(t₅₀, slew)`: raising slew with the anchor fixed moves the waveform *earlier below* the anchor and *later above* it — the two ramps are **incomparable** in the pointwise order, light loads read the below-anchor part, heavy loads the above-anchor part. The abstraction fails to respect the order the physics preserves.

Consequently a faithful recomputation (L0/03's DAE enclosure) **will and must reproduce** the non-monotonicity — it is a property of the defined quantity, not of simulation noise — and the repair is one of:

1. **Enclosure over the quotient** (current plan): four-corner interpolation, slew intervals in [02](02-verified-sta.md). Sound, mildly pessimistic, no new theory.
2. **Per-arc sign certificates** from the library census; interval fallback only on flagged cells. The smooth zero crossing suggests the flagged region is small and characterisable.
3. **Waveform-envelope STA**: propagate earliest/latest waveform bounds instead of `(arrival, slew)` scalars — monotone by the comparison lemma at every composition step, with the scalar tables as a lossy abstraction. Industry's CCS/ECSM models are a gesture in this direction; for a *verified* engine it is arguably the principled foundation, and it dissolves the timing half of M4, leaving only the genuine P/V/T-parameter monotonicity question.

## The correlation structure

The parameter space is not one box. A sound model distinguishes three tiers, because they compose differently:

| tier | varies | composes as |
|---|---|---|
| **global** (process corner, V, T) | per die | one consistent assignment — the corner |
| **local** (OCV: per-cell random variation) | per cell, independent | **quadrature**: a 20-stage path sees √20 ≈ 4.5× the per-stage σ, not 20× |
| **shared-path** (clock prefix) | common to launch and capture | counted **once** — CPPR removes the double-debit |

Getting these tiers wrong in either direction is the classic failure: linear accumulation of local variation makes deep paths unclosable (the √n is what rescues them — the same nothing-accumulates pattern as everywhere else in the stack); ignoring shared clock prefixes double-charges skew and fails hold checks that actually pass.

The formal object: `Θ = Θ_global × Πcells Θ_local`, delay arcs as functions on `Θ`, and P4 as the axiom "the fabricated die's parameters lie in `Θ`" — which absorbs what E4's empirical half used to say. The soundness theorem quantifies over `Θ` and the corner check plus quadrature bound plus CPPR must jointly dominate it.

## Derates, honestly

Industrial OCV derates (flat ±% margins) are an *engineering approximation of the quadrature bound* — a linearisation applied uniformly. In a verified setting they are either derived (from the local-σ data, D3/D4) or replaced by the quadrature computation itself. Advanced-node POCV/statistical timing is this file's content done properly by industry — at 130 nm the simpler tiered model suffices, which is one more way the node choice keeps L2 tractable.

## Obligations

1. The vertex theorem with per-arc monotonicity certificates, and the measured fallback set.
2. The three-tier composition theorem: corner ∘ quadrature ∘ CPPR dominates `Θ`.
3. The seam with [02](02-verified-sta.md): slew merging interacts with tier 2 (merged slews across differently-derated paths), which is where graph-based analysis quietly loses soundness.

## First experiments

- The library-wide monotonicity census (shared with [02](02-verified-sta.md)) — it decides how big the fallback set is, i.e. whether M4 is a footnote or a project.
- Compute one real path's slack three ways — flat derate, quadrature, full interval — and compare the pessimism. This is the number that tells you what soundness costs at this node.

## Effort

Months, gated on the census. The mathematics is elementary; the work is stating the tier model so that P4's axiom content is exactly the empirical residue and nothing more.
