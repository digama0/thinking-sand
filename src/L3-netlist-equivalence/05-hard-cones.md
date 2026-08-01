# L3/05 — Hard cones and the transformation contingency table

## Background

Equivalence checking has one famous nemesis: the multiplier. For most logic, the SAT-based machinery of [04](04-equivalence-certificates.md) is robust, but comparing two structurally different multiplier implementations — say, a naive shift-and-add against a **Booth–Wallace array** (the standard fast architecture: recode the multiplier digits to halve the partial products, then sum them through a tree of carry-save adders) — is provably brutal: the XOR-rich structure of binary arithmetic is exactly what the resolution proof system underlying SAT solvers handles exponentially badly, so the miter that "should" be easy runs forever. The field's dedicated answer is **algebraic** rather than Boolean: model each gate as a polynomial equation and verify, by systematic polynomial reduction (computer algebra, not SAT), that the circuit's output polynomial equals `a·b`; the **PAC** format packages such reductions as certificates a small checker can replay, SAT's LRAT story transplanted to polynomial arithmetic.

This chapter's actual claim is that the famous problem does not arise here — for a structural reason worth spelling out. The wall is triggered by comparing *structurally alien endpoints with no shared derivation*. But the shipped netlist's arithmetic was not conjured from nothing: Yosys elaborates the RTL's `+` into a **width-generic template** — a recursive circuit definition parameterised by bit-width, the "circuit generator" of this project's earliest design discussions — and ABC then only massages that structure through small local rewrites, each logged in [04](04-equivalence-certificates.md)'s trail. So the proof splits into one induction over the template ("for every width n, the template computes addition" — a textbook induction on the carry recurrence, proved once for all instances) plus the per-rewrite trail checks, and no alien-endpoint comparison ever happens. The PAC machinery stays shelved as a fallback.

The chapter's second half guards a different flank: synthesis transformations that would break the register correspondence ρ wholesale. **Retiming** is the canonical one — moving flops across combinational logic to balance delays, perfectly sound and perfectly destructive of any flop-to-register mapping. Others (re-encoding an FSM's states, merging equal registers, inserting **scan chains** — the test-mode circuitry that threads all flops into a shiftable chain for factory testing) each break a different assumption the equivalence proof rests on. This flow has all of them switched off; the table's job is to convert "switched off" from a configuration hope into a *checked* property of the reproduced build, with a named certificate ready should any of them ever appear.

## Statement

Two residual categories where [04](04-equivalence-certificates.md)'s architecture needs reinforcement: cones where SAT structurally blows up (arithmetic), and synthesis transformations that break register boundaries (absent from this flow, but each needs a named certificate so their absence is a *verified configuration*, not luck).

## Arithmetic: generic theorems, not SAT

The plan for arithmetic cones is **width-generic structural proof**, with per-instance checking confined to the local peepholes on top. The shipped cone descends from the RTL operator with full structural continuity:

```
RTL +/*  —elaborate→  $add/$mul  —techmap→  template structure  —ABC→  shipped cone
                                  └─ width-GENERIC theorem ─┘    └─ 04's local trail ─┘
```

The middle step is Yosys's `techmap.v` / `alumacc` instantiating a **width-generic template** — a recursive structure over `n`. `∀n. ⟦template_add(n)⟧ = bvadd_n` is a textbook induction on the carry recurrence, proved **once**, covering every instance at every width; likewise the other `$alu`/`$macc` templates. We do not own the generator, but the generator is small, fixed, pinned Verilog — the generic-generator proof from the project's original design discussions, in validation form. Identifying *which* templates the pinned Yosys uses is a deliverable of [03](03-register-correspondence.md)'s reproduction. The final step is ABC's cut-local rewrites — [04](04-equivalence-certificates.md)'s trail; each check is a 4-input peephole, never a multiplier.

**The "multiplier wall" is not intrinsic to arithmetic — it is intrinsic to endpoint-vs-endpoint comparison of structurally alien implementations** (bit-blasted `*` against a derivation-free Booth–Wallace array: exponential resolution, sweeping starves). With template theorem + trail, that comparison never occurs. **PAC** ([Kaufmann & Biere](../bibliography.md#kaufmann-biere-2019)) — polynomial-calculus certificates with a small verified checker — is therefore the *fallback*, earning its place only on trail loss or on a structurally alien vendor block with no derivation history; this flow has neither.

The PCPI case factors completely: picorv32's multiply/divide (optional — whether the shipped configuration instantiates them is L4's parameterisation record; check before budgeting anything) are **iterative**, so correctness splits into an RTL-level loop invariant (`acc = a · b_low` — standard, L4/L5's world) plus a step-function cone that is an *adder*: generic theorem + trail. The scary version of this problem belongs to cores with single-cycle combinational multipliers, not to this one.

## The contingency table: boundary-breaking transformations

The flow's configuration avoids every transformation that destroys register correspondence (Findings: retiming off, `SYNTH_BUFFERING 0`, no sequential optimisation flags). Under unbounded proof capacity none of them are *forbidden* — each admits a certificate — and the table's job is to make "we don't need this machinery" a checked property of the reproduced flow rather than an assumption:

| transformation | breaks | certificate if ever needed |
|---|---|---|
| retiming | register boundaries wholesale | integer node-labelling; check the linear constraints per edge |
| FSM re-encoding | state encoding | the state bijection, checked on the transition relation |
| sequential don't-care opt | equivalence off reachable states | care-set + an unreachability invariant (IC3-shaped) |
| clock gating | unconditional flop update | enable equivalence + unobservability-when-gated |
| register merging | ρ's bijectivity | the merge witness: proof the merged flops were equal |
| scan insertion | adds a mode | conditional refinement under `scan_en = 0` |

Each row is a known technique with literature behind it; none is exploratory. The point of writing them down is asymmetric risk: discovering mid-proof that the flow *did* apply one of these without a witness would invalidate ρ silently — so [03](03-register-correspondence.md)'s instrumented reproduction should also **assert the absence** of each row (grep the flow's pass list), converting the table from contingency to certificate-of-absence.

## Obligations

1. **Identify and generically prove the pinned Yosys arithmetic templates** (`techmap.v`, `alumacc`) — one induction per template, the load-bearing item of this file.
2. Determine the shipped PCPI configuration (with L4); if present, state the iterative loop invariant and check the step cone reduces to the adder template.
3. Emit the certificate-of-absence for the six rows from the reproduced flow's logs.
4. Import a PAC checker (Pacheck-class) rather than building one — same policy as LRAT — and keep it shelved unless the trail is lost.

## Effort

If the PCPI check comes back "absent": days — this file reduces to the certificate-of-absence. If present: weeks, dominated by wiring the PAC checker to [00](00-netlist-object.md)'s cone extraction.
