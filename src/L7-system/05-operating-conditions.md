# L7/05 — The operating-conditions clause

## Background

Every datasheet has a table called **recommended operating conditions**: supply voltage between here and here, temperature between here and here, clock no faster than this — and every other promise in the document is implicitly conditional on that table. This chapter builds the formal analogue of that table, and the reason it is needed is a fact about modern chips that surprises outsiders: *software can reconfigure the hardware out from under its own correctness proof.*

The mechanism is **configuration registers** (CSRs, control/status registers): memory-mapped registers whose bits are wired to physical knobs. The sharpest example is the clock. This chip does not simply run at a fixed frequency; it contains a **PLL** (phase-locked loop) — an analog circuit that takes the board's reference clock and multiplies it up to the core frequency — and the multiplication factor, trim, and clock-source selection are all set by software-writable registers. The entire timing story of L2 is a proof that the logic settles within *one specific clock period*; a single store instruction to the PLL configuration can shrink that period below what was proved. Nothing in the hardware prevents it. The same pattern recurs for the pad drive modes (which the interface timing sign-off assumed fixed) and the flash controller's mode bits (which the bus latency bound depends on).

So hypotheses of lower-layer theorems turn out to depend on *register state*, which makes them **reachability conditions**: either prove the hypothesis for every register value the software can actually reach, or draw a line — inside the line, the spec's promises; outside it, explicitly no promises. The second option is what this chapter constructs, and it must also say precisely what "no promises" means. The answer deliberately falls short of the C programmer's "undefined behaviour" (where the spec permits literally anything): here, out-of-condition operation floods the machine's state with unknowns, but the *electrical safety* envelope still holds — a misconfigured clock computes garbage, it does not damage the die — and a reset restores the machine to the specified regime. Garbage, bounded, recoverable: weak enough to be true, and deliberately too weak for anything safety-critical to lean on.

## Statement

`Sys(F)` must take a stance on every software-reachable knob that can invalidate a lower layer's hypotheses — the theorem-shaped version of a datasheet's "recommended operating conditions" table. An S4-class authored choice; deciding it early keeps the overview's metatheorem free of design-specific side conditions on `F`.

## The pattern, and its known instances

**Register-dependent hypotheses of lower-layer theorems become reachability conditions.** Per knob, exactly two discharge routes: *prove* the hypothesis over every reachable setting, or *declare* the excess unspecified in the spec.

| knob | hypothesis threatened | status |
|---|---|---|
| PLL trim (`itrim`) + divider + source mux | timing closure's period (L2's bridge hypothesis 2) | **F6** — reachable range vs. closed range unverified |
| pad drive-mode / GPIO config chain | interface timing sign-off modes | **F4** — mode coverage unverified |
| XIP mode bits | the bus latency bound `B(config)` ([02](02-bus-contract.md)) | third instance, filed on arrival |

The table is expected to grow one row per discovered knob; the file exists so the third-and-later instances are filing operations, not rediscoveries.

## What "unspecified" means — precisely, and deliberately weakly

Not C-style undefined behaviour. Per L2/00's value lattice: the state floods with **X** — *envelope-bounded demonic nondeterminism*. The damage tier (L0/07's V-conditions) is still excluded — an out-of-spec clock configuration computes garbage, it does not burn the die — and **recovery is provable**: restore the configuration, reset, and X-elimination re-enters the tracked fragment. So the clause's semantics is: outside recommended operating conditions, `Sys(F)` constrains `obs` only to the electrically safe trace set, until the next reset re-anchors.

This weakness is a feature twice over: it is *true* of the physics (the envelope genuinely still holds), and it keeps the UB clause from ever being load-bearing for safety-critical reasoning — nothing above may assume out-of-spec behaviour is *absent*, only that it is recoverable.

## Obligations

1. The clause itself, as a component of `Sys`: the recommended-conditions predicate over configuration state, and the X-flood semantics outside it.
2. Per-row resolution: F6's range computation (L2/05 obligation 5), F4's mode coverage, `B(config)`'s domain.
3. The audit discipline shared with L6/02: no lower-layer proof may consume a register-dependent hypothesis without a row here.

## Effort

Days for the clause; the rows resolve at their owning layers. The value is the slot: every future knob lands in a named place.
