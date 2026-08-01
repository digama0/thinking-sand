# L2/01 — The bridge theorem (M5)

## Statement

Over the timed model of [00](00-timed-model.md):

> Let `N` be the netlist with `pll.ringosc` excised (X5) and partitioned into clock domains with declared asynchronous boundaries ([06](06-boundaries.md)). Suppose:
>
> 1. *(domain)* every cell's load and input slew lie inside its contract's domain — `max_capacitance` / `max_transition`. **Currently false for the shipped design (F2)**;
> 2. *(closure)* setup and hold hold at every flop, at every corner, with respect to the clock arrival function — certified by STA ([02](02-verified-sta.md)). **Currently false at 3 of 9 corners (F1)**;
> 3. *(exceptions)* every path excluded from (2) carries a justified SDC exception ([04](04-sdc-exceptions.md)). **Unverified (F3, F4)**;
> 4. *(conditioning)* no fault event (P2) and no unresolved synchroniser read (P1) occurs in `[0, T]`.
>
> Then every run of the timed model over `[0, T]` agrees with `Mealy(N)`: at each clock edge `n`, every flop holds `s_n`, and `s_{n+1} = δ(s_n, i_n)`.

Everything above L2 presupposes this, and nobody has written it down. It is the highest value-per-effort novel contribution in the project.

## Proof sketch

Induction on clock cycles with invariant **"at the start of cycle n, all flops hold `s_n` stably."**

- *Propagation.* From the invariant, the combinational DAG settles: max-delay bounds along every path (hypothesis 2's setup half) give all flop inputs stable at `δ(s_n, i_n)`-consistent values by `arr(f) − t_su` for every flop `f`.
- *No early corruption.* Min-delay bounds (the hold half) give that no flop input changes before `arr(f) + t_h` — the *new* values racing through short paths cannot violate the just-captured state.
- *Capture.* The window rule fires deterministically at every flop; outputs become `s_{n+1}` within `t_cq`, re-establishing the invariant. ∎

Three structural remarks that carry more weight than the induction itself:

**The clock edge is a restoration point in the time domain.** The invariant is *fully re-established* every cycle, so timing error does not accumulate — the same mechanism, in time, as gate restoration in voltage. There is no drift mode: a violated constraint fails immediately and deterministically, not gradually.

**Setup and hold are asymmetric, and only one is negotiable.** `T_clk` appears in the setup inequality and is absent from the hold inequality. Setup failure is a performance property (clock slower); **hold failure is unfixable at any frequency, post-silicon**. Corollary: CTS is not logically neutral — hold depends on skew, and useful skew makes the clock tree an active participant in correctness ([05](05-clock.md)).

**Cycles are already cut.** Every feedback loop passes through a flop (W3, measured: exactly one exception, excised). Cutting at flops turns the cyclic sequential graph into a DAG of combinational segments, each with one max- and one min-delay obligation — which is why STA is a graph traversal and the induction needs no fixed point.

## Where the theorem's shape breaks

Each of these violates a hypothesis structurally, not numerically:

| construct | what breaks | status here |
|---|---|---|
| combinational loops | the DAG cut | only `pll.ringosc` — excised, provably minimal |
| latch-based time borrowing | no clean capture edge; windows span stages | absent (flop-based design) |
| wave pipelining | multiple waves in flight per segment | absent |
| multicycle paths | capture skips edges; *two* extra claims (destination not enabled between; source held throughout) plus a hold adjustment | **zero declared** — a genuine gift |
| clock gating | the arrival function becomes data-dependent | see [05](05-clock.md) |

## The conditioning is the theorem's honest edge

Hypothesis (4) is not a technicality: it is **where ε enters the whole project** (MAIN's † marks). The theorem is deterministic *on the event* "no strike, no unresolved read"; [06](06-boundaries.md) and L0/06 bound the event's complement. Stating M5 unconditionally would be false; smearing the probability through the induction would be unworkable. The conditional form is the correct interface.

## Open problems

1. **Write it.** Bounded-delay model, window rule, per-cycle induction — a solid paper, not a decade. Its absence is a fact about nobody working at the boundary, not about difficulty. [Lööw](../BIBLIOGRAPHY.md#loow-2021)'s stack is the closest prior art and stops short of this statement.
2. The multi-domain version: the theorem above is per-domain; the composition across declared boundaries is [06](06-boundaries.md)'s.
3. Whether hypothesis (1) can be weakened from "in domain" to "in domain or provably unobservable this cycle" — the F2 violations may be on nets whose values are dead; that would repair the shipped design's status without touching silicon.

## First experiments

- State and prove the single-domain theorem for a toy: two flops, three gates, interval delays. Every structural feature (both window halves, the escape hatch, slew propagation) already appears at this size.
- Check whether the F2-violating nets are functionally dead (open problem 3) — this is cheap and would clear one of the two false hypotheses.

## Effort

Months for the single-domain statement and proof; the multi-domain composition rides on [06](06-boundaries.md).
