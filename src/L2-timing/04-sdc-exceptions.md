# L2/04 — SDC exceptions, and constraint completeness

## Background

STA's great virtue — it checks every path — is also a problem, because some paths *should not* be checked. A signal crossing from an external pin with no timing relationship to the internal clock can never satisfy a setup deadline stated against that clock; a configuration wire written once at boot will never transition during operation; a path through logic that no reachable input combination can actually activate imposes a phantom constraint. Left in place, such paths either fail the analysis spuriously or force the clock slower to accommodate journeys that never happen. The industry's mechanism for handling them is the **SDC file** (Synopsys Design Constraints — the de facto standard format): alongside defining the clocks, it lists **timing exceptions**, of which the important kinds are `set_false_path` ("do not check this path — I assert it doesn't matter"), `set_case_analysis` ("analyse with this pin frozen at this constant — we are in the mode where it is"), and `set_multicycle_path` ("this path is allowed N clock periods rather than one").

Read those glosses again with a verifier's eye: every exception is a *human assertion* that removing a check is sound — and no tool anywhere validates any of them. The STA engine obeys the SDC as commanded. An exception wrongly *omitted* merely costs frequency; an exception wrongly *added* deletes a real check, and the resulting chip carries a timing violation that no analysis ever saw. Exception inventories are one of the largest unaudited trust surfaces in industrial flows — hand-maintained chip-level SDCs routinely carry hundreds of assertions in a Tcl program whose *evaluation* is itself a task.

This design's constraint file makes the opposite trade, and the audit inverts with it. The flow *generates* the SDC, and what it generates is minimal: **one declared clock** (the external core clock, with an uncertainty margin), default driving-cell and load models, and **zero exceptions** — no false paths, no case analysis, no multicycle paths. There is nothing over-asserted to audit. The trust surface moves to what is *missing*: the design has more clock domains than the SDC declares — the JTAG port clocks the debug transport logic from its own pin, and the serial TileLink bridge clocks its pad-side half from the link clock — and **a path in an undeclared domain is not excepted, it is simply unanalysed**. Unconstrained-is-unchecked is more dangerous than excepted-with-a-claim, because no assertion exists to audit.

## Statement

Every path STA skips carries a claim that skipping is sound — whether the skip is an explicit exception or a silent gap in the constraints. This file audits both directions: the (empty) exception inventory, and the **completeness** of the constraint set against the design's actual clock-domain structure.

The measured inventory (the generated `ChipTop.mapped.sdc` plus the clock fragment): **1** `create_clock` (`clock_uncore`, 50 ns, 2 ns uncertainty), **1** trivial `set_clock_groups`, **0** `set_false_path`, **0** `set_case_analysis`, **0** `set_multicycle_path`.

## Step zero: what the constraints do not say

The audit's first deliverable is the diff between the declared clock set and the netlist's clock-domain census ([05](05-clock.md)'s machinery):

| domain | source | in the SDC? | consequence |
|---|---|---|---|
| core clock | `clock_uncore` pad | **yes** | the analysed domain |
| JTAG | `jtag_TCK` pad | **no** | debug-transport paths unanalysed; crossings to the core domain unconstrained |
| serial link | `serial_tl_0_clock_in` pad | **no** | the bridge's pad-side half unanalysed; the link-to-core crossing unconstrained |
| async reset | `reset_io` pad | n/a (not a clock) | reset-recovery/removal checks need their own constraint |

The gaps are not necessarily *unsound* — the crossings in question land in synchroniser structures ([06](06-boundaries.md)'s inventory), and the domains are low-speed — but "necessarily" is exactly what an audit refuses to assume. Each row must end in one of: a declared clock plus analysed crossings; a justified exception with its discharge; or a recorded finding that the flow's signoff does not cover the domain.

## The claim classes, kept ready

The four-way classification the audit framework carries (from designs whose files do have exceptions), because rows will appear here as the constraint set is completed:

| class | claim | discharge |
|---|---|---|
| **logically false** | no transition can propagate along the path | 2-vector SAT on the netlist |
| **asynchronous** | the endpoint tolerates unconstrained data | structural synchroniser check + P1 (input-side); exported interface guarantees (output-side) |
| **static** | the source cannot change during operation | sequential reachability |
| **mode** (`set_case_analysis`) | the pin is constant *in this mode* | mode-coverage over reachable configurations |

**Logically false** carries one classical trap worth keeping in view: the correct criterion is about *transitions*, not values. Static (one-vector) sensitisation is both unsound and incomplete for delay — the honest query is "no input/state *pair* propagates a transition along the path" (the false-path/viability literature, McGeer–Brayton). The safe direction for justifying an exclusion is the two-vector unsatisfiability, which is a well-defined SAT obligation on the netlist plus a reachability assumption on the state.

**Asynchronous** is where the undeclared domains will land when the set is completed: declaring a crossing false does not make the *interface* safe; the actual claim is that the receiving endpoint treats the data as unconstrained, i.e. **a synchroniser stands behind it** — a structural netlist predicate (two-flop chain, no combinational fanout from the first flop, single-domain clocking) plus P1's residue — [06](06-boundaries.md)'s machinery, not SAT.

**Multicycle**, for the record, asserts *two* things (destination not enabled on intervening edges; source held stable throughout) plus a hold-side adjustment that defaults wrong. This design declares none — a genuine simplification, noted so its absence is recognised as load-bearing.

## The work plan

1. The clock-domain census against the netlist ([05](05-clock.md)); the domain/SDC diff table pinned by the layer's checker.
2. Per gap: complete the constraint (declare the clock, constrain the crossing) or record the finding — with the flow re-run under the completed set, since new constraints can surface new violations.
3. The synchroniser predicate over the crossing endpoints ([06](06-boundaries.md)), replacing assumption with structure.
4. The reset-recovery constraint question settled explicitly.

## Obligations

1. A formal semantics for the flat constraint set (what a declared clock, an uncertainty, and any future exception *mean* to [02](02-verified-sta.md)'s plumbing).
2. The completeness theorem shape: every sequential element's clock pin traces to a declared clock, or its absence is a named finding.
3. The two-vector sensitisation query, stated against `Mealy(N)`, held ready for the first real exception.
4. The synchroniser predicate, shared with [06](06-boundaries.md).

## Effort

**Weeks, needing only the flow's own artifacts.** The audit is smaller than a hand-written chip's — the generated file has nothing to elaborate and nothing over-asserted — and the completeness half is the part with teeth.
