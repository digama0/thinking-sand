# L0/03 — Per-cell field bounds and terminal behaviour

## Background

This chapter is where the physics gets *computed*, so it needs two pieces of context: what the computation is, and what discipline makes a computation trustworthy inside a proof.

The computation. A standard cell — an inverter, a NAND gate — is a handful of transistors plus a little internal wiring, and simulating its behaviour means solving a small system of **differential equations**: each node's voltage changes at a rate set by the currents flowing onto it, currents given by the device model. (Strictly a **DAE** — differential-*algebraic* equations, the flavour where some equations are instantaneous constraints rather than rates; circuit equations always come out this way, and it changes which solvers apply.) Industry does this with **SPICE**, the venerable analog simulator: give it the transistor netlist, it integrates the equations numerically and reports waveforms. The foundry has already done exactly this, thousands of times, to produce the **Liberty file** that L2 consumes — each cell's delay and output slew simulated across a grid of (input slew, output load) pairs and tabulated. So the object this chapter must produce is not novel in *shape* at all: it is the Liberty table again. What changes is the epistemic status of the numbers.

The discipline is **validated numerics** (interval computation). An ordinary numerical solver returns a number that is *close to* the answer, with error estimated by heuristics; a validated solver returns an *interval* together with a proof that the true solution lies inside it, by doing all arithmetic on intervals with outward rounding and bounding every truncation term. This costs looseness — the intervals are wider than the likely error — but yields statements a proof assistant can consume. Validated integration of small ODE/DAE systems is a mature specialty (the chapter's reading list names the standard tools), and a logic gate's equation system is small; the genuinely new thing here is only scale and interface — running the machinery over a whole cell library, against an *interval-valued* device model, with a Liberty-shaped table of certified bounds as output.

What makes this chapter the layer's centre of gravity is **amortisation**. Everything on the die is one of ~400 library cells; a cell verified once is verified for every one of its hundred thousand instances, and for every other design ever fabricated on this process. The unit of work — one cell, one corner, end to end — is measurable in days, and the first experiment below is precisely to measure it, because unit × 400 cells × 17 corners is the number that decides where in its estimated range the whole layer lands.

## Statement

For each of the ~400 standard cells, bound the terminal behaviour over the operating range:

```
cell × (input slew, output load, corner) ⟼ enclosure on (delay, output slew, output level)
```

**This deliverable is a Liberty table — an interval-valued, derived one.** The shipped `.lib` is exactly this object (NLDM — pure table lookup, no current-source model at this node), produced by SPICE and asserted; L0/03's version is produced with bounds and a stated derivation.

## Why it factorises this way

The cell is the right unit for three independent reasons:

1. **Amortisation.** ~400 cells, verified once, cover every design on the process forever. This is the single largest leverage point in the project.
2. **The DAE is confined here.** The nonlinear solve involves a handful of transistors. At chip scale it would be hopeless; at cell scale it is small. See [04](04-lumping-composition.md) for why this confinement is legitimate.
3. **The domain is bounded and known.** One cell's geometry, from L1's coloured image.

## The problem to solve

Per cell, the domain is the cell's own geometry and the fields within it:

- **Devices** at each poly∩diff intersection, with interval-valued I-V from [02](02-device-models.md).
- **Intra-cell parasitics** — the local li1/met1 routing inside the cell. Small but not zero, and *linear*, so L1's variational enclosure machinery applies unchanged on this small domain.
- **Boundary conditions** at the pins, parameterised by input slew and output load.

Then solve the resulting nonlinear DAE with enclosures rather than point values, and tabulate.

## What makes this hard

**Verified DAE integration with enclosures.** Taylor models, [CAPD](../BIBLIOGRAPHY.md#capd-2021), [VNODE-LP](../BIBLIOGRAPHY.md#nedialkov-2006)-style validated integration exist and are mature for small ODE systems. A CMOS gate is small. The DAE structure is also understood: modified nodal analysis yields index ≤ 2, with a topological characterisation of when it is index 1 ([Estévez Schwarz & Tischendorf](../BIBLIOGRAPHY.md#estevez-schwarz-tischendorf-2000) 2000), and [Pryce](../BIBLIOGRAPHY.md#pryce-2001)'s Σ-method gives the structural analysis that Taylor-series DAE solvers ([Nedialkov & Pryce](../BIBLIOGRAPHY.md#nedialkov-pryce-2005), [DAETS](../BIBLIOGRAPHY.md#nedialkov-pryce-2005)) are built on. There is even a formal-verification-of-analog-circuits lineage at single-circuit scale: [Greenstreet & Mitchell](../BIBLIOGRAPHY.md#greenstreet-mitchell-1999)'s projection-based reachability (a verified toggle element), [Dang–Donzé–Maler](../BIBLIOGRAPHY.md#dang-donze-maler-2004)'s hybridization (a ΔΣ modulator), [Althoff & Krogh](../BIBLIOGRAPHY.md#althoff-krogh-2014)'s zonotope reachability for nonlinear index-1 DAEs, surveyed by [Zaki et al.](../BIBLIOGRAPHY.md#zaki-tahar-bois-2008); the reachability toolboxes ([CORA](../BIBLIOGRAPHY.md#althoff-cora-2015), [Flow*](../BIBLIOGRAPHY.md#flowstar-2013), [JuliaReach](../BIBLIOGRAPHY.md#juliareach-2019)) are the living descendants. **What nobody has done is run any of this at library scale, against an interval-valued device model, with a Liberty table as the output object.** The gap is industrialisation and the interval-model interface, not the existence of the mathematics.

**The table's extent is a hypothesis, not a convenience.** The measured data is decisive here: `max_transition = 1.5` is *exactly* `index_1`'s largest value, and `max_capacitance = 0.181284` is *exactly* `index_2`'s largest. Beyond the characterised region the consumer extrapolates and the numbers become **vacuous rather than wrong**. So L0/03 must export the domain along with the values, and L2 must check the design stays inside it. Cf. finding F2 — the shipped design does *not*.

**Interpolation must be an enclosure, and the obvious shortcut is unsound.** Real (slew, load) pairs fall between grid points. Take the enclosing grid box and the extremes over it — but `cell_fall` is **non-monotone in slew** at two grid points (an artifact of the 50%-crossing delay definition with slow ramps and light loads). So take the max over **all four corners** of the enclosing cell, never the largest-index corner.

And be precise about what that bounds: the corner-max encloses the *bilinear interpolant* (which always lies within the corner range), **not the underlying function** — a non-monotone function can peak strictly inside a grid box, above every corner. The shipped table asserts values at the sample points and nothing in between, so no sound enclosure of the physical delay can be extracted from it alone. The derived table can close this gap because a DAE enclosure yields a derivative (or modulus-of-continuity) bound between samples; that bound is part of the deliverable, not an optional extra.

That non-monotonicity is worth dwelling on: it is evidence in production data that the monotonicity assumptions underlying corner-based methodology are **not free**, which matters for [04](04-lumping-composition.md).

**Corners multiply.** 17 corner files in the SKY130 HD library. Each is a separate solve.

## Relationship to L1

L0/03 and L1's extraction solve the *same linear problem on complementary domains* — inside cells and between them. The machinery should be shared: one verified elliptic solver with enclosures, applied to two families of domains. Building it twice would be a mistake.

The difference is that inside a cell the problem is coupled to nonlinear boundary conditions at the devices, and outside it is purely linear.

## Open problems

1. **Verified DAE enclosure integration at cell scale.** The mathematics exists; the application does not.
2. How coarse can the device enclosure be while still yielding a usable delay bound? If the answer is "quite coarse", E1's precision requirement drops and the whole layer gets cheaper.
3. Whether the 17 corners can be reduced by proving monotonicity in the corner parameters — and the Liberty non-monotonicity above suggests the answer is "not universally."

## First experiments

- **`inv_1`, end to end.** GDS → extracted transistor netlist → interval device model → intra-cell parasitics → DAE enclosure → compare against the shipped `.lib` entry. The shipped table gives you an oracle: if your enclosure does not contain SPICE's value, something is wrong on one side.
- Measure the cost. This is the unit multiplied by 400 × 17 corners, and it decides where in its one-to-three-year range L0 lands.
- Check whether the enclosure width is dominated by the device model, the parasitics, or the integration — that tells you where to spend effort.

## Effort

The dominant item of L0: the per-cell unit × ~400 cells × 17 corners. Its first experiment prices it, and the answer sets where in its one-to-three-year range the layer lands.

## Reading

[Rump](../BIBLIOGRAPHY.md#rump-1999)'s INTLAB and the validated-numerics literature. [CAPD](../BIBLIOGRAPHY.md#capd-2021) / [VNODE-LP](../BIBLIOGRAPHY.md#nedialkov-2006) ([Nedialkov](../BIBLIOGRAPHY.md#nedialkov-2006)) for validated ODE integration; [Nedialkov & Pryce](../BIBLIOGRAPHY.md#nedialkov-pryce-2005) ([DAETS](../BIBLIOGRAPHY.md#nedialkov-pryce-2005)) and [Pryce](../BIBLIOGRAPHY.md#pryce-2001)'s Σ-method for the DAE structural side; [Estévez Schwarz & Tischendorf](../BIBLIOGRAPHY.md#estevez-schwarz-tischendorf-2000) for the MNA index results. [Greenstreet & Mitchell](../BIBLIOGRAPHY.md#greenstreet-mitchell-1999), [Dang–Donzé–Maler](../BIBLIOGRAPHY.md#dang-donze-maler-2004), [Althoff & Krogh](../BIBLIOGRAPHY.md#althoff-krogh-2014), and the [Zaki et al.](../BIBLIOGRAPHY.md#zaki-tahar-bois-2008) survey for formal analog verification; [CORA](../BIBLIOGRAPHY.md#althoff-cora-2015) / [Flow*](../BIBLIOGRAPHY.md#flowstar-2013) / [JuliaReach](../BIBLIOGRAPHY.md#juliareach-2019) for current reachability tooling. [Liberty format documentation](../BIBLIOGRAPHY.md#liberty-format) for exactly what the shipped tables assert.
