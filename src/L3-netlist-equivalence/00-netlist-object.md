# L3/00 — The netlist object and its Mealy semantics

## Background

Between the RTL a human wrote and the geometry the fab printed sits the **netlist**: the design expressed as a list of *gates* and the *wires* connecting them. It is produced from the RTL by **synthesis** — a compiler, in every meaningful sense: it parses the Verilog, maps the described logic onto a fixed vocabulary of available gates, and optimises hard along the way, restructuring the logic beyond recognition while (one hopes) preserving its function. The gate vocabulary is the **standard cell library**: a catalog of a few hundred pre-designed, pre-characterised primitive circuits — NAND gates, inverters, flip-flops, multiplexers, each in several drive strengths — provided with the fabrication process. Everything computational on the die is an instance of one of these cells; this design's synthesis netlist has 51,359 of them, drawn from just 96 cell types, and place-and-route adds more (clock buffers, hold-fix buffers, physical cells) before the netlist is final.

The netlist's file format is **structural Verilog** — the same language as the RTL, but stripped of everything programmatic: no `always` blocks, no assignments, no control flow, just instance declarations ("here is a NAND2 named `_04531_`, its pin A connects to net `_1234_`...") repeated a few hundred thousand times. Where the RTL is a program, the netlist is a parts list with a wiring diagram, and its semantics is correspondingly simpler to define — which is why this chapter is the cleanest formal artifact in the book.

That semantics is a **Mealy machine**: the classical mathematical form of a clocked circuit, consisting of a state (here, one bit per **flop** — flip-flop, the library's storage cell), a next-state function, and an output function. Reading a Mealy machine off a netlist works because the netlist separates cleanly into its sequential cells (the flops — which cells those are is declared in the library, a lookup rather than an inference) and everything else, the combinational cells, which form a **DAG** — a directed graph with no cycles — from flop outputs and input ports to flop inputs and output ports. One clock cycle means: evaluate the DAG in dependency order, each cell applying its little Boolean function; then update every flop simultaneously with the value at its data pin. The preconditions that make this well-defined (no cycles, exactly one driver per wire, nothing floating) are precisely the well-formedness checks of [01](01-well-formedness.md).

## Statement

Define `N` and `Mealy(N)` — the shared object of [the overview's spec tower](../overview.md#the-spec-tower) and the left-hand side of this layer's theorem.

## One parse, three consumers

`N = ⟦ChipTop.mapped.v⟧` (and, for the physical layers, its post-P&R successor) under a single parser. The same object is: L1's LVS target (`N_intended`), L2's STA subject, and this layer's left-hand side. That identification is used silently everywhere and must be established once — it is **X1's obligation**, a verified parser for a deliberately tiny language.

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

Weeks. This is the cleanest formal artifact in the entire stack — the reason the bottom-up route was attractive before L4's census tax was measured — and it should be built early since every other file in L3 types against it.
