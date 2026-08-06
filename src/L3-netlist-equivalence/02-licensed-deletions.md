# L3/02 — The licensed deletions

## Background

A newcomer's mental image of a chip — gates computing things — describes a modest fraction of one. The finished layout's instance census tells the real story: alongside the logic sit **physical cells**, present for electrical and manufacturing reasons — **decaps** (decoupling capacitors, smoothing the power supply against demand spikes), **tap cells** (connecting the transistors' silicon wells to the rails to prevent latch-up), **fill cells** (spacers keeping the fabricated layer densities uniform), and antenna **diodes** (protecting gates from charge build-up during fabrication) — usually outnumbering the logic outright once fill is inserted. Another large class is the **clock tree**: the clock signal cannot physically drive thousands of flops from one wire, so it is distributed through a tree of buffers — carefully balanced so every flop sees its edge at nearly the same moment, and including thousands of pure *delay* buffers inserted only to fix hold timing (this flow's hold repair alone inserts several thousand). Add ordinary signal buffers and inverter pairs, and the logic that L4's semantics actually describes is a minority of what gets fabricated.

For the equivalence proof, all of this must go — the RTL has no counterpart for a decap — but the book's discipline is that *nothing is deleted by classification convention*. "It's a fill cell, ignore it" is an assumption; "its pins touch only power rails, therefore it cannot affect any logic net" is a theorem, checkable per cell. Each deletion class below carries its licence: the physical cells go by the measured W4 property, the clock tree collapses into the sentence "all flops update together" — a licence that is exactly as good as L2's timing theorem, and conditional on it — and buffer chains collapse by library lemmas (`buf` is the identity; two inverters cancel).

One more object appears here: the **macro**. Not everything on the die is standard cells — larger pre-built blocks are placed as opaque units. In this design there are exactly **five macro instances of three kinds**, and all are the same thing: SRAM arrays (the two data-memory banks, the two instruction-cache data arrays, and the tag array). These are not deleted but become **holes** in the netlist, each closed by a *contract*: the macro's promised behaviour (a synchronous memory with the port discipline its datasheet states), assumed by this layer and discharged elsewhere. What makes these holes unusually honest is that the macros come from an **open generator**: their transistor-level netlists, layouts, and characterisation are all published, so the contract is *checkable-by-effort* — at transistor level, by L0's machinery — rather than a foundry black box that no analysis can enter. And the obligation is **parametric**: one proof per macro kind covers every instance and every depth the generator emits, which is why memory size costs area, never verification.

## Statement

Reduce the hardened netlist to the instances that carry logical content, with **each deletion licensed by one named obligation** rather than by classification convention. The synthesis netlist starts at 51,359 cells (10,416 sequential); place-and-route adds the clock tree, hold buffers, and physical cells, and the exact census of the final layout is a measured deliverable of the flow ([findings](../findings.md)). The classes and their licences:

| class | licence to delete |
|---|---|
| PHYSICAL (decap/tap/fill/diode) | **W4**: pins touch only rails — purely structural, measured per netlist |
| CLOCK (buffers, gates, delay buffers) | cleanliness ([L2/05](../L2-timing/05-clock.md)) + timing closure (M5) ⟹ collapse to the global tick; the clock-gate cells additionally carry L4/02's primitive contract |
| BUF/INV | `buf = id`, inverter pairs cancel, polarity folds into the consumer's function — library lemmas only |
| **LOGIC + SEQ** | **kept** — this is `Mealy(N)` |
| SRAM macros (5 instances, 3 kinds) | **not deleted: holes**, closed by parametric contracts |

Two remarks on the big rows. The physical deletion is the largest single simplification in the project and rests entirely on W4's one property. The clock deletion is the bridge theorem's payoff made concrete: the entire tree — including every delay buffer that exists purely to shape the arrival function — vanishes into the sentence "all flops update together," *conditional on* L2's hypotheses; the deletion is exactly as sound as timing closure is. One genuinely new entry versus a flat design: this netlist's clock tree contains **clock gates** (the ICG cells L4/02 carved out as primitives), so the collapse must carry the gating condition — "all flops *whose gate is enabled* update together" — which is the gated-clock soundness obligation L2 owns.

## The macro contracts

Per kind, the contract states: a synchronous memory of the given geometry — one read-write port (the second, read-only port of the generator's interface is tied off and its outputs unused, a fact W-checks must see rather than assume), byte write masks where present, one-cycle read latency, disabled-read data unconstrained (matching L4/03's X idiom). Three kinds, three contracts, five instances covered. The discharge routes, in increasing ambition: assume with the published characterisation as evidence (X4-class, the starting point); simulate the published transistor netlist against the contract (the generator's own regression, replayed); prove at L0's level from the published layout — open-collateral analogues of the standard-cell obligations, amortised exactly like them.

## What remains

`|State| = 2^10416` at the synthesis netlist alone. That number settles methodology once and for all: **refinement plus induction with a supplied invariant; never reachability, never model checking.** Every plan that begins "enumerate the reachable states" is dead on arrival, which is why L5's invariant is the project's irreducible content.

## Obligations

1. State each deletion as a theorem over [00](00-netlist-object.md)'s semantics: `Mealy(N) ≃ Mealy(N ∖ PHYSICAL)` given W4; the clock collapse given L2 (with the gating condition); buffer collapse given the library lemmas.
2. The three macro contracts, stated; the tied-off second ports verified structurally; the discharge route per kind decided and recorded in the ledger.
3. The BUF/INV collapse must respect [03](03-register-correspondence.md)'s ρ — inverter absorption flips polarity, and the register mapping must record per-bit polarity or the CEC will chase phantom mismatches.
4. The final-layout census, measured and pinned when the flow closes.

## Effort

Weeks for the deletion theorems; the macro contracts are days to state, with their deeper discharge routes priced as optional depth.
