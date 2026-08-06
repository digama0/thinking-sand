# L1/05 — The geometric checks

## Background

This chapter collects the layer's finite, mechanical checks, and three of them guard against physical phenomena that have not yet been introduced. Each is a classic chip-killer with a geometric cure.

**Latch-up** is CMOS's oldest self-destruct mode. The wells and diffusions that form a chip's transistor pairs *also*, unavoidably, form a parasitic four-layer PNPN structure — a **thyristor**, a device whose defining property is that once triggered it conducts hugely and latches on, held by its own feedback until power is removed. Triggered (by a voltage transient or a particle strike), the parasitic thyristor shorts the supply rails through the silicon, and the chip either browns out or cooks. The cure is **well taps**: frequent, low-resistance connections tying each well solidly to its supply rail, which starve the parasitic structure of the voltage drop it needs to trigger. "A tap within distance d of every device" is the design rule; the deeper reading — developed in L0 — is that tap coverage removes a *second solution branch* of the device equations, making the transistor's nominal behaviour the only one available.

**Multi-cell upsets** concern memory protected by **ECC** (error-correcting codes — extra check bits stored alongside each data word, enough to correct any single flipped bit). The code's mathematics assumes at most one bit of a word fails at a time; but a single particle strike ionises a *region*, and can flip several physically adjacent cells at once. The cure is **interleaving**: place the bits of one logical word physically far apart, so one strike's radius covers at most one bit per word. Note what kind of fact this is — a coding-theory assumption discharged by *placement geometry*, checkable in neither the netlist (which has no positions) nor the code's algebra (which has no particles), only in the layout.

The **antenna effect** is the strangest of the three: a defect mechanism of the *unfinished* chip. During fabrication, plasma etching deposits electric charge on whatever metal is exposed; a long wire connected, at that mid-fabrication moment, only to a transistor gate funnels all its collected charge into the gate's few nanometres of oxide and punctures it — destroying the transistor before the chip is even complete. Whether this happens depends on the *order* layers are built: the wire's eventual connection to a protective diode may not exist yet when the charge arrives. Hence the oddity flagged below: the antenna check quantifies over prefixes of the build sequence — it is a property of the fabrication history, not of the finished geometry, and the finished layout alone cannot express it.

## Statement

The finite, decidable obligations L1 owns. These are the *discharge points* for conditions other layers only **state** — see [L0/09](../L0-device-physics/09-cut-discipline.md)'s dispatch table. All are near-linear; none needs a PDE. They are gated on extraction and on having placement data, not on difficulty.

## The checks

### G1 — tap coverage (discharges V5)

```
∀ device d.  ∃ well tap t.  dist(d, t) ≤ d_max   (same well)
```

Nearest-neighbour query over device and tap positions; `O(n log n)` with a k-d tree. A finished layout carries tap cells by the tens of thousands (the flow places them on a fixed grid), so the tap set is large and the query is the whole cost.

**This is a hypothesis of well-posedness, not a reliability rule.** Latch-up is a *second solution branch* of the stationary device PDE (M1); tap coverage destroys the parasitic thyristor and hence the branch. Filing it under reliability is the field's convention; it is what makes "the transistor's I-V characteristic" well-defined at all.

### G2 — ECC bit interleaving (discharges X2)

```
∀ ECC word w.  ∀ bits b ≠ b' ∈ w.  dist(cell(b), cell(b')) > R_MCU
```

where `R_MCU` is the measured multi-cell-upset radius — a **D3/D4-class empirical input**, not something derivable.

**The sharpest cross-layer obligation in the project.** ECC's independence assumption is discharged by layout geometry: the netlist cannot see placement, the code's algebra cannot see particles, and the obligation lives in the GDS where neither can look. Needs the ECC word structure as an input, which comes from L3/L5, so it is the one check here that is not self-contained.

Applicable only if the design has ECC — the SRAM macros and the tile configuration should be examined before assuming so (the tiny configuration elides ECC).

### G3 — antenna ratio

```
∀ net n. ∀ layer ℓ. ∀ prefix P of the process order.
    area(metal(n) ∩ P) / area(gate(n) ∩ P)  ≤  ratio_max
    ∨  ∃ protection diode connected to n within P
```

**The odd one out: it quantifies over prefixes of the build sequence, not over the finished layout.** Charge accumulated on floating metal damages a gate oxide *during processing*, and only until the protecting diode's layer is deposited. So the finished layout carries no record of whether the check passes — the process *order* is an input.

It is why this design carries **44,541 antenna diodes** (`diode_2`), and it is the clearest case in L1 of a rule that cannot be phrased as a property of `M` alone.

### G4 — min width, spacing, enclosure

Exactly hypotheses (H1), (H2) of [01](01-topology-preservation.md) and (D1)–(D3) of [02](02-extraction-lvs.md). Polygon morphology plus connected components; near-linear with a scanline.

Recall the sharpening: **min-spacing ⟺ (H2)**, but **min-width is necessary and not sufficient for (H1)** — the notch and neck rules supply the rest, because erosion of a connected set can disconnect at a neck.

### G5 — shielding coverage (the design-side hypothesis of M2)

```
∀ net pairs (n,m) beyond the truncation radius.
    grid metal is interposed, with aperture parameter ≤ a and pitch ≤ p
```

The combinatorial half of [04](04-screening.md): the analysis supplies `α(a/p)`, this check supplies that the geometry really provides the barriers the cascade assumes. Sparsely-gridded regions would fail it locally, and nobody currently looks.

### G6 — fill is tied, not floating

```
∀ metal fill shape f.  f is connected to a rail
```

Floating conductors **relay** rather than screen — they couple in and out, shortcutting 04's aperture chain. So this is a *precondition of the locality argument*, not a manufacturing nicety. Trivial to check; potentially expensive to fix if it fails.

## Summary

| | discharges | input needed | complexity | self-contained? |
|---|---|---|---|---|
| G1 tap coverage | V5 / M1 | device + tap positions | O(n log n) | yes |
| G2 interleaving | X2 | placement + **ECC word structure** | linear | **no** (needs L3/L5) |
| G3 antenna | — | layout + **process order** | linear per layer | **no** (needs the recipe) |
| G4 width/spacing | (H1),(H2),(D1)–(D3) | drawn layout | near-linear | yes |
| G5 shielding | M2's hypothesis | layout + grid | near-linear | yes |
| G6 tied fill | M2's hypothesis | layout + connectivity | linear | yes |

Two of the six need inputs from outside L1, and both of those inputs are things a layout tool does not record: the ECC word structure and the process order. Worth noting because it is the same pattern as the antenna rule generally — **some geometric obligations are not properties of the geometry.**

## First experiments

- G6 on the flow's layout: is the metal fill tied? A single connectivity query, and the answer determines whether 04's argument needs its harder version.
- G1 on the extracted device positions, once L1/02's extraction runs.
- Establish whether the design has ECC at all before investing in G2.

## Effort

Weeks each, gated on extraction and placement parsing rather than on the algorithms. This is the cheapest part of L1 and a reasonable place to start building infrastructure the rest of the layer needs anyway.
