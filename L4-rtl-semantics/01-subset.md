# L4/01 — The subset: 19 sites, measured

## Statement

A semantics for **the synthesisable subset this design actually uses** — not for Verilog. The general artifact is large and contested; the specific one is 19 individually inspectable sites, and the categories that make Verilog semantics genuinely awful are *absent*, measured rather than hoped:

| construct | count | consequence |
|---|---|---|
| `#` delays | **0** | no scheduling games |
| X literals (`'bx`) | **0** | no X-optimism/pessimism asymmetry in the source |
| `casex` | **0** | — |
| `force` / `release` / `deassign` | **0** | — |
| UDPs, `fork`/`join`, events | **0** | — |
| `always @*` | 15 | latch-inference risk → [02](02-comb-blocks.md) |
| posedge blocks with blocking `=` | 2 of 25 | intra-block order-dependence → [00](00-elaborated-object.md) |
| `casez` | 1 | wildcard patterns: `?`/`z` bits in the *case item* are don't-cares — one site, one convention to fix |
| `initial` | 1 | power-up value → [03](03-x-and-reset.md) |

(Census over `picorv32.v`, 3,044 lines; the surrounding SoC RTL needs the same sweep, which is mechanical.)

## The admissible-subset move, third instance

This is the same manoeuvre as L1/00 (GDS: forbid pathtype 1, self-intersection, non-90° SREF) and L3/00 (structural Verilog: ~20 productions): **define the semantics for a well-formed subset chosen to match what production artifacts actually contain, and *check* membership rather than assuming it.** The subset boundary is enforced by the front end — a construct outside it is a rejection, not a guess. The pattern's value is that the semantics' hard cases become parse errors: nobody has to decide what `force` means because the checker proves it never occurs.

The discipline that follows: **write the semantics for exactly what appears.** Every construct in the subset gets its meaning from [00](00-elaborated-object.md)'s simple semantics; every construct outside it is rejected; there is no third category of "handled approximately."

## Why this beats the alternatives that were considered

The generated cores (VexRiscv/SpinalHDL, the LiteX wrapper) are ~550 KB of machine-emitted Verilog — *narrower* in construct usage but hostile to invariant authoring, and their generators have no written-down IR semantics to appeal to (FIRRTL is the counterexample, unavailable here — [04](04-adequacy.md)). Hand-written picorv32 costs 19 sites of care and buys a source a human can state an invariant over. That trade was the target-selection decision, and this census is its receipt.

## Obligations

1. Run the same census over the SoC-level RTL (`caravel_core.v` RTL, housekeeping, wrapper) — the 19-site figure is core-only.
2. Freeze the subset grammar as the front end's acceptance language; wire the census into it as a regression (a construct appearing after an upstream bump must fail loudly).
3. The `casez` convention: one site, fix the don't-care semantics explicitly.

## Effort

Days — the census exists; the work is promoting it from measurement to enforced boundary.
