# L4/02 — Combinational blocks: completeness and acyclicity

## Statement

The two well-formedness conditions on the combinational sublanguage, without which [00](00-elaborated-object.md)'s step function is not defined. These are W1–W4's analogues one level up, and one of them is the single most consequential check in the layer.

## Completeness: the 15 `always @*` blocks

An `always @*` block that fails to assign an output on some control path makes that output *hold its previous value* on that path — Verilog silently infers a **latch**, and the block is no longer combinational. The formal condition:

```
∀ block B, ∀ output v of B, ∀ control path π through B:   π assigns v
```

Decidable per block by path enumeration or, robustly, by checking the generated logic has no latch (Yosys warns; the check should be a hard failure in our front end). This is the check that *changes the circuit* if missed — a phantom state element appears, ρ (L3/03) has no RTL counterpart for it, and the refinement is false, not merely harder. It is also load-bearing for L3: the "naive netlist" oracle is well-defined only conditional on these 15 checks — the obligation is genuinely shared between layers.

The standard idiom (default-assign at block top, then override) discharges most blocks syntactically; the residue needs per-path inspection. Fifteen blocks is an afternoon.

## Acyclicity: the RTL-level W3

Combinational blocks and `assign`s read each other's outputs; the read-depends-on graph must be acyclic for the fixpoint-free valuation to exist. Verilog permits combinational loops (the language would give simulation nontermination or oscillation; hardware would give L3/W3 violations). The check is the same SCC computation as W3, over RTL signal dependencies instead of nets — expected clean (the netlist-level W3 found only the PLL, which is not RTL), but "expected" is exactly what this file exists to replace with "checked."

One subtlety absent at netlist level: **apparent** cycles through a block that never realise (block A reads x, writes y; block B reads y, writes x; but on disjoint control paths). The netlist after synthesis resolves this through mux structure; at RTL the honest options are the conservative syntactic check (reject apparent cycles — likely sufficient here) or a per-path refinement. Take the conservative check unless it fails.

## The blocking-assignment residue

The 2 clocked blocks using `=` are not combinational-block problems, but they are resolved with the same machinery: within a block, blocking assignments impose sequential evaluation, so either the semantics models intra-block ordering (a small operational layer over the two blocks only) or the blocks are **rewritten to non-blocking normal form and proved equivalent once** — a two-site, one-time obligation. The rewrite option keeps [00](00-elaborated-object.md)'s two-phase semantics uniform and is the recommendation.

## Obligations

1. The 15 completeness checks, as front-end hard failures (shared with L3's naive-netlist well-definedness).
2. The RTL-level SCC check, conservative version.
3. The 2-block normal-form rewrite with its equivalence proof.

## Effort

Days. Small, sharp, and everything downstream assumes it silently — which is precisely why it gets its own file.
