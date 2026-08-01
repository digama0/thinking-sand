# L6/01 — The authored IRQ specification (S3)

## Statement

Write the specification that does not exist: picorv32's interrupt mechanism is **custom** — no standard to conform to — and its spec must be authored before L5/05 can prove anything against it. This is the single most error-prone artifact in the project and the least likely to be caught by anything downstream: **S3, the sharpest surviving specification axiom.**

## What must be specified

The spec extends the Sail base with state and steps:

**State.** The 32-line pending set (with per-line latching per `LATCHED_IRQ` and permanent masks per `MASKED_IRQ`); the software mask register; the four q-registers; the timer's countdown register — *architectural*, since `timer` reads/writes it; and — a requirement discovered by L5's measure analysis — an explicit **waiting state** for `waitirq`, so the implementation's stall is a spec-visible stutter rather than a liveness violation.

**Steps**, joining the instruction step as the spec's second kind ([L5/01](../L5-microarchitecture/01-refinement.md)'s disjunction):

- **IRQ entry**: at an instruction boundary with unmasked pending lines — return pc and pending set delivered into q-registers, mask updated, jump to `PROGADDR_IRQ`, *atomically* (no observable intermediate — L5/05's obligation 2 is the implementation side).
- **The six instructions**: `getq`/`setq` (q-register access), `retirq` (return + unmask), `maskirq` (mask exchange), `waitirq` (enter the waiting state), `timer` (exchange countdown). Encodings occupy custom-0 space; [03](03-coverage.md) must treat them as implemented.
- **Timer expiry** raising its line; external lines set by the environment (the IRQ *map* — which device drives which line — is deliberately **not** here: it is L7/03's system wiring. This spec is parameterised by the lines, portable with the core).

**Underspecification within S3 itself** — the authored spec inherits [02](02-underspecification.md)'s discipline: e.g. simultaneous-line arbitration order and the exact boundary cycle of entry ("eventually, at a commit point" vs. "at the next commit point") are choices to record, not facts to discover.

## Authoring methodology: breaking the circularity

Spec and implementation share an author here; the evidence must not. The anchors, in order of independence (developed in [L5/05](../L5-microarchitecture/05-interrupts.md)):

1. **Formalise the documentation first** — picorv32's README prose — *then* diff against RTL behaviour, so every discrepancy surfaces as a recorded finding resolved in one deliberate direction, never silently toward the RTL.
2. **Shipped and third-party firmware** using the IRQ instructions: the spec must make observed, working software correct. Software written by others against the documentation is the nearest thing to an independent semantics.
3. **riscv-formal's IRQ checks** via RVFI's `rvfi_intr` — prior art for what "an interrupt retired correctly" observably means.

## Obligations

1. The state + step formalisation above, parameterised by lines and by the relevant configuration bits (`ENABLE_IRQ_QREGS`, `ENABLE_IRQ_TIMER`).
2. The doc-first draft, the RTL diff, and the discrepancy log (each entry an S3-fidelity data point).
3. The firmware anchor corpus (shared with L5/05).

## Effort

Months, thinking-dominated — the counterweight to [03](03-coverage.md)'s typing-dominated bulk. The fidelity risk is priced in AXIOMS as S3 and cannot be engineered away, only anchored.
