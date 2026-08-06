# L4/02 — Combinational blocks: completeness and acyclicity

## Background

Combinational logic — the half of RTL that computes rather than remembers — is only *combinational* if two conditions hold, and Verilog enforces neither. This chapter is about checking them, and the failure modes are worth seeing concretely because both are classic ways real designs go wrong.

The first condition is **completeness**. An `always @*` block is meant to describe a pure function: for any inputs, compute the outputs. But consider a block that assigns `out` inside `if (sel) out = a;` and forgets the `else`. When `sel` is low, the block assigns nothing — and Verilog's semantics says `out` then *keeps its previous value*. Keeping a previous value is memory: the "combinational" block now describes a storage element, and synthesis tools dutifully build one — a **latch** (a level-sensitive storage element, transparent while its enable is high, as opposed to the edge-triggered flip-flops of clocked logic). This "latch inference" is silent, legal, and changes the circuit's state space: a state element exists in the netlist that the RTL's author never intended, no reset touches, and no proof about the intended design accounts for. The fix is a per-block check that *every control path assigns every output* — mechanical, and worth its weight in gold.

The second condition is **acyclicity**. Combinational blocks read each other's outputs, and if the read-dependency graph contains a cycle — block A computes x from y while block B computes y from x — there is no well-defined order to evaluate them in, and "evaluate all combinational logic" stops being a definition. (In physical hardware the same cycle is a feedback loop that may oscillate or settle unpredictably; the netlist-level version of this check is L3's W3.) The check is a standard graph computation: build the dependency graph, find its **strongly connected components** (maximal sets of nodes mutually reachable from each other — the canonical algorithm is Tarjan's, linear time), and demand every component be a single node. The one wrinkle at RTL level is *apparent* cycles that never realise because the two directions occur on disjoint control paths — where the honest options are a conservative syntactic rejection or a finer per-path analysis, and conservatism wins unless it actually fails.

## Statement

The two well-formedness conditions on the combinational sublanguage, without which [00](00-elaborated-object.md)'s step function is not defined. These are W1–W4's analogues one level up, and one of them is the single most consequential check in the layer.

## Completeness: one level-sensitive block, by design

An `always @*` block that fails to assign an output on some control path makes that output *hold its previous value* on that path — the language silently infers a **latch**, and the block is no longer combinational. The formal condition:

```
∀ block B, ∀ output v of B, ∀ control path π through B:   π assigns v
```

The emitted design makes this almost a non-event: the compiler expresses combinational logic as `assign` expressions, so the design cone contains exactly **one** `always @*` block — and it is a latch *on purpose*. `EICG_wrapper`, the integrated-clock-gate model, latches its enable while the clock is low (`if (!in) en_latched = en || test_en`) and gates the clock with the latched enable — the textbook glitch-free clock gate, mapped to a dedicated clock-gate library cell in hardening. The right treatment is not to "fix" the incomplete block but to remove it from the combinational sublanguage entirely: the wrapper is a **primitive** with its own contract (enable sampled while the clock is low; the gated clock equals `clk ∧ en_latched`), consumed by L2's clock analysis. The completeness check then quantifies over the remaining blocks — expected to pass vacuously — and its standing job is to catch any *unintended* latch a future generator bump might introduce, the failure that *changes the circuit*: a phantom state element appears, ρ (L3/03) has no RTL counterpart for it, and the refinement is false, not merely harder.

## Acyclicity: the RTL-level W3

Combinational blocks and `assign`s read each other's outputs; the read-depends-on graph must be acyclic for the fixpoint-free valuation to exist. Verilog permits combinational loops (the language would give simulation nontermination or oscillation; hardware would give L3/W3 violations). The check is the same SCC computation as W3, over RTL signal dependencies instead of nets — to be re-run over the emitted cone by the layer's checker (yosys's `scc` pass), with zero SCCs the expected verdict for compiler-emitted code and any hit a generator finding.

The same elaboration answers a third question for free — wires that are *read but never driven*, which are X sources. Most such reports are artifacts of reading a module whose drivers live in an absent macro (here, the SRAM macros), so the discriminator is whether the unit under check is a **closed hierarchy**; the sweep must therefore run with the macro behavioural models in place, and any genuinely undriven wire is a finding whose harmlessness must be established, never assumed.

One subtlety absent at netlist level: **apparent** cycles through a block that never realise (block A reads x, writes y; block B reads y, writes x; but on disjoint control paths). The netlist after synthesis resolves this through mux structure; at RTL the honest options are the conservative syntactic check (reject apparent cycles — likely sufficient here) or a per-path refinement. Take the conservative check unless it fails.

## The blocking-assignment residue

There is none in the design cone: the emitted clocked blocks are uniformly non-blocking (the census's four blocking sites are DPI harness collateral outside the cone). [00](00-elaborated-object.md)'s two-phase semantics therefore applies without a normal-form rewrite — one whole class of order-dependence obligations deleted by the compiler's discipline.

## Obligations

1. The completeness check over the cone's blocks, as a front-end hard failure (shared with L3's naive-netlist well-definedness), with the clock-gate wrapper carved out as a primitive.
2. The RTL-level SCC check, conservative version.
3. The clock-gate primitive contract, stated once and exported to L2.

## Effort

Days. Small, sharp, and everything downstream assumes it silently — which is precisely why it gets its own file.
