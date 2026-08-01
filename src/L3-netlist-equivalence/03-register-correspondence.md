# L3/03 — The register correspondence ρ (F5)

## Statement

Exhibit `ρ`: a mapping between RTL state elements and netlist flops — a bijection up to `opt_dff`-eliminated constants and resizer cloning (1→many) — such that [04](04-equivalence-certificates.md)'s bisimulation can be cut at register boundaries. **Whether ρ exists is F5, the layer's single load-bearing unknown**, and it is decidable by experiment rather than by argument.

## Why only registers (and ports) need correspondence

The equivalence needs bit-level correspondence at exactly two places: **ports** (preserved by construction — synthesis cannot rename or drop them) and **state elements**. Internal nets need *none* — internal restructuring is precisely what combinational equivalence checking absorbs, and it is where ABC does all its work. So the entire gap between RTL and netlist reduces to one question: do the flops correspond?

The corollary that saves the project from a research problem: **do not recover buses.** Synthesis flattened every word into unrelated single-bit nets named `_1234_`; bit-level→word-level lifting is genuinely hard and entirely unnecessary — the word structure comes from the RTL side of ρ, and the netlist side stays bits forever.

## What ρ must record

- **The bijection**, modulo the two legal deviations: constants (`opt_dff` removes a flop whose input is provably constant — the RTL bit maps to a constant, and the *proof* that it was constant is part of the certificate) and clones (resizer fanout duplication — one RTL bit, several netlist flops, all provably equal).
- **Per-bit polarity** — [02](02-licensed-deletions.md)'s inverter absorption can leave a netlist flop storing the *negation* of its RTL counterpart.
- **Reset correspondence**: the bisimulation is stated from reset-reachable states, so ρ must map RTL initial states to netlist post-reset states — with deliberately-uninitialised bits on both sides refining the spec's reset nondeterminism ([00](00-netlist-object.md)) rather than demanding equality of X.

## What threatens ρ

Yosys's `opt_dff`/`opt_merge` can remove constant-driven flops and merge duplicated ones, and **Yosys emits no SVF-equivalent** — the commercial flow's hint file recording exactly the register transformations, absent here. The flow's configuration is favourable (retiming off — the one transformation that destroys register boundaries wholesale — and `SYNTH_BUFFERING 0`), but favourable is not known.

## The decision procedure: reproduce the synthesis

**Do this before anything else in the project.** Versions are pinned exactly (FINDINGS: OpenLane `05fac72e…`, docker tag, PDK commit). Yosys is single-threaded and essentially deterministic; ABC's seeds are fixed by default. Reproducing the shipped netlist converts archaeology into experiment: instrument the flow to **dump ρ directly** — log every `opt_dff`/`opt_merge` action, emit the name mapping before mangling — and the witness falls out of the run instead of being reverse-engineered from the artifact.

The nondeterminism concentrates in P&R (multithreaded routing, placement seeds, hash order, floating point), which is **function-preserving** — a different DEF is harmless, and one verifies the shipped DEF rather than reproducing it. Synthesis, the stage that would actually hurt, is the deterministic one. Fortunate, and worth stating as the reason this experiment is expected to succeed.

Both outcomes are results: reproduction yields ρ as a logged witness; failure means the shipped netlist's provenance is not fully recorded — a finding about the artifact worth having before investing in anything downstream.

## Obligations

1. Run the reproduction; diff against `gl_caravel_core.v`; extract ρ from instrumentation.
2. Define the ρ format (bijection + constants-with-proofs + clone classes + polarity + reset map) as the interface [04](04-equivalence-certificates.md) consumes.
3. If reproduction fails: fall back to *inference* — name-hint matching plus simulation-based candidate pairing, then per-pair verification. Strictly worse (the witness becomes a search result), but the verification step is the same either way.

## Effort

The experiment: days to weeks of flow wrangling. It is the highest information-per-effort action available in the entire project, which is why the top README lists it first.
