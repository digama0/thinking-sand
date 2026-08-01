# L5/01 — The refinement statement

## Background

How do you prove that one machine correctly implements another? The two machines don't even step at the same rate: the ISA executes one instruction per step, while the hardware takes three or four clock cycles to get through one instruction, with the intermediate cycles holding half-finished work that corresponds to no ISA state at all. The technique that bridges this — the central proof technique of the entire book, used here at full strength — is the **simulation proof**, best understood as a picture before formulas. Here it is, for one ALU instruction walking picorv32's FSM:

```
ISA  ····▶ A ────────────────────────step────────────────────────▶ B ──step──▶ ····
           ▲                                                       ▲
         α │                                                     α │
RTL  ····▶ s₀ ──cycle──▶ s₁ ──cycle──▶ s₂ ──cycle──▶ s₃ ──cycle──▶ s₄ ──▶ ····
           fetch         ld_rs1        ld_rs2        exec          fetch
           m = 4         m = 3         m = 2         m = 1         (commit)
```

The two rails run at their own rates — one instruction per step above, one clock cycle per rung below — and the struts are the **abstraction function** α, which reads the architectural state (register file, program counter) out of a hardware state at the **sync states**: the cycles where the machine is architecturally clean, here the returns to `fetch`. The middle states are the **stutters**. They get no struts, because mid-instruction the hardware embodies no ISA state; they are characterised instead by the **invariant** `I` — the description of the reachable-ish states, [02](02-invariant.md)'s subject and the layer's real work — together with the **measure** `m`, a counter that strictly decreases every stuttering cycle and thereby forces the next commit within bounded time. (Without it, a machine could stutter forever, implementing nothing while never being caught.) The final cycle is the **commit**: the transition back into `fetch` with the instruction's effects landed, the only edge whose ISA shadow moves. The trailing arrows are the next instruction beginning — the ladder continues like this in both directions. The proof obligation is *local*, one cell at a time; induction tiles the cells into the global statement that every run of the hardware, viewed through α, is a legal run of the spec. A global claim about infinite behaviours is bought with finite, checkable, per-cell facts — that trade is the whole magic of the method.

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

## Commit points, α's domain, and RVFI

For a multicycle FSM the commit point is structural: the transition back into `fetch` (or into the IRQ entry) is where the instruction's effects are complete and architectural state is directly readable. α reads: register file, pc, the q-registers and mask (S3 state), and memory-as-seen-through-the-bus. (For pipelined processors, which are never architecturally clean, constructing α is the famous hard part — Burch and Dill's *flushing* builds it by symbolically draining the pipe. This core visits its own abstraction function every few cycles, one of the larger dividends of the target choice.)

**α's domain is a formulation choice, and the statement above made it.** The natural form is *partial*: α defined at commit points only, with mid-instruction states described by `I` plus "within `m` cycles of the last sync state" and no architectural readout of their own — the form RVFI's retirement semantics matches, and the one to author. The statement's total `α : I → States(ISA)` is its completion along the run — α of a mid-instruction state is α of its last commit point — well-defined *as a function* here only because nothing architectural is destroyed mid-instruction (the register file writes at commit; clause 3 of the invariant stages everything else, so the sync ancestor's readout is recoverable from the current state). On a machine without that property the completion exists only as a simulation **relation** `R ⊆ States(⟦RTL⟧) × States(ISA)`, and the per-cycle square reads R-preservation instead of α-equality. The two forms prove the same refinement; the choice is where the bookkeeping lives.

The **RVFI ports** ([00](00-microarchitecture.md)) are the source's own commit-point declaration — `rvfi_valid` pulses exactly at retirement, `rvfi_intr` marks IRQ entry. Even if compiled out of the shipped netlist, α should be *defined to agree with RVFI's semantics*, for two reasons: it inherits the designer's intent instead of guessing, and it makes riscv-formal's existing per-instruction BMC results directly comparable evidence.

## The measure is a WCET table

`m` is a lexicographic sum: (position in the FSM path) + (remaining iterations of the shift/PCPI loops) + (outstanding bus wait). The last summand is why the bus contract must carry a **latency bound** — with an unbounded `mem_ready` the measure does not exist and the refinement silently weakens from "commits happen" to "commits happen if the bus answers." So the statement is conditional on the contract's bound `B`, which the SoC proof (L7/B2) discharges for the actual fabric, with the XIP flash path as the worst case.

Read merely as a liveness device, `m` proves commits happen *eventually* — which wastes what the proof actually builds. Every component of `m` is a concrete design constant: FSM path length per instruction class (≤ 5 states), loop iteration counts (the two-stage shifter's ≤ 10, the divider's data-dependent-but-≤ 33), memory transactions × `B(config)`. So the same induction proves **commit within `w(i)` cycles**, where `w(i) = path(i) + iters(i) + mem(i)·B(config)` — a computable per-instruction **worst-case execution time** — and the honest simulation statement is quantitative: the stutter case carries a budget, not just a decrease.

WCET composes upward by literal addition: an execution of instruction sequence σ completes within `Σ_{i∈σ} w(i)` cycles. On any modern core that sentence is false and its repair is an entire discipline — cache and pipeline state make an instruction's timing depend on execution history, industrial WCET analysis is abstract interpretation over that state, and *timing anomalies* (local worst cases that fail to compose globally) are the field's standing hazard. picorv32 is **timing-compositional by construction**: no cache, no pipeline, no speculation means `w(i)` is history-independent and the sum is exact. One more row of [00](00-microarchitecture.md)'s absence table paying out — a hard-real-time core by accident of its simplicity, with the timing theorem obtained by reading the refinement's own measure quantitatively.

Program-level bounds carry three conditions, each tracked elsewhere: the bus bound `B(config)` (a flash-fetch instruction's `w` is mostly the SPI transaction, so the table is configuration-indexed); trap-freedom along σ; and interrupts, which insert handler cycles into any bound — handled by the standard decomposition: state the bound with IRQs masked (interference-free and exact, the right mode for critical sections), or add response-time analysis (bounded IRQ arrival rate × handler WCET) on top. The ISA-visible half of the export already exists: `rdcycle`/`rdinstret` make cycle counts architectural, and [03](03-instruction-obligations.md)'s counter lemma — instret ticks exactly at commit points — is the same quantitative structure seen from inside the ISA.

**The load-bearing consumer is L7/04's graceful death.** The hold-up inequality `t_holdup(C, I, ΔV) ≥ t_epilogue^max` prices a physical capacitor off the worst-case duration of the quiesce path — which must therefore be a theorem, not a measurement: `t_epilogue^max = (Σ w over the epilogue path, IRQs masked) × T_clk^max`, with the seconds-per-cycle factor bounded *over the decaying-supply trajectory*, since the oscillator slows as the rail sags (X5's frequency enclosure extended to the down-ramp, V8's temporal sibling). Brown-out recovery knowing it can finish its job in time is exactly this chain: WCET cycles × worst-case period ≤ stored energy's runway.

## Interrupts enter the *statement*, not just the proof

An IRQ redirects the commit transition: instead of `α(s) →_isa α(s')` by the fetched instruction, the machine takes the IRQ entry step of the `ISA ⊕ IRQ` spec (L6/S3) — save state to q-registers, mask, jump to `PROGADDR_IRQ`. So the simulation diagram's commit case is a *disjunction over the spec's two step kinds*, and preemption points are exactly commit points — an instruction in flight is never abandoned. That claim (no mid-instruction preemption) is itself an invariant clause, and `waitirq`'s stall state is the one place the measure needs the environment: `m` decreases only given eventual IRQ arrival, so `waitirq` is carved out as a *spec-visible* stutter (the ISA ⊕ IRQ spec has an explicit waiting state — L6 must include it).

## What is deliberately not in the statement

No timing (L2 discharged it), no probabilistic terms (conditioning happened at the overview's †-lines), no bus implementation (contract-abstracted), no netlist (L3 licensed the RTL view). The statement is purely a relation between two transition systems — which is the payoff of the entire tower below it.

## Obligations

1. Write α against the RVFI definition; check it on simulation traces before any proof (cheap oracle).
2. Fix the measure's lexicographic structure and extract the FSM path bounds from [00](00-microarchitecture.md)'s state graph.
3. The conditional-on-`B` formulation, with `B` named as an L7 deliverable.
4. **Derive the WCET table `w(i)`** per instruction class from the FSM graph and the configuration record; validate against picorv32's own documented per-instruction cycle counts and against simulation; export it (cycles, configuration-indexed) as the object L7/04's epilogue sizing consumes.

## Effort

Weeks to state precisely; stating it *first* is the layer's own first experiment, since every downstream choice (invariant clauses, IC3 targets) types against it.
