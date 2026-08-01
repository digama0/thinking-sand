# L7/00 — `Sys(F)` and `obs`: the two definitions

## Background

A specification, in the sense used throughout this book, is a *set of allowed behaviours*, and a behaviour is a **trace**: a sequence of observations over time. To specify a machine you must therefore first answer a question that sounds trivial and is not: *observations of what?* A program's variables are not observable — they are an abstraction maintained by the processor. The processor's registers are not observable either — they are voltages on wires buried under fifteen layers of metal. The only physical interface a chip has is its **pads**: the few dozen metal contacts around the die's edge that the package's pins bond to. Everything the chip will ever do to the world, it does by moving pad voltages; everything the world does to the chip arrives the same way. So the top-level specification must ultimately be a set of allowed *pad-voltage histories*, and this chapter defines both sides of that statement: `Sys(F)`, the allowed set, and `obs`, the function that turns a physical run of the die into a trace that can be compared against it.

To see what has to go into `Sys`, look at what surrounds the processor core. A microcontroller has no screen or keyboard; it talks to the world through a handful of serial protocols, each of which is a small machine in its own right. The program itself lives in an external **flash memory chip** — a separate physical part on the board — reached over **SPI** (Serial Peripheral Interface), a protocol in which the controller wiggles a clock wire and shifts data one bit per clock edge; fetching a single instruction this way takes dozens of processor cycles. The arrangement where the CPU fetches instructions directly out of external flash on demand, rather than copying the program into RAM first, is called **XIP** ("execute in place"), and it is how this chip runs. Text output leaves over a **UART** (universal asynchronous receiver-transmitter), the simplest serial protocol there is: one wire, held high when idle, on which each byte is sent as a *start bit* (a 1→0 drop that announces "byte coming"), eight data bits, and a *stop bit*, each lasting one *bit cell* whose duration is set by the agreed **baud rate**. There is no shared clock — the receiver times the bit cells with its own clock, which is why clock accuracy (P6) will do real work in this chapter. Finally, the general-purpose pins (**GPIO**) are software-configurable: the same physical pad can be an input, an output, or a UART line depending on configuration registers. The meaning of a pad voltage therefore depends on state — a fact `obs` has to carry explicitly.

Two properties of trace sets do heavy lifting here and deserve their plain-language forms up front. **Refinement** (`⊑`) is the statement "every behaviour of the implementation is an allowed behaviour of the spec" — nothing more; where the spec offers several options (nondeterminism), the implementation may take any. **Prefix closure** is the property that if a trace is allowed, so is every initial segment of it — in other words, *the spec never forbids stopping*. That sounds like a technicality until you remember that this machine's power can vanish at any instant: a spec that promised "the UART will print `hello`" unconditionally would be falsified by pulling the plug mid-`hell`. Prefix-closed specs make power loss survivable by construction, and the price — the spec can never promise that anything *will* happen, only that whatever happens is right — is repaid by attaching an explicit time bound `T` to every liveness claim ("if powered through cycle N, the byte has appeared").

One more translation. The pad voltage is an analog quantity; calling it "0" or "1" is a claim, not a measurement. L0 defines the *regimes* — voltage-and-stability conditions under which a node counts as logic 0, logic 1, or neither — and `obs` classifies pad samples through those regimes. Where no regime applies (mid-transition, during power ramps), the trace records that honestly rather than rounding to a bit.

## Statement

Define the two objects the overview's top-level statement quantifies over. The ISA is not the top: an ISA transition system does not produce pad traces, and the map from architecture to observable behaviour goes through everything the SoC wraps around the core. Before L7 existed, that map was used by the overview while being defined by nobody.

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

`obs(d,F,E) ⊑ Sys(F)` is trace refinement up to stuttering at the physical alphabet, prefix-closed, with liveness expressed as bounded progress (every claim carries its `T`). The ε-conditioning lives at the overview's †-lines, not here — `Sys` itself is a deterministic-spec-with-nondeterminism object, never probabilistic.

## Obligations

1. The alphabet definition: sampling, regime classification, per-pad configuration indexing.
2. The derivation stack: physical → bit-cell → byte → "the UART printed *hello*", each level with its validity conditions.
3. The `Sys` composition operator itself — how ISA steps, memory-map reads, and device models join into one trace set (the fibred/synchronised product; small but must be written once).

## Effort

Weeks; every other L7 file plugs into these two definitions.
