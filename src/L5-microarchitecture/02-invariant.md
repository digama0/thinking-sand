# L5/02 — The invariant

## Statement

Invent `I` — the irreducible content of the whole project, the one artifact no tool, decision procedure, or amount of compute produces. Everything else in the stack is either mechanical, certified, or measured; this is the part that is *thought*.

## Invariant entropy, the governing quantity

Proof work is proportional to neither spec size nor gate count but to **invariant entropy** — the number of independent design decisions `I` must name. The operational test: a decision is free if the proof is generic over it or its consequence is recoverable by running the machine; expensive if `I` must describe it. Free here: datapath width, adder topology, ALU sharing. Expensive elsewhere, absent here: store buffers, in-flight misses, speculative state ([00](00-microarchitecture.md)'s absence table). picorv32's entropy is dominated by one structure — the FSM — which is why the invariant is *monolithic but small*.

## The clause sketch

What `I` must actually say, per the anatomy:

1. **Control sanity**: `cpu_state` is one-hot, and in a state reachable for the latched instruction class (a shift instruction is never in `stmem`, etc.).
2. **Decode coherence**: the ~50 latched `instr_*`/`is_*` flags equal `decode(latched instruction word)` — decode happened once and nothing has drifted. This is the largest clause by width and the shallowest by depth.
3. **Partial-result meaning, per state**: in `ld_rs2`, the rs1 operand register holds `regfile[rs1(insn)]`; in `shift`, the accumulator holds the partially-shifted value with the loop counter consistent; in `ldmem/stmem`, address/wdata/wstrb registers hold what the ISA step requires.
4. **Bus transaction coherence**: `mem_valid ⟹` the FSM is in a memory state and the request registers are stable since assertion (the handshake discipline, [04](04-memory-pcpi.md)).
5. **IRQ state coherence**: mask/pending/q-registers consistent with the S3-spec state; no mid-instruction preemption pending ([05](05-interrupts.md)).
6. **α-well-definedness**: at commit states, the architectural readout is total.

Clauses 1–2 and 4 are exactly the *local control invariants* IC3-class engines find unaided; clause 3 is borderline; the glue — that the clauses jointly imply the commit step matches the ISA — is human work.

## The automation calibration

An inductive invariant is a **certificate**: `init ⊆ I`, `I ∧ T ⊆ I'`, `I ⊆ P` — three queries, each LRAT-checkable. So untrusted engines may *invent* clauses and we pay only for checking. The plan: build the invariant-checking path first, throw IC3 at clauses 1, 2, 4 phrased as safety properties, and measure the hit rate before hand-authoring anything. Expect the engines to clear the tedious majority and die on clause 3's per-state semantic content — but *measure*, because the split determines the layer's real cost.

The state space forbids the alternative outright: 2^(regfile + latches) — reachability and model checking are dead on arrival; refinement plus induction is the only game ([L3/02](../L3-netlist-equivalence/02-licensed-deletions.md) said the same from below).

## Structure of the work

Monolithic is not a defect here: the core is one module, one FSM, everything local — good for *stating* `I` (no cross-module protocol), bad only for parallelising the authoring. The per-instruction quantification lives in [03](03-instruction-obligations.md); this file owns the machine-wide skeleton those obligations plug into.

## Obligations

1. Phrase clauses 1–6 as machine-checkable predicates over `⟦RTL⟧`'s state.
2. The IC3 calibration run; record the found/failed split.
3. The glue lemma: `I` + commit transition ⟹ the ISA ⊕ IRQ step (with [01](01-refinement.md)).

## Effort

The heart of the layer's estimate — yet the *volume* is small: the genuinely irreducible content is plausibly a few hundred lines of clauses plus the glue lemma. The years are the surrounding machinery (symbolic simulation, bitvector automation, the stuttering framework), not the thinking.
