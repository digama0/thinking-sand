# L5/04 — The buses and the debug module

## Background

This chapter proves the core's half of the bargains struck at its external ports. The general story — what a bus is, why memory latency varies, and how assume-guarantee reasoning splits an interface proof into promises proved by each side separately — is introduced in [L7/02](../L7-system/02-bus-contract.md)'s background, worth reading first; L7 authors the fabric's promises to the core, and here the core proves its own request discipline in return.

The protocol at the tile's ports is **TileLink**: requests on the A channel (opcode, address, size, source ID), responses on the D channel tagged with the matching source ID, valid/ready handshakes per beat, multi-beat bursts for transfers wider than the bus. The fetch side issues **cache-line refill bursts** — a line-aligned read streamed over consecutive beats; the data side issues the accesses the DTIM and the memory map serve, including the A extension's atomic operations, which TileLink carries as first-class opcodes rather than as read-modify-write sequences improvised by the master.

One more port exists that most tours omit: the **debug module**, through which an external agent over JTAG can halt the core, single-step it, and run abstract commands — reaching architectural state without going through the program. For refinement purposes it is a side door, and the standard treatment is the one L3/05 gives scan chains: state the theorem **conditional on the door staying shut**, and spec the door separately via the RISC-V debug specification's own register model when it is used.

## Statement

The tile's TileLink masters and the debug module, as contracts: what the core *guarantees* about its requests (proved here), what it *assumes* about responses (L7's contract, with its latency bound `B`), and the debug-inactive conditionality stated once.

## The instruction port

The I-cache's refill master. Guarantees, provable as invariant clauses ([02](02-invariant.md) clause 7):

```
Gi1  refills are well-formed: line-aligned base, legal size, a single
     source ID per outstanding refill, beats accepted per the handshake
Gi2  a refill, once started, is not abandoned (except by reset)
Gi3  fetch addresses are execute-region addresses (no device-region fetches)
```

Assumed: the D-beat within `B` per beat, data valid at the beat, boot-region reads return `F`'s contents (L7's A4, with the split between bridge-proved and far-agent-assumed marked there).

## The data port

The data-side master:

```
Gd1  requests are legal TileLink: aligned to their size, permitted opcodes,
     source IDs within the negotiated set, stable until accepted
Gd2  byte masks well-formed and consistent with the retiring access width
Gd3  no speculative writes: a store's request issues only for a retiring store
Gd4  atomic requests carry the correct AMO opcode and operand; an SC issues
     only against its own valid reservation
```

Gd3 is where the pipeline meets the memory: flushed instructions must not have touched the bus. The assumed half mirrors the instruction port's.

## The debug module

The standard debug architecture: a **debug module** on the peripheral bus, driven by a **debug transport module** that terminates the JTAG pins, with halt-request/resume/abstract-command machinery reaching the core. Two facts shape the treatment. First, the module's *register model is imported* — the RISC-V debug specification defines `dmcontrol`, `abstractcs`, and friends — so unlike a bespoke debug unit there is a document to be faithful to rather than semantics to author. Second, the module is also a **bus master**: system-bus access lets the external agent read and write memory directly, which is one of the load paths for `F` (L7/03). The refinement is stated **conditional on debug-inactive** (no halt request in flight, no abstract command executing); the conditionality is one hypothesis, threaded once through [01](01-refinement.md)'s statement. The hardware-side obligation here is only that *inactive means invisible* — a non-interference lemma of the same shape as [05](05-interrupts.md)'s masked-interrupt one.

## What the absences buy

No coherence protocol in flight (the tiny configuration's bus topology is incoherent by construction), no store buffer, no miss queues beyond the single refill: the memory system is a small set of masters with static discipline, and the whole arch-class topic "memory hierarchy" reduces to the contracts above plus one latency bound. The counterfactual — caches with miss queues, store buffers with forwarding, a coherence protocol — is priced in [00](00-microarchitecture.md)'s table; this file is the demonstration that the generated machine stays on the cheap side of it.

## Obligations

1. Gi1–Gi3 and Gd1–Gd4 as invariant clauses, with the simulation oracle re-run against this core first (execute a real image with the clauses asserted continuously; a clause that survives a real run is worth stating, and one that does not is found here rather than in a proof attempt).
2. The debug non-interference lemma, and the debug-inactive hypothesis threaded through the statement.
3. The burst-length/line-size agreement between the cache and the refill master (one constant, two readers — pin it in the configuration record).

## Effort

Weeks; the protocol clauses are IC3-shaped. The value is in the *statement discipline* — every later surprise about "what does the bus promise" lands here or in L7, never diffusely.
