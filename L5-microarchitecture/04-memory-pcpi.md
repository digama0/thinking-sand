# L5/04 — The memory interface and PCPI

## Statement

The core's two ports into the outside world — the bus and the coprocessor interface — as assume-guarantee pairs: what the core *guarantees* about its requests (proved here), what it *assumes* about responses (L7's contract), and the internal consistency obligation between picorv32's two views of one transaction.

## The bus: guarantee half

The core's obligations, provable as invariant clauses ([02](02-invariant.md) clause 4):

```
G1  mem_valid, once asserted, holds — with addr/wdata/wstrb stable — until mem_ready
G2  requests are well-formed: wstrb ∈ legal byte-lane patterns; mem_instr tags fetches
G3  no new request before the previous handshake completes
```

The assume half — responses eventually arrive (with L7's bound `B`), data valid at `ready`, flash addresses return `F`'s contents — is consumed by [01](01-refinement.md)'s measure and [03](03-instruction-obligations.md)'s load/store lemmas, never re-proved here. This split is what keeps the cache-less memory system a *function of the contract*: the entire arch-class topic "memory hierarchy" reduces, for this core, to one handshake discipline plus one latency bound.

## The look-ahead interface: one transaction, two views

picorv32 exposes the same access twice: the registered interface (`mem_*`) and a combinational **look-ahead** (`mem_la_*`) that presents address/write-data a cycle early so tightly-coupled memories can skip a wait state. Internal obligation:

```
LA  the la_* signals are a functional preview: whenever a registered request
    appears at cycle n, la announced exactly it at n−1 (and la never lies)
```

Which view the Caravel SoC consumes is a checkable fact of the RTL (extract, don't assume); the refinement must cover the consumed one, and `LA` makes covering either sufficient. This is a miniature of L2/06's exported-guarantee discipline: the core publishes *two* timing shapes of one contract, and the proof must keep them coherent rather than pick one silently.

## PCPI: the coprocessor protocol

The port (`pcpi_valid/insn/rs1/rs2 → pcpi_wr/rd/wait/ready`) is a second assume-guarantee pair: the core guarantees a decoded mul/div instruction is presented stably until `ready`; the coprocessor guarantees a response, with `pcpi_wait` licensing long operations (feeding the measure the same way `B` does). The shipped configuration decides whether any coprocessor exists at all (`ENABLE_MUL/DIV`, default 0 — L4's record gates this file's second half).

If present: the units are **iterative** — and the proof factors exactly as [L3/05](../L3-netlist-equivalence/05-hard-cones.md) forecast: an RTL-level loop invariant (`acc = a · b_low`, or the shift-subtract division invariant with its remainder bound) plus per-cycle step cones that are adders — machinery the plan owns already. The divider adds the one wrinkle: a data-dependent iteration count, absorbed by the measure's lexicographic slot.

**Trap subtlety**: with `ENABLE_PCPI` variants, an instruction *nobody claims* (no internal unit, no coprocessor `ready`) must resolve to the illegal-instruction trap after the timeout — a liveness-flavoured clause of the invariant that the decode sweep ([03](03-instruction-obligations.md)) must coordinate with, and historically the kind of corner where cores hide bugs.

## The counterfactual, priced

What this file would contain for a real memory hierarchy: cache-line state in the invariant, a store buffer as a pending-write delta in every load lemma, miss-status registers, and the assume half exploding from one latency bound into an ordering model. [00](00-microarchitecture.md)'s absence table prices it; this file is the demonstration that the baseline column is real — the whole memory system here is ~three guarantee clauses, one preview lemma, and a bound.

## Obligations

1. G1–G3 and `LA` as invariant clauses; check them first by simulation against the design's own testbench (cheap oracle, shared with L4/04's harness).
2. Extract which interface the SoC consumes; record it beside the configuration.
3. If PCPI is live: the two loop invariants and the nobody-claims trap clause.

## Effort

Weeks; the protocol clauses are IC3-shaped and the loop invariants are textbook. The value is in the *statement discipline* — every later surprise about "what does the bus promise" lands here or in L7, never diffusely.
