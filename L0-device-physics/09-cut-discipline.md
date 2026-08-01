# L0/09 — The cut discipline

## Statement

The per-cell transistor-level combinatorics that license [04](04-lumping-composition.md)'s composition: **where may the network be cut, and why is every bistable inside a component rather than spanning components?**

This is a narrow document. An earlier draft collected *all* the combinatorial obligations here, which was a scoping error — most of them are about artifacts L0 does not own. See [the dispatch table](#where-the-other-conditions-are-discharged) for where they went.

## The object: channel-connected components

Bryant's decomposition ([BIBLIOGRAPHY](../BIBLIOGRAPHY.md#bryant-1984)). Partition nodes by connectivity through **source/drain** terminals; transistor **gates** are unidirectional inputs and therefore the boundaries.

```
inside a CCC   : bidirectional; needs full switch-level analysis; charge sharing possible
between CCCs   : unidirectional (through gates); restoring
```

This is exactly why cuts are legitimate only at CCC boundaries: only there is signal flow unidirectional, so a component's terminal contract composes without a fixed-point argument. It is the transistor-level counterpart of [05](05-digital-abstraction.md)'s restoration property — the same fact about where information flows one way.

## The three obligations, per cell (×~400)

**C1 — CCC structure.** Compute the partition: each cell's CCCs, and the graph they form under gate-terminal edges.

**C2 — PUN/PDN duality.** For static CMOS the pull-up and pull-down networks are series/parallel duals, so for every input assignment exactly one conducts. This is **V1(a)** — the *within-cell* half of "no conducting path from Vdd to GND" — and it is the half genuinely about transistors rather than about netlist topology. Checking it is a graph-duality test on the transistor network, not a simulation.

**C3 — bistables are CCC-internal.** Every cycle in the cell's CCC graph must lie inside one declared sequential element. A cycle spanning CCCs is an unintended latch or oscillator. This is what makes [04](04-lumping-composition.md)'s claim — "every bistable loop is internal to a component" — a checked fact rather than a hope.

All three need **extracted transistor netlists** for the library, the same extraction [03](03-cell-enclosures.md) requires. That dependency, not the algorithms, sets the cost.

## Where the other conditions are discharged

[07](07-operating-envelope.md)'s envelope is L0's, but most of its conditions are *discharged* against artifacts other layers own. The envelope **states** them; the owning layer **checks** them.

| condition | discharged at | how |
|---|---|---|
| V1(a) no Vdd→GND path *within* a cell | **L0/09** (here) | C2, PUN/PDN duality |
| V1(b) no contention *between* cells | **L3** | one driver per net — 26 nets, all tri-state, all in `pll.ringosc` |
| — acyclicity, no floating reads, inertness | **L3** | netlist well-formedness; 1 SCC, all in `pll.ringosc` |
| V2 crowbar current bounded | **L2** | `max_transition`, which also bounds Liberty's domain |
| V3 below avalanche | L0/07 | analytic (type B — ionisation integral) |
| V4 thermal | — | **not combinatorial**: workload-dependent |
| V5 tap coverage | **L1** | nearest-neighbour query on device positions |
| V6 electromigration | **L1** + activity model | combinatorial only once activity is fixed |
| V7 no manufacturing defect | — | P5, statistical, not checkable |
| X2 ECC bit interleaving | **L1** | per-word adjacency check on placement |
| — antenna area | **L1** | order-dependent: quantifies over *prefixes* of the process sequence |

Two things this makes visible. The envelope is a genuinely cross-cutting concern: L0 owns the *statement* of every safety condition but the *check* for only one of them. And the checks cluster in L1 and L3 — where the geometry and the netlist actually live — which is what one would want, and is the argument that the layer split is by artifact rather than by topic.

## Open problems

1. **Formalise the cut licence**: signal flow between CCCs is unidirectional, therefore composition at CCC boundaries is sound. This is the theorem [04](04-lumping-composition.md) needs and currently assumes.
2. Extract transistor netlists for the library and run C1–C3. Gated on the same extraction as [03](03-cell-enclosures.md).
3. **Non-static-CMOS cells break C2 as stated.** The shipped design uses `einvn`/`einvp` (tri-state) and `conb` (constant generators), neither of which is a complementary pair. Enumerate the exceptions and give each its own contract — this is a small, bounded list, but it must be written down rather than assumed away.

## First experiments

- Extract `inv_1`, `nand2_1`, `dfxtp_1` and compute CCCs by hand. Three cells sizes the ×400 obligation and tests whether C2's duality check is as mechanical as it looks.
- Check `dfxtp_1` against C3: its bistable should be exactly one CCC-internal cycle. If the decomposition does not show that cleanly, the cut discipline needs rethinking *before* it is relied on.

## Effort

Gated on the library transistor extraction shared with [03](03-cell-enclosures.md). The algorithms are near-linear and the per-cell problems are tiny; the cost is entirely in getting ~400 extracted netlists into usable form.

*(The "weeks, not years" claim in an earlier draft belonged to L3's netlist checks, not here — those are already done. See L3.)*

## Reading

[Bryant](../BIBLIOGRAPHY.md#bryant-1984) on switch-level simulation and the channel-connected-component decomposition — the source of the cut discipline. [Melham](../BIBLIOGRAPHY.md#melham-1993) for transistor-level CMOS in HOL.
