# L2/04 — SDC exceptions

## Statement

Every path STA skips carries a human claim that skipping is sound. **No tool checks any of them.** This file classifies the claims, gives each class its discharge method, and is the project's tractable entry point: weeks of work on a real fabricated design, where a negative result is as publishable as a positive one.

The shipped inventory (`signoff/caravel/caravel.sdc`, 406 lines): **112** `set_false_path`, **45** `set_case_analysis`, **2** `set_clock_groups`, **0** `set_multicycle_path`. The danger is asymmetric — omitting an exception over-constrains and costs frequency; adding one wrongly skips a real check and the chip fails. Every one of the 159 is a place where safety was traded for frequency on someone's judgement.

## Step zero: the SDC is a program

SDC is Tcl — conditionals, variables (`$clk_period`), mode branches. The same flop output (`housekeeping/_6817_/Q`) is pinned to **both 0 and 1** in different branches. Nothing can be classified until the Tcl is *elaborated* into flat per-mode constraint sets; the flat sets, not the script, are the objects the claims below attach to.

## The four classes, with their discharge statements

| class | count here | claim | discharge |
|---|---|---|---|
| **logically false** | few | no transition can propagate along the path | 2-vector SAT on the netlist |
| **asynchronous** | dominant (`mprj_io[*]`) | the endpoint tolerates unconstrained data | structural synchroniser check + P1 |
| **static** | config signals | the source cannot change during operation | sequential reachability |
| **mode** (`set_case_analysis`) | 45 | the pin is constant *in this mode* | mode-coverage over reachable configurations |

**Logically false** is the clean case, with one classical trap: the correct criterion is about *transitions*, not values. Static (one-vector) sensitisation is both unsound and incomplete for delay — the honest query is "no input/state *pair* propagates a transition along the path" (the false-path/viability literature, McGeer–Brayton). The safe direction for justifying an exclusion is the two-vector unsatisfiability, which is a well-defined SAT obligation on the netlist plus a reachability assumption on the state.

**Asynchronous** is the dominant class here — 40× `-from mprj_io[*]` and friends: external GPIO with no timing relationship to the internal clock. Declaring the path false does not make the *interface* safe; the actual claim is that the receiving endpoint treats the data as unconstrained, i.e. **a synchroniser stands behind it**. That is a structural netlist predicate (two-flop chain, no combinational fanout from the first flop, single-domain clocking) plus P1's residue — [06](06-boundaries.md)'s machinery, not SAT. **F1 lives here**: the failing `in2reg` hold paths are presumably all of this class; nobody has checked that each one lands on a synchroniser.

**Static** claims are sequential: the signal is written once during configuration and never again. Discharge is reachability over the configuration state machine — bounded and shallow if the design's configuration story is as simple as it looks, but a *proof about reachable states*, not about the netlist graph.

**Mode** claims are the subtle ones. `set_case_analysis` pins flop outputs to constants, and timing was verified separately per mode. Soundness needs **coverage**: every reachable configuration lies in some verified mode (F4). The pad-configuration modes tie this directly to L7's GPIO config space — the same object seen from the timing side.

**Multicycle**, for the record, asserts *two* things (destination not enabled on intervening edges; source held stable throughout) plus a hold-side adjustment that defaults wrong. Caravel declares none — a genuine simplification, noted so its absence is recognised as load-bearing.

## The work plan

1. Elaborate the Tcl into flat per-mode constraint sets; diff the modes against each other (the `_6817_` double-pin falls out here as two modes, or as a bug).
2. Classify all 159 into the four classes — mostly mechanical from the pin names and netlist context.
3. Discharge per class: SAT for the logical ones, the synchroniser predicate for the asynchronous ones, reachability sketches for static/mode.
4. **Close F1**: map every failing `in2reg` hold path to its covering exception and check the exception is justified. Either outcome is a result — a clean pass proves what everyone assumes about a fabricated chip; a gap is a real finding in shipped silicon.

## Obligations

1. A formal semantics for the flat constraint sets (what a false path *means* to [02](02-verified-sta.md)'s excluded-path plumbing).
2. The two-vector sensitisation query, stated against `Mealy(N)` with a reachability side condition.
3. The synchroniser predicate, shared with [06](06-boundaries.md).
4. Mode coverage, shared with L7's configuration model (F4).

## Effort

**Weeks to months, needing only artifacts already in `data/`.** This is the recommended first real work of the entire project — see the top README's "where to start".
