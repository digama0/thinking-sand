# L2/01 — The bridge theorem (M5)

## Background

Every layer above this point reasons about the chip as a clocked state machine: state now, one step, state next. That picture is not physics — it is a *theorem-shaped claim* that industrial practice believes, acts on, and has never stated. Designers say the design "meets timing" or "closes timing" (**timing closure**), meaning the checking tools report that every flop's setup and hold requirements are satisfied at the intended clock period; and everyone proceeds as if closure implies the discrete abstraction is sound. The implication is almost surely true. It is also nowhere written down as mathematics — with its hypotheses enumerated, its conclusion stated over a defined model, and its edge cases forced into the open. Writing it down is this chapter, and the exercise is the book's central specimen of the pattern *"a design rule is secretly a hypothesis of a theorem nobody wrote."*

The proof shape is worth previewing in words because it explains *why* the synchronous discipline works, not just that it does. It is an induction over clock cycles, and the invariant is simply "at the start of each cycle, every flop stably holds the state the Mealy machine says it should." Given that, the settled combinational values are the right ones by the time the setup margin requires (the *fast enough* half); the newly-launched values of the next cycle cannot corrupt the capture (the *not too fast* half, hold); so the edge captures exactly the Mealy machine's next state, and the invariant is re-established — *fully*, every cycle. That last point is the profound one: the clock edge is a **restoration point in time**. Nothing carries over; timing error does not accumulate across a trillion cycles any more than voltage noise accumulates across a chain of restoring gates. The tower's recurring motif — every layer has a mechanism that resets its own error to zero — appears here in its temporal form.

The asymmetry between the two halves also deserves plain statement, because it drives real engineering behaviour. The clock period appears in the setup inequality only: a setup-slow chip can always be rescued by clocking it slower, which is why vendors can sell slower parts from an imperfect batch ("binning"). Hold contains no period at all — it is a race between two paths launched by the *same* edge — so a hold-violating chip is broken at every frequency, forever, in silicon. Hold bugs are the ones that kill tapeouts, and the reader will see hold appear as the sharp edge in several findings below.

## Statement

Over the timed model of [00](00-timed-model.md):

> Let `N` be the hardened netlist, partitioned into clock domains with declared asynchronous boundaries ([06](06-boundaries.md)). Suppose:
>
> 1. *(domain)* every cell's load and input slew lie inside its contract's domain — `max_capacitance` / `max_transition` — an F-series row until the flow's signoff closes it;
> 2. *(closure)* setup and hold hold at every flop, at every corner, with respect to the clock arrival function — certified by STA ([02](02-verified-sta.md)) — likewise an F-series row until multi-corner closure is achieved and pinned;
> 3. *(constraints)* the constraint set is complete — every domain declared, every excluded path justified ([04](04-sdc-exceptions.md));
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
| combinational loops | the DAG cut | expected none (no on-die oscillator); W3's check enforces it |
| latch-based time borrowing | no clean capture edge; windows span stages | absent as a *design style*; the clock-gate ICG latches are primitives with their own contract ([05](05-clock.md)) |
| wave pipelining | multiple waves in flight per segment | absent |
| multicycle paths | capture skips edges; *two* extra claims (destination not enabled between; source held throughout) plus a hold adjustment | **zero declared** — a genuine gift |
| clock gating | the arrival function becomes data-dependent | see [05](05-clock.md) |

## The conditioning is the theorem's honest edge

Hypothesis (4) is not a technicality: it is **where ε enters the whole project** (the overview's † marks). The theorem is deterministic *on the event* "no strike, no unresolved read"; [06](06-boundaries.md) and L0/06 bound the event's complement. Stating M5 unconditionally would be false; smearing the probability through the induction would be unworkable. The conditional form is the correct interface.

## Open problems

1. **Write it.** Bounded-delay model, window rule, per-cycle induction — a solid paper, not a decade. Its absence is a fact about nobody working at the boundary, not about difficulty. [Lööw](../bibliography.md#loow-2021)'s stack is the closest prior art and stops short of this statement.
2. The multi-domain version: the theorem above is per-domain; the composition across declared boundaries is [06](06-boundaries.md)'s.
3. Whether hypothesis (1) can be weakened from "in domain" to "in domain or provably unobservable this cycle" — domain violations on dead nets would then not falsify the hypothesis; worth stating before the first signoff report is adjudicated.

## First experiments

- State and prove the single-domain theorem for a toy: two flops, three gates, interval delays. Every structural feature (both window halves, the escape hatch, slew propagation) already appears at this size.
- When the flow's signoff reports slew/cap violations, check whether the violating nets are functionally dead (open problem 3) — cheap, and it decides how each report adjudicates.

## Effort

Months for the single-domain statement and proof; the multi-domain composition rides on [06](06-boundaries.md).
