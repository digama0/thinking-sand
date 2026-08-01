# L7/02 — The bus contract

## Background

A **bus** is the shared pathway over which a CPU reaches everything that is not itself: memory, the flash controller, the UART. "Reaching" something over a bus is a small protocol, not a single act. In picorv32's native protocol, the core raises a signal called `mem_valid` while presenting an address (and, for a store, data); the surrounding fabric does whatever is needed to serve the request — which may take one clock cycle or many — and raises `mem_ready` when the answer is present. Cycles spent waiting are called **wait states**. This valid/ready **handshake** is the entire vocabulary of the interface: everything the core ever learns about the outside world arrives as a `ready` with data attached.

The number of wait states varies wildly, and that variance is the crux of this chapter. On-chip RAM answers in a cycle. But an instruction fetch that has to go to the external flash chip becomes a serial SPI transaction — command byte, address bytes, then the data, shifted a few bits per clock — easily dozens of core cycles, with the exact count depending on how the flash controller is configured. Academic verification work almost universally assumes memory answers instantly; that assumption is false of every real system, and a proof built on it says nothing about the fabricated chip.

The technique for handling an interface like this without verifying both sides at once is **assume-guarantee reasoning**, and it is used at every interface in this book, so it is worth stating carefully here at its first major appearance. Split the interface's obligations by *direction*: what the fabric promises the core (the *assume* half — requests get answered, answers are stable, flash reads return the program's actual bytes), and what the core promises the fabric (the *guarantee* half — requests are well-formed, held stable until answered, never overlapping). The core's correctness proof (L5) *assumes* the first half and *proves* the second; the SoC-level proof (B2 in [01](01-boundary.md)) then *proves* the first half about the actual fabric, at which point the assumption is discharged and the two proofs compose into an unconditional statement. Each side's proof is finite and local; neither ever has to look inside the other. The one danger in this style — a circularity where each side's promise is justified only by the other's — is avoided here because the split is by polarity: no clause is simultaneously assumed and guaranteed by the same party.

One promise in the assume half is quietly the most important: not *that* requests are answered, but that they are answered **within a bound** `B`. Without a bound, "the processor executes the program" degenerates into "the processor executes the program if the memory ever answers" — a statement with no liveness content at all. Producing that single number (really, a function of the flash controller's configuration) requires knowing the worst case of everything between the core and the flash chip, and is where this chapter earns its place in the tower.

## Statement

Author the contract at the core's memory port — the formerly orphaned artifact L5 consumes. It is the *interface half of `Sys`*: what the fabric promises the core. Authored here, **assumed** by L5's refinement, **discharged** against the SoC RTL as part of B2.

## The contract

Over picorv32's native valid/ready handshake (with the look-ahead variant's consistency handled on the core side — L5/04's `LA` lemma):

**Assume half (the fabric's promises, this file's content):**

```
A1  every request is answered:  mem_valid ⟹ mem_ready within B cycles
A2  mem_rdata is valid and stable when mem_ready
A3  no spurious ready (ready only in response to a request)
A4  reads from flash-mapped addresses return F's contents,
    through the XIP controller's wait-state behaviour
A5  reads/writes to RAM/peripheral addresses behave per the memory map [03]
```

**Guarantee half** — the core's request discipline (G1–G3: stable-until-ready, well-formed strobes, no overlapping requests) — is *morally part of the core's external spec* and is proved in [L5/04](../L5-microarchitecture/04-memory-pcpi.md); the contract is the assume-guarantee pair, split by polarity across the two layers.

## The latency bound B is load-bearing

Without `A1`'s bound, L5's measure does not exist and "instructions commit" silently weakens to "commit if the bus answers" — the refinement's liveness content hangs on this one number. `B`'s worst case is the **XIP path**: an instruction fetch missing the (config-dependent) prefetch means an SPI transaction — dozens of core cycles, wait states set by the flash's speed grade and the controller's mode bits. So `B` is not a constant but a function of the XIP configuration — one more register-dependent hypothesis in the F4/F6 family, resolved the same way ([05](05-operating-conditions.md)): either quantify over reachable XIP configs or declare the excess out of spec.

**Most academic work assumes a magic single-cycle memory — a load-bearing cheat this file exists to avoid.** The contract's entire point is that the fabric's real behaviour (wait states, arbitration with the housekeeping port, RAM's single-cycle path vs. flash's dozens) fits behind five clauses and one bound.

## Discharge at B2

Against the SoC RTL: the fabric between core and DFFRAM/XIP/housekeeping is ordinary synchronous logic, so A1–A5 become invariant-style lemmas about it — with `A4`'s flash side remaining conditional on the flash device model (X4's B3 batch) while the *controller's* wait-state generation is B2-provable RTL. The split point (controller proved, device assumed) should be marked in the clause itself.

## Obligations

1. The five clauses stated over the handshake alphabet, with `B(config)` explicit.
2. Check against picorv32's own testbench transactions (days — the L5-unblocking experiment).
3. The B2 discharge lemmas; the A4 split point marked.
4. Arbitration: whether housekeeping's flash pass-through can starve the core (an `A1` threat — if the arbiter admits starvation, `B` is conditional on housekeeping quiescence, which must then be a recorded spec condition).

## Effort

Days to author; the discharge is B2 work. The arbitration check (4) is the one place a surprise could hide.
