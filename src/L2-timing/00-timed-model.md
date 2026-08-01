# L2/00 — The timed model

## Statement

Fix the object the bridge theorem quantifies over: what "the physical circuit" means at L2's altitude. Everything in this layer is a statement about this model; its *adequacy* is not L2's problem — it is the conclusion of L0/03–05 and L1/03, delivered as `Contracts(N)`.

## The model

A network of components with typed terminals, driven by a clock arrival function.

**Combinational cells.** Each instance computes its Boolean shadow `f` under a bounded-delay rule: if the inputs are stable (in valid regimes) from time `t`, the output is stable at `f(inputs)` from some `t' ∈ t + [d_min, d_max]`, where `[d_min, d_max]` is the cell's contract arc evaluated at the actual (input slew, output load) — an **interval-valued function with an explicit domain**, not a constant. Outside the domain the contract says nothing (this is where F2 bites). Output slew is likewise an interval function, because it is the next stage's input.

**Wires.** Each net delays and degrades: an RC enclosure from L1/03 gives interval wire delay and slew degradation per (driver, receiver) pair.

**Flops.** The window rule: if the data input is stable throughout `[t_edge − t_su, t_edge + t_h]`, the output becomes that value within `[t_cq_min, t_cq_max]` after the edge. **Otherwise the output is unconstrained** — an arbitrary signal for an arbitrary time. This nondeterministic escape hatch is deliberate: it is metastability's slot in the model. Probability enters nowhere in the model itself; it enters only when [06](06-boundaries.md) bounds how often the unconstrained case arises (P1).

**Clock.** A **realised edge sequence** `(t_n)` — the edges as they actually occur, not `n·T_nom` — with an arrival function `arr_n : Flop → interval` per edge covering tree skew. All hypotheses are **per-interval**: `T_n = t_{n+1} − t_n ≥ T_min`, plus pulse-width bounds. This coordinate choice is load-bearing: the oscillator's phase random-walks unboundedly (X5's diffusion — `Var[t_n] ∝ n`), but its *increments* are stationary with tiny variance, so event-indexed semantics with per-interval hypotheses quotients the divergent mode out entirely. Absolute time exists only at L7's interface claims, each carrying its own accuracy term. Supplied by [05](05-clock.md); consumed by everything.

**Semantics.** A run assigns each net a signal (a function from time to regime-classified values) consistent with all component rules. The model is **possibilistic**: every downstream theorem quantifies over *all* runs, which is what makes interval delays sound and is the same universal-quantification move L0/00 made over field solutions.

## The value lattice: 0, 1, X

Between L0/05's physical regimes and `Mealy(N)`'s Booleans sits a three-valued logical layer, and naming it resolves several loose ends at once. **X** is the *untracked* value: in abstract-interpretation terms `γ(X)` = the entire safe region of regime space, with `γ(0)`, `γ(1)` the definite subregions. X covers settled-but-unpredicted values (a flop that violated its window and resolved cleanly to *some* rail), mid-swing transients, genuine saddle metastability, and unpowered — reserve the word "metastable" for the saddle phenomenon specifically; X is epistemic, not physical.

Three properties carry the weight:

- **X is drive-recoverable.** A controlling definite input forces a definite output (`AND(0,X)=0`); a flop capturing a definite value exits X. This is what distinguishes *untracked* from *broken*, and it is why reset works: power-up is all-X, and L4's initialisation obligation is precisely an **X-elimination proof** — the reset sequence, run in ternary semantics, reaches definiteness on every bit the invariant reads. Checkable by ternary symbolic simulation.
- **Reading X is demonic beyond "some fixed unknown Boolean."** During an unresolved window the same mid-rail wire can be read 0 by one receiver and 1 by another (thresholds differ), so the fresh-Boolean-variable model is **unsound** (it proves `x∧¬x=0`); Kleene ternary is sound because `X∧¬X=X`. The timed model is consistent with this for free: the escape hatch is at waveform level — one voltage, disagreement in the readers.
- **Z is deleted, not modelled.** Classical HDL logic is four-valued; W1/W2 (one driver per net, no floating reads — measured clean) are exactly the licence to drop the undriven value and work ternary. The unpowered case inside `γ(X)` is load-bearing here: Caravel's user area is a separate power domain, and the `mgmt_protect`/`mprj_logic_high` macros exist to keep reads of a possibly-unpowered domain definite.

This layer also gives hypothesis violations their honest meaning: an **overclocked core stays physically healthy** — combinational wires are ordinary late transients — but mass window violations flood the *captured state* with X. `Mealy(N)` over {0,1} stops describing the chip; the ternary machine over {0,1,X} still soundly does; the envelope still holds; recovery (restore the clock, reset, re-drive definiteness) remains provable. L7's operating-conditions clause should define "unspecified" as exactly this: envelope-bounded demonic nondeterminism — far weaker than C-style undefined behaviour.

## Why this level exists at all

One could state the bridge theorem directly over `Contracts(N)`'s dynamical semantics. The bounded-delay model is the *right intermediate* because it is exactly what STA computes over — the theorem "STA pass ⟹ closure hypothesis" ([02](02-verified-sta.md)) is only crisp if the model's delay vocabulary and STA's coincide. The model is the standard one from the asynchronous-circuits literature (bounded-delay), specialised with contract-valued rather than constant delays.

## Obligations

1. **Adequacy is inherited, and the seam must be stated**: every run of L0/04's contract-network semantics projects to a run of this model. This is a lemma against L0, not an axiom — but it must be written, because the two models' notions of "stable" (regime membership vs. voltage band) must be aligned once.
2. **Well-formedness inputs**: combinational acyclicity and one-driver-per-net (L3's W1/W3, measured clean after the PLL excision).
3. The domain conditions (`max_transition`, `max_capacitance`) are *part of the model*: a run that exits a contract's domain satisfies the model vacuously, so the theorems above it say nothing. Cf. F2.

## First experiments

- Write the model formally (signals, component rules, runs) for a three-cell circuit and check the flop escape hatch composes correctly — an unconstrained output must be *absorbable* by a downstream window hypothesis, not contagious by fiat.
- Prove the projection lemma (obligation 1) for a single inverter against L0/05's regime semantics.

## Effort

Small — weeks of definition work. It is scaffolding, but every other file in L2 types against it.
