# L4/00 — The elaborated object

## Statement

Define `⟦·⟧ : Config → RTL → TransitionSystem` — the word-level transition system that is L3's right-hand side and L5's left-hand side. A definition, not a theorem; its correctness notion is adequacy ([04](04-adequacy.md)).

## The semantics, directly — not via the LRM

The Verilog LRM defines an event-driven scheduler with delta cycles and nondeterministic event ordering. We do **not** formalise it. `⟦·⟧` is defined as the *simple synchronous semantics* directly:

```
State  = declared regs (as bitvectors) ∪ memories
Input  = input ports
step   = 1. evaluate all combinational blocks/assigns to a fixpoint-free
            valuation (acyclic — [02](02-comb-blocks.md))
         2. evaluate every non-blocking RHS in the pre-state
         3. commit all non-blocking assignments simultaneously
```

Two-phase non-blocking commit is what makes `always @(posedge)` blocks order-independent among themselves; the acyclic combinational pass is W3's analogue one level up.

**The implicit theorem this definition rides on — scheduler independence:** for programs in [01](01-subset.md)'s subset (non-blocking in clocked blocks, complete and acyclic combinational blocks, no delays/UDPs/triggers), every LRM-conformant scheduling computes exactly this semantics — the event-order nondeterminism is unobservable. This is what "semantically tame" *formally means*, and it is the content that [04](04-adequacy.md)'s cross-checks probe empirically instead of proving: we define the clean semantics, and validate that the tools' LRM interpretations agree with it on this design. Proving scheduler independence for the subset would upgrade the adequacy story from tested to derived — a real (and bounded) formalisation target, but not on the critical path.

The two known deviations from "order doesn't matter" are exactly the flagged sites: the **2 clocked blocks using blocking `=`** (order-dependent *within* the block — either model the intra-block sequencing explicitly or rewrite-and-prove-equivalent) and latch inference ([02](02-comb-blocks.md)).

## Word-level from the start

`wire [31:0]` is one declaration, so `State` is over **bitvectors**: SMT bitvector theory applies directly to L5's proof, arithmetic is `+`/`*` rather than carry chains, and the netlist-side structure of arithmetic is entirely L3/05's business (generic templates + trail). The word/bit boundary is crossed exactly once, at ρ (L3/03), and never inside this layer.

## Configuration is part of the object

picorv32 is heavily parameterised — `ENABLE_MUL`, `ENABLE_DIV`, `ENABLE_IRQ`, `ENABLE_REGS_16_31`, `BARREL_SHIFTER`, `COMPRESSED_ISA`, counters, … — and `⟦·⟧` takes the **shipped** configuration as an argument. Recording it exactly is a deliverable, not bookkeeping: it determines which ISA subset L6 must cover, whether L3/05's PCPI cones exist, and which of the 19 sites are even elaborated. Elaboration (parameter resolution, `generate` unrolling) happens before the semantics and is part of X1-style front-end validation.

## Obligations

1. Write the semantics for the subset (small — the step function above plus expression evaluation over bitvectors).
2. Extract and record the shipped configuration from the management-core build.
3. State scheduler independence precisely, even if its proof is deferred — the statement is the layer's honesty about what the LRM relationship is.

## Effort

Weeks for the definition; the deferred scheduler-independence proof is the only open-ended item and is severable.
