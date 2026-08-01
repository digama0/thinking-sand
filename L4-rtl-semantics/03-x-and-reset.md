# L4/03 — X and initialisation

## Statement

`⟦RTL⟧` as defined is **two-valued** — every register holds a definite bitvector — which is a *strengthening* of reality: power-up state is all-X ([L2/00](../L2-timing/00-timed-model.md)'s value lattice), and real cores deliberately leave registers unset. The obligation is to justify the strengthening exactly where it is used and refine it where it is not justifiable.

## The resolution, in three parts

**Where the spec claims definiteness, prove X-elimination.** pc, the FSM state, and reset-defined CSRs must be definite after reset. The obligation: the reset sequence, run in *ternary* semantics from the all-X state, drives these bits definite. This is checkable by ternary symbolic simulation (industrial "X-prop" verification), and its quantification over the all-X start state means it covers arbitrary pre-reset garbage — so brown-out recovery and SEU-recovery reset ride on the same proof (L7's epoch model consumes exactly this).

**Where the spec permits nondeterminism, refine into it.** RISC-V leaves general registers unspecified at reset. Implementation-X on those bits is not eliminated but **matched**: the refinement maps untracked implementation state into the spec's own reset nondeterminism. The register file simply never needs an X-elimination argument — a large saving discovered by aligning the obligation with what the spec actually claims.

**Where neither applies, prove value-independence.** Any remaining uninitialised bit must never flow to an observation before being written. In ternary terms: X from that bit never reaches a definite-claimed output. These are the classical value-independence lemmas, now stated as X-flow properties — per-bit, mechanical, and expected few after the first two parts have consumed the bulk.

## The one `initial` block

The census found exactly one. Its semantics (a power-up value, distinct from reset behaviour) must be given explicitly — synthesis tools map `initial` on registers inconsistently across targets (FPGA bitstream init vs. ASIC nothing-at-all), so for this ASIC flow the honest reading is: **`initial` is documentation unless the netlist shows an initialised cell.** Check what Yosys did with it in the shipped netlist; the answer decides whether the site is semantics or comment.

## Interfaces

This file is where three layers meet, deliberately thin: [L2/00](../L2-timing/00-timed-model.md) supplies the value lattice and the claim that reset is an X-elimination event; L3/03's ρ requires the reset-state correspondence this file establishes; L7's epoch model consumes "X-elimination from arbitrary state" as its per-epoch base case. The proof lives once, here.

## Obligations

1. The ternary reset simulation for the definite-claimed set (pc, FSM, CSRs).
2. The spec-nondeterminism matching clause in the refinement statement (with L5/L6: which architectural state is reset-unspecified).
3. The residual value-independence sweep.
4. Resolve the `initial` site against the shipped netlist.

## Effort

Weeks, mostly tooling for the ternary simulation; the conceptual work was done when the obligation was split three ways.
