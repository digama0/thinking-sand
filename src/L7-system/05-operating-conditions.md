# L7/05 — The operating-conditions clause

## Background

Every datasheet has a table called **recommended operating conditions**: supply voltage between here and here, temperature between here and here, clock no faster than this — and every other promise in the document is implicitly conditional on that table. This chapter builds the formal analogue of that table, and the reason it is needed is a fact about modern chips that surprises outsiders: *software can reconfigure the hardware out from under its own correctness proof.*

The mechanism is **configuration registers**: memory-mapped registers whose bits are wired to physical knobs. The sharpest instance on most chips is the clock — a software-programmable PLL whose settings can shrink the clock period below what the timing proof covered. This design *does not have one*: the core clock arrives at a pad from the board, unmultiplied, so the most dangerous knob of all is simply absent, and "the clock is in range" moves out of the register table entirely — it becomes a condition on the *environment* (the board's promise, P6's family), not on reachable software states. What remains software-reachable is tamer but real: a **clock gater** that can stop the clock, a **tile-reset setter** that can hold the processor in reset, the UART's **divisor register** on which the byte view's validity depends, and the **debug module**, an external agent with the authority to halt the core at any time.

So hypotheses of lower-layer theorems turn out to depend on *register state*, which makes them **reachability conditions**: either prove the hypothesis for every register value the software can actually reach, or draw a line — inside the line, the spec's promises; outside it, explicitly no promises. The second option is what this chapter constructs, and it must also say precisely what "no promises" means. The answer deliberately falls short of the C programmer's "undefined behaviour" (where the spec permits literally anything): here, out-of-condition operation floods the machine's state with unknowns, but the *electrical safety* envelope still holds — a misconfiguration computes garbage or stalls, it does not damage the die — and a reset restores the machine to the specified regime. Garbage, bounded, recoverable: weak enough to be true, and deliberately too weak for anything safety-critical to lean on.

## Statement

`Sys(F)` must take a stance on every software-reachable knob that can invalidate a lower layer's hypotheses — the theorem-shaped version of a datasheet's "recommended operating conditions" table. An S4-class authored choice; deciding it early keeps the overview's metatheorem free of design-specific side conditions on `F`.

## The pattern, and its known instances

**Register-dependent hypotheses of lower-layer theorems become reachability conditions.** Per knob, exactly two discharge routes: *prove* the hypothesis over every reachable setting, or *declare* the excess unspecified in the spec.

| knob | hypothesis threatened | status |
|---|---|---|
| clock gater | every liveness bound — a gated clock stalls all progress | to classify: quantify (progress claims conditional on ungated) or declare |
| tile-reset setter | same shape: a held reset is a liveness hole | same resolution family |
| UART divisor | the byte view's bit-cell timing ([00](00-sys-and-obs.md)'s derivation) | validity condition on the derivation, per configured baud |
| debug-module halt authority | the latency bound `B` and every WCET-flavoured claim | the debug spec's halt semantics as a spec actor; claims conditional on "not halted" |

Notably *absent* from the table, by design rather than by luck: a clock multiplier (none exists — the board owns clock safety), pad function muxing (pad functions are fixed), and persistent-store write paths (there is no writable persistent store — [04](04-power-epochs.md)). The table is expected to grow one row per discovered knob; the file exists so the later instances are filing operations, not rediscoveries.

## What "unspecified" means — precisely, and deliberately weakly

Not C-style undefined behaviour. Per L2/00's value lattice: the state floods with **X** — *envelope-bounded demonic nondeterminism*. The damage tier (L0/07's V-conditions) is still excluded — an out-of-spec configuration computes garbage, it does not burn the die — and **recovery is provable**: restore the configuration, reset, and X-elimination re-enters the tracked fragment. So the clause's semantics is: outside recommended operating conditions, `Sys(F)` constrains `obs` only to the electrically safe trace set, until the next reset re-anchors.

This weakness is a feature twice over: it is *true* of the physics (the envelope genuinely still holds), and it keeps the UB clause from ever being load-bearing for safety-critical reasoning — nothing above may assume out-of-spec behaviour is *absent*, only that it is recoverable. The same layered-UB pattern appears one level down in L6/03's spec-UB clause for reserved instruction encodings: at every layer, "undefined" means undefined *at this layer's alphabet*, bounded by all the layers below — no knob and no instruction is a halt-and-catch-fire.

## Obligations

1. The clause itself, as a component of `Sys`: the recommended-conditions predicate over configuration state, and the X-flood semantics outside it.
2. Per-row resolution: the gating/reset liveness conditioning, the divisor's validity condition, the debug-halt actor model.
3. The audit discipline shared with L6/02: no lower-layer proof may consume a register-dependent hypothesis without a row here.

## Effort

Days for the clause; the rows resolve at their owning layers. The value is the slot: every future knob lands in a named place.
