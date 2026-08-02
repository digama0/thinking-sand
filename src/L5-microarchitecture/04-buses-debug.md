# L5/04 — The buses and the debug port

## Background

This chapter proves the core's half of the bargains struck at its external ports. The general story — what a bus is, why memory latency varies, and how assume-guarantee reasoning splits an interface proof into promises proved by each side separately — is introduced in [L7/02](../L7-system/02-bus-contract.md)'s background, worth reading first; L7 authors the fabric's promises to the core, and here the core proves its own request discipline in return.

The protocol at both ports is **Wishbone**, the open-source SoC bus the LiteX ecosystem standardises on: a master raises `CYC` (a bus cycle is in progress) and `STB` (a transfer is requested) with address, data, and byte-select lines, and the slave answers with `ACK` (or `ERR`); cycles the slave spends not answering are the wait states. The instruction port additionally uses Wishbone's **registered-feedback burst** signalling (`CTI`/`BTE`): the master announces an incrementing burst — here, a cache-line refill — so the slave can stream consecutive words without per-beat re-arbitration. The data port issues plain single-beat transactions, one outstanding at a time.

One more port exists that most tours omit: the **debug bus**, through which an external agent can halt the core, single-step it, and inject instructions — reaching architectural state without going through the program. For refinement purposes it is a side door, and the standard treatment is the one L3/05 gives scan chains: state the theorem **conditional on the door staying shut**, and spec the door separately if it is ever to be used.

## Statement

The core's two Wishbone masters and the debug port, as contracts: what the core *guarantees* about its requests (proved here), what it *assumes* about responses (L7's contract, with its latency bound `B`), and the debug-inactive conditionality stated once.

## The instruction port

[`IBusCachedPlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/IBusCachedPlugin.scala)'s refill master. Guarantees, provable as invariant clauses ([02](02-invariant.md) clause 7):

```
Gi1  bursts are well-formed: CYC/STB held, incrementing CTI/BTE discipline,
     line-aligned base, fixed length (one cache line = 8 beats)
Gi2  a burst, once started, is not abandoned (except by reset)
Gi3  fetch addresses are execute-region addresses (no data-region fetches)
```

Assumed: `ACK` within `B` per beat, `DAT` valid at `ACK`, flash-region reads return `F`'s contents (the XIP path — L7's A4, with the split between controller-proved and flash-assumed marked there).

## The data port

[`DBusSimplePlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/DBusSimplePlugin.scala)'s single-beat master:

```
Gd1  one outstanding transaction; CYC/STB/address/data stable until ACK/ERR
Gd2  byte selects well-formed and consistent with the retiring access width
Gd3  no speculative writes: a store's beat issues only for a retiring store
```

Gd3 is where the pipeline meets the memory: flushed instructions must not have touched the bus. The assumed half mirrors the instruction port's, minus bursts.

## The debug port

[`DebugPlugin`](https://github.com/SpinalHDL/VexRiscv/blob/master/src/main/scala/vexriscv/plugin/DebugPlugin.scala) exposes halt/step/injection over a bus mastered (in the [shipped SoC](https://github.com/efabless/caravel_mgmt_soc_litex/blob/503eda0790085712ffef7f4ad8934c7daed3237f/verilog/rtl/mgmt_core.v)) by a LiteX CSR bridge — so *software on the same SoC* can drive its own core's debug port, and the plugin's `resetOut` feeds back into the core's reset. The refinement is stated **conditional on debug-inactive** (no halt request, no injection, `resetOut` low); the conditionality is one hypothesis, threaded once through [01](01-refinement.md)'s statement. Whether the shipped firmware ever exercises the port is a `Sys(F)`-level fact; the hardware-side obligation here is only that *inactive means invisible* — a non-interference lemma of the same shape as [05](05-interrupts.md)'s masked-interrupt one.

## What the absences buy

No coprocessor port, no cache-coherence traffic, no outstanding-transaction queue: the entire memory system is two masters with static discipline, and the whole arch-class topic "memory hierarchy" reduces to the contracts above plus one latency bound. The counterfactual — caches with miss queues, store buffers with forwarding — is priced in [00](00-microarchitecture.md)'s table; this file is the demonstration that the shipped machine stays on the cheap side of it.

## Obligations

1. Gi1–Gi3 and Gd1–Gd3 as invariant clauses; check them first by simulation against the SoC's own testbenches (cheap oracle, shared with L4/04's harness).
2. The debug non-interference lemma, and the debug-inactive hypothesis threaded through the statement.
3. The burst-length/line-size agreement between the cache and the refill master (one constant, two readers — pin it in the [configuration record](../tools/config-record.py)).

## Effort

Weeks; the protocol clauses are IC3-shaped. The value is in the *statement discipline* — every later surprise about "what does the bus promise" lands here or in L7, never diffusely.
