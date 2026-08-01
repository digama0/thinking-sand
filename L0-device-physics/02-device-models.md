# L0/02 — Device models: the nonlinear part

## Statement

Give each transistor a terminal I-V relation valid over the operating range, as an *enclosure* rather than a point value, and identify what that relation rests on.

This is where the nonlinearity lives, where restoration comes from, and where the project's deepest empirical axiom sits.

## Why devices are special

The interconnect is **linear**: superposition applies, the network has a rational transfer function, model order reduction is exact, and rigorous enclosures are available (L1).

Devices are **nonlinear**, and they are the *reason the digital abstraction exists* — gain
> 1 in the transition region is what makes the rails attracting fixed points. So they carry disproportionate importance relative to their contribution to the numbers (which is smaller than interconnect's at any modern node).

## Three routes, and their costs

**Route A — solve drift–diffusion.** The van Roosbroeck system. Existence established; **uniqueness not known in general** and genuinely false where latch-up or snapback occur (see [00](00-field-problem.md)). Even setting that aside, a per-device PDE solve is computationally hopeless at 400 cells × operating range × corners.

**Route B — compact models (what industry does).** BSIM or PSP: fitted algebraic relations with hundreds of parameters, calibrated against measured silicon. Deterministic, fast, composable. Cost: **axiom E1**, unfalsifiable in principle, and it gets *thicker* at smaller nodes as quantum confinement, quasi-ballistic transport and self-heating are folded into the fit.

**Route C — switch-level abstraction.** Model the MOSFET as a bidirectional switch with strength and charge sharing ([Bryant](../BIBLIOGRAPHY.md#bryant-1984)'s MOSSIM lineage; [Melham](../BIBLIOGRAPHY.md#melham-1993)'s HOL CMOS work). This is the *target* abstraction for producing Boolean functions, and it is far coarser than either of the above.

The chain actually used is **C resting on B**: the switch abstraction's justification is the device's I-V characteristic, which comes from a fitted model. There is no route to a Boolean function that avoids either a non-unique PDE or an underived fit.

**With foundry-level control there is a fourth option worth noting**: define the cell library at transistor level and prove cell → Boolean via switch-level modelling, pushing the axiom down to "the switch-level MOSFET abstraction is sound." That covers the whole library at once instead of per-cell characterisation, and is a strictly better axiom. Not available for validating someone else's shipped design.

## What must actually be proved

For each cell, the obligation is not "the device model is right" but:

> Given the device model **as an enclosure** over the operating range and corners, the cell's terminal behaviour lies within a region from which the Boolean function can be read off with positive noise margin.

Two things follow. First, the device model enters as an *interval*, so E1's fidelity claim is "the true I-V lies in the enclosure," which is weaker and more defensible than "the model is correct." Second, the switch-level abstraction only has to be valid *coarsely* — you need the ON/OFF distinction and enough gain, not accurate currents.

For the interval representation itself, plain intervals will be too loose — terminal currents share the same underlying parameters, and naive intervals count that uncertainty independently at every use. The standard remedies are affine arithmetic ([de Figueiredo & Stolfi](../BIBLIOGRAPHY.md#de-figueiredo-stolfi-2004)), which tracks first-order correlations, and Taylor models ([Makino & Berz](../BIBLIOGRAPHY.md#makino-berz-2003)) for higher order; both are mature and both have validated implementations.

## The uniqueness side condition

Latch-up is a second solution branch of the device PDE, and the design rule that eliminates it is **tap coverage**: every device within a bounded distance of a well tie.

So the layout rule normally filed under "reliability" is really the side condition making the single-branch assumption valid — i.e. a *hypothesis of well-posedness*, not a manufacturing constraint. It belongs in the same category as L1's min-width rules, which turned out to be hypotheses of a topology-preservation theorem.

This is worth stating as a general pattern: **several DRC rules are secretly the side conditions of theorems nobody has written.**

## Open problems

1. **Uniqueness for stationary drift–diffusion under operating bias**, or a characterisation of when the parasitic branch is reachable. Genuinely open.
2. Turn tap-coverage rules into a *proved* sufficient condition for single-branch operation.
3. Formalise a switch-level model with strengths and charge sharing, and prove it sound with respect to an interval-valued compact model. Nobody has done this for a real library.
4. Self-heating: at advanced nodes it enters the *functional* path. Absent at 130 nm; record as a scope boundary.

## First experiments

- Take `inv_1`: extract its transistor netlist (`magic`/`netgen`), attach an interval-valued device model, and derive the terminal enclosure. This is the unit that gets multiplied by 400 — measuring it decides whether L0 is two years or five.
- Check how coarse the device enclosure can be while still yielding positive noise margin. If the margin is large (it should be, at 1.8 V), E1's precision requirement is weak, which materially reduces what must be assumed.

## Reading

[Markowich](../BIBLIOGRAPHY.md#markowich-1986), *The Stationary Semiconductor Device Equations*. [Bryant](../BIBLIOGRAPHY.md#bryant-1984), "A switch-level model and simulator for MOS digital systems" (IEEE Trans. Computers 1984) — the MOSSIM II model: strengths, charge sharing, and the ternary algebra. [Melham](../BIBLIOGRAPHY.md#melham-1993), *Higher Order Logic and Hardware Verification* (1993) — transistor-level CMOS in HOL, the closest existing formalisation of Route C. The [BSIM4 technical manual](../BIBLIOGRAPHY.md#bsim4-manual) (Berkeley) for what E1 actually asserts — the SKY130 PDK models are BSIM4, evaluated under ngspice; [Gildenblat et al.](../BIBLIOGRAPHY.md#gildenblat-2006) for PSP, the surface-potential alternative. [de Figueiredo & Stolfi](../BIBLIOGRAPHY.md#de-figueiredo-stolfi-2004) on affine arithmetic; [Makino & Berz](../BIBLIOGRAPHY.md#makino-berz-2003) on Taylor models.
