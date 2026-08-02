#!/usr/bin/env python3
"""Clock-network cleanliness (L2/05): the licence for L3's clock-tree deletion.

For every sequential cell, walk its clock/gate pin BACKWARD through drivers to
the network's sources. A path node is *clean* if it is a single-input
function-preserving cell (buffer or inverter, of any drive family — post-CTS
trees are made of clkbuf/clkinv/clkdlybuf, and delay buffers are identity
functions too). Everything else is enumerated, never silently accepted:

    source   input port | macro pin | constant generator | flop output
             (a flop Q clocking other flops = a derived/bit-bang clock)
    node     clock-gate cell (dlclk*: GCLK = CLK & latch(GATE)) — legitimate
             gating, continues upward through its CLK pin, enable recorded
    node     any multi-input logic cell — a clock mux/gate in plain logic;
             the arrival function is data-dependent there (the a22o driving
             housekeeping's csclk is the known instance)

Output: per clock ROOT (the source or unclean node a sink ultimately reaches),
the number of sequential sinks, the path-cell census, and the enumerated
exceptions. "All flops update together" is sound exactly for the sinks whose
root is a single clean clock source.

Usage: clockcheck.py <gate-level.v>
"""
import sys
import collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from netgraph import OUT, PWR, IN, SEQ, PHYS  # noqa: E402
from synccheck import parse, build, BUFINV, CLOCK_PINS  # noqa: E402


def classify_driver(nets, pins_of, net):
    """-> (kind, detail, next_nets):  kind in
    {port/floating, macro, const, flop-out, clockgate, bufinv, logic}"""
    d = nets[net].driver
    if d is None:
        macro = [(c, p) for k, c, i, p in nets[net].readers if k == 'macro']
        if macro:
            return 'macro', f'{macro[0][0]}.{macro[0][1]}', []
        return 'port/floating', net, []
    cell, inst, pin = d
    ins = [n for p, n in pins_of[inst].items() if p in IN and p not in PWR]
    if 'conb' in cell:
        return 'const', cell.split('__')[-1], []
    if 'dlclk' in cell:
        clk = next((pins_of[inst].get(c) for c in ('CLK', 'CLK_N')), None)
        gate = next((pins_of[inst].get(c) for c in ('GATE', 'GATE_N')), None)
        return 'clockgate', f'{cell.split("__")[-1]} enable<-{gate}', [clk] if clk else []
    if SEQ.search(cell):
        return 'flop-out', f'{inst} ({cell.split("__")[-1]})', []
    if BUFINV.search(cell) and len(ins) == 1:
        return 'bufinv', cell.split('__')[-1], ins
    return 'logic', f'{inst} ({cell.split("__")[-1]})', ins


def trace_root(nets, pins_of, net, memo):
    """Walk upward through clean buffers; return (root_kind, root_detail,
    census Counter of path cell kinds, exceptions list)."""
    if net in memo:
        return memo[net]
    census = collections.Counter()
    exceptions = []
    seen = set()
    cur = net
    while True:
        if cur in seen:
            memo[net] = ('cycle', cur, census, exceptions)
            return memo[net]
        seen.add(cur)
        kind, detail, nxt = classify_driver(nets, pins_of, cur)
        census[kind] += 1
        if kind == 'bufinv' and nxt:
            cur = nxt[0]
            continue
        if kind == 'clockgate':
            exceptions.append(('clockgate', detail))
            if nxt:
                cur = nxt[0]
                continue
        if kind == 'logic':
            exceptions.append(('logic', detail))
        memo[net] = (kind, detail, census, exceptions)
        return memo[net]


def survey(path):
    """-> (ninsts, nsinks, ngates, by_root, all_exc, nets, pins_of)."""
    insts, decls = parse(path)
    nets, outs_of, pins_of = build(insts)
    sinks = []   # (inst, cell, clockpin, net)
    for cell, name, pins in insts:
        if cell.startswith('sky130') and SEQ.search(cell) and 'dlclk' not in cell:
            for p, n in pins:
                if p in CLOCK_PINS:
                    sinks.append((name, cell, p, n))
    ngates = sum(1 for c, _, _ in insts if 'dlclk' in c)
    memo = {}
    by_root = collections.defaultdict(list)
    all_exc = collections.Counter()
    for inst, cell, p, n in sinks:
        kind, detail, census, exc = trace_root(nets, pins_of, n, memo)
        by_root[(kind, detail)].append((inst, cell))
        for e in exc:
            all_exc[e] += 1
    return len(insts), len(sinks), ngates, by_root, all_exc, nets, pins_of


def main():
    path = sys.argv[1]
    ninsts, nsinks, ngates, by_root, all_exc, _, _ = survey(path)
    print(f'{path}: {ninsts:,} instances, {nsinks:,} sequential clock sinks, '
          f'{ngates} clock-gate cells\n')

    print(f'{len(by_root)} distinct clock roots:')
    for (kind, detail), members in sorted(by_root.items(), key=lambda kv: -len(kv[1])):
        print(f'  {len(members):6,} sinks <- [{kind}] {detail}')

    if all_exc:
        print('\nenumerated exceptions on clock paths (sink-weighted):')
        for (k, d), c in all_exc.most_common(20):
            print(f'  {c:6,}x [{k}] {d}')
    else:
        print('\nno gating, no muxing, no logic on any clock path')


if __name__ == '__main__':
    main()
