# L7/00 — `Sys(F)` and `obs`: the two definitions

## Background

A specification, in the sense used throughout this book, is a *set of allowed behaviours*, and a behaviour is a **trace**: a sequence of observations over time. To specify a machine you must therefore first answer a question that sounds trivial and is not: *observations of what?* A program's variables are not observable — they are an abstraction maintained by the processor. The processor's registers are not observable either — they are voltages on wires buried under many layers of metal. The only physical interface a chip has is its **pads**: the few dozen metal contacts around the die's edge that the package's pins bond to. Everything the chip will ever do to the world, it does by moving pad voltages; everything the world does to the chip arrives the same way. So the top-level specification must ultimately be a set of allowed *pad-voltage histories*, and this chapter defines both sides of that statement: `Sys(F)`, the allowed set, and `obs`, the function that turns a physical run of the die into a trace that can be compared against it.

To see what has to go into `Sys`, look at what surrounds the processor core. This chip has no screen or keyboard; it talks to the world through a handful of serial interfaces, each of which is a small machine in its own right. Bulk data crosses the boundary over the **serial TileLink port**: on-chip bus transactions are cut into 32-bit *phits* and shifted across the pads under the link's own clock, so a single off-chip memory access takes dozens of core cycles — and the same port, driven from outside, is how a host can write a program image into the chip's memory before releasing it to run. Text output leaves over a **UART** (universal asynchronous receiver-transmitter), the simplest serial protocol there is: one wire, held high when idle, on which each byte is sent as a *start bit* (a 1→0 drop that announces "byte coming"), eight data bits, and a *stop bit*, each lasting one *bit cell* whose duration is set by the agreed **baud rate**. There is no shared clock — the receiver times the bit cells with its own clock, which is why clock accuracy (P6) will do real work in this chapter. A **JTAG** port reaches the standard RISC-V debug module — a five-wire agent that can halt the core, read its registers, and write memory, which makes it both a load path for `F` and a spec-visible actor. Finally, a **`custom_boot`** pin selects the boot behaviour, and a **clock tap** pin exports an observable copy of the internal clock. Pad functions in this design are *fixed* — there is no pin-multiplexing machinery — which removes a whole class of configuration-indexed observation problems before they start.

Two properties of trace sets do heavy lifting here and deserve their plain-language forms up front. **Refinement** (`⊑`) is the statement "every behaviour of the implementation is an allowed behaviour of the spec" — nothing more; where the spec offers several options (nondeterminism), the implementation may take any. **Prefix closure** is the property that if a trace is allowed, so is every initial segment of it — in other words, *the spec never forbids stopping*. That sounds like a technicality until you remember that this machine's power can vanish at any instant: a spec that promised "the UART will print `hello`" unconditionally would be falsified by pulling the plug mid-`hell`. Prefix-closed specs make power loss survivable by construction, and the price — the spec can never promise that anything *will* happen, only that whatever happens is right — is repaid by attaching an explicit time bound `T` to every liveness claim ("if powered through cycle N, the byte has appeared").

One more translation. The pad voltage is an analog quantity; calling it "0" or "1" is a claim, not a measurement. L0 defines the *regimes* — voltage-and-stability conditions under which a node counts as logic 0, logic 1, or neither — and `obs` classifies pad samples through those regimes. Where no regime applies (mid-transition, during power ramps), the trace records that honestly rather than rounding to a bit.

## Statement

Define the two objects the overview's top-level statement quantifies over — the map from architecture to pad-level observable behaviour that, before this layer existed, the overview used while nobody defined it.

```
Sys(F)  =  traces at the pads of:
             ISA (L6)                          the core's contract
           ⊕ SoC memory map                    what each address means      [03]
           ⊕ serial TileLink bridge model      off-chip traffic, phits     [02, 03]
           ⊕ UART model                        the observable output channel [03]
           ⊕ boot machinery (ROM, boot-address the load paths for F, and
             register, custom_boot, debug)     the first fetch             [03]

obs(d,F,E)  =  the physical trace: sampled pad voltages of die d,
               classified through L0's regimes, at L2's clock granularity
```

Both are definitions; the theorem connecting them is the whole rest of the repository.

## The trace alphabet — the load-bearing choice

`obs` is defined at the **physical alphabet**: timed, regime-classified pad samples. This is forced, not stylistic, by the epoch analysis ([04](04-power-epochs.md)): an epoch ends in `valid-prefix · ramp-down-tail`, and prefix closure — the property that lets a machine *stop* without violating anything — holds at the physical level only. A truncated byte is a prefix of a timed trace but not of any byte sequence, so **abstract views (bytes, phits, transactions) are derived, never primitive**, or epoch composition is unstatable. (The tail is demonic — adversarially unconstrained, the spec holding under *every* resolution — only without supervisor + fail-safe-pad discipline; with them it refines to a *specified* truncate-idle-decay shape — [04](04-power-epochs.md).)

Consequences worth pinning:

- **The UART channel is a timed trace against the baud clock** — bit cells, start/stop framing — with P6's clock-accuracy bound doing quantitative work in the derivation of the byte view. Where framing errors land (open problem: garbage byte vs. excluded-by-derivation) is a real spec decision.
- **The serial TileLink channel is a timed trace against the link clock** — its phit view and transaction view are two more floors of the same derivation stack, with the clock-domain crossing between link clock and core clock as the validity condition.
- **Start of trace**: from power-on reset; the boot window before reset release is spec'd by the pads' reset-state defaults and the boot machinery ([04](04-power-epochs.md)'s boot-window promise), not demonic.

## Refinement shape

`obs(d,F,E) ⊑ Sys(F)` is trace refinement up to stuttering at the physical alphabet, prefix-closed, with liveness expressed as bounded progress (every claim carries its `T`). The ε-conditioning lives at the overview's †-lines, not here — `Sys` itself is a deterministic-spec-with-nondeterminism object, never probabilistic.

## Obligations

1. The alphabet definition: sampling, regime classification, the per-pad fixed interpretations.
2. The derivation stack: physical → bit-cell → byte → "the UART printed *hello*" (and physical → phit → TileLink transaction), each level with its validity conditions.
3. The `Sys` composition operator itself — how ISA steps, memory-map reads, and device models join into one trace set (the fibred/synchronised product; small but must be written once).

## Effort

Weeks; every other L7 file plugs into these two definitions.
