# Reading list — getting up to speed

Introductory and canonical textbooks for the fields this project spans. The [BIBLIOGRAPHY](BIBLIOGRAPHY.md) cites *specific results* with verified identifiers; this list is pedagogy — books are given by author and title only (all are standard and easily found), linking to a BIBLIOGRAPHY entry where the same work is also cited. Each entry says what it is *for* here, tagged by layer.

The project's centre of gravity for a reader arriving from formal methods is the hardware and the physics; for a reader arriving from hardware, it is the opposite. The first four sections are the important ones.

## Computer architecture (L5–L7)

- **Harris & Harris, *Digital Design and Computer Architecture* (RISC-V edition)** — the single best on-ramp: gates → HDL → a working microarchitecture, in the project's own ISA. Read this and L5/00 becomes familiar territory.
- **Patterson & Hennessy, *Computer Organization and Design* (RISC-V edition)** — the standard first course, ISA-centric; the background for L6.
- **Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*** — the graduate text; caches, pipelines, speculation, OOO. Read it to understand what L5/00's absence table is *pricing* — everything in this book is something picorv32 doesn't have.

## Electrical engineering (L0, L2)

- **Agarwal & Lang, *Foundations of Analog and Digital Electronic Circuits*** — uniquely apt here: it *states the lumped-matter discipline as explicit assumptions* before using it, which makes it the informal ancestor of L0/04's composition theorem. The rare intro text that admits where circuit theory comes from.
- **Horowitz & Hill, *The Art of Electronics*** — the practical canon; what real circuits do in the space between the theorems. The supervisor/BOR/decoupling material of L7/04 is bench knowledge from here.
- **Sedra & Smith, *Microelectronic Circuits*** — the standard devices-to-amplifiers course; the MOSFET-as-circuit-element background for L0/02.

## Classical electromagnetism (L0/00–01, L1)

- **Griffiths, *Introduction to Electrodynamics*** — the undergraduate canon; everything L1's electrostatics needs, readably.
- **Purcell & Morin, *Electricity and Magnetism*** — the relativity-first treatment; the best answer to *why* magnetism is inevitable, and the right intuition for L0/01's EQS/MQS split.
- **Jackson, *Classical Electrodynamics*** — the graduate reference; boundary-value problems at the strength L1/03's enclosures actually require.
- **[Haus & Melcher](BIBLIOGRAPHY.md#haus-melcher-1989), *Electromagnetic Fields and Energy*** — the careful quasistatics treatment L0/01 leans on directly.

## Quantum theory and solid state (L0/02, L0/08)

For this project the solid-state route is the load-bearing one — the QFT that matters for devices is many-body condensed-matter theory, not particle physics.

- **Griffiths, *Introduction to Quantum Mechanics*** — the standard first course.
- **Ashcroft & Mermin, *Solid State Physics*** — the canon: band structure, effective mass, semiclassical transport — the physical content behind E1, and most of what L0/08's tower actually rests on.
- **Kittel, *Introduction to Solid State Physics*** — the lighter alternative.
- **Zee, *Quantum Field Theory in a Nutshell*** — the friendliest QFT entry point.
- **Peskin & Schroeder, *An Introduction to Quantum Field Theory*** (or **Schwartz, *Quantum Field Theory and the Standard Model***) — the standard course, either one.
- **Altland & Simons, *Condensed Matter Field Theory*** — field theory pointed at solids; the QFT that is actually adjacent to device physics.

## Semiconductor devices (L0/02)

- **Pierret, *Semiconductor Device Fundamentals*** — the introductory device course.
- **Taur & Ning, *Fundamentals of Modern VLSI Devices*** — the modern MOSFET in depth; what BSIM is a fit *of*.
- **[Sze & Ng](BIBLIOGRAPHY.md#sze-ng-2007), *Physics of Semiconductor Devices*** — the reference; avalanche and breakdown for L0/07.

## VLSI and the physical flow (L1–L3)

- **Weste & Harris, *CMOS VLSI Design*** — the whole industrial flow in one book: layout, DRC, timing, clocking, the cell library. The layers' industrial counterpart, and the fastest way to see what L1–L3 are formalising.
- **Rabaey, Chandrakasan & Nikolić, *Digital Integrated Circuits*** — devices → gates → wires; its interconnect and delay chapters are L2's background.
- **Bhasker & Chadha, *Static Timing Analysis for Nanometer Designs*** — the industrial practice that L2/02 makes sound.

## Mathematics of the lower layers (L0/00, L1/03)

- **Evans, *Partial Differential Equations*** — the standard graduate text; weak solutions and Lax–Milgram as L0/00 uses them.
- **Brezis, *Functional Analysis, Sobolev Spaces and Partial Differential Equations*** — the toolkit behind row 3 and L1/03's variational bounds.
- **Tucker, *Validated Numerics*** — a short introduction to rigorous computation; L0/03's method in miniature.
- **Moore, Kearfott & Cloud, *Introduction to Interval Analysis*** — the interval-arithmetic foundation under every enclosure in the book.
- **MacKay, *Information Theory, Inference, and Learning Algorithms*** — for L0/06's coding half; freely available and a pleasure.

## Formal methods (for the hardware reader)

- **Nipkow & Klein, *Concrete Semantics*** — operational semantics and machine-checked proof, hands-on; the mindset of L4–L5.
- **Kroening & Strichman, *Decision Procedures*** — SAT, SMT, bitvectors; L3's engine room.
- **Clarke, Grumberg, Kroening, Peled & Veith, *Model Checking*** — the standard text for the technique this project explicitly *cannot* use at scale (2^5774 states — L3/02) but borrows ideas from everywhere (IC3, invariants as certificates).
- **[Melham](BIBLIOGRAPHY.md#melham-1993), *Higher Order Logic and Hardware Verification*** — the historical centre of transistor-level formal verification; L0/09's ancestor.
