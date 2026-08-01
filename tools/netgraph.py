#!/usr/bin/env python3
"""Structural obligations on a SKY130 gate-level netlist (L0/09, L3 well-formedness).

Checks, in the order the documents cite them:
  W1  every net has exactly one driver          (no contention  -> V1)
  W2  every read net has a driver               (no floating reads)
  W3  no combinational cycle                    (acyclicity; every bistable inside a cell)
  W4  physical-only cells touch rails only      (inertness, licences the 85% deletion)

Usage: netgraph.py <gate-level.v> [--top MODULE]

Pin directions are declared explicitly below rather than guessed; any pin name not in
the table is reported and the run fails, because a silently misclassified pin would turn
a real contention into a clean bill of health.
"""
import re, sys, collections

OUT = {'X', 'Y', 'Q', 'Q_N', 'HI', 'LO', 'COUT', 'COUT_N', 'SUM', 'GCLK',
       'Z'}   # Z: output of einvn/einvp, the tri-state enabled inverters
PWR = {'VPWR', 'VGND', 'VNB', 'VPB', 'KAPWR', 'LOWLVPWR', 'VPWRIN'}
IN = {'A', 'A0', 'A1', 'A2', 'A3', 'A4', 'A_N', 'A1_N', 'A2_N', 'B', 'B1', 'B2',
      'B_N', 'B1_N', 'B2_N', 'C', 'C1', 'C_N', 'D', 'D1', 'D_N', 'S', 'S0', 'S1',
      'CLK', 'CLK_N', 'RESET_B', 'SET_B', 'GATE', 'GATE_N', 'SLEEP', 'SLEEP_B',
      'DE', 'TE', 'TE_B', 'SCD', 'SCE', 'NOTIFIER', 'DIODE', 'CIN', 'M', 'H'}
# cells that cut the graph (contain a bistable): flops, latches, clock gates
SEQ = re.compile(r'__(sdf|df|edf|dl|sedf|dlrtp|dlxtp|dlclk|dlyg)')
# NB: conb_1 is NOT here -- it is a constant *generator* (drives HI/LO), so it is a
# functional cell with a signal output, not an inert filler. W4 caught this
# misclassification on its first run, which is the check working as intended.
PHYS = re.compile(r'__(decap|fill|tapvpwrvgnd|tap_|diode)')
# tri-state drivers: may legitimately share a net, so W1 must not count them as contention
TRI = re.compile(r'__(einv|ebuf)')


def parse(path):
    txt = open(path, errors='replace').read()
    inst = re.compile(r'(sky130_\w+)\s+(\\?\S+?)\s*\(([^;]*?)\)\s*;', re.S)
    conn = re.compile(r'\.(\w+)\s*\(\s*([^)]*?)\s*\)')
    out = []
    for m in inst.finditer(txt):
        pins = [(p, n.strip()) for p, n in conn.findall(m.group(3))]
        out.append((m.group(1), m.group(2), pins))
    ports = set()
    pm = re.search(r'\bmodule\s+\w+\s*\((.*?)\)\s*;', txt, re.S)
    if pm:
        ports = {t.strip().lstrip('\\') for t in pm.group(1).split(',') if t.strip()}
    return out, ports, txt


def main():
    path = sys.argv[1]
    insts, ports, txt = parse(path)
    print(f'{path}: {len(insts):,} instances, {len(ports)} top-level ports\n')

    unknown = collections.Counter()
    drivers = collections.defaultdict(list)   # net -> [(cell, inst, pin)]
    readers = collections.defaultdict(list)
    edges = collections.defaultdict(set)      # net -> {nets it combinationally drives}
    phys_bad = []
    ncells = collections.Counter()

    for cell, name, pins in insts:
        ncells[cell] += 1
        ins, outs = [], []
        for p, net in pins:
            if p in PWR:
                continue
            elif p in OUT:
                outs.append(net); drivers[net].append((cell, name, p))
            elif p in IN:
                ins.append(net); readers[net].append((cell, name, p))
            else:
                unknown[p] += 1
        if PHYS.search(cell):
            # inertness: a physical-only cell must have no signal pins at all.
            # (antenna diodes have a DIODE pin, which is a pure load -- allowed)
            sig = [p for p, _ in pins if p not in PWR and p != 'DIODE']
            if sig:
                phys_bad.append((cell, name, sig))
        if not SEQ.search(cell):
            for i in ins:
                edges[i] |= set(outs)

    if unknown:
        print('!! UNCLASSIFIED PINS -- fix the table before trusting anything below:')
        for p, k in unknown.most_common():
            print(f'   {p} ({k:,})')
        sys.exit(1)

    # W1 contention -- tri-state drivers separated out, they may legitimately share
    multi = {n: d for n, d in drivers.items() if len(d) > 1}
    tri = {n: d for n, d in multi.items() if all(TRI.search(c) for c, _, _ in d)}
    hard = {n: d for n, d in multi.items() if n not in tri}
    print(f'W1  nets with >1 driver          : {len(multi):,}'
          f'   (tri-state-only {len(tri):,}, mixed/static {len(hard):,})')
    for n, d in list(hard.items())[:6]:
        print(f'    ! {n}  <- ' + ', '.join(f'{c.split("__")[-1]}.{p}' for c, _, p in d[:4]))
    for n, d in list(tri.items())[:4]:
        print(f'      tri {n}  <- ' + ', '.join(f'{c.split("__")[-1]}.{p}' for c, _, p in d[:4]))

    # W2 floating reads
    undriven = [n for n in readers
                if n not in drivers and n.lstrip('\\') not in ports
                and n not in ('1\'b0', '1\'b1') and not n.startswith('1\'b')]
    print(f'W2  read nets with no driver     : {len(undriven):,}')
    for n in undriven[:6]:
        print(f'      {n}  read by {len(readers[n])}')

    # W3 combinational cycles (iterative Tarjan)
    idx, low, on, stk, cyc = {}, {}, set(), [], []
    counter = [0]
    for root in list(edges):
        if root in idx:
            continue
        work = [(root, iter(edges.get(root, ())))]
        idx[root] = low[root] = counter[0]; counter[0] += 1
        stk.append(root); on.add(root)
        while work:
            v, it = work[-1]
            adv = False
            for w in it:
                if w not in idx:
                    idx[w] = low[w] = counter[0]; counter[0] += 1
                    stk.append(w); on.add(w)
                    work.append((w, iter(edges.get(w, ()))))
                    adv = True
                    break
                elif w in on:
                    low[v] = min(low[v], idx[w])
            if adv:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == idx[v]:
                comp = []
                while True:
                    w = stk.pop(); on.discard(w); comp.append(w)
                    if w == v:
                        break
                if len(comp) > 1 or v in edges.get(v, ()):
                    cyc.append(comp)
    print(f'W3  combinational cycles (SCCs)  : {len(cyc):,}'
          + (f'   sizes {sorted((len(c) for c in cyc), reverse=True)[:8]}' if cyc else ''))
    for c in sorted(cyc, key=len, reverse=True)[:3]:
        print(f'      SCC of {len(c)} nets, e.g. {c[:3]}')

    # W4 inertness
    print(f'W4  physical cells w/ signal pins: {len(phys_bad):,}')
    for c, n, s in phys_bad[:6]:
        print(f'      {c} {n}: {s}')

    tot = sum(ncells.values())
    nphys = sum(k for c, k in ncells.items() if PHYS.search(c))
    nseq = sum(k for c, k in ncells.items() if SEQ.search(c))
    print(f'\n    cells: {tot:,}  physical {nphys:,} ({100*nphys/tot:.1f}%)  '
          f'sequential {nseq:,}  nets {len(set(drivers) | set(readers)):,}')


if __name__ == '__main__':
    main()
