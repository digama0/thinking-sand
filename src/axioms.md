# The axiom register

The primary deliverable. With unbounded proof capacity everything else is time; this list is what the result would actually *be*.

Each entry: what is assumed, which layer introduces it, whether it is testable, and what it would take to push it further down.

**Reassessment pass (2026-07).** Test applied to every entry: *is this a fact about the world outside the mathematics — fabrication, environment, intent — or merely an unproven theorem?* Entries failing the test are marked **T→theorem** with a named discharge route (they remain assumptions only until that route is executed), retired (**R**), or moved to the Discharged section. The result is summarised in [The irreducible core](#the-irreducible-core).

Status key —
* **A** unfalsifiable in principle (specification fidelity)
* **E** empirical, testable
* **P** physical/probabilistic, no deterministic statement exists
* **T→theorem** removable, discharge route named
* **R** retired — not needed for the per-die validation claim.

---

## Specification-side (errors here are silent)

| # | axiom | layer | status | notes |
|---|---|---|---|---|
| S2 | The Sail RISC-V model faithfully captures the standard | L6 | **A** (small) | Smaller than it looks: `sail-riscv` is the standard's official *golden model* — adopted by RISC-V International, and new extensions must extend it for ratification. Residue: the model's fidelity to the ratified manuals, plus the Sail→prover translation's trust status (L6 open problem 4). Mitigate by running the official compliance suite against the imported model. |
| S3 | The residual authored semantics are what was intended | L6 | **A** (re-scoped 2026-08-02) | Originally: picorv32's custom IRQ scheme, documented only as README prose — the sharpest specification axiom. The shipped VexRiscv core instead uses the **standard machine-mode CSR/trap/interrupt machinery** (CsrPlugin), so the bulk of the old S3 dissolves into S2's import (the Sail privileged subset). What remains authored: the LiteX SoC's device/CSR semantics and any VexRiscv behaviour outside the ratified model (debug unit, cache side effects) — smaller, but the same unfalsifiable character; the doc-first-then-diff discipline carries over. |
| S4 | Where RISC-V is underspecified, our chosen refinement is acceptable | L6 | **A** | Interrupt timing ("eventually"), WARL field choices, some PMA behaviour. Conformance to an underspecified spec is not a statement. |

## Empirical models (testable, calibrated, never derived)

| # | axiom | layer | status | notes |
|---|---|---|---|---|
| E1 | The compact device model (BSIM) enclosure contains the true device | L0 | **E** | **The tower's one physical axiom.** Weakened to interval containment (L0/02) — "the true I-V lies in the enclosure," not "the model is correct." L0/08 is the argument that this is the right place for the physics tower to bottom out: digging deeper only relocates the axiom to worse-validated, harder mathematics. Everything marked "modulo E1" below discharges into this single entry. **Data: D4**, with D2 behind the fit. |
| E4 | Corner models bound the actual PVT distribution | L1/L2 | **merged** | No independent content: the empirical half ("actual dies lie within the corner parameter ranges") is P4; the mathematical half ("box extremes are attained at corners") is M4 — an obligation, not an axiom. |
| E6 | DRC rules imply manufacturability | L1 | **R** | Retired: a *yield* claim, not a correctness claim. For validating an existing, fabricated, tested die, manufacturability is moot. What the proof needs — as-fabricated geometry within tolerance — is E7's restated content; per-die escapes are P5's. |
| E7 | The as-fabricated geometry lies within the stated tolerance family of the drawn layout | L1 | **E** | Restated (absorbing what E6 actually contributed): litho + etch + CMP + overlay keep this die's geometry inside the family over which L1's enclosures and sandwich theorem are quantified. Sits *between* LVS and the fab — the mask is deliberately **not** the drawn layout (OPC), so LVS-verified geometry is not what prints. Scales worst as features shrink relative to wavelength. Irreducible: it is a claim about a physical object, checked only statistically (process control) and indirectly (test). **Data: D3** — the partially unpublished class; provenance via the DRC-deck inversion (see the register). **Now carries L1/01's hypothesis (H3)** — *no spurious material*: the sandwich alone permits the fabricated set to contain an island that meets no eroded net, i.e. a net absent from the drawn layout, and the topology-preservation theorem is **false** without it. Not checkable (it quantifies over `A`); the physical reason it holds is that etch and litho *displace edges* rather than nucleate islands, so an edge-displacement process model would imply it. |

## Physical / probabilistic (no deterministic theorem exists)

| # | axiom | layer | status | notes |
|---|---|---|---|---|
| P1 | Synchronisers resolve | L2 | **P** (shrunk) | Irreducible in principle — [Marino](bibliography.md#marino-1981)'s theorem (L0/05): no continuous bistable escapes unbounded settling. But the *rate* becomes a theorem: τ is the unstable eigenvalue at the metastable saddle, derivable as an enclosure from E1's interval model (M8), and the settling-time distribution follows. Surviving axiom content: the asynchronous-input arrival process is bounded (environmental — P6-class). |
| P2 | No single-event upsets outside the ECC budget | L0 | **P** (shrunk) | Poisson, linear in area×time, does **not** shrink with margin. But most of its parameters are derivable modulo E1: Q_crit and collection cross-section from device physics, masking/AVF from netlist + timing (L0/06), interleaving from layout (X2's route). Irreducible core: the **flux** ([JEDEC JESD89A](bibliography.md#jesd89a)) and the measured multi-cell upset radius — environmental and empirical facts. **Data: D5** (flux); the upset radius is a D3/D4-class measurement. |
| P4 | Process variation stays within corners | L1 | **P** | Absorbs E4's empirical half: as-fabricated device and interconnect parameters of shipped dies lie within the corner ranges. Becomes *yield*, caught by test, not a runtime failure. Fluctuation granularity (discrete dopants, RTN — L0/08) enters here as part of the corner spread. **Data: D3 + D4** (corner ranges). |
| P5 | The fabricated die is defect-free on the tested faults | L1 | **P** | Per-die assurance is statistical: ATPG coverage (~99% stuck-at), not proof. A far larger hole than anything in the proof. Irreducible for existing silicon; the only shrink available is better coverage *accounting*, which is computable. **Data: D3** (defect density D₀) + the measured coverage of the actual test set. |
| P6 | Environment within spec | L2 | **P** | The collector for every bound the world must supply: supply voltage and droop, temperature, clock-reference accuracy, asynchronous-input arrival rates (P1's residue), radiation flux (P2's residue), jitter budget (X5's residue). Irreducible by nature — no theorem constrains the environment. **Data: D5**. |

## Structural / interface

| # | axiom | layer | status | notes |
|---|---|---|---|---|
| X3 | Coupling beyond the extraction window is bounded in aggregate | L1 | **T→theorem (on M2)** | The assumption standing in for the screening theorem. Removable the day M2 is proved; **not** justified by per-pair smallness — the naive far-field sum over ~42k nets diverges without screening. |
| X4 | The SPI flash, UART and other devices meet their datasheets | L7 | **A/E** | A scoping dial, not a monolith: L7's boundary decision (B1 core / B2 SoC / B3 device) determines exactly which batch of it each theorem is conditional on — B1 needs none. Required in full only for the claim about the device you can hold. |
| X5 | The PLL produces a clock of frequency f ± tolerance | L2 | **T + P** | Reassessed: *not* unfalsifiable. The ring oscillator is a circuit made of the same devices L0 models. (i) Existence of a stable limit cycle with a frequency enclosure is a computer-assisted-proof target of standard type — interval Poincaré maps ([Zgliczyński](bibliography.md#zgliczynski-1997), [Galias](bibliography.md#galias-2001)) over the interval device model (M8) — modulo E1. (ii) What genuinely survives is **phase diffusion**: the limit cycle's zero Floquet exponent means no restoration along phase, thermal noise accumulates as a Wiener process, and jitter is the one place thermal noise survives macroscopically (L0/06; [Demir](bibliography.md#demir-mehrotra-roychowdhury-2000)'s theory). Its coefficient is derivable; its budget lands in P6. "Cannot live inside the synchronous abstraction" remains true — it lives in L0's dynamical layer instead. **Measured (L3): the excision is provably *minimal*** — `pll.ringosc` contains the netlist's only combinational cycle (1 SCC, 64 nets) *and* its only multi-driver nets (26, all tri-state), and excising it leaves the netlist acyclic and contention-free. |

## Empirical inputs (the data register)

The axiom tables above are model-adequacy *claims*; this table is the *numbers* those claims consume. Discipline: every number enters a proof as an **interval with stated provenance**, never a point value. Per number the axiom is "the true value lies in the stated interval"; the proof determines the **required width** (from the margin budget), metrology determines the **available width**, and the health metric is the ratio.

| # | class | examples | required vs available | consumed by |
|---|---|---|---|---|
| D1 | fundamental constants | k_B, e, h — **exact** since the 2019 SI redefinition; ε₀, α at ~10⁻¹⁰ relative | ~2 digits vs exact — free | P3's discharge (kT), charge counting (e, Q_crit), capacitance (ε₀) — these enter L0's own arguments **directly, independent of E1** |
| D2 | bulk material data (Si, SiO₂, metals) | ε_r(SiO₂) ≈ 3.9, ε_r(Si) ≈ 11.7, E_g = 1.12 eV, n_i(300 K) ≈ 10¹⁰ cm⁻³; **mobility and ionisation vs dopant concentration** ([Caughey–Thomas](bibliography.md#caughey-thomas-1967), [Masetti](bibliography.md#masetti-1983) fits); v_sat; [Chynoweth](bibliography.md#chynoweth-1958) coefficients; metal resistivities; thermal conductivities | ~10% needed vs ~1% available | L1's enclosures consume ε_r and ρ **directly, not via E1**; L0/07's avalanche and thermal criteria; the rest via E1's fit |
| D3 | process / facility metrology | layer thicknesses, t_ox, sheet resistances ± corners (**published** in the PDK); overlay σ, CD-control σ, LER amplitude and correlation length, etch bias vs density, defect density D₀ (**not published**) | **the binding class** — required ≈ available | E7's tolerance family — these are literally the `r_m = bias + k·σ + overlay` of L1's sandwich theorem; P4's corner ranges; P5's defect statistics |
| D4 | device calibration | the SKY130 BSIM4 model-card parameters per device flavour, with corner spreads (**published**); the doping profiles behind them (**not published**) | interval width set by the noise margin — L0/02 argues coarse suffices | E1 — this *is* E1's data |
| D5 | environmental reference | [JEDEC JESD89A](bibliography.md#jesd89a) flux spectrum; ambient temperature range; supply tolerance; reference-oscillator accuracy (datasheet) | datasheet-level | P2's λ; P6's bounds; X4 |

Three notes:

- **The unpublished half of D3 has an observable shadow: the DRC deck.** Spacing and enclosure values encode the foundry's own margin arithmetic (`rule ≈ f(overlay, CD σ, …)`), so the tolerance family can be *inferred* from rules the foundry publishes and stakes its yield on, rather than assumed. This inversion should be performed explicitly and recorded as the provenance of E7's intervals — it is the same move as reading DRC rules as theorem hypotheses, applied to data.
- **Why the data floor is D2, not the standard model.** The most optimistic anchor — fundamental constants only — is blocked by L0/08's chain gaps: ab initio methods reach percent accuracy at best on the quantities that matter (the DFT bandgap problem), no better than measurement. D1 still enters directly where L0 uses it, but everything material is measured, and would remain measured even with the reduction chain proved.
- **Liberty tables and extraction decks are deliberately absent** from this register: after E2's and E3's discharge routes they are *derived* objects, not inputs. D4's unpublished doping profiles are why Route A (solving the device PDE) is blocked by data availability as well as by mathematics.

## Discharged and retired

Kept for the record; identifiers remain valid where other documents cite them.

| # | was | verdict |
|---|---|---|
| S1 | The netlist semantics is the right semantics | **Discharged** — In this project the netlist's Mealy semantics is *derived*, not posited — per-cell Boolean functions (L0/05's (A)) + the bridge theorem (M5) + LVS (L1) yield it as the conclusion of the physical stack. |
| P3 | Thermal noise does not cross the noise margin | **Discharged** — a theorem modulo E1: barrier ≈ 7,500 kT ⟹ ~10⁻³²⁵⁷ (L0/06); the quantum-tunnelling analogue is smaller still (L0/08). One caveat is load-bearing: the discharge requires *restoration*, and fails on the oscillator's phase mode — that residue is X5/P6's jitter, not a level-noise failure. |
| X1 | The netlist printer / file parser is faithful | **Obligation, not axiom** — a verified parser/printer for a ~20-production format is standard work ([CompCert](bibliography.md#compcert-2009)-style validated front-ends). Route known, no empirical content; it was never a claim about the world. |
| E2 | Standard-cell Liberty tables match SPICE match silicon | **Discharged** — Route: L0/03 derives interval-valued tables (with inter-sample derivative bounds) from E1's interval device model by verified DAE enclosure. The shipped `.lib` then *exits the trusted base* and is demoted to an oracle for cross-checking. |
| E3 | The extraction rule deck (pattern library) is accurate | **Discharged** — Route: L1's variational enclosures — Dirichlet/Thomson two-sided bounds, [Nakao–Plum–Watanabe](bibliography.md#nakao-plum-watanabe-2019) machinery. Accuracy target ~5% against 10–20% carried margin, so rigorous-but-loose suffices. The far-field part additionally needs M2. |
| E5 | The delay model (cell + interconnect) matches physical behaviour | **Discharged** — Subsumed: cell part by E2's route (L0/03), interconnect part by E3's route (L1), composition by M3/M5. Not a separate assumption once those land. |
| E6 | DRC rules imply manufacturability | **Retired** — yield economics, not per-die correctness. Needed content restated into E7. |
| X2 | Errors within an ECC word are independent | Route: "cells of one word are pairwise ≥ r apart" is a decidable layout check (L1 machinery); the empirical content — the upset radius r, growing with scaling ([Ibe et al.](bibliography.md#ibe-2010)) — moves into P2's parameter set. Still the clearest cross-layer obligation in the project: the check lives in the GDS, invisible to both the code's algebra and the netlist. |

## Currently *false* or unestablished for the shipped design

Not axioms — open defects in the assumption set, discovered during scoping. These will most likely be discharged by modifying the design.

| # | claim | layer | status |
|---|---|---|---|
| F1 | Hold is met at all corners | L2 | **FAILS, now sharply** (findings: *F1 confronted*). The core signoff's own SDC constrains `mprj_io_in` as 4 ns *synchronous* inputs and false-paths only `rstb_h`/`gpio_in_core` — the mprj false paths live in the chip-level SDC only — so the failing `in2reg` paths are real constrained paths from async pads. The shipped reports carry **no per-path evidence for the failing corners** (the final nom run is all-MET, +0.58 hold). Closure: reproduce the ss-corner STA from the fully-pinned inputs (netlist + SPEF + SDC + Liberty); blocked on an OpenSTA run. |
| F2 | All loads/slews lie within the Liberty characterisation range | L2 | **FAILS.** `t-max` passes "except max_tran & max_cap". Beyond the table the tool *extrapolates*, so those timing numbers are vacuous rather than merely wrong. |
| F3 | The SDC exceptions are justified | L2 | **PARTIALLY SUBSTANTIATED, and the shape is now known** (`tools/sdc-audit.py`, `tools/synccheck.py`; findings). Every false path in every mode is asynchronous-external; behind them **no two-flop synchroniser exists anywhere in housekeeping** — the input side resolves into source-synchronous SPI capture (sound under its own assumptions) plus **40 single-flop captures on the core clock**, whose discharge must be a software-paced settling argument, not the synchroniser predicate. `gpio_in_core` is the design's one verified two-flop synchroniser. |
| F4 | Declared `set_case_analysis` modes cover all reachable configurations | L2 | **UNVERIFIED, and sharpened three ways** (findings): the shipped run timed **one of the eight modes**; `mprj_io[3]` (SPI CSB) clocks/gates and async-resets housekeeping flops yet is **declared a clock in no mode** — SCK modes pin it to a constant, so CSB-edge timing (SPI transactions themselves) lies outside every analysed mode; and the SPI shift domain's clock is a **mux** (`csclk` = external SCK path OR the wishbone bit-bang clock `wbbd_sck` — which is itself a *flop output*, a register-generated clock declared in no mode), so mode coverage must also cover the clock-select state and the bit-bang clock is untimed everywhere. |
| F5 | Register correspondence survives synthesis | L3 | **UNKNOWN.** Yosys `opt_dff`/`opt_merge` can remove or merge flops, and Yosys emits no SVF-equivalent guidance. Decidable by re-running the flow. |
| F8 | Reserved encodings trap | L5/L6 | **FAILS** (`tools/partition.py`; exact BDD comparison of the spec patterns against the decoder's own legality cubes). The shipped decoder **accepts 4,292,609 reserved words**: all of LOAD funct3=110 (2²² words), the reserved shift-immediate variants (98,304), and `sret` (one word, landing in `mret`'s decode slot). They execute as *something* — the decoder minimiser used reserved space as don't-cares — so the coverage sweep's traps-correctly claim must carve them out, and what they execute *as* becomes authored alias rows in the residue (S3), extractable from the decode control signals. The refinement-critical direction holds: **zero** spec-legal words are rejected. |
| F7 | The target is the shipped core | L3–L5 | **RESOLVED — the target follows the silicon.** The pinned netlists carry the **VexRiscv/LiteX** management core: VexRiscv `MinDebugCache` (pipelined RV32I + I-cache + machine-mode CSRs + debug), identified from the GL's own plugin registers and pinned by `check-l5.py`. picorv32 remains pinned as the comparison core. |
| F6 | Reachable clock configurations respect timing closure | L2/L7 | **UNVERIFIED.** Closure is signed off against the SDC period, but the PLL trim (`itrim`) and divider are software-visible housekeeping registers and the ring oscillator's corner spread is tens of percent — so whether every reachable configuration keeps the realised period ≥ the closed period is unknown (L2/05 obligation 5). **Not an axiom**: the reachable range is computable from X5's enclosure × register semantics, modulo E1. Discharge: (i) prove range ⊆ closure; or (ii) declare out-of-range configuration *unspecified* in `Sys(F)` — the datasheet "recommended operating conditions" move, an S4-class spec choice (L7). The external-clock half is already P6's. Second instance (after F4) of the general pattern: **register-dependent hypotheses of lower-layer theorems become reachability conditions.** |

---

## Open mathematical questions

Not axioms — things that might be theorems, that the project needs, and that nobody has. Distinguished from the tables above because effort could in principle remove them. Note the **T→theorem** routes above land here: executing them is what shrinks the register.

| # | question | layer | notes |
|---|---|---|---|
| M1 | **Uniqueness for stationary drift–diffusion under operating bias** | L0/02 | Existence is established; uniqueness is known only near equilibrium and **genuinely fails** where latch-up or snapback occur — a parasitic thyristor is a real bistable device. So "the transistor's I-V characteristic" is not well-defined from first principles. Industry dodges this by not solving the PDE (→ E1). Tap-coverage rules are secretly the side condition that kills the second branch. **May be bypassable**: state all enclosures universally over weak solutions of the *transient* problem; what is then needed is unreachability of the second basin from the unpowered state under tap coverage, and the method fails safe if that cannot be shown (L0/00). |
| M2 | **The screening exponent α** | L1 | The far-field coupling sum does not obviously converge: net counts grow polynomially in distance while unscreened coupling decays only logarithmically. Convergence rests on cascaded mesh apertures giving `C_far(d) ≲ C_adj·α^(d/p)`. Deriving α from a harmonic-measure estimate is the load-bearing open problem of L1 — *all* local extraction depends on it, and X3 retires when it lands. |
| M3 | **The lumping/composition theorem** | L0/04 | "The lumped circuit model is sound with respect to the field problem, with this error bound." Universally assumed, never stated in a form usable as a verification hypothesis. The right formal frame is ISS small-gain / contraction (L0/04). |
| M4 | **Where monotonicity holds** | L0/04, L2 | Corner-based methodology is sound iff the response is monotone in the corner parameters — otherwise the extremes are not at the corners. Assumed industry-wide. **Production data violates it**: `cell_fall` is non-monotone in input slew at two grid points of `inv_1`. Absorbs E4's mathematical half. **Diagnosed (L2/03)**: the violation is an artifact of the `(t₅₀, slew)` quotient — the 50% anchor vs. conduction from V_th — while the *waveform-level* map is monotone by ODE comparison (given E1 states `I` increasing in `V_in`). So M4 splits: the timing half dissolves under waveform-envelope propagation; the genuinely open residue is monotonicity in the P/V/T parameters proper. |
| M5 | **The bridge theorem** | L2 | Timing closure ⟹ the discrete Mealy semantics is sound. Everything above L2 presupposes it, and S1's discharge route runs through it. Tractable — a paper, not a decade. |
| M6 | An explicit constant in the quasi-static error bound | L0/01 | `‖φ_Maxwell − φ_EQS‖ ≤ C·(L/λ)²·‖source‖` with `C` geometry-dependent. The theorem shape exists ([Ammari–Buffa–Nédélec](bibliography.md#ammari-buffa-nedelec-2000)); the explicit constant over realistic geometry does not. Without it the reduction is qualitative. |
| M7 | **The regime decomposition: robust invariance + progress** | L0/05 | The honest form of "the digital abstraction". Not a static noise-margin claim but (I) you never leave the union of valid regimes under bounded disturbances, (P) transitions complete in bounded time, (A) the induced discrete map is the Boolean function. Needs barrier certificates for (I) and a Lyapunov functional for (P). The van Roosbroeck **free energy** is the natural candidate, but it decreases toward *equilibrium* — adapting it to a boundary-driven steady state is the open piece. Metastability is precisely the failure of (P). |
| M8 | **The two non-restoring modes: metastable saddle and oscillator phase** | L0/05, L2 | The two places restoration fails, and therefore the two places physical content survives to the ledger: the synchroniser's τ (unstable eigenvalue at the saddle) and the oscillator's frequency and phase-diffusion coefficient (Floquet analysis of the limit cycle). Both are eigenvalue-enclosure problems over the interval device model — the same machinery as L0/03. Discharging M8 converts P1's rate bound and X5's frequency claim into theorems modulo E1. Prior art is mature: interval Poincaré maps ([Zgliczyński](bibliography.md#zgliczynski-1997), [Galias](bibliography.md#galias-2001)) for the orbits; [Demir–Mehrotra–Roychowdhury](bibliography.md#demir-mehrotra-roychowdhury-2000) for phase noise. |

M2, M3, M5 and M7 are the four where the project's structure genuinely depends on the answer. M1 is the only one that is open *mathematics* rather than open *formalisation* — and the enclosure formulation may sidestep it. M8 is the ledger-shrinker: it exists purely to convert axioms into theorems.

Note M7 subsumes what a static "noise margin" argument was doing: the margin is the **robustness radius of the invariant set**, and restoration is the contraction that makes the set attracting — not separate phenomena.

## The irreducible core

If every **T→theorem** route is executed and every M is proved, the register collapses to:

| cluster | entries | why no proof reaches it |
|---|---|---|
| specification fidelity | S3, S4, S2's residue | intent is not a mathematical object |
| the physical model | E1 | the tower's one empirical axiom; position chosen deliberately (L0/08) |
| this particular die | E7, P4, P5 | fabrication is sampling and test is statistical; no theorem reaches the object itself |
| the environment | P6 (absorbing P1's arrival bound, P2's flux, X5's jitter budget) | no theorem constrains the world |
| surviving randomness | P1, P2 residues | [Marino](bibliography.md#marino-1981)'s theorem; Poisson arrivals — irreducible in principle, quantified by theorems |
| scope | X4 | a choice, not a claim |

Twenty-two entries reduce to roughly eleven, and **every survivor is a statement about the world — fabrication, environment, intent — rather than about mathematics.** Each survivor's numerical content is an interval-containment claim over the data register (D1–D5) above — so the fully reduced trusted base is: the intent claims, the D-intervals with their provenance, and the Poisson/[Marino](bibliography.md#marino-1981) residues. The middle of the stack becomes theorem all the way through: the only assumption *below* the netlist is E1 (plus the die/environment cluster), and the only assumptions *above* it are the three specification-fidelity claims at the very top. That shape — empirical floor, unfalsifiable ceiling, theorems in between — is the honest form of "the chip is verified."
