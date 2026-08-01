# MAIN — the mathematical content

> *"If you wish to make an apple pie from scratch, you must first invent the universe."*
> — Carl Sagan, *Cosmos*

The statement the project is trying to establish, and how it dispatches into layers. Project structure and tooling live in the repository's root README; the flow's jargon is in the [glossary](glossary.md), and textbook on-ramps for the fields the tower spans are in the [reading list](reading-list.md). This file covers what is actually being proved.

## The top-level statement

Let `d` be a fabricated die, `F` a flash image, `E` an environment (supply, clock, temperature, radiation, asynchronous inputs). Write `obs(d,F,E)` for the observable trace at the pads and `Sys(F)` for the pad-trace semantics of the system specification — both **defined by [L7](L7-system/README.md)**, not primitive.

```
     Envelope(d, E)                                     ← L0/07, V1–V7
  ∧  Axioms                                             ← AXIOMS.md
  ⟹  P[ obs(d,F,E) ⊑ Sys(F) ]  ≥  1 − ε(T)

      ε(T)  =  λ·A·T·AVF          particle strikes         (P2)
            +  N_sync·P_meta(T)   unresolved synchronisers (P1)
            +  P_droop            supply excursions        (P6)
```

(Symbols: `λ` is the particle flux and `A` the die area; **AVF**, the architectural vulnerability factor, is the fraction of raw bit-flips that matter architecturally; `N_sync` counts the synchroniser boundaries where the design meets unclocked inputs. All three ε-terms are derived, not decorative — each has its own chapter.)

Three features of this statement are deliberate and worth defending.

**It is probabilistic, and irreducibly so.** No amount of proof removes `ε`. P1 is irreducible by [Marino](BIBLIOGRAPHY.md#marino-1981)'s theorem — no continuous bistable escapes unbounded settling — and P2 is a Poisson process driven by an external flux. What proof *can* do is derive their coefficients rather than measure them, which is what shrinks P1 and P2 in the axiom register without eliminating them.

**Both ends are slots filled by their own layers, and neither is a placeholder for something easy.** `Envelope` is L0's, and is a genuine intersection of five structurally different constraint shapes ([L0/07](L0-device-physics/07-operating-envelope.md)). `Sys` is L7's, its ISA core is L6's, and part of *that* does not exist yet — [picorv32](https://github.com/YosysHQ/picorv32)'s interrupt mechanism is custom, so S3 must be authored rather than imported ([L6](L6-isa/README.md)).

**`⊑` is trace refinement up to stuttering, not equality.** The implementation takes many cycles per architectural step; L5's obligation is a stuttering simulation with a measure function, not a cycle-accurate correspondence.

## The spec tower

The named objects at the seams. Every layer README opens with which of these it consumes and supplies; a layer is either a **theorem** connecting two of them or a **definition** supplying one.

| object | what it is | supplied by |
|---|---|---|
| `Field(A)` | trajectory space of the transient field problem on fabricated geometry `A` | [L0/00](L0-device-physics/00-field-problem.md) (definition) |
| `Contracts(N)` | netlist `N` with each cell carrying its timed assume-guarantee contract (interval Liberty arc + regime classes + noise margin) and each net its RC enclosure | [L0/03–05](L0-device-physics/03-cell-enclosures.md) + [L1/03](L1-geometry/03-capacitance-enclosures.md) |
| `Mealy(N)` | the discrete machine induced by the cells' Boolean functions — a *Mealy machine* is a clocked finite-state machine over bitvectors, outputs computed from state and current input | *derived* — formerly axiom S1; falls out of L0/05's (A) + M5 |
| `⟦RTL⟧` | word-level transition system of the source text | [L4](L4-rtl-semantics/README.md) (definition) |
| `ISA` | `Sail-RV32I(config) ⊕ authored-IRQ ⊕ S4-choices` | [L6](L6-isa/README.md) (definition) |
| `Sys(F)`, `obs` | pad-trace semantics of the system spec; the physical observation map | [L7](L7-system/README.md) (definition) |

One identification is used silently everywhere and stated only here: **`N` is a single shared object.** The netlist that L1's LVS certifies the geometry against, the netlist L2's STA runs on, and the left-hand side of L3's equivalence are all `⟦gl_caravel_core.v⟧` under one parse — X1's obligation, one parser, three consumers.

## The organising principle

> With unbounded proof capacity, the deliverable is the **axiom list**.

Everything merely hard collapses to time. What survives is what is *not* a theorem: specification fidelity, empirical models, physical facts, and genuinely probabilistic phenomena. So each layer is organised around what it **discharges** and what it **introduces**, and the running register is [AXIOMS.md](AXIOMS.md) — with the open *mathematical* questions (M1–M8) kept separate from the axioms, because effort could in principle remove them.

**Notation.** Lettered identifiers index the appendix registers: **S/E/P/X**+number are axioms, **F**+number are findings about the shipped design (unestablished or false hypotheses), **M**+number are the open mathematical questions — all in [AXIOMS](AXIOMS.md). Layer-local check families are defined in their owning chapters: **W1–W4** (netlist well-formedness, L3/01), **G1–G6** (geometric checks, L1/05), **V1–V8** (the operating envelope, L0/07), **C1–C7** (spec choices, L6/02), **B1–B3** (claim boundaries, L7/01). The spec-tower objects are introduced just below; the standalone value **X** — the untracked third logic value — is in the [glossary](glossary.md). Reading top-down, these appear before their definitions; every mention is a link.

## The dispatch

Each layer's named obligations. This is the proof skeleton; the layer documents are the expansions.

Five layers are **theorems**, three are **definitions** — marked, because a definition line in the chain below is an object being supplied, not a claim being proved. (The tables here run bottom-up, L0→L7, following the composition; the book's chapters run top-down, L7→L0, because the material gets progressively crunchier as you descend — start wherever suits.)

| layer | kind | establishes / supplies | named obligations | effort |
|---|---|---|---|---|
| **[L0](L0-device-physics/)** | theorem | `Field(d) ⊑ Contracts(N)`; the error model is Poisson | **M3** lumping/composition · **M7** regime decomposition (I)(P)(A) · **M1** device uniqueness · CCC cut discipline · **M8** metastable eigenvalue | 1–3 yr |
| **[L1](L1-geometry/)** | theorem | layout ⟹ `N` + RC enclosures, ∀A in the E7 family | **(H1)(H2)(H3)** sandwich · **(D1)–(D3)** device-level · **M2** screening · Dirichlet/Thomson bracket · G1–G6 | 2–4 yr |
| **[L2](L2-timing/)** | theorem | `Contracts(N) ⊑ Mealy(N)` given timing closure | **M5** the bridge theorem · **M4** where monotonicity holds · SDC exception classification | 1–1.5 yr |
| **[L3](L3-netlist-equivalence/)** | theorem | `Mealy(N) ≈ρ ⟦RTL⟧` | **W1–W4** well-formedness *(run — see [Status](#status))* · CEC with certificates · **ρ**, the register correspondence (F5) | 6–9 mo |
| **[L4](L4-rtl-semantics/)** | definition | `⟦RTL⟧` | 19 enumerated Verilog sites | 3–6 mo |
| **[L5](L5-microarchitecture/)** | theorem | `⟦RTL⟧ ⊑ ISA` | **the invariant** — stuttering refinement at a commit point | 1–2 yr |
| **[L6](L6-isa/)** | definition | `ISA` | **S2** [Sail](https://github.com/riscv/sail-riscv) fidelity · **S3** the authored IRQ spec · **S4** underspecification choices | 6–9 mo |
| **[L7](L7-system/)** | definition | `Sys(F)`, `obs` | **X4** device models · the bus contract · the boundary decision (core / SoC / device) | ~6 mo |

**The effort accounting.** Figures are for one competent person and are the **sums of the subcomponent estimates**. The original per-layer figures — seeded before the decomposition at "a few years each" — ran roughly 2× higher; scoping the pieces is precisely what revised them, and the sums reflect the better understanding, so they replaced the anchors. One cross-cutting cost is priced separately because no layer owns it: **shared infrastructure** — the hybrid proof framework itself, bitvector automation, symbolic simulation, and the LRAT/PAC checker integrations — **1–2 person-years**, consumed by every theorem layer. Naive sequential total: **8–15 person-years**, before the FPGA alternative (which deletes L1's 2–4).

Note one deliberate inversion: L3's theorem *consumes* L4's object, so proof order is not layer order. The numbering is by artifact altitude — netlist below RTL — not by logical dependency.

## How they compose

```
device d ∈ Envelope
  ⊨ L0   Field(d) ⊑ Contracts(N)                     [M3, M7; modulo E1]        †
  ⊨ L1   N and RC well-defined ∀A in the E7 family   [(H1)(H2) checked, E7 ⊨ (H3); M2]
  ⊨ L2   Contracts(N) ⊑ Mealy(N)                     [M5; F1–F4 to clear]       †
  ⊨ L3   Mealy(N) ≈ρ ⟦RTL⟧                           [W1–W4 ✓, CEC, ρ = F5]
  ≔ L4   ⟦RTL⟧                                       [19 sites]
  ⊨ L5   ⟦RTL⟧ ⊑ ISA                                 [the invariant]
  ≔ L6   ISA  = Sail-RV32I ⊕ picorv32-IRQ            [S2, S3, S4]
  ≔ L7   Sys(F) = ISA ⊕ memory map ⊕ devices         [X4, bus contract]
  ────────────────────────────────────────────────────────
       obs(d,F,E) ⊑ Sys(F)   with probability ≥ 1 − ε(T)
```

**† is where ε enters.** The two marked lines hold on the event *"no particle strike (P2) and no unresolved synchroniser read (P1) during [0,T]"*; every line above them is deterministic conditional on that event, and ε(T) is exactly the probability of its complement (plus P6's droop term). The probability in the conclusion is not smeared across the chain — it is the measure of the conditioning event for two specific lines.

## Interfaces

Each layer exports a thin object. The **functional** chain and the **physical** chain are nearly independent and meet only at the netlist:

```
                    L7  Sys(F): pad traces (memory map, XIP, UART, obs)
                     ↑  composition of the tower, at the boundary chosen
                    L6  ISA (Sail + the picorv32-specific parts that must be authored)
                     ↑  refinement proof — invariants, word-level          ← THE WORK
                    L5  RTL (buses, arithmetic, hierarchy intact)
                     ↑  semantics of the synthesisable subset
                    L4  ─────────────────────────────────
                     ↑  equivalence w/ certificates
                    L3  gate netlist  ←── meeting point ───┐
                                                           │ annotations (delay, RC)
                    L2  timing: closure ⟹ Mealy sound ─────┤
                    L1  geometry: GDS ⟹ netlist + RC ──────┤
                    L0  devices: cells ⟹ Boolean functions ┘
```

**The refinement proof never touches RC.** Electrical data exists solely to discharge L2's hypotheses. That is the cleanest seam in the stack and should be preserved deliberately — see [L2](L2-timing/README.md) on keeping crosstalk out of the interface, and treating any net that would need a functional coupling constraint as a layout bug.

Note also that the layer split is by **abstraction target**, not by physical object: L0 and L1 solve instances of the *same* field problem on complementary domains, and [L0/04](L0-device-physics/04-lumping-composition.md) is what licenses gluing them. The corollary is that safety conditions are stated in one layer and discharged in another — [L0/09](L0-device-physics/09-cut-discipline.md) carries the dispatch table, and L0 turns out to own the *statement* of every envelope condition but the *check* for only one.

## Three structural facts that recur at every layer

These are why the edifice is possible, and they shape every proof in it.

**1. Nothing accumulates.** Every layer has a mechanism that resets the error budget: gate restoration kills noise accumulation across logic depth; the clock edge kills timing-error accumulation across cycles; local variation adds in quadrature (√n) rather than linearly along a path; ECC plus scrubbing converts a linear-in-time failure rate into a quadratic one. Consequently every proof here is inductive with a **fixed** invariant, never one tracking a growing quantity.

**2. Continuous perturbations get discharged; discrete events get carried.** The continuous mechanisms are suppressed by hundreds of orders of magnitude — thermal escape faces a ~7,500 kT barrier, giving ~10⁻³²⁸⁵ — and should be *bounded away and deleted*, not carried as epsilons. The discrete ones (particle strikes, manufacturing defects) are Poisson, do not shrink with margin, and are handled by redundancy or by test, never by better analysis. **Confusing the two is the most common modelling error in this area**, and the trap is that coupling capacitance *looks* like the first kind and behaves like the second: it is additive, so its far-field sum needs a genuine convergence argument (M2) rather than a smallness claim.

**3. Amortisation is the whole game.** ~400 standard cells verified once cover every design on the process. A fixed vertical stack is exactly what makes the extraction pattern library finite. `gpio_control_block` appears 38 times. The per-design entropy is far smaller than the artifact size suggests: 291 MB of GDS carries perhaps a few MB of real content, and 275,608 instances reduce to ~21,600 that matter.

## A pattern worth naming

Recurring often enough to be a heuristic rather than a coincidence:

> **A real physical instability, prevented by a design rule, which is therefore secretly a hypothesis of a well-posedness or boundedness claim rather than a manufacturing constraint.**

Instances so far: min-width and min-spacing are the hypotheses of L1's topology-preservation theorem; tap coverage is what destroys latch-up's second PDE solution branch (M1), i.e. what makes "the transistor's I-V characteristic" well-defined; the voltage rating keeps impact-ionisation terms out of the model and hence keeps global existence available; tied metal fill is a precondition of M2's cascade, since floating conductors *relay* rather than screen.

**Several DRC rules are the side conditions of theorems nobody has written**, and recovering those theorems may be the cleanest way to say what a rule deck actually means.

## Status

**Open mathematics** (M1–M8 in [AXIOMS.md](AXIOMS.md)): M2 (the screening exponent) and M5 (the bridge theorem) are the two the project's structure most depends on; M1 (uniqueness for stationary drift–diffusion) is the only one that is open *mathematics* rather than open *formalisation*.

**Established for the shipped design** — the parts that are not speculative:

- W1–W4 run clean, and prove X5's PLL excision **minimal**: `pll.ringosc` holds the netlist's only combinational cycle (1 SCC, 64 nets) *and* its only multi-driver nets (26, all tri-state, discharged structurally by complementary enables). Excise it and the netlist is acyclic and contention-free.
- The Liberty tables are non-monotone in slew at two grid points of the simplest cell, so the interpolation enclosure must take the max over all four corners of the enclosing cell — and corner-based methodology's monotonicity hypothesis (M4) is not free.

**Unestablished for the shipped design** (F1–F5): three of nine corners fail `in2reg` hold; one passes only modulo `max_tran`/`max_cap`, meaning parts of the design sit outside the Liberty characterisation range where STA is *vacuous* rather than merely inaccurate; 159 SDC exceptions are unverified; register correspondence through synthesis is unknown. **The hypotheses of the bridge theorem are not currently established for this design as shipped.**

See [FINDINGS.md](FINDINGS.md) for the measured data behind all of it.

The chapters descend the tower from here: [L7](L7-system/README.md) first — the claim — down to [L0](L0-device-physics/README.md), where it runs out of turtles.
