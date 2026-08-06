# L5/01 — The refinement statement

## Background

How do you prove that one machine correctly implements another? The two machines don't even step at the same rate: the ISA executes one instruction per step, while the hardware spreads each instruction across pipeline stages, retiring one per cycle at best and pausing for stalls, cache misses, and flushes — with the in-flight remainder corresponding to no ISA state at all. The technique that bridges this — the central proof technique of the entire book, used here at full strength — is the **simulation proof**, best understood as a picture before formulas. Here it is, for a run in which one instruction retires, the pipe then stalls twice (an interlock, then a cache miss), and a second instruction retires:

```
ISA  ····▶ A ────step────▶ B ······························▶ B ────step────▶ C ▶ ····
           ▲               ▲                                 ▲               ▲
         α │             α │                               α │             α │
RTL  ····▶ s₀ ──cycle───▶ s₁ ──cycle───▶ s₂ ──cycle───▶    s₃ ──cycle───▶  s₄ ▶ ····
           (retire)        (stall)       (miss refill)      (bubble)        (retire)
```

The struts are the **abstraction function** α, which reads the architectural state (register file, program counter, CSRs) out of a hardware state at the **retirement boundaries** — the cycles where the WriteBack stage completes an instruction and the machine's committed state is architecturally clean. Between retirements the hardware is mid-flight everywhere at once; those cycles are **stutters**, and they are characterised not by α but by the **invariant** `I` — the description of the reachable in-flight states, [02](02-invariant.md)'s subject and the layer's real work — together with the **measure** `m`, a counter that strictly decreases across every stutter and thereby forces the next retirement within bounded time. (Without it, a machine could stall forever, implementing nothing while never being caught.) The trailing arrows continue the ladder in both directions. The proof obligation is *local*, one cell at a time; induction tiles the cells into the global statement: every run of the hardware, viewed through α, is a legal run of the spec. A global claim about infinite behaviours is bought with finite, checkable, per-cell facts — that trade is the whole magic of the method.

## Statement

`⟦RTL⟧ ⊑ ISA`: a stuttering simulation whose shape is fixed now, even though its invariant is future work —

```
∃ I ⊆ States(⟦RTL⟧)          the invariant                    [02]
∃ α : I → States(ISA)         abstraction, read at retirement
∃ m : I → ℕ                   the measure

init:  reset states ⊆ I   ∧   α maps them into ISA reset states
                              (X ⊑ spec reset nondeterminism — L4/03)
step:  s ∈ I, s →_rtl s'  ⟹  s' ∈ I  ∧
         either  α(s') = α(s)  ∧  m(s') < m(s)        (stutter)
         or      α(s) →_isa α(s')                     (retire / trap / interrupt)
```

conditional on the **bus contract** (authored in L7, assumed here), on **debug-inactive** ([04](04-buses-debug.md)), and stated over the [configuration record](../tools/config-record.py) (L4).

## Commit points, α's domain, and the trace port

Retirement is where the pipeline is architecturally honest: when [WriteBack](00-microarchitecture.md) completes an instruction, the register file, CSRs, and committed pc are exactly what the ISA says after that instruction. α reads them there. Flushed instructions never reach WriteBack, so a flush is — automatically — a stretch of stutters, and "flushed work has no architectural effect" lands in the invariant rather than in α. (For pipelines generally, constructing α is the famous hard part — [Burch & Dill](../bibliography.md#burch-dill-1994)'s *flushing* builds it by symbolically draining the pipe; Manolios's WEB refinement is the standard alternative when flushing fails. An in-order pipe with in-order retirement sits at the tractable end of that spectrum: draining is well-defined and short, with the bypass network priced in the invariant rather than in α.)

**α's domain is a choice, and the statement above made it.** The lean formulation leaves α *partial* — defined at retirement boundaries only, with mid-flight states described by `I` plus "within `m` cycles of the last retirement" and no architectural readout of their own; this is the form a retirement interface matches ([RVFI](https://github.com/YosysHQ/riscv-formal)'s discipline), and the one to author. The statement's total `α : I → States(ISA)` is its completion along the run — α of a mid-flight state is α of its last retirement — well-defined *as a function* only when nothing architectural is destroyed mid-instruction; on a machine where that fails, the completion exists only as a simulation **relation** `R ⊆ States(⟦RTL⟧) × States(ISA)`, and the per-cycle cell reads R-preservation instead of α-equality. The two forms prove the same refinement; which is available for this pipe (in-order retirement, writes only at WriteBack) is settled when α is actually written — the first experiment below.

**The trace port is the designer-declared anchor.** The core exposes retirement events (valid, instruction word, pc, exception status) on its own instruction-trace port — the interface the ecosystem's co-simulation flows check against a golden model. α should be *defined to agree with the trace port's semantics*: it inherits intent instead of guessing, and it makes trace-based co-simulation runs directly comparable evidence.

## The measure is a retirement-gap bound

`m` bounds cycles-to-next-retirement, and every source of stutter is enumerable and individually bounded:

| stutter source | bound |
|---|---|
| pipeline refill after flush (taken branch, trap, `mret`, `fence.i`) | pipe depth |
| hazard interlock | writer's remaining stages (≤ pipe depth) |
| iterative shift in flight | ≤ 32 cycles |
| I-cache miss | one burst refill = f(`B`) — the bus contract's latency bound |
| dBus transaction | f(`B`) |

Two of those rows are now **measured** on a real execution ([`run-sim.sh`](../tools/run-sim.sh), which runs the shipped core on a built image and records the retirement-gap distribution at the writeBack commit point). Over 200,000 cycles and ~50,000 retirements the observed gaps are: **3 cycles** overwhelmingly — the taken-branch refill of the startup code's idle loop, i.e. the "pipeline refill" row at pipe depth — a small tail at 4–7 for the store sequence, and a handful of large gaps that are I-cache misses. And the cache row's `f(B)` is not just a shape but a *law*: sweeping the memory's wait states gives a worst gap that is **exactly affine, `gap_max = 24 + 8·B`**, whose slope is the **8-word cache line** measured independently in the [configuration record](../tools/config-record.py) — each word of the burst refill pays the bus latency once. The measure's shape and the cache geometry corroborate each other from different directions. (Measured bounds are lower bounds on the true worst case: this is one execution, not a proof. What they establish is that the table's *form* is right.)

The last two rows are why the bus contract must carry a **latency bound**: with an unbounded response channel the measure does not exist and the refinement silently weakens from "instructions retire" to "instructions retire if the bus answers." State it conditionally: `m` exists given the contract's bound `B`; the SoC proof (L7/B2) discharges `B` for the actual fabric, with the off-chip serial-link path as the worst case.

Read quantitatively, the table is a **worst-case execution time** story with one honest complication and one honest mercy. The complication: fetch timing is history-dependent through the cache, so per-instruction bounds do not add exactly. The mercy: the cache is **two lines**, so the pessimistic miss-every-line bound is nearly tight, and a sound program-level bound is `Σ w(i)` with `w` charged at miss-inclusive rates — still literal addition, just of slightly larger constants; the interlock stalls depend only on the adjacent instruction pair, so they compose pairwise. Program-level bounds carry the same three side conditions as any WCET claim: `B(config)`, trap-freedom along the path, and interrupts — handled by masking (`mie`, exact, the right mode for critical sections) or by response-time analysis on top. **The load-bearing consumer is L7/04's graceful death**: `t_holdup ≥ t_epilogue^max` prices a physical capacitor off the worst-case cycles of the quiesce path (IRQs masked) times a clock-period upper bound *taken over the decaying-rail trajectory* — the oscillator slows as the supply sags, so the seconds-per-cycle factor uses the slowest clock the epilogue traverses.

## Traps and interrupts enter the *statement*, not just the proof

The commit case is a *disjunction over the spec's step kinds*: an ordinary retirement, or a trap/interrupt step of the machine-mode spec (L6) — `mepc`/`mcause`/`mstatus` updated and control redirected to `mtvec`, atomically. Preemption points are retirement boundaries: an instruction in flight is either retired or flushed, never half-committed — itself an invariant clause ([05](05-interrupts.md)). Interrupt *arrival* is environmental; the measure's decrease is unconditional because a pending interrupt forces a trap step, not a stall.

## What is deliberately not in the statement

No timing (L2 discharged it), no probabilistic terms (conditioning happened at the overview's †-lines), no bus implementation (contract-abstracted), no netlist (L3 licensed the RTL view). The statement is purely a relation between two transition systems — which is the payoff of the entire tower below it.

## Obligations

1. Write α against the trace-port definition; check it on simulation traces before any proof (cheap oracle).
2. Settle α-total vs. R-relational for this pipe by writing the completion.
3. The stutter-source table's bounds, extracted from the emitted RTL (with [00](00-microarchitecture.md)'s stage-graph extraction), and the conditional-on-`B` formulation with `B` named as an L7 deliverable.
4. The miss-inclusive `w(i)` table, validated against simulation; exported for L7/04's epilogue sizing.

## Effort

Weeks to state precisely; stating it *first* is the layer's own first experiment, since every downstream choice (invariant clauses, IC3 targets) types against it.
