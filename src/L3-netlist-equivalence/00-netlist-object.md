# L3/00 — The netlist object and its Mealy semantics

## Statement

Define `N` and `Mealy(N)` — the shared object of [MAIN's spec tower](../MAIN.md#the-spec-tower) and the left-hand side of this layer's theorem.

## One parse, three consumers

`N = ⟦gl_caravel_core.v⟧` under a single parser. The same object is: L1's LVS target (`N_intended`), L2's STA subject, and this layer's left-hand side. That identification is used silently everywhere and must be established once — it is **X1's obligation**, a verified parser for a deliberately tiny language.

Structural Verilog is a *file format*, not a programming language: module instantiations, wire declarations, port connections — **~20 productions**, no `always`, no assignments, no scheduling, no delta cycles, no X literals. The admissible-subset move from L1/00 (GDS) applies again: parse exactly what production output uses, reject the rest.

## The semantics, in outline

```
State  = Flop → 𝔹                        (5,774 bits at this hierarchy level)
Input  = Port_in → 𝔹
δ, λ   = topological evaluation of the combinational DAG through
         each cell's Boolean function (L0/05's (A)), then flop update
```

~30 lines of definition. Its preconditions are exactly [01](01-well-formedness.md)'s checks: acyclicity (W3) makes the topological evaluation well-defined; one-driver-per-net (W1) makes net values functions; no floating reads (W2) closes the evaluation; inertness (W4) lets the physical cells drop out of `State` entirely.

**Registers are lookup, not inference.** The library declares which cells are sequential and which pin is clock/data/reset/enable — identifying `State` is a table join, not pattern recognition. Clock and reset network identification is mechanical reachability ([L2/05](../L2-timing/05-clock.md)'s cleanliness check).

## What this semantics *is*, epistemically

Two facts that took the project a while to get right:

**S1 is derived, not posited.** "The netlist's Mealy semantics is the right semantics" was originally an axiom; it is now the *conclusion* of the physical stack — per-cell Boolean shadows (L0/05) + the bridge theorem (M5) + LVS (L1) yield it. This layer consumes that conclusion; nothing here assumes it.

**The two-valued semantics is the tracked fragment.** `Mealy(N)` over {0,1} describes the machine only inside the bridge theorem's hypotheses; the honest ambient object is the ternary machine over {0,1,X} ([L2/00](../L2-timing/00-timed-model.md)'s value lattice), and the two-valued view is entered by X-elimination at reset and *maintained* by timing closure. Where the RTL deliberately leaves state uninitialised, implementation-X refines the spec's own reset nondeterminism rather than being eliminated — the bisimulation of [03](03-register-correspondence.md) is stated from reset-reachable states for exactly this reason.

**Bits, not words.** `Mealy(N)` is over individual nets; the word structure lives only on the RTL side, and [03](03-register-correspondence.md) explains why it must never be reconstructed from below.

## Obligations

1. **X1**: the verified parser — CompCert-style validated front-end for a 20-production grammar. Standard work, no empirical content.
2. The ~30-line semantics, written once, with its four preconditions imported from [01](01-well-formedness.md) as hypotheses rather than assumptions.
3. The pin-direction table (43 names, declared not inferred — `tools/netgraph.py`'s table is the prototype) promoted into the semantics as the library signature.

## Effort

Weeks. This is the cleanest formal artifact in the entire stack — the reason the bottom-up route was attractive before L4's 19-site tax was measured — and it should be built early since every other file in L3 types against it.
