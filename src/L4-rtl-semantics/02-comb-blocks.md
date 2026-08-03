# L4/02 — Combinational blocks: completeness and acyclicity

## Background

Combinational logic — the half of RTL that computes rather than remembers — is only *combinational* if two conditions hold, and Verilog enforces neither. This chapter is about checking them, and the failure modes are worth seeing concretely because both are classic ways real designs go wrong.

The first condition is **completeness**. An `always @*` block is meant to describe a pure function: for any inputs, compute the outputs. But consider a block that assigns `out` inside `if (sel) out = a;` and forgets the `else`. When `sel` is low, the block assigns nothing — and Verilog's semantics says `out` then *keeps its previous value*. Keeping a previous value is memory: the "combinational" block now describes a storage element, and synthesis tools dutifully build one — a **latch** (a level-sensitive storage element, transparent while its enable is high, as opposed to the edge-triggered flip-flops of clocked logic). This "latch inference" is silent, legal, and changes the circuit's state space: a state element exists in the netlist that the RTL's author never intended, no reset touches, and no proof about the intended design accounts for. The fix is a per-block check that *every control path assigns every output* — mechanical, and worth its weight in gold.

The second condition is **acyclicity**. Combinational blocks read each other's outputs, and if the read-dependency graph contains a cycle — block A computes x from y while block B computes y from x — there is no well-defined order to evaluate them in, and "evaluate all combinational logic" stops being a definition. (In physical hardware the same cycle is a feedback loop that may oscillate or settle unpredictably; the netlist-level version of this check is L3's W3.) The check is a standard graph computation: build the dependency graph, find its **strongly connected components** (maximal sets of nodes mutually reachable from each other — the canonical algorithm is Tarjan's, linear time), and demand every component be a single node. The one wrinkle at RTL level is *apparent* cycles that never realise because the two directions occur on disjoint control paths — where the honest options are a conservative syntactic rejection or a finer per-path analysis, and conservatism wins unless it actually fails.

## Statement

The two well-formedness conditions on the combinational sublanguage, without which [00](00-elaborated-object.md)'s step function is not defined. These are W1–W4's analogues one level up, and one of them is the single most consequential check in the layer.

## Completeness: the 15 `always @*` blocks

An `always @*` block that fails to assign an output on some control path makes that output *hold its previous value* on that path — Verilog silently infers a **latch**, and the block is no longer combinational. The formal condition:

```
∀ block B, ∀ output v of B, ∀ control path π through B:   π assigns v
```

Decidable per block by path enumeration or, robustly, by checking the generated logic has no latch — and this is **checked** ([`rtlcheck.py`](../tools/rtlcheck.py)): yosys elaborates the shipped core, the SoC, housekeeping and the GPIO control block, and **not one `$dlatch` appears in any of them**. Every combinational block assigns its outputs on every path. This is the check that *changes the circuit* if missed — a phantom state element appears, ρ (L3/03) has no RTL counterpart for it, and the refinement is false, not merely harder. It is also load-bearing for L3: the "naive netlist" oracle is well-defined only conditional on these 15 checks — the obligation is genuinely shared between layers.

The standard idiom (default-assign at block top, then override) discharges most blocks syntactically; the residue needs per-path inspection. Fifteen blocks is an afternoon.

## Acyclicity: the RTL-level W3

Combinational blocks and `assign`s read each other's outputs; the read-depends-on graph must be acyclic for the fixpoint-free valuation to exist. Verilog permits combinational loops (the language would give simulation nontermination or oscillation; hardware would give L3/W3 violations). The check is the same SCC computation as W3, over RTL signal dependencies instead of nets — and it is now **checked** rather than expected ([`rtlcheck.py`](../tools/rtlcheck.py)): yosys's `scc` pass reports **zero** strongly-connected components in all four units. The netlist-level W3 found only the PLL, which is not RTL; the RTL level is clean outright.

The same elaboration answers a third question for free — wires that are *read but never driven*, which are X sources. Most such reports are artifacts of reading a module whose drivers live in an absent macro, so the discriminator is whether the unit is a **closed hierarchy**. Exactly one of the four is: the shipped core, which instantiates nothing it does not also define. It contains **two undriven wires**, both fed as inputs to the instruction cache — `io_cpu_fetch_isRemoved`, which the cache never reads, and `io_cpu_fetch_mmuRsp_bypassTranslation`, which it latches into a register nothing reads. Both are X-inert, so nothing downstream changes; but they are real dangling signals in shipped RTL, and the reason they are harmless is a fact that had to be established rather than assumed.

One subtlety absent at netlist level: **apparent** cycles through a block that never realise (block A reads x, writes y; block B reads y, writes x; but on disjoint control paths). The netlist after synthesis resolves this through mux structure; at RTL the honest options are the conservative syntactic check (reject apparent cycles — likely sufficient here) or a per-path refinement. Take the conservative check unless it fails.

## The blocking-assignment residue

The 2 clocked blocks using `=` are not combinational-block problems, but they are resolved with the same machinery: within a block, blocking assignments impose sequential evaluation, so either the semantics models intra-block ordering (a small operational layer over the two blocks only) or the blocks are **rewritten to non-blocking normal form and proved equivalent once** — a two-site, one-time obligation. The rewrite option keeps [00](00-elaborated-object.md)'s two-phase semantics uniform and is the recommendation.

## Obligations

1. The 15 completeness checks, as front-end hard failures (shared with L3's naive-netlist well-definedness).
2. The RTL-level SCC check, conservative version.
3. The 2-block normal-form rewrite with its equivalence proof.

## Effort

Days. Small, sharp, and everything downstream assumes it silently — which is precisely why it gets its own file.
