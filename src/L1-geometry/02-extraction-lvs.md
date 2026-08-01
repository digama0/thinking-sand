# L1/02 — Extraction and LVS

## Background

A layout is polygons; a netlist is transistors and wires. **Extraction** is the map between them — the recognition procedure that reads a circuit back out of geometry — and its key fact is a beautiful economy of the CMOS process: *a transistor is not drawn; it happens.* Wherever a polysilicon shape crosses an active (diffusion) region, the crossing **is** a MOSFET: the poly strip over the crossing is the gate, insulated from the silicon by the thin oxide grown between them; the two pieces of active region on either side are the source and drain; and the surrounding well determines whether it is the N-type or P-type flavour. Even the transistor's electrical parameters are geometric readings — channel length L is the width of the poly strip, channel width W the extent of the active region it crosses. Wires, likewise, are just the connected clumps of metal-and-via material. So extraction is: intersect two layers to find the devices, compute 3D connected components to find the nets, record which touches which.

**LVS** — "layout versus schematic" — is the industrial check built on extraction: extract the circuit from the drawn polygons and compare it, as a graph, against the intended netlist. The comparison is graph isomorphism, which is notoriously hard in general and easy here for a concrete reason the chapter explains: the graph's nodes are richly labelled (device types, W/L values, port names), and the labels shatter the graph into tiny equivalence classes before any search begins. A clean LVS run is the flow's certificate that *what was drawn is the circuit that was meant* — which, chained with [01](01-topology-preservation.md)'s sandwich theorem ("what is printed is topologically what was drawn"), yields the layer's full conclusion: what is printed is the circuit that was meant.

This chapter also owns a piece of honesty about [01](01-topology-preservation.md): writing the composition revealed that the sandwich theorem as stated covers *nets* but not *devices* — a printed distortion could in principle sever a transistor or detach a terminal without violating any net-level hypothesis — so the device-level analogues (D1)–(D3) are added here, and the enclosure/extension design rules find their formal role as exactly those hypotheses.

## Statement

The layout implements the intended netlist: `Ext(M(A)) ≅ N_intended`, an isomorphism of labelled graphs.

## The extraction map

Given a material distribution `M` ([00](00-layout-object.md)):

**Devices.** Connected components of `poly ∩ active`. Each is one MOSFET: the component is the **gate**, the two active regions it separates are **source and drain**, the surrounding well fixes the type. This is the sense in which *a transistor is the intersection of two rectangles* — visible directly in `inv_1`, where poly (0.430 µm wide) crosses diff (0.670 × 2.250 µm).

**Parameters.** `L` = the poly dimension across the channel, `W` = the active dimension along it. Both are **read off the geometry**, which is why the geometry family propagates into device parameters and hence into E1's enclosure. (On FinFET these quantise to fin counts — a strictly easier map, since the parameter is an integer.)

**Nets.** Connected components of `Cond(M)` — 3D, through vias.

**Incidence.** Which device terminals meet which nets.

`Ext(M)` is the resulting labelled bipartite graph.

## Theorem

> Under [01](01-topology-preservation.md)'s hypotheses (H1)–(H3), plus a device-level analogue (D1)–(D3) below:
>
> ```
> Ext(M(A)) ≅ Ext(M(D))    for every A in the sandwich
> ```
>
> so checking `Ext(M(D)) ≅ N_intended` on the **drawn** layout settles the **fabricated** one.

That composition is the soundness of LVS as actually practised, and it is the point of having 01 at all.

### A gap in 01, found by writing this

**01's stated conclusion includes "ν preserves incidence with device terminals", but the proof as given does not deliver it.** The proof handles *nets* — components of `Cond` — and says nothing about devices, which are components of `poly ∩ active` and perturb under their own sandwich.

What is needed is a device-level analogue:

- **(D1)** `(poly ∩ active) ⊖ B_r` has the same number of components as `poly ∩ active`, each nonempty and connected — i.e. no device is severed or split.
- **(D2)** distinct devices stay separated: `dist` between components exceeds the summed radii plus overlay. **Note this is a *different* rule from net spacing** — it is poly-over-active spacing, and it is why gate-to-gate and poly-extension rules exist.
- **(D3)** incidence is stable: a terminal that meets net `N` in `D` meets `ν(N)` in `A`. This does *not* follow from (D1)+(D2); it needs the source/drain active region to remain attached to its net under perturbation, which is what **enclosure and extension rules** supply.

(D3) is the interesting one: it is precisely where **line-end pullback** bites, since a poly line end that retracts can expose channel, and a contact that pulls back can detach a terminal. So the enclosure rules flagged in 01 as "systematic and directional" are the hypotheses of (D3), not of the net-level theorem.

**Action: 01's theorem statement should be weakened to nets only, with (D1)–(D3) added here.** Left as-is in 01 with a pointer, so the gap is visible rather than silently patched.

## Why the isomorphism check is easy

Graph isomorphism is hard in general and trivial here, for a specific reason: **label diversity**. Devices carry (type, W, L); nets carry names when they survive synthesis, and port nets carry them always. Refinement by labels partitions the graph into tiny cells before any search begins. Production LVS tools exploit exactly this and scale to hundreds of millions of devices.

So the difficulty is **not** the isomorphism. It is that `Ext` must be *well-defined*.

## The real obligations

**E1 (well-definedness).** `Ext(M)` picks out finitely many devices and nets, with unambiguous terminal assignment. Non-obvious cases that must be decided rather than inherited from tool behaviour:

- a poly shape crossing active **twice** ⟹ two devices sharing a gate net;
- poly over field oxide (no active beneath) ⟹ **no** device — this is why `npc` and field-poly layers exist;
- **abutted diffusion**: two devices sharing a source/drain region with no contact between, which is a normal and space-saving idiom, not an error;
- a device whose "two sides" are actually one connected active region (a poly ring) — must be excluded or given a convention.

**E2 (parameter tolerance).** Real LVS compares `W`/`L` up to a tolerance, so the statement is isomorphism *up to parameter windows* — and the windows must contain the whole geometry family, linking directly to 01's `r`.

**E3 (computability).** All predicates are polygon boolean operations plus connected components: near-linear with a scanline.

## First experiments

- Run `magic`/`netgen` LVS on `data/pdk/inv_1.gds` against its schematic and read the extracted device parameters. Two devices expected; check `W`, `L` against the measured geometry (poly 0.430 wide over diff 0.670 × 2.250).
- Enumerate which of E1's edge cases actually occur in the SKY130 HD library. If none do, the well-definedness obligation shrinks to a short list of excluded patterns.
- Attempt (D1)–(D3) on the same cell to size the device-level sandwich.

## Effort

Small relative to the rest of L1 — the algorithms are standard and the checking is cheap. The cost is in E1's conventions and in the (D1)–(D3) gap above, neither of which is deep, but both of which have to be *decided* rather than discovered.
