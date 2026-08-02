# L4/01 — The subset, measured

## Background

Verilog is really two languages sharing a syntax. One is for *describing hardware*; the other is for *writing testbenches* — simulation-only code that pokes the design with stimuli, and may freely use constructs with no physical counterpart: `#10` ("wait ten simulated nanoseconds"), `force` (reach in and override a wire), `fork` (spawn parallel processes). Synthesis tools accept only the first language — the **synthesisable subset** — and even that subset has dark corners the standard leaves loose: `casex`'s treatment of unknown values is a famous source of simulation/synthesis mismatch, and an explicit `'bx` literal drags the simulator's "unknown" value into design semantics. A formal semantics for *all* of Verilog would be enormous, contested, and mostly spent on constructs that describe no hardware.

The move this chapter makes — the same one the book makes at every layer where a messy industrial format appears — is to refuse the general problem. Instead: choose a well-behaved subset, give the semantics for exactly that subset, and *mechanically check* that the design lies inside it, so that every dark corner becomes a parse error rather than a semantic question. Nobody has to formalise what `force` means if a checker proves `force` never occurs. The empirical discovery that makes this cheap here is in the table below: measured over its 3,044 lines, picorv32 uses essentially none of the dangerous constructs, and the residue needing individual care is 19 specific places in the file — few enough to inspect by hand, which is precisely the "semantically tame" property for which this core was selected.

## Statement

A semantics for **the synthesisable subset this design actually uses** — not for Verilog. The target sources are the machine-emitted pair — [`VexRiscv_MinDebugCache.v`](https://github.com/efabless/caravel_mgmt_soc_litex/blob/503eda0790085712ffef7f4ad8934c7daed3237f/verilog/rtl/VexRiscv_MinDebugCache.v) and [`mgmt_core.v`](https://github.com/efabless/caravel_mgmt_soc_litex/blob/503eda0790085712ffef7f4ad8934c7daed3237f/verilog/rtl/mgmt_core.v) — whose census ([`check-l4.py`](../tools/check-l4.py); [Findings](../findings.md#the-management-core-in-the-pinned-netlist-is-vexriscv)) is *narrow*: zero delays, zero `casex`, zero force-class constructs, 7 don't-care `'bx` literals, 2 blocking-assignment blocks, and 541 `always @*` blocks between them. For calibration, the census of the hand-written comparison core ([picorv32](https://github.com/YosysHQ/picorv32), also measured by the checker):

| construct | count | consequence |
|---|---|---|
| `#` delays | **0** | no scheduling games |
| `casex` | **0** | — |
| `force` / `release` / `deassign` | **0** | — |
| UDPs, `fork`/`join`, events | **0** | — |
| X literals (`'bx`) | **25** | deliberate don't-cares: synthesis chooses freely, simulation propagates X — per-site value-independence obligations, or refinement into spec nondeterminism ([03](03-x-and-reset.md)) |
| `always @*` | 15 | latch-inference risk → [02](02-comb-blocks.md) |
| posedge blocks with blocking `=` | 5 of 24 (38 stmts) | intra-block order-dependence → [00](00-elaborated-object.md) |
| `casez` | 1 | wildcard patterns: `?`/`z` bits in the *case item* are don't-cares — one site, one convention to fix |
| `initial` | 1 | power-up value → [03](03-x-and-reset.md) |

(Census over `picorv32.v`, 3,044 lines; the surrounding SoC RTL needs the same sweep, which is mechanical.)

## The admissible-subset move, third instance

This is the same manoeuvre as L1/00 (GDS: forbid pathtype 1, self-intersection, non-90° SREF) and L3/00 (structural Verilog: ~20 productions): **define the semantics for a well-formed subset chosen to match what production artifacts actually contain, and *check* membership rather than assuming it.** The subset boundary is enforced by the front end — a construct outside it is a rejection, not a guess. The pattern's value is that the semantics' hard cases become parse errors: nobody has to decide what `force` means because the checker proves it never occurs.

The discipline that follows: **write the semantics for exactly what appears.** Every construct in the subset gets its meaning from [00](00-elaborated-object.md)'s simple semantics; every construct outside it is rejected; there is no third category of "handled approximately."

## The generated-source situation

The target sources are machine-emitted — [SpinalHDL](https://github.com/SpinalHDL/SpinalHDL) for the core, [LiteX](https://github.com/enjoy-digital/litex) for the SoC — and neither generator has a written-down IR semantics to appeal to (FIRRTL is the counterexample, unavailable here — [04](04-adequacy.md)). The consequences cut both ways. Per construct, generated Verilog is *easier*: the emitters use a small, disciplined idiom, and the shipped pair has fewer dark-corner constructs than the hand-written comparison core at 25× the block count. Per meaning, it is *harder*: there is no human-written source to consult when the semantics is in doubt, so the adequacy checks of [04](04-adequacy.md) — differential simulation, the CEC cross-check — carry more of the layer's weight.

## Obligations

1. Run the same census over the SoC-level RTL (`caravel_core.v` RTL, housekeeping, wrapper) — the census covers the picorv32 file only.
2. Freeze the subset grammar as the front end's acceptance language; wire the census into it as a regression (a construct appearing after an upstream bump must fail loudly).
3. The `casez` convention: one site, fix the don't-care semantics explicitly.

## Effort

Days — the census exists; the work is promoting it from measurement to enforced boundary.
