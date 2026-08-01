# L2/05 — The clock: generation and distribution

## Statement

Produce the clock arrival function `arr : Flop → interval` that [00](00-timed-model.md) presupposes, and account for the one circuit that manufactures time rather than consuming it.

## Generation (X5)

Caravel's clock is either the external pad clock or the on-die `digital_pll` — a **ring oscillator**: a deliberate combinational loop, the one circuit that cannot live inside the synchronous abstraction it powers. Measured (L3's W1/W3): `pll.ringosc` contains the netlist's *only* cycle and its *only* multi-driver nets, so the excision is provably minimal — the black-box boundary is exactly the oscillator, not a convenience region around it.

What replaces the black box is a contract with two parts (AXIOMS X5, M8):

1. **Frequency**: the oscillator has a stable limit cycle with period in a stated interval — a computer-assisted-proof target of standard type: interval Poincaré maps ([Zgliczyński](../BIBLIOGRAPHY.md#zgliczynski-1997), [Galias](../BIBLIOGRAPHY.md#galias-2001)) over E1's interval device model. The `itrim` delay-trim mux (the 26 tri-state nets) parameterises the period.
2. **Phase diffusion**: along the limit cycle the zero Floquet exponent means *no restoration in phase* — thermal noise accumulates as a Wiener process ([Demir–Mehrotra–Roychowdhury](../BIBLIOGRAPHY.md#demir-mehrotra-roychowdhury-2000)). Jitter is the one place thermal noise survives to the macroscopic ledger; its coefficient is derivable (M8), its budget lands in P6 and inside `arr`'s interval width.

## Distribution

The clock network is 15,306 cells — buffers, inverters, and 9,910 `clkdlybuf4s15` *delay* buffers inserted for hold fixing and skew management. Two obligations:

**Cleanliness.** Every flop's clock pin is reachable from a clock source through clock-cell types only, with no data-dependent logic except declared gating. A mechanical reachability check on the netlist, and the licence for L3's deletion of the entire network into the sentence "all flops update together." If gating cells are present (`dlclk*`-family), each adds a conditional-arrival term and an enable-stability check — enumerate rather than assume absent.

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

1. The cleanliness check as a tool run (netgraph-style; an afternoon), including the gating-cell census.
2. `arr` as a derived object: clock-network STA + jitter, with the CPPR-relevant tree structure preserved rather than flattened.
3. The X5 contract statement — frequency interval + diffusion coefficient — as the formal boundary of the excision (the proof itself is M8's, in L0's machinery).
4. External-vs-PLL clock selection: the mux implies two `arr` functions and two closure runs; check both were actually signed off.
5. **Connect X5's frequency enclosure to the SDC period**, quantified over reachable PLL configurations (trim, divider, source mux) — **F6**. Determine whether any reachable setting produces a period below signoff; if yes, the residue is a `Sys(F)` operating-conditions clause (L7 open problem 0), not an axiom.

## First experiments

- Run the cleanliness reachability check; count gating cells. Cheap, and it converts "clock network clean" from assumption to measurement — the same upgrade W1–W4 made for well-formedness.
- Extract per-flop insertion delays from the signoff reports and plot the skew distribution: the hold failures (F1) should correlate with its tails.

## Effort

The checks: weeks. The X5/M8 contract proof is L0-effort and only its *statement* is owed here.
