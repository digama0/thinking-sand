# L2/06 — Boundaries: the window hypothesis at the edge

## Background

The setup/hold guarantee rests on a shared clock: every flop's input settles in time *because* the launching flop was tripped by a related edge one period earlier. A signal arriving from outside — a button press, a byte from a device on its own oscillator — has no such relationship. It changes whenever it changes, which will sooner or later be exactly inside some flop's forbidden window. This is the **clock-domain crossing (CDC)** problem, and it cannot be engineered away, because it is not an engineering defect — it is a small impossibility theorem. A circuit asked to decide, in bounded time, which side of an edge an arbitrarily-timed event fell on is being asked for a discontinuous function of a continuous input; some input must land on the boundary of the decision. Physically, a flop capturing a transitioning input can be caught **metastable**: balanced at the unstable equilibrium between 0 and 1 — the ball on the top of the hill — its output hovering at an invalid middle voltage for an unbounded time before restoration finally tips it to a rail.

Unbounded, but not unpaid-for: the escape probability is exponential in the settling time allowed (`e^{−t/τ}`, with τ a few gate delays). The standard gadget exploiting this is the **two-flop synchroniser**: the first flop takes the hit — it is *permitted* to go metastable — and its output is given a full clock period to settle before the second flop samples it; the residual probability that metastability survives that long is astronomically small per event, and summed over events it becomes a quantified failure rate — the industry's **MTBF** (mean time between failures) calculation, and the origin of the `N_sync · P_meta(T)` term in the project's top-level ε. This is one of the two places in the entire tower where correctness is genuinely probabilistic rather than certain (the other is particle strikes), which is why the synchroniser gets a precise treatment below rather than a nod.

The chapter's organising idea is that "no clock relationship at all" is only the worst rung of a **ladder**. Interfaces come with graded degrees of timing relationship — same clock; clock travelling alongside the data (*source-synchronous*, how SPI works); same frequency but unknown phase (*mesochronous*); nominally-same frequency with drift (*plesiochronous*, from Greek "close in time"); nothing (*asynchronous*) — and each rung supports a cheaper gadget, with a weaker assumption about the world, at a lower price. (The mid-ladder gadgets are **FIFOs** — first-in-first-out buffer queues that absorb phase or rate mismatch at a cost in latency.) Placing each of the chip's real interfaces on its correct rung, and paying each rung's exact price and no more, is the discipline this chapter enforces.

## Statement

The bridge theorem's input-stability hypothesis is stated against the CPU's clock, and the world is not on that clock. The hypothesis is never *projected outward* — it is **weakened at the boundary and re-manufactured inside**: every interface has a gadget that accepts a strictly weaker assumption about the world and produces signals satisfying the window hypothesis internally, at a price.

This file owns the multi-domain composition of [01](01-bridge-theorem.md) and the P1 accounting.

## The ladder

What can be assumed depends on how much clock relationship exists. Each grade has its gadget, its residual external assumption, and its price:

| relationship | external assumption | gadget | price |
|---|---|---|---|
| **synchronous** (same clock, bounded skew) | window relative to the shared edge | ordinary IO flop | none — STA extended across the boundary |
| **source-synchronous** (clock travels with data) | window relative to the *transported* edge | capture flop in received domain + FIFO | latency; a CDC moved inside |
| **mesochronous** (same frequency, unknown phase) | frequency identity | phase-compensating FIFO | latency |
| **plesiochronous** (nominal frequency, drift) | frequency ratio within tolerance | FIFO + slip compensation | occasional stall |
| **asynchronous** (no relationship) | **rate only** — min pulse width, bounded arrival rate | synchroniser | **P1's ε**, 1–2 cycles |

Reading down: the assumption weakens phase → transported phase → frequency → tolerance → rate, and the price climbs latency → throughput → probability. Note that "same nominal frequency from a different oscillator" is *not* synchronous — independent oscillators drift unboundedly in phase; only clocks derived from one source give windows.

**This is the restoration pattern's third instance.** Gates restore levels, clock edges restore time, boundary gadgets restore *phase*: the invariant is re-established at the boundary instead of the error propagating. It is why the window hypothesis never has to leave the die.

## The synchroniser, precisely

The bottom rung deserves its formal statement because it is where determinism ends:

> First flop: deliberately exempted from the window hypothesis; on violation its output is unconstrained ([00](00-timed-model.md)'s escape hatch) but **restoration drives it to a rail** with `P(unresolved after t) ≈ (T₀/T_c)·e^{−t/τ}`, τ the metastable saddle's unstable eigenvalue (M8, an enclosure modulo E1). Second flop: its window hypothesis is established by ordinary STA on the flop-to-flop path — a full period of settling.

No assumption about the input's *phase* survives. The irreducible external assumptions are **rate**: pulses shorter than a period can be missed outright, and the arrival statistics enter the MTBF. Both are P6-class environment facts, which is exactly where P1's residue was already filed. `N_sync · P_meta(T)` in MAIN's ε is the sum of these per-boundary terms.

Per-frame **clock recovery** (UART RX) is a hybrid rung: synchronise once on the start edge (paying P1 once per frame), then rely on *frequency tolerance* — ±2–3% over ~10 bit periods — rather than phase. This is where P6's clock-accuracy bound does quantitative work.

## Multi-domain composition

The per-domain bridge theorem composes across declared boundaries:

> Partition the flops by clock domain. If each domain satisfies [01](01-bridge-theorem.md)'s hypotheses internally, and every inter-domain net crosses through a ladder gadget whose external assumption holds, then the composite implements a network of Mealy machines communicating through nondeterministic-latency channels — with the channel nondeterminism bounded by the gadget contracts, and ε summing the P1 terms.

The abstraction above L2 is therefore *not* one Mealy machine but this network; for Caravel it collapses back to nearly one machine because the secondary domains (`hk_serial_clk`, `hk_serial_load`, `hkspi_clk` — the two `set_clock_groups` declarations) are low-speed configuration paths.

## The outward direction

Symmetric, and easy to forget: the world's flops need *our* outputs stable in *their* windows. For each interface the proof **exports** a guarantee in the same graded vocabulary — a derived AC-timing table (clk-to-out min/max from STA) for synchronous peers, a frequency-accuracy bound for the UART TX, minimum pulse widths for async consumers. B3's composition at L7 is precisely matching our exports against the peers' assumptions and vice versa. The datasheet AC-timing page is the theorem-shaped version of this, derived rather than characterised.

## Caravel's boundary inventory

| interface | rung | notes |
|---|---|---|
| `mprj_io[*]` GPIO | asynchronous | the 112 false paths ([04](04-sdc-exceptions.md)); synchroniser presence unverified — **F1/F3's home** |
| SPI flash | source-synchronous outward (chip emits SCK); MISO return | capture sound because the round trip fits the period at the low SPI rate — a real hypothesis, write it down |
| UART RX | clock recovery | frequency-tolerance budget |
| housekeeping SPI | external `hkspi_clk` (declared clock, 100 ns) | the `set_clock_groups` pair |
| reset | async assert, synchronised release | `xres_buf`, `simple_por` (X4-class analog model) |

## Obligations

1. The synchroniser predicate (structural: two-flop chain, no fanout from the first flop, one domain) — shared with [04](04-sdc-exceptions.md)'s asynchronous class.
2. The multi-domain composition theorem above.
3. The per-boundary P1 ledger: enumerate every crossing (this list *is* P1's scope) and its `N_sync` contribution.
4. The exported AC-timing table as a derived artifact, handed to L7.

## First experiments

- Enumerate every inter-domain net and every async input; check each lands on the synchroniser pattern. This is simultaneously [04](04-sdc-exceptions.md)'s asynchronous-class discharge and the F1 closure — one experiment, two findings.
- Compute the UART tolerance budget from the design's divisor and check it against P6's oscillator spec.

## Effort

Weeks for the inventory and predicate; the composition theorem is months and leans on [01](01-bridge-theorem.md)'s form.
