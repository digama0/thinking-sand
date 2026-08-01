# L7/02 — The bus contract

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
