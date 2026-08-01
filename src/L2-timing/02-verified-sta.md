# L2/02 — Verified STA

## Background

How does anyone check setup and hold across a design with hundreds of thousands of paths? Not by simulation — no test could exercise every path at its worst — but by **static timing analysis (STA)**: a tool that never runs the design at all. It treats the netlist as a graph whose edges are annotated with delay ranges, and computes, for every node, the earliest and latest possible moment a signal transition can arrive there — a longest-path/shortest-path computation over a DAG, polynomial and fast. Comparing each flop's latest arrival against its setup deadline and earliest arrival against its hold requirement yields a per-flop **slack** (margin: how much room is left, negative meaning violated), and a design "meets timing" when no slack is negative. Because it covers *all* paths by construction rather than the exercised ones, STA is the industry's **sign-off** instrument — the analysis whose verdict is the go/no-go for fabrication.

Where do the edge delays come from? From the **Liberty file**, the cell library's timing characterisation: for each cell, each arc (this input to this output), the library vendor ran analog circuit simulations across a grid of operating points and tabulated the results. A delay is *looked up*, in a table indexed by the two context quantities that L2/00's background introduced — the input's slew and the output's load — and since the arguments rarely land exactly on grid points, the tool *interpolates* between samples. That one word carries this chapter's hardest problem: interpolation is an estimate, not a bound, and the measured tables are not even monotone (a slower input edge occasionally yields a *smaller* tabulated delay — an artifact of how "delay" is anchored to waveform midpoints; the physics behind it is [03](03-corners.md)'s subject). A verified STA must replace every such convenience with something that is actually sound, and the three deviations catalogued below are where standard practice and soundness part ways.

"Verified" here means the strong sense established elsewhere in the book: not a carefully-written reimplementation, but an engine accompanied by a machine-checked theorem that *if the pass reports no violation, then hypothesis (2) of the bridge theorem holds in the timed model*. The algorithm is textbook; the content is the soundness statement — and, as so often in this project, the places where proving soundness forces the discovery that the standard practice being formalised quietly isn't.

## Statement

> If the STA algorithm, run over the contract arcs and the clock arrival function, reports no violation on any non-excepted path at any corner, then hypothesis (2) of the [bridge theorem](01-bridge-theorem.md) holds.

STA is a decidable, polynomial graph algorithm — longest/shortest path on a delay-annotated DAG. Verifying an implementation of it is ordinary work; the content of this file is the *soundness statement* connecting the algorithm to the model, and three places where standard practice is subtly unsound and the verified version must deviate.

## The algorithm

Forward pass over the flop-cut DAG, per corner:

```
arr(n)   = max over fanin edges e of  [ arr(src e) + cell_delay_e(slew_in, load) + wire_delay_e ]
slew(n)  = slew table of the winning/merged arc          ← propagates WITH arrival
```

then backward required times from each flop's window (`arr_clk(f) − t_su` for setup at the slow corner, `arr_clk(f) + t_h` for hold at the fast corner), and `slack = required − arrival`. Hold uses min-delay arcs and the early/late clock split; CPPR credits the shared clock-path prefix once ([03](03-corners.md)).

Composition is a *traversal*, not a sum: both table arguments are context-dependent (load from L1's extraction, slew from the upstream cell), so per-cell delays cannot be precomputed. Setup/hold constraints are themselves 2-D tables of (data slew, clock slew).

## Three unsoundnesses in standard practice

The verified version is not a transcription of an industrial engine; these must be done differently.

**1. Interpolation must use the enclosing box, all four corners.** `cell_fall` is non-monotone in input slew at two grid points of the *simplest cell in the library* (measured — FINDINGS). Bilinear interpolation between samples is a model choice, not a bound; the sound rule is the max/min over all four surrounding grid points, and even that is a bound only given an inter-sample variation assumption, which E2's discharge route (L0/03) must supply as a derivative bound on the table.

**2. Worst-slew merging is conservative only under monotonicity.** Graph-based STA propagates a single merged (worst) slew at reconvergence. "Worst slew ⟹ worst delay" is exactly the monotonicity that the measured tables violate. The sound options: propagate slew *intervals*, or fall back to path-based analysis on the paths where the table is non-monotone. This is M4 surfacing inside the algorithm, not just in the corner methodology.

**3. Negative delays are legitimate, but causality bounds them — check it.** A delay entry is the difference of two 50%-anchor *labels*, and at light load / slow slew the output's label can precede the input's (conduction starts at V_th, below the anchor — [03](03-corners.md)'s mechanism), so `d < 0` is bookkeeping, not back-propagation. But the output cannot respond before the input *starts* moving, so `d ≥ −(t₅₀ − t_start)` ≈ `−O(slew)` with the coefficient set by the library's trip-point conventions. An entry below that bound is a characterisation error. This is a mechanical table-validity sweep, and it matters doubly for **hold**: negative *min*-delay entries shorten short paths, so an erroneously negative entry manufactures phantom hold violations — or masks real ones if clamped to zero, which some tools do and which is exactly the kind of silent repair a verified engine must not perform.

**4. Domain checking is part of the pass, not a lint.** Every table lookup must assert its arguments lie inside the characterised region (`max_transition`, `max_capacitance`). Outside it the industrial tool extrapolates and the result is **vacuous rather than wrong** — the shipped design's `t-max` corner does exactly this (F2). In the verified engine an out-of-domain lookup is a *failed hypothesis*, reported as such.

## Plumbing to the exceptions

STA does not decide which paths matter; the SDC does. The soundness statement is therefore conditional: the pass certifies closure **on non-excepted paths**, and every excepted path must carry a justification per its class ([04](04-sdc-exceptions.md)). The verified engine's job includes emitting the *exact* excluded-path set, so that (3)'s obligation is discharged against what was actually skipped rather than against what the Tcl was believed to mean.

## Obligations

1. The soundness theorem above, against [00](00-timed-model.md)'s model — the real content; the traversal itself is textbook.
2. The interpolation enclosure with the derivative-bound side condition (from L0/03).
3. Slew-interval propagation or a per-arc monotonicity certificate (with [03](03-corners.md)).
4. Re-derive the shipped design's timing verdict with the verified rules and compare against the OpenSTA reports in `signoff/` — agreement is evidence, disagreement is a finding either way.

## First experiments

- Run the interpolation enclosure over the full SKY130 HD library: for every cell, arc, corner, check monotonicity in both table arguments and measure how wide the four-corner enclosure is versus bilinear. Mechanical; directly sizes how much pessimism soundness costs, and produces the M4 violation census as a by-product.
- Reproduce one path's arrival time by hand from the tables against the signoff report's value.

## Effort

The engine: months (it is a few hundred lines plus the table machinery). The soundness proof: the larger half, and it depends on [00](00-timed-model.md) being written first.
