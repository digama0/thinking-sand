# L3/04 — Equivalence by certificate

## Statement

> Given ρ ([03](03-register-correspondence.md)) and the deletions ([02](02-licensed-deletions.md)): for every register/port boundary pair, the combinational cone in the reduced netlist computes the same function as the corresponding cone in the elaborated RTL — established by **checking certificates**, with exploratory SAT confined to where no certificate exists.

Per-cone equivalence + ρ + matched reset then compose into the bisimulation `Mealy(N) ≈ρ ⟦RTL⟧`.

## Why CEC scales, and why that dictates the architecture

SAT sweeping works by proposing candidate-equivalent *internal* nodes via random simulation and proving each with a small local SAT call, using previously proven equivalences as rewrites. The candidates exist because **both sides are the same design through one tool** — structural similarity is the fuel. Two consequences:

- **An independent reference model is the wrong architecture.** Comparing a hand-written model against a synthesised netlist destroys the internal equivalence points; the miter becomes one enormous SAT problem. (This is quite apart from the register-mapping problem an independent model creates.) The RTL that *generated* the netlist is the right comparand.
- **Register boundaries bound every miter.** With ρ in hand, each proof obligation is one cone — picorv32's are shallow — so even certificate-free fallback SAT stays tractable per cone.

**Unmap rather than map**: substitute each SKY130 cell's verified Boolean function (L0/05) to bring the shipped netlist down to generic gates, instead of technology-mapping the RTL side up. Free — L0 already produced the functions — and it removes tech mapping from the comparison entirely.

## The certificate architecture: instrument ABC's trail

ABC's optimisations are local rewrites drawn from a **finite precomputed library** — the 222 NPN classes of 4-input functions for `rewrite`, plus `refactor`/`balance`/`resub`. Every application is a table lookup plus a structural substitution; the justification already exists as a table entry — **ABC just doesn't write it down.**

The plan, enabled by [03](03-register-correspondence.md)'s reproduction of the flow (we control the run, so we can patch the tool):

1. **Verify the NPN library once, exhaustively** — 222 lemmas over 4-input functions, trivially checkable.
2. **Log the trail**: `(cut, before, after, library-entry)` per rewrite — a modest patch to an open-source tool.
3. **Check the trail**: each step is congruence (substitution at a cut, pointer-level if the representation is a hash-consed AIG (And-Inverter Graph — the two-input-AND-plus-inverter normal form equivalence tools operate on)) plus one library lemma. No search at check time.
4. **Residual cones** — anything the trail doesn't cover (`proc`/`techmap` structural expansion, don't-care-free `resub`) — fall back to per-cone SAT **with LRAT proofs**, checked not trusted.

This is the `K(G₁) = K(G₂)` congruence architecture the project sketched from the start, landing at its cheapest available site: local rewrites, precomputed justifications, open tool. It is the best available answer to *avoid poorly-specified exploratory obligations*.

## The naive netlist: useful oracle, wrong comparand

`read_verilog; hierarchy; proc; memory_map; techmap` — no `opt`, no `abc` — produces a "naive" netlist whose function is fixed by the language and whose *structure* is fixed by Yosys's `techmap.v`, a small readable rule library one could formalise. Caveats: `proc` is not a no-op (`proc_rmdead` prunes unreachable branches), and well-definedness is conditional on L4's 15 `always @*` latch-inference checks — the obligation is shared between layers.

But as a CEC comparand it is the **worst case**: its ripple-carry adders share nothing structurally with ABC's output, so sweeping starves. Its role is differential testing and semantics cross-validation ([L4](../L4-rtl-semantics/README.md)'s CEC cross-check), not the equivalence proof itself. The trail architecture makes this moot: with the trail, the comparand is each intermediate netlist against the next, and structural similarity is maximal at every step.

## Obligations

1. The NPN library verification (one-time, mechanical).
2. The ABC patch and trail format; the trail checker against [00](00-netlist-object.md)'s semantics.
3. The composition theorem: per-cone equivalences + ρ + reset correspondence ⟹ bisimulation.
4. LRAT checking for residual cones — standard machinery, imported not built.

## Effort

The patch and checker: months. The composition theorem: weeks once 00/03 exist. The certificate route's cost scales with the *trail length*, not the design size — which is the point.
