# Appendix: The platform assessment — why the target is changing

This book was scoped against Caravel: a fabricated, fully open SKY130 chip whose
every artifact — RTL, netlist, SDC, parasitics, GDS, signoff reports — is public
at a pinned commit. That was the right choice for a study whose thesis is *the
axiom ledger*, because it made the gap between "claimed" and "checkable"
measurable on a real object rather than a hypothetical one.

Working the checker phase to the point where the tools actually ran produced a
clear answer to a question the book had not asked directly: **can this platform
carry the whole tower?** The answer is no, and the reasons are worth recording,
because they are findings rather than inconveniences — and because the same
reasons point at what should replace it.

## What was established about Caravel

All of the following are measured, and each is pinned by a checker in
[Findings](findings.md) and the [Scoreboard](scoreboard.md).

**The shipped signoff does not reproduce from the shipped inputs.** Re-running
the `caravel_core` timing analysis from the committed netlist, the committed
SDC, the committed RCX parasitics and the Liberty from the open_pdks build the
chip was signed off with, OpenSTA reproduces the committed *nominal* hold number
to 0.01 ns (+0.59 against +0.58) — so the method is faithful — and then gives
**+1.29 ns with zero violating paths** at the slow corner that `signoff.rpt`
records as **failing**. Alongside it: **22,193 of the SPEF's 41,542 nets (53%)
name nets absent from the committed netlist**, so most parasitics never attach.
F1 is a documented reproducibility gap, and note the direction: this shows the
evidence is absent, not that the chip is unsound.

**The RTL's own provenance is broken.** `mgmt_core.v` records LiteX revision
`470fc6f`, which exists in no reachable repository; its migen pin predates the
file's commit by ten months; and its header format was retired from LiteX before
the file was committed. The build environment was stale and partly unpublished.

**The committed generator does not produce the shipped core.** `caravel.py` asks
for `cpu_variant="minimal+debug"`, which LiteX maps to the *uncached*
`VexRiscv_MinDebug`; the cached variant in the silicon was hand-added in a
separate 2021 commit and is not a target of the upstream generator at all. Its
invocation was recovered (`-d --iCacheSize 64` plus the documented MinDebug
flags), verified by a control that regenerates `MinDebug` byte-identically.

**The design and its harness cannot be brought to one era.** Regenerating the
core from a pinned modern generator gives a configuration-identical machine with
a *better* decoder — the reserved-accept set collapses from 4,292,609 words to
one — but leaves a 2026 core inside a 2021 enclosure, with the GDS, netlist,
parasitics and STA all describing the fabricated 2021 part. Rebuilding
`caravel_core` to close that gap ran into **eight distinct obstacles, seven of
them cleared** and the last an RTL property of the generated SoC (27
conflicting-initial-value errors). The full chain is recorded in
`flow/caravel_core/NOTES.md`.

**What did work, completely.** The core alone goes RTL → synthesis → placement →
CTS → routing → GDS → nine-corner signoff, with magic DRC 0, klayout DRC 0,
routing DRC 0 and LVS 0. The timing outcome is instructive: the *same three slow
corners fail as in 2021, for the opposite reason* — the modern flow fixes hold
everywhere by inserting 2,409 hold buffers and pays for it in setup. So the
pipeline is not the problem.

## Why the platform is nonetheless the wrong target

Three structural reasons, none of which more effort would fix.

**`caravel_core` is a harness, not a design under test.** The platform ships it
as a hardened macro precisely so that users consume it as GDS/LEF/LIB and place
their work in the user area. Rebuilding it means fighting the design's intent —
which is exactly why it dragged in fourteen missing macro models, an `inout`
blackbox limitation, and a pad frame nobody wanted to reason about.

**Pinning the old toolchain conflicts with the goal.** The endgame is to
*modify* the tools to emit certificates. A frozen container is a sealed box:
patching yosys inside one means reconstructing its 2023 dependency graph. The
modern flow is nix-built from source and can be patched. The certification
requirement therefore argues for all-modern, which in turn means giving up on
matching the fabricated part.

**The lower layers cannot follow.** L0–L3 reason about a specific GDS, netlist
and extraction. Retargeting the RTL without retargeting those makes L3's
netlist-versus-RTL equivalence name two different designs. Coherence requires
that everything be produced by one flow at one era — which is achievable, but
not while anchored to a 2021 artifact.

## What the replacement has to satisfy

One coherent artifact, understandable end to end, with nothing borrowed out of
position. Concretely: every layer's object produced by a flow we run, from
sources we can modify, at a single pinned era.

**The physical ceiling is fixed and low.** SKY130 and IHP's SG13G2 are both
130nm and GF180 is 180nm; no smaller open PDK exists. "Modern" can therefore
mean modern *microarchitecture* — out-of-order execution, branch prediction, an
MMU, a cache hierarchy, Linux capability — but never modern frequency. A complex
core at 130nm lands in the 50–150 MHz range.

**Memory area bounds fabrication, not the tower.** On-chip SRAM dominates the
die: at 0.142 mm² per KiB from the sky130 macro, cache and scratchpad outweigh
the logic they serve by roughly five to one in the configuration measured below.
That is a real constraint on what fits in a shuttle slot, and it is worth
stating as one — but it is not a constraint on the verification, and the two
should not be run together.

Two reasons. First, memory is the most *parametric* thing in the design: the
obligation is discharged against the macro and the banking that composes it,
and a proof that a 256×32 array meets its contract is not re-paid per bank. A
larger memory costs area and nothing else. Second, the subject is a **CPU, not a
computer**. `ChipLikeRocketConfig` already puts main memory — 4 GiB of it — off
the die, reached over serial TileLink through the pins. What the tower owes
there is the *protocol*: that the port's transactions mean what L5 says they
mean. The DRAM on the far side is somebody else's part, named as an external
assumption in the same register as the power-on reset, and its size is not a
number this book has to carry.

So the honest statement of the constraint is: on-chip memory sets how much of
the hierarchy can be *fabricated* at 130nm, while the pin protocol sets how much
has to be *proved*. Shrinking a cache buys silicon, not certainty.

**A physical object remains reachable.** Efabless closed in March 2025, but the
route recovered: ChipFoundry restored SKY130 MPW access, wafer.space added
GF180MCU, and Cadence began its own SKY130 shuttle. Current chipIgnite terms are
roughly $15k for 100 packaged parts on a ~5-month cycle, with the submission
being a **GDSII of the user area** — which is precisely what this project's flow
already emits.

**One harness solves the coherence problem exactly.** Of the offered templates,
**OpenFrame** (~15 mm², 44 GPIOs) contains *only* a padframe, a power-on-reset
circuit and a project-ID ROM — no SoC. Everything inside is the designer's. And
those three leftovers map onto things this book already treats as external: the
pad cells are PDK primitives of the same class as standard cells (L0/L1's
compact-model axioms), and the power-on reset is already an X4-class assumption
named in [L7/04](L7-system/04-power-epochs.md). Nothing lands out of position.
At 15 mm² the area budget is about forty times the 0.37 mm² our VexRiscv
occupied.

**The ecosystem has a centre of gravity, and it is not where we are.** Research
SoC work has consolidated on **Chisel + Chipyard**, with **CIRCT** — the
LLVM/MLIR hardware compiler — having replaced the Scala FIRRTL compiler as the
lowering path. That matters to this book specifically: [L4/04](L4-rtl-semantics/04-adequacy.md)
argues at length that a *specified* IR with a documented lowering would let the
RTL-semantics layer "shrink to nearly nothing," and names FIRRTL as the
unavailable counterfactual. It is no longer unavailable, and the modern form of
it is MLIR — the same infrastructure compiler-verification research already
uses. Verification has consolidated on **Verilator, cocotb and SymbiYosys**,
where this project's tooling already sits. SpinalHDL and LiteX, which the
Caravel target forced on us, are outside that mainstream.

## The decision

Move the target to a Chipyard-generated SoC, hardened by our own flow, in an
OpenFrame-style harness, with every revision pinned from the first commit.

What this costs, stated plainly: the F1 work and the reproducibility findings
demote from load-bearing tower content to a **standalone result about the state
of open silicon** — which is what they always deserved to be, and which is not
diminished by the move. L0–L2 re-base onto layout we produce, which is a gain.
The "fabricated chip" claim weakens to "fabricable," which the shuttle route
keeps honest.

What it buys: one artifact, one era, one flow, a specified IR under the
semantics layer, and a toolchain we can modify when the certification work
starts.
