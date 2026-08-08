# rocket-sram22 — the flow of record

Upstream's physical decisions (the 3588 × 2992 µm floorplan, five SRAM22 macro
instances with rotated placements) ported into librelane, whose per-step process
model fits this machine. `config.json` + `tools/build-rocket.sh` reproduce it;
run `gds3` is the run of record.

## Results

| | |
|---|---|
| die | 3588 × 2992 µm = **10.73 mm²** |
| synthesis | 50,354 cells; 5 SRAM22 instances (2× 2048×32, 2× 512×32, 1× 64×32) |
| detailed routing | **0 violations** (first fully clean route of this design) |
| timing | **all nine corners pass** at 100 ns: hold +0.05…+0.26 ns, setup +25.6…+28.3 ns |
| timing caveat | 19,110 max-slew / 1,145 max-cap / 1,817 max-fanout violations — F2 open (see below) |
| BEOL DRC (KLayout, tiled) | **150 flow-owned violations, all at macro interfaces**; 89,931 macro-internal bitcell hits belong to the SRAM22 collateral |
| LVS | not run — Magic cannot read SRAM22 GDS (`sky130_fd_bd_sram` cells, layer 64/44); needs a non-Magic extraction route |

The clock choice is the book's own conservative-verification move made concrete:
at 50 ns the design passes hold everywhere but fails setup on unrepaired
high-fanout nets (worst path ~83 ns); at 100 ns it closes outright. The repair
step that would fix those nets is unrunnable (below), so the slow clock buys
closure at the price of frequency — 10 MHz, honestly labeled.

## The resizer memory pathology

OpenROAD's `repair_design` retains ~600 KB **per iteration** (not per repair —
a synthesis-side fanout cap cut repairs 4× but left the growth curve identical),
reaching 25 GiB on this design's ~62k-violation queue and getting OOM-killed
at the same iteration in four consecutive runs across two flows. Hammer's
timing-driven global placement dies the same way (it runs the resizer
internally, in one process carrying all of P&R). One of these kills took the
whole machine down. Mitigations that stuck: every flow launch runs under
`ulimit -v`; `SYNTH_ABC_BUFFERING` + `MAX_FANOUT_CONSTRAINT 10` at synthesis;
the repair step skipped and priced (the F2 rows above).

## DRC engineering (the file `sky130A_mr_tiled.drc`)

The PDK deck as shipped cannot verify this design on a 32 GB machine:

* **Monolithic deep mode needs >14 GiB** and 5–16 h; it died twice in the
  16M-polygon `mcon` block (once taking the box down, once against its cap
  after degrading — threads failing to spawn at the address-space ceiling).
* The repo copy enables the deck's own commented-out **tiling** (500 µm tiles,
  10 µm borders, `deep` off): peak 2.5 GB, 1 h 44 m, same rule content.
* **`sram_exclude` defaults to false and librelane never passes it** — and it
  would not matter here: the exclusion guards FEOL rules only, the BEOL section
  has none, and SRAM22's GDS carries no `areaid` waiver markers at all. Bitcell
  geometry is therefore logic-rule-checked no matter what; the 89,931
  macro-internal hits are that artifact, separated from the flow's 150 by
  coordinate clustering against the macro boxes (the triage that took minutes
  and belongs in the layer checker).
* FEOL is deliberately not re-checked on the assembled die: cell-internal
  geometry is the library's and the generator's pre-verified collateral — the
  amortisation argument L1 makes, applied.

## Signoff coverage for SRAM22 designs, summarized

Magic: cannot parse the macro GDS (hard stop). KLayout: works, but only with
deck surgery (tiling) on ordinary hardware, and with no waiver mechanism for
the bitcells. Netgen LVS: blocked on Magic extraction. Upstream's own flow
sets `drc.magic.generate_only: true` — they never ran Magic on it either.
This is F8's theme at ecosystem scale: for macro-bearing sky130 designs,
open-tools signoff is one engine deep exactly where it claims to be redundant.
