# L2/04 — SDC exceptions

## Background

STA's great virtue — it checks every path — is also a problem, because some paths *should not* be checked. A signal crossing from an external pin with no timing relationship to the internal clock can never satisfy a setup deadline stated against that clock; a configuration wire written once at boot will never transition during operation; a path through logic that no reachable input combination can actually activate imposes a phantom constraint. Left in place, such paths either fail the analysis spuriously or force the clock slower to accommodate journeys that never happen. The industry's mechanism for handling them is the **SDC file** (Synopsys Design Constraints — the de facto standard format): alongside defining the clocks, it lists **timing exceptions**, of which the important kinds are `set_false_path` ("do not check this path — I assert it doesn't matter"), `set_case_analysis` ("analyse with this pin frozen at this constant — we are in the mode where it is"), and `set_multicycle_path` ("this path is allowed N clock periods rather than one").

Read those glosses again with a verifier's eye: every exception is a *human assertion* that removing a check is sound — and no tool anywhere validates any of them. The STA engine obeys the SDC as commanded. An exception wrongly *omitted* merely costs frequency; an exception wrongly *added* deletes a real check, and the resulting chip carries a timing violation that no analysis ever saw. This design ships 159 such assertions. Each is a judgement call by a designer, encoded in a scripting language (SDC files are Tcl programs, with variables and conditionals — so even determining *what* was asserted requires evaluating the script), and collectively they are one of the largest unaudited trust surfaces in the whole flow. That is exactly the kind of thing this project exists to audit, and since the shipped SDC is in `data/` and the checks are bounded, this chapter is the recommended first real work of the entire project.

The discharge methods sort by what kind of claim each exception secretly is — and the sorting is the chapter's content. Some are *combinational* claims ("no transition propagates here"), which reduce to SAT queries on the netlist. Some are *interface* claims ("this input is asynchronous"), which are really claims that a **synchroniser** — the two-flop construction of [06](06-boundaries.md) that safely receives clock-less signals — stands behind the pin, a structural check. Some are *sequential* claims ("this wire never changes after boot"), needing reachability arguments. And the mode-analysis pins are claims about *configuration coverage* — that every mode the software can actually reach was one of the modes analysed — which ties directly to L7's configuration registers. Four classes, four different proof technologies, none of them exotic; what is novel is only the discipline of demanding them.

## Statement

Every path STA skips carries a human claim that skipping is sound. **No tool checks any of them.** This file classifies the claims, gives each class its discharge method, and is the project's tractable entry point: weeks of work on a real fabricated design, where a negative result is as publishable as a positive one.

The shipped inventory (`signoff/caravel/caravel.sdc`, 406 lines): **112** `set_false_path`, **45** `set_case_analysis`, **2** `set_clock_groups`, **0** `set_multicycle_path`. The danger is asymmetric — omitting an exception over-constrains and costs frequency; adding one wrongly skips a real check and the chip fails. Every one of the 159 is a place where safety was traded for frequency on someone's judgement.

## Step zero: the SDC is a program

SDC is Tcl — conditionals, variables (`$clk_period`), mode branches. The same flop output (`housekeeping/_6817_/Q`) is pinned to **both 0 and 1** in different branches. Nothing can be classified until the Tcl is *elaborated* into flat per-mode constraint sets; the flat sets, not the script, are the objects the claims below attach to.

**Done** — `tools/sdc-audit.py` (a tclsh harness stubbing every SDC command) elaborates the full mode space: **8 modes** (`io_4_mode` × `ios_mode` × `IO_SYNC`), shipped setting SCK/OUT/0, 87–139 flat constraints each; results in [Findings](../findings.md#sdc-exceptions). The `_6817_` double-pin resolved as **modes, not a bug**: 0 in all SCK modes, 1 in all GPIO modes — it is `hkspi_disable` (named by the core SDC's own comment), and the other cross-mode conflicts are exactly the `DM[2:0]` pad drive-mode bus.

**Scoping note — there are two SDCs.** The 8-mode file above is the *chip-level* `signoff/caravel/caravel.sdc`. The `caravel_core` signoff used its own single-mode `caravel_core.sdc`, which constrains **all** inputs as 4 ns synchronous arrivals against `clk` and false-paths only `rstb_h` and `gpio_in_core` — so at the core level the failing `in2reg` hold paths were *real constrained paths*, not excepted ones ([Findings: F1 confronted](../findings.md#f1-confronted-the-shipped-timing-evidence)). Both files are audited by `check-l2.py`.

## The four classes, with their discharge statements

| class | count (measured, per mode) | claim | discharge |
|---|---|---|---|
| **logically false** | **0** | no transition can propagate along the path | 2-vector SAT on the netlist |
| **asynchronous** | **all of them** (36–39; `mprj_io[*]`, `gpio`, `resetb`) | the endpoint tolerates unconstrained data | structural synchroniser check + P1 (input-side); exported interface guarantees (output-side) |
| **static** | **0** | the source cannot change during operation | sequential reachability |
| **mode** (`set_case_analysis`) | 41 distinct pins; 4 mode-selects | the pin is constant *in this mode* | mode-coverage over reachable configurations |

The classification came back cleaner than the plan anticipated: **every false path in every mode is asynchronous-external** — no logically-false claims, no static claims, nothing unclassified. Two consequences. The SAT and reachability machinery rows 1 and 3 budgeted for are *not needed for this design's false paths at all*; and the asynchronous class splits by direction — the shipped OUT mode's 34 exceptions are `-to` the pads, where the claim is about the **external consumer's** timing (L2/06's exported-guarantee side), not about any synchroniser in this netlist.

**Logically false** is the clean case, with one classical trap: the correct criterion is about *transitions*, not values. Static (one-vector) sensitisation is both unsound and incomplete for delay — the honest query is "no input/state *pair* propagates a transition along the path" (the false-path/viability literature, McGeer–Brayton). The safe direction for justifying an exclusion is the two-vector unsatisfiability, which is a well-defined SAT obligation on the netlist plus a reachability assumption on the state.

**Asynchronous** is the dominant class here — 40× `-from mprj_io[*]` and friends: external GPIO with no timing relationship to the internal clock. Declaring the path false does not make the *interface* safe; the actual claim is that the receiving endpoint treats the data as unconstrained, i.e. **a synchroniser stands behind it**. That is a structural netlist predicate (two-flop chain, no combinational fanout from the first flop, single-domain clocking) plus P1's residue — [06](06-boundaries.md)'s machinery, not SAT. **F1 lives here**: the failing `in2reg` hold paths are presumably all of this class; nobody has checked that each one lands on a synchroniser.

**Static** claims are sequential: the signal is written once during configuration and never again. Discharge is reachability over the configuration state machine — bounded and shallow if the design's configuration story is as simple as it looks, but a *proof about reachable states*, not about the netlist graph.

**Mode** claims are the subtle ones. `set_case_analysis` pins flop outputs to constants, and timing was verified separately per mode. Soundness needs **coverage**: every reachable configuration lies in some verified mode (F4). The pad-configuration modes tie this directly to L7's GPIO config space — the same object seen from the timing side.

**Multicycle**, for the record, asserts *two* things (destination not enabled on intervening edges; source held stable throughout) plus a hold-side adjustment that defaults wrong. Caravel declares none — a genuine simplification, noted so its absence is recognised as load-bearing.

## The work plan

1. ~~Elaborate the Tcl into flat per-mode constraint sets~~ — **done** (`tools/sdc-audit.py`; the `_6817_` double-pin fell out as two modes).
2. ~~Classify into the four classes~~ — **done**: all asynchronous; see the table.
3. ~~The synchroniser predicate for the input-side entries~~ — **run** (`tools/synccheck.py`; [Findings](../findings.md#the-synchroniser-audit-l204-step-3-l206s-predicate-f1f3)): behind the `mprj_io` exceptions there are **no two-flop synchronisers**. The input side resolves into source-synchronous SPI capture (bits 3/4 acting as clocks; 615 flops on a *muxed* shift clock), and **40 single-flop core-clock captures** whose discharge must be software pacing + single-stage settling — a weaker claim than the predicate, now to be stated and priced (P1's `N_sync`). `gpio_in_core` is the one verified two-flop synchroniser. Remaining: the exported-interface argument for the output side.
4. **Close F1**: map every failing `in2reg` hold path to its covering exception — the endpoint census above now says what the endpoints *are*; what remains is matching the signoff report's specific failing paths against them.
5. **F4, sharpened**: the shipped file pins one mode of eight, and the modes' constraint sets genuinely differ — determine from the OpenLane logs whether the other seven were ever timed, and whether `-logically_exclusive` (an unverified claim, SCK modes only) is justified.

## Obligations

1. A formal semantics for the flat constraint sets (what a false path *means* to [02](02-verified-sta.md)'s excluded-path plumbing).
2. The two-vector sensitisation query, stated against `Mealy(N)` with a reachability side condition.
3. The synchroniser predicate, shared with [06](06-boundaries.md).
4. Mode coverage, shared with L7's configuration model (F4).

## Effort

**Weeks to months, needing only artifacts already in `data/`.** This is the recommended first real work of the entire project — it is first on the repository README's "where to start" list.
