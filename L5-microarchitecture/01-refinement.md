# L5/01 — The refinement statement

## Statement

`⟦RTL⟧ ⊑ ISA`: a stuttering simulation whose shape is fixed now, even though its invariant is future work —

```
∃ I ⊆ States(⟦RTL⟧)          the invariant                    [02]
∃ α : I → States(ISA)         abstraction, read at commit points
∃ m : I → ℕ                   the measure

init:  reset states ⊆ I   ∧   α maps them into ISA reset states
                              (X ⊑ spec reset nondeterminism — L4/03)
step:  s ∈ I, s →_rtl s'  ⟹  s' ∈ I  ∧
         either  α(s') = α(s)  ∧  m(s') < m(s)        (stutter)
         or      α(s) →_isa α(s')                     (commit)
```

conditional on the **bus contract** (authored in L7, assumed here) and stated over the **shipped configuration** (L4's record).

## Commit points are FSM-defined, and the designer already declared them

For a multicycle FSM the commit point is structural: the transition back into `fetch` (or into the IRQ entry) is where the instruction's effects are complete and architectural state is directly readable — no Burch–Dill flushing needed, because the machine *visits* its own abstraction function every few cycles. α reads: register file, pc, the q-registers and mask (S3 state), and memory-as-seen-through-the-bus.

The **RVFI ports** ([00](00-microarchitecture.md)) are the source's own commit-point declaration — `rvfi_valid` pulses exactly at retirement, `rvfi_intr` marks IRQ entry. Even if compiled out of the shipped netlist, α should be *defined to agree with RVFI's semantics*, for two reasons: it inherits the designer's intent instead of guessing, and it makes riscv-formal's existing per-instruction BMC results directly comparable evidence.

## The measure

`m` bounds cycles-to-next-commit: a lexicographic sum of (position in the FSM path) + (remaining iterations of the shift/PCPI loops) + (outstanding bus wait). The last summand is why the bus contract must carry a **latency bound** — with an unbounded `mem_ready` the measure does not exist and the refinement silently weakens from "commits happen" to "commits happen if the bus answers." State it conditionally: `m` exists given the contract's bound `B`; the SoC proof (L7/B2) discharges `B` for the actual fabric, with the XIP flash path as the worst case.

## Interrupts enter the *statement*, not just the proof

An IRQ redirects the commit transition: instead of `α(s) →_isa α(s')` by the fetched instruction, the machine takes the IRQ entry step of the `ISA ⊕ IRQ` spec (L6/S3) — save state to q-registers, mask, jump to `PROGADDR_IRQ`. So the simulation diagram's commit case is a *disjunction over the spec's two step kinds*, and preemption points are exactly commit points — an instruction in flight is never abandoned. That claim (no mid-instruction preemption) is itself an invariant clause, and `waitirq`'s stall state is the one place the measure needs the environment: `m` decreases only given eventual IRQ arrival, so `waitirq` is carved out as a *spec-visible* stutter (the ISA ⊕ IRQ spec has an explicit waiting state — L6 must include it).

## What is deliberately not in the statement

No timing (L2 discharged it), no probabilistic terms (conditioning happened at MAIN's †-lines), no bus implementation (contract-abstracted), no netlist (L3 licensed the RTL view). The statement is purely a relation between two transition systems — which is the payoff of the entire tower below it.

## Obligations

1. Write α against the RVFI definition; check it on simulation traces before any proof (cheap oracle).
2. Fix the measure's lexicographic structure and extract the FSM path bounds from [00](00-microarchitecture.md)'s state graph.
3. The conditional-on-`B` formulation, with `B` named as an L7 deliverable.

## Effort

Weeks to state precisely; stating it *first* is the layer's own first experiment, since every downstream choice (invariant clauses, IC3 targets) types against it.
