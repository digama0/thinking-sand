# Data provenance — the generated artifact stack

**Nothing is fetched that can be generated.** The book's artifacts — RTL, netlist, constraints, layout, reports — are produced by the flow in this repository from pinned sources. The repo-root `data/` and build directories are gitignored; regenerate rather than trust.

## Pins — deliberately, exactly

| component | what | pin |
|---|---|---|
| Chipyard | the SoC framework: generators, Hammer, the tutorial flow configs | commit `e27c6561c0066c1f60bf4eb4885a38391c850ac0` (2026-07-27) |
| firtool (CIRCT) | FIRRTL → SystemVerilog | release `1.75.0`, sha256-pinned binary |
| SRAM22 macros | the sky130 SRAM collateral (LEF/GDS/lib/SPICE/Verilog) | `rahulk29/sram22_sky130_macros` master `75cbe961` (2026-05-06) |
| Hammer | the physical-design driver | `hammer-vlsi 1.2.0` (with the compatibility patches recorded in [findings](findings.md)) |
| PDK | sky130A via ciel | open_pdks build `8afc8346a57fe1ab7934ba5a6056ea8b43078e71` |
| riscv-opcodes | the standard's machine-readable encodings (L6/03's spec side) | pinned SHA in the fetch script |
| EDA tools | yosys, OpenROAD, Magic, KLayout, Netgen, OpenSTA, Verilator | version-pinned, checksum-verified installs via `tools/install-toolchain.sh` |

Refs are commit SHAs, not branches. The findings quote exact instance counts, census numbers, and report values from artifacts these pins produce; a floating ref would silently invalidate all of it. **If you bump a pin: re-run the flow, re-run the checkers, and re-derive Findings — never one without the other.**

Two provenance facts worth stating as facts rather than policy:

- **The chain has one root.** Every layer's artifact descends from one elaboration of one pinned configuration — the property F7 names, kept true by the re-elaboration diff (L4/04) rather than assumed.
- **The pins decay.** The upstream flow did not run against current components without patches ([findings: upstream flow drift](findings.md#upstream-flow-drift)); the patches are recorded, small, and applied to open code. This is the cost — and the point — of choosing patchable-modern over frozen-container: nothing is hidden behind a working binary.

## What the flow produces

```
generated-src/            the elaboration: FIRRTL, SystemVerilog, device tree,
                          per-device register maps, memory configuration
syn-rundir/               ChipTop.mapped.v (the netlist N), ChipTop.mapped.sdc,
                          synthesis reports
par-rundir/               floorplan, placement, CTS, routing, ChipTop.gds,
                          extraction, timing reports
signoff                   DRC (two engines), LVS, multi-corner STA
```

The book's layer subjects map onto these: L4 reads the SystemVerilog (and its FIRRTL ancestor), L3 the mapped netlist, L2 the SDC and timing reports, L1 the GDS and extraction, L7/L6/L5 the elaboration's metadata and the RTL.

## Tools that consume this

The per-layer scoreboards `tools/check-l0.py` … `check-l7.py` (run all via `tools/check-all.py`; rendered into the book as the [scoreboard](scoreboard.md)) drive the extractors. The suite is being re-anchored to the generated artifacts; the scoreboard names each checker's status honestly — a checker that has not run against the current artifacts reports TODO, not a stale PASS.

| role | consumes | produces |
|---|---|---|
| RTL census | the emitted SystemVerilog | L4/01's construct table, as a regression |
| netlist graph checks | `ChipTop.mapped.v` | W1–W4 (L3/01) |
| clock/domain census | netlist + SDC | L2/04's completeness table, L2/05's gating census |
| memory-map diff | RTL decode + device tree + regmaps | L7/03's three-way diff |
| decoder extraction | the emitted core | L6/03's partition |
| configuration record | elaboration metadata + RTL | the record L4–L6 scope against |
| flow runner | all pinned sources | the artifact stack above, reproducibly |

## The analysis toolchain — pinned for the same reason

[`tools/install-toolchain.sh`](https://github.com/digama0/thinking-sand/blob/master/tools/install-toolchain.sh) installs the EDA tools **version-pinned and sha256-verified**, on the same principle as the sources: a number in Findings produced by a floating tool is a number nobody can reproduce. A checksum mismatch aborts the install; re-running is idempotent.

Installing a tool does not discharge an obligation — it removes the precondition. The scoreboard rows stay `TODO` until a checker actually uses the tool.
