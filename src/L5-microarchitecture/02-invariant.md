# L5/02 — The invariant

## Background

The simulation cell of [01](01-refinement.md) is stated "from any state satisfying `I`" — and that qualifier is not a convenience, it is load-bearing. From a truly arbitrary state the cell is false: a state where the Execute stage's payload says "branch" while its control bits say "store" will step to something no ISA transition explains. Such states can never actually *arise* — but "can never arise" is a claim about all reachable states, and the reachable set of a machine with thousands of flip-flops is beyond any computation. The escape is one of the oldest ideas in program verification, due in essence to Floyd and Hoare: don't compute the reachable set — *describe a superset of it that maintains itself*. An **inductive invariant** is a predicate `I` such that (a) all initial states satisfy it, and (b) any single step from a state satisfying it lands in a state satisfying it. Induction then gives reachable ⊆ `I` for free, and the simulation cell only ever needs to be proved from `I`-states.

The catch — and the reason this chapter is flagged as the irreducible heart of the project — is that `I` must be *invented*, and the invention is forced to encode genuine understanding of the design. The property you want is almost never inductive by itself: "the retired state matches the ISA" says nothing about a half-finished shift or a mid-refill cache line, so a step from such a state cannot be shown to preserve it. To close the induction you must *strengthen* the invariant — add clauses describing every piece of in-flight machinery precisely enough that each clause's preservation follows from the others. Every stage register the generator emitted, every interlock corner, every implicit assumption in the RTL must be named in a clause. That is why proof effort tracks what this book calls *invariant entropy* — the number of independent design decisions `I` must describe — rather than gate count or spec size.

Invention is not entirely unaided, though, and calibrating the aid is this chapter's practical plan. **Model checkers** are tools that try to prove properties of finite-state systems automatically; the classical kind explores states exhaustively (dead on arrival here), but the modern kind — **IC3** is the standard algorithm name — works by *guessing and repairing invariant clauses*: it accumulates small clauses, checks inductiveness with a SAT solver, and refines on failures. On the shallow, structural parts of an invariant (pipeline control sanity, handshake discipline) such engines routinely succeed unaided; on clauses expressing *what a stage payload means*, they mostly fail — that content is semantic, and no amount of clause search recovers it. The economics are favourable either way, because an inductive invariant is a **certificate**: whatever untrusted engine produced it, checking it means checking three entailments, each a SAT query with a machine-checkable proof. Let the engines mine the tedium, pay trust only at the checker, and measure where the boundary actually falls — that measurement, not any estimate, determines this layer's true cost.

## Statement

Invent `I` — the irreducible content of the whole project, the one artifact no tool, decision procedure, or amount of compute produces. Everything else in the stack is either mechanical, certified, or measured; this is the part that is *thought*.

## Invariant entropy, the governing quantity

Proof work is proportional to neither spec size nor gate count but to **invariant entropy** — the number of independent design decisions `I` must name. The operational test: a decision is free if the proof is generic over it or its consequence is recoverable by running the machine; expensive if `I` must describe it. Free here: datapath width, adder topology, decoder encoding. Expensive, and present: the pipeline's occupancy discipline, the interlock rule, the flush protocol, the two cache lines. Expensive and *absent* — forwarding networks, speculative state, miss queues, TLBs ([00](00-microarchitecture.md)'s table) — is what keeps the total moderate: the machine's entropy concentrates in one in-order pipe with the simplest possible hazard rule.

## The clause sketch

What `I` must actually say, per the anatomy:

1. **Pipeline control sanity**: the stage valid/stall/flush arbitration bits are mutually coherent (no stage simultaneously firing and flushed; stalls propagate upstream contiguously).
2. **Per-stage payload coherence**: each stage's control bundle equals the decode of the instruction it travels with — the generated decoder's output, replayed. Wide, shallow, per stage.
3. **In-flight semantics, per station**: the [`LightShifter`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/ShiftPlugins.scala)'s accumulator holds the partially-shifted value with its counter consistent; a mid-flight [`DBusSimple`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/DBusSimplePlugin.scala) transaction's address/data registers hold what the retiring instruction requires; the fetch front end's pc chain is consistent with the committed pc plus in-flight redirects.
4. **Interlock correctness**: no instruction advances past Decode while an in-flight writer targets one of its source registers; the write-back buffer's pending write is reflected in hazard detection.
5. **Flush correctness**: instructions younger than a taken redirect never reach WriteBack; the redirect target is the one the retiring step computed.
6. **I-cache agreement**: each of the two valid lines equals backing memory at its tag — modulo the `fence.i` window, whose obligation is exactly that software cannot observe the staleness.
7. **Wishbone transaction coherence**: `CYC/STB` discipline, single outstanding dBus beat, iBus burst-refill bookkeeping ([04](04-buses-debug.md)).
8. **CSR coherence**: `mstatus.MIE`/`mie`/`mip` consistent with the spec state; the external-interrupt array's mask/pending pair consistent with its CSRs ([05](05-interrupts.md)).
9. **α-well-definedness**: at retirement boundaries, the architectural readout is total.

Clauses 1, 4, and 7 are exactly the *local control invariants* IC3-class engines find unaided; 2 is wide but mechanical; 3, 5, 6 carry the semantic content the human supplies; the glue — that the clauses jointly imply the retirement step matches the ISA — is human work.

## The automation calibration

An inductive invariant is a **certificate**: `init ⊆ I`, `I ∧ T ⊆ I'`, `I ⊆ P` — three queries, each LRAT-checkable. So untrusted engines may *invent* clauses and we pay only for checking. The plan: build the invariant-checking path first, throw IC3 at clauses 1/4/7 phrased as safety properties, and measure the hit rate before hand-authoring anything. Expect the engines to clear the structural majority and die on clauses 3/5/6 — but *measure*, because the split determines the layer's real cost.

The state space forbids the alternative outright: reachability and model checking over the full machine are dead on arrival; refinement plus induction is the only game (L3/02 said the same from below).

## Structure of the work

The pipe seams the authoring naturally: clause families attach to stages and to plugins ([00](00-microarchitecture.md)'s tour is the index), so the invariant parallelises across stations in a way a monolithic state machine would not. The per-instruction quantification lives in [03](03-instruction-obligations.md); this file owns the machine-wide skeleton those obligations plug into.

## Obligations

1. Phrase the clause sketch as machine-checkable predicates over `⟦RTL⟧`'s state.
2. The IC3 calibration run; record the found/failed split.
3. The glue lemma: `I` + retirement transition ⟹ the ISA step (with [01](01-refinement.md)).

## Effort

The heart of the layer's estimate — yet the *volume* is small: the genuinely irreducible content is plausibly a few hundred lines of clauses plus the glue lemma. The years are the surrounding machinery (symbolic simulation, bitvector automation, the stuttering framework), not the thinking.
