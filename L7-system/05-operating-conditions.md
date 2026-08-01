# L7/05 — The operating-conditions clause

## Statement

`Sys(F)` must take a stance on every software-reachable knob that can invalidate a lower layer's hypotheses — the theorem-shaped version of a datasheet's "recommended operating conditions" table. An S4-class authored choice; deciding it early keeps MAIN's metatheorem free of design-specific side conditions on `F`.

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
