# L7/00 — `Sys(F)` and `obs`: the two definitions

## Statement

Define the two objects MAIN's top-level statement quantifies over. The ISA is not the top: an ISA transition system does not produce pad traces, and the map from architecture to observable behaviour goes through everything the SoC wraps around the core. Before L7 existed, that map was used by MAIN while being defined by nobody.

```
Sys(F)  =  traces at the pads of:
             ISA (L6)                          the core's contract
           ⊕ SoC memory map                    what each address means      [03]
           ⊕ SPI-flash XIP controller model    fetch from F, wait states    [02, 03]
           ⊕ UART model                        the observable output channel [03]
           ⊕ GPIO/pad configuration            which pads mean what, when   [03]

obs(d,F,E)  =  the physical trace: sampled pad voltages of die d,
               classified through L0's regimes, at L2's clock granularity
```

Both are definitions; the theorem connecting them is the whole rest of the repository.

## The trace alphabet — the load-bearing choice

`obs` is defined at the **physical alphabet**: timed, regime-classified pad samples. This is forced, not stylistic, by the epoch analysis ([04](04-power-epochs.md)): an epoch ends in `valid-prefix · ramp-down-tail`, and prefix closure — the property that lets a machine *stop* without violating anything — holds at the physical level only. A truncated byte is a prefix of a timed trace but not of any byte sequence, so **abstract views (bytes, transactions) are derived, never primitive**, or epoch composition is unstatable. (The tail is demonic — adversarially unconstrained, the spec holding under *every* resolution — only without supervisor + fail-safe-pad discipline; with them it refines to a *specified* truncate-idle-decay shape — [04](04-power-epochs.md).)

Consequences worth pinning:

- **The UART channel is a timed trace against the baud clock** — bit cells, start/stop framing — with P6's clock-accuracy bound doing quantitative work in the derivation of the byte view. Where framing errors land (open problem: garbage byte vs. excluded-by-derivation) is a real spec decision.
- **Which pads carry meaning is configuration-dependent** — the pad functions are runtime-configured, and F4's `set_case_analysis` modes are exactly this fact's timing-side shadow. `obs`'s per-pad interpretation is indexed by the GPIO configuration state.
- **Start of trace**: from power-on reset; the boot window before reset release is spec'd by hardware defaults ([04](04-power-epochs.md)'s boot-window promise), not demonic.

## Refinement shape

`obs(d,F,E) ⊑ Sys(F)` is trace refinement up to stuttering at the physical alphabet, prefix-closed, with liveness expressed as bounded progress (every claim carries its `T`). The ε-conditioning lives at MAIN's †-lines, not here — `Sys` itself is a deterministic-spec-with-nondeterminism object, never probabilistic.

## Obligations

1. The alphabet definition: sampling, regime classification, per-pad configuration indexing.
2. The derivation stack: physical → bit-cell → byte → "the UART printed *hello*", each level with its validity conditions.
3. The `Sys` composition operator itself — how ISA steps, memory-map reads, and device models join into one trace set (the fibred/synchronised product; small but must be written once).

## Effort

Weeks; every other L7 file plugs into these two definitions.
