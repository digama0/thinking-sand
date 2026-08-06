# L4/01 — The subset, measured

## Background

Verilog (and its superset SystemVerilog) is really two languages sharing a syntax. One is for *describing hardware*; the other is for *writing testbenches* — simulation-only code that pokes the design with stimuli, and may freely use constructs with no physical counterpart: `#10` ("wait ten simulated nanoseconds"), `force` (reach in and override a wire), `fork` (spawn parallel processes), DPI calls into C. Synthesis tools accept only the first language — the **synthesisable subset** — and even that subset has dark corners the standard leaves loose: `casex`'s treatment of unknown values is a famous source of simulation/synthesis mismatch, and an explicit `'bx` literal drags the simulator's "unknown" value into design semantics. A formal semantics for *all* of the language would be enormous, contested, and mostly spent on constructs that describe no hardware.

The move this chapter makes — the same one the book makes at every layer where a messy industrial format appears — is to refuse the general problem. Instead: choose a well-behaved subset, give the semantics for exactly that subset, and *mechanically check* that the design lies inside it, so that every dark corner becomes a parse error rather than a semantic question. Nobody has to formalise what `force` means if a checker proves `force` never occurs. What makes this cheap here is that the RTL is **compiler output**: the SystemVerilog is emitted by CIRCT's `firtool` from FIRRTL, and a compiler back end emits a small, rigid idiom — the same handful of construct shapes, thousands of times.

## Statement

A semantics for **the synthesisable subset this design actually uses** — not for SystemVerilog. The target source is the emitted design cone: ~230 modules of machine-generated SystemVerilog (80 K lines across the emitted collateral, which also carries the simulation harness — excluded from the cone by the synthesis file list). The census, measured over the emitted files:

| construct | count | consequence |
|---|---|---|
| `#` delays | **0** in the design cone | no scheduling games (3 sites in DPI harness files, outside the cone) |
| `casex` / `casez` | **0** | — |
| `force` / `release` / `deassign` | **0** | — |
| UDPs, `fork`/`join`, events | **0** | — |
| DPI imports | **0** in the cone (harness only) | — |
| `always @(posedge …)` | 608 | the clocked bulk — uniformly non-blocking |
| blocking `=` in clocked blocks | **0** in the cone (4 sites, all in one harness file) | the order-dependence class is *absent* |
| `always @*` | **1** — the clock-gate wrapper | a *deliberate* latch: the ICG primitive ([02](02-comb-blocks.md)) |
| X literals (`'bx`) | 23, **all one idiom** | `read_data = en ? mem[addr] : 'bx` — memory-read don't-cares ([03](03-x-and-reset.md)) |
| `initial` | 425, **all one idiom** | the register-randomization initializer, whose synthesis-visible content is empty ([03](03-x-and-reset.md)) |
| `assert` and monitor modules | 3,938 mentions in 85 files | simulation-guarded verification collateral — an adequacy asset ([04](04-adequacy.md)) |

The numbers say something structural: a compiler back end has *already done* the subset-discipline work. There is exactly one level-sensitive block in the entire design, one X-idiom, one initializer idiom — because one code generator emitted everything. The dark-corner constructs are not rare; they are absent, and absent *by construction* rather than by an author's care.

## The admissible-subset move, third instance

This is the same manoeuvre as L1/00 (GDS: forbid pathtype 1, self-intersection, non-90° SREF) and L3/00 (structural Verilog: ~20 productions): **define the semantics for a well-formed subset chosen to match what production artifacts actually contain, and *check* membership rather than assuming it.** The subset boundary is enforced by the front end — a construct outside it is a rejection, not a guess. The pattern's value is that the semantics' hard cases become parse errors: nobody has to decide what `force` means because the checker proves it never occurs.

The discipline that follows: **write the semantics for exactly what appears.** Every construct in the subset gets its meaning from [00](00-elaborated-object.md)'s simple semantics; every construct outside it is rejected; there is no third category of "handled approximately."

## The generated-source situation

The target source is machine-emitted, and — unlike most generated RTL — its generator has a *written-down input semantics*: the design exists as FIRRTL, an intermediate representation with a specification, before `firtool` lowers it to SystemVerilog. The consequences cut both ways. Per construct, the emitted code is *easier* than hand-written RTL: one idiom per construct class, no dark corners, no author styles. Per meaning, the SystemVerilog is the *output of a compiler nobody has verified* — so the layer carries two anchors instead of one: the emitted-subset semantics defined here, and the FIRRTL-level semantics one storey up, with the lowering between them as a checkable seam ([04](04-adequacy.md)). That second anchor is what a hand-written design can never have.

## Obligations

1. Re-run the census as an enforced boundary over the *synthesis file list* (the design cone, mechanically separated from the harness collateral); pin it as a regression — a construct appearing after a generator bump must fail loudly.
2. Freeze the subset grammar as the front end's acceptance language.
3. The clock-gate wrapper's primitive contract ([02](02-comb-blocks.md)) — the one construct that is not combinational-or-clocked.

## Effort

Days — the census is measured; the work is promoting it from measurement to enforced boundary.
