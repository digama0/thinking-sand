# L3/02 — The licensed deletions

## Background

A newcomer's mental image of a chip — gates computing things — describes about 8% of this one. The instance census tells the real story: of 275,608 placed cells, 235,566 compute nothing at all. They are **physical cells**, present for electrical and manufacturing reasons: **decaps** (decoupling capacitors, smoothing the power supply against demand spikes), **tap cells** (connecting the transistors' silicon wells to the rails to prevent latch-up), **fill cells** (spacers keeping the fabricated layer densities uniform), and antenna **diodes** (protecting gates from charge build-up during fabrication). Another 15,306 cells are the **clock tree**: the clock signal cannot physically drive thousands of flops from one wire, so it is distributed through a tree of buffers — carefully balanced so every flop sees its edge at nearly the same moment, and including thousands of pure *delay* buffers inserted only to fix timing. Add ordinary signal buffers and inverter pairs, and the logic that L4's semantics actually describes is a small minority of what was fabricated.

For the equivalence proof, all of this must go — the RTL has no counterpart for a decap — but the book's discipline is that *nothing is deleted by classification convention*. "It's a fill cell, ignore it" is an assumption; "its pins touch only power rails, therefore it cannot affect any logic net" is a theorem, checkable per cell. Each deletion class below carries its licence: the physical cells go by the measured W4 property, the clock tree collapses into the sentence "all flops update together" — a licence that is exactly as good as L2's timing theorem, and conditional on it — and buffer chains collapse by library lemmas (`buf` is the identity; two inverters cancel).

One more object appears here: the **macro**. Not everything on the die is standard cells — larger pre-built blocks (the RAM, the analog PLL, the housekeeping controller) are placed as opaque units, 97 of them. These are not deleted but become **holes** in the netlist: for each, either recurse (it has its own gate-level netlist inside — verify it with the same machinery) or contract (it is analog or foundry-opaque — write down its promised behaviour as an assumption in the ledger). The happy surprise of this design is that its RAM is not a foundry black box but **DFFRAM** — a memory *compiled out of ordinary standard cells*, flops and multiplexers — so the largest would-be assumption is instead a recursion target, provable like everything else.

## Statement

Reduce 275,608 instances to the ~21,600 that carry logical content, with **each deletion licensed by one named obligation** rather than by classification convention. The reductions are where most of the netlist goes; the licences are where the honesty lives.

| class | count | share | licence to delete |
|---|---|---|---|
| PHYSICAL (decap/tap/fill/diode) | 235,566 | 85.5% | **W4**: pins touch only rails — purely structural, measured 0 violations |
| CLOCK | 15,306 | 5.6% | cleanliness ([L2/05](../L2-timing/05-clock.md)) + timing closure (M5) ⟹ collapse to the global tick |
| BUF/INV | 3,109 | 1.1% | `buf = id`, inverter pairs cancel, polarity folds into the consumer's function — library lemmas only |
| **LOGIC + SEQ** | **15,853 + 5,774** | 7.8% | **kept** — this is `Mealy(N)` |
| macros | 97 | — | **not deleted: holes**, see below |

Two remarks on the big rows. The physical deletion is the largest single simplification in the project and rests entirely on W4's one property — which is why [01](01-well-formedness.md) treats that check's self-caught misclassification (`conb_1`) as a feature. The clock deletion is the bridge theorem's payoff made concrete: 15,306 cells — including 9,910 delay buffers that exist purely to shape the arrival function — vanish into the sentence "all flops update together," *conditional on* L2's hypotheses; the deletion is exactly as sound as timing closure is.

## The macros are holes, and one of them can be opened

The 97 macro instances are not deletions but **boundaries**: `RAM128`/`RAM256`, `housekeeping`, `gpio_control_block` ×38, `gpio_defaults_block` ×38, `spare_logic_block` ×4, `mgmt_protect`, `simple_por`, `digital_pll`, `caravel_clocking`, `user_id_programming`. Each needs either recursion (it has its own gate netlist — verify it with the same machinery, once, amortised over instances) or a contract (analog: `simple_por` X4-class, `digital_pll` X5).

The RAM is the important case: **it is not an SRAM macro.** `defines.v` declares `USE_CUSTOM_DFFRAM` — the memory is DFFRAM, a compiled array of standard-cell flops and muxes (2 blocks × 256 words). So the biggest would-be behavioural-model axiom is instead a *recursion target*: its gate netlist exists, W1–W4 apply to it, and its behavioural model ("a memory") becomes a provable per-macro theorem rather than an assumed one. On a design with a foundry SRAM macro this hole cannot be opened; here it can, and should be, because a memory's read-mux tree is exactly the kind of regular structure certificates handle well.

`user_id_programming` is the opposite extreme: a metal-mask ROM — its "netlist" is a constant vector fixed by geometry (L1's business), trivially contract-able.

## What remains

`|State| = 2^5774` at this hierarchy level alone. That number settles methodology once and for all: **refinement plus induction with a supplied invariant; never reachability, never model checking.** Every plan that begins "enumerate the reachable states" is dead on arrival, which is why L5's invariant is the project's irreducible content.

## Obligations

1. State each deletion as a theorem over [00](00-netlist-object.md)'s semantics: `Mealy(N) ≃ Mealy(N ∖ PHYSICAL)` given W4; the clock collapse given L2; buffer collapse given the library lemmas.
2. The macro contract inventory: per macro, *recursion or contract*, decided explicitly. Opening DFFRAM is the high-value instance.
3. The BUF/INV collapse must respect [03](03-register-correspondence.md)'s ρ — inverter absorption flips polarity, and the register mapping must record per-bit polarity or the CEC will chase phantom mismatches.

## Effort

Weeks for the deletion theorems; the DFFRAM recursion is the one substantial piece, and it doubles as the first real test of [04](04-equivalence-certificates.md)'s machinery on a regular structure.
