# L7/02 — The bus contract

## Background

A **bus** is the shared pathway over which a CPU reaches everything that is not itself: memories, peripherals, the outside world. "Reaching" something over a bus is a small protocol, not a single act. In this design the protocol is **TileLink**, the interconnect standard of the Rocket ecosystem: an agent issues a request on its **A channel** — opcode, address, size, a *source ID* tag — while a valid/ready handshake governs when the beat transfers; the fabric routes the request to the addressed device, and the response comes back on the **D channel**, tagged with the same source ID. Cycles spent waiting are called **wait states**. This channel pair is the entire vocabulary of the interface: everything the core ever learns about the outside world arrives as a D-channel beat with data attached.

The number of wait states varies wildly, and that variance is the crux of this chapter. The tightly-integrated data memory answers in a cycle or two. An instruction-cache refill from the boot ROM crosses the fabric — a handful of cycles. But an access to an address mapped behind the **serial TileLink port** leaves the chip: the transaction is serialised into 32-bit phits, clocked across the pads at the link's own (slower) clock, served by whatever agent sits on the far end, and returned the same way — easily dozens or hundreds of core cycles, with the exact count depending on the link clock ratio and the far agent. Academic verification work almost universally assumes memory answers instantly; that assumption is false of every real system, and a proof built on it says nothing about the fabricated chip.

The technique for handling an interface like this without verifying both sides at once is **assume-guarantee reasoning**, and it is used at every interface in this book, so it is worth stating carefully here at its first major appearance. Split the interface's obligations by *direction*: what the fabric promises the core (the *assume* half — requests get answered, answers are stable, fetches return the program's actual bytes), and what the core promises the fabric (the *guarantee* half — requests are well-formed, legal TileLink, source IDs managed, never exceeding the negotiated concurrency). The core's correctness proof (L5) *assumes* the first half and *proves* the second; the SoC-level proof (B2 in [01](01-boundary.md)) then *proves* the first half about the actual fabric, at which point the assumption is discharged and the two proofs compose into an unconditional statement. Each side's proof is finite and local; neither ever has to look inside the other. The one danger in this style — a circularity where each side's promise is justified only by the other's — is avoided here because the split is by polarity: no clause is simultaneously assumed and guaranteed by the same party.

One promise in the assume half is quietly the most important: not *that* requests are answered, but that they are answered **within a bound** `B`. Without a bound, "the processor executes the program" degenerates into "the processor executes the program if the memory ever answers" — a statement with no liveness content at all. Producing that single number (really, a function of the configuration and, for off-chip addresses, the far agent's contract) requires knowing the worst case of everything between the core and the addressed device, and is where this chapter earns its place in the tower.

## Statement

Author the contract at the tile's memory port — the formerly orphaned artifact L5 consumes. It is the *interface half of `Sys`*: what the fabric promises the core. Authored here, **assumed** by L5's refinement, **discharged** against the SoC RTL as part of B2.

> **Scope note.** The tile's ports speak **TileLink** ([L5/04](../L5-microarchitecture/04-buses-debug.md) has the guarantee halves); the clauses below are written in a generic request/response idiom and must be instantiated over the TileLink channel signals — the contract's shape (assume/guarantee split, the latency bound `B`, the off-chip worst case) is protocol-independent.

## The contract

Over the A/D channel pair at the tile boundary:

**Assume half (the fabric's promises, this file's content):**

```
A1  every request is answered:  an accepted A-beat gets its D-beat within B cycles
A2  D-channel data is valid and stable when the beat fires
A3  no spurious responses (every D-beat answers an outstanding A-beat,
    matching source ID; no duplication, no invention)
A4  fetches from the boot region return F's contents; accesses to
    serial-TileLink-mapped addresses behave per the far agent's contract
A5  reads/writes to memory-mapped devices behave per the memory map [03]
```

**Guarantee half** — the core's request discipline (legal TileLink: aligned addresses, permitted opcodes and sizes, source-ID management within the negotiated bounds) — is *morally part of the core's external spec* and is proved in [L5/04](../L5-microarchitecture/04-buses-debug.md); the contract is the assume-guarantee pair, split by polarity across the two layers.

## The latency bound B is load-bearing

Without `A1`'s bound, L5's measure does not exist and "instructions commit" silently weakens to "commit if the bus answers" — the refinement's liveness content hangs on this one number. `B`'s worst case is the **off-chip path**: an access mapped behind the serial TileLink port becomes a phit-serialised transaction — dozens to hundreds of core cycles, set by the link clock ratio and the far agent's response time. So `B` is not a constant but a function of the configuration — clock gating state, link clocking, and for off-chip addresses the X4 contract of the far end — one more register-dependent hypothesis, resolved the same way as the other configuration knobs ([05](05-operating-conditions.md)): either quantify over reachable configurations or declare the excess out of spec.

**Most academic work assumes a magic single-cycle memory — a load-bearing cheat this file exists to avoid.** The contract's entire point is that the fabric's real behaviour (wait states, arbitration among the tile, the debug module, and the inbound serial-link master; the DTIM's near-single-cycle path vs. the serial link's dozens) fits behind five clauses and one bound.

## Discharge at B2

Against the SoC RTL: the fabric between tile, memories, and peripherals is ordinary synchronous logic, so A1–A5 become invariant-style lemmas about it — with `A4`'s off-chip side remaining conditional on the far agent's model (X4's B3 batch) while the *bridge's* serialisation behaviour is B2-provable RTL. The split point (bridge proved, far agent assumed) should be marked in the clause itself.

## Obligations

1. The five clauses stated over the channel alphabet, with `B(config)` explicit.
2. Check against the tile's TileLink transactions in simulation (days — the L5-unblocking experiment).
3. The B2 discharge lemmas; the A4 split point marked.
4. Arbitration: whether an inbound serial-TileLink master or the debug module can starve the tile (an `A1` threat — if the fabric's arbitration admits starvation, `B` is conditional on those agents' quiescence, which must then be a recorded spec condition).

## Effort

Days to author; the discharge is B2 work. The arbitration check (4) is the one place a surprise could hide.
