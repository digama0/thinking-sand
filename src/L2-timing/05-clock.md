# L2/05 — The clock: generation and distribution

## Background

Everything in this layer is measured against clock edges, so something must *make* them, and the making is analog. An on-chip clock generator is a **ring oscillator** — a loop of an odd number of inverters, whose contradiction ("my output must be my input's negation, but my input is my output") can never settle and therefore oscillates, at a frequency set by the loop's total gate delay. A **PLL** (phase-locked loop) wraps such a ring with a control circuit that compares the ring's output (divided down) against a stable external reference and continuously nudges the ring's speed to match — giving a fast on-chip clock disciplined by a slow accurate crystal. The essential irony for this project: the one circuit that *produces* the clock is a deliberate combinational loop and can never satisfy the synchronous discipline it makes possible. It must be cut out of the netlist and replaced by a mathematical contract about its output.

That contract has to face a genuinely subtle piece of physics: an oscillator has no sense of absolute time. Amplitude disturbances die out (the limit cycle restores them), but a disturbance *along* the cycle — arriving a femtosecond early stays a femtosecond early forever — is never corrected, so thermal noise accumulates in the phase as a random walk. This is **jitter**: the realised edges wander unboundedly from the ideal grid `n·T` as time passes, even though each *individual* period is extremely accurate. The model downstream is built to be immune to this (it indexes by edge number and constrains only edge-to-edge intervals, so the divergent absolute phase simply never appears in any hypothesis), but the residue is real and appears wherever the chip must agree about time with the outside world.

The distribution side has its own vocabulary. The clock reaches thousands of flops through a **clock tree** of buffers, built by a synthesis step called **CTS** (clock tree synthesis); **insertion delay** is the source-to-flop travel time through the tree, and **skew** is the difference in insertion delay between two flops — the quantity the hold check consumes, since a race between two flops is run against their *relative* edge timing. The trap this chapter defuses: it is tempting to file the clock tree under "plumbing that preserves function," and it is not — modern flows deliberately *unbalance* the tree ("useful skew") to fix timing, and nearly ten thousand cells in this design exist solely to shape arrival times. The clock tree is a load-bearing participant in correctness, and the arrival function it realises is a first-class object of the proof.

## Statement

Produce the clock arrival function `arr : Flop → interval` that [00](00-timed-model.md) presupposes, and account for the one circuit that manufactures time rather than consuming it.

## Generation (X5)

Caravel's clock is either the external pad clock or the on-die `digital_pll` — a **ring oscillator**: a deliberate combinational loop, the one circuit that cannot live inside the synchronous abstraction it powers. Measured (L3's W1/W3): `pll.ringosc` contains the netlist's *only* cycle and its *only* multi-driver nets, so the excision is provably minimal — the black-box boundary is exactly the oscillator, not a convenience region around it.

What replaces the black box is a contract with two parts (Axioms X5, M8):

1. **Frequency**: the oscillator has a stable limit cycle with period in a stated interval — a computer-assisted-proof target of standard type: interval Poincaré maps ([Zgliczyński](../bibliography.md#zgliczynski-1997), [Galias](../bibliography.md#galias-2001)) over E1's interval device model. The `itrim` delay-trim mux (the 26 tri-state nets) parameterises the period.
2. **Phase diffusion**: along the limit cycle the zero Floquet exponent means *no restoration in phase* — thermal noise accumulates as a Wiener process ([Demir–Mehrotra–Roychowdhury](../bibliography.md#demir-mehrotra-roychowdhury-2000)). Jitter is the one place thermal noise survives to the macroscopic ledger; its coefficient is derivable (M8), its budget lands in P6 and inside `arr`'s interval width.

## Distribution

The clock network is 15,306 cells — buffers, inverters, and 9,910 `clkdlybuf4s15` *delay* buffers inserted for hold fixing and skew management. Two obligations:

**Cleanliness.** Every flop's clock pin is reachable from a clock source through clock-cell types only, with no data-dependent logic except declared gating. A mechanical reachability check on the netlist, and the licence for L3's deletion of the entire network into the sentence "all flops update together." If gating cells are present (`dlclk*`-family), each adds a conditional-arrival term and an enable-stability check — enumerate rather than assume absent.

**Done** (`tools/clockcheck.py`; [Findings](../findings.md#clock-network-cleanliness-l205)): 5,774 sinks resolve to the SDC's three declared clocks plus 23 sinks inside the `pll.ringosc` excision; **zero gating cells**; every path outside the excision is pure buffer/inverter. The one wrinkle lives in housekeeping: its SPI domain's clock is a *mux* of the pad SCK path with `wbbd_sck`, a **flop output** — a register-generated clock no SDC mode declares (F4).

**Arrival enclosure.** STA over the clock network's own arcs yields per-flop insertion delay intervals; `arr(f)` is that interval widened by jitter. Skew — the *difference* between two flops' arrivals — is what the hold inequality consumes, and CPPR ([03](03-corners.md)) exists precisely because launch and capture share a tree prefix whose variation cancels.

**CTS is not logically neutral.** This deserves its own emphasis because the L1-era intuition "place-and-route preserves function" fails here: hold correctness *depends on skew*, and useful-skew methodology deliberately unbalances the tree to steal setup margin — making the clock tree an active participant in the correctness argument, not plumbing. The 9,910 delay buffers are the visible evidence: about 6% of all logic-bearing cells exist purely to shape `arr`.

## What `arr`'s width is made of

```
arr(f) = nominal insertion delay
         ± tree variation (corner + OCV tiers, 03)
         ± jitter (phase diffusion, above)
         ± duty/pulse-width effects for the flop's min-pulse checks
```

Recovery/removal checks on asynchronous set/reset pins, and minimum-pulse-width checks, are the same window rule as setup/hold with different table entries — they ride along in [02](02-verified-sta.md) once `arr` is available; no new theory.

## Ordinal time, and where the period claim actually lands

[00](00-timed-model.md) indexes the semantics by the realised edge sequence, so phase diffusion is quotiented out and the per-interval deviation `T_n − T_nom` splits three ways with three fates:

1. **Stochastic period jitter** `σ_T = √(cT)`: picoseconds against nanosecond margins — a Gaussian-tail term, **discharged** P3-style, not carried.
2. **Accumulated jitter over bounded horizons**: enters only L7's absolute-time interface claims (UART frame budget `√(10T·c)` — negligible; the start-bit resync re-anchors each frame).
3. **Deterministic period offset** — P/V/T moves the ring oscillator by *tens of percent*, dwarfing diffusion, and this part is an **unchecked obligation**: the SDC's `create_clock -period` is a claim about the oscillator that nothing connects to X5's frequency enclosure. Closure is valid only if realised min period ≥ signoff period — and the PLL trim (`itrim`) and divider are **software-visible housekeeping registers**, so this is a *reachable-configuration* condition (the chip can in principle be told to overclock itself), same class as F4, discharged through L7's configuration model.

## Obligations

1. ~~The cleanliness check as a tool run, including the gating-cell census~~ — **done** (`tools/clockcheck.py`; zero gating cells, roots as above).
2. `arr` as a derived object: clock-network STA + jitter, with the CPPR-relevant tree structure preserved rather than flattened.
3. The X5 contract statement — frequency interval + diffusion coefficient — as the formal boundary of the excision (the proof itself is M8's, in L0's machinery).
4. External-vs-PLL clock selection: the mux implies two `arr` functions and two closure runs; check both were actually signed off.
5. **Connect X5's frequency enclosure to the SDC period**, quantified over reachable PLL configurations (trim, divider, source mux) — **F6**. Determine whether any reachable setting produces a period below signoff; if yes, the residue is a `Sys(F)` operating-conditions clause (L7 open problem 0), not an axiom.

## First experiments

- Run the cleanliness reachability check; count gating cells. Cheap, and it converts "clock network clean" from assumption to measurement — the same upgrade W1–W4 made for well-formedness.
- Extract per-flop insertion delays from the signoff reports and plot the skew distribution: the hold failures (F1) should correlate with its tails.

## Effort

The checks: weeks. The X5/M8 contract proof is L0-effort and only its *statement* is owed here.
