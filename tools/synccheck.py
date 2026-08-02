#!/usr/bin/env python3
"""Synchroniser check for asynchronous inputs (L2/04 step 3, L2/06's predicate; F1/F3).

For each named input port, trace its combinational fanout through the gate-level
netlist to the first sequential cells, then test the structural two-flop
synchroniser predicate on every data-pin capture:

    stage-1 flop's Q (through at most a chain of single-fanout buffers/inverters)
    feeds exactly one load, the D pin of a second flop on the same clock net.

Every other termination of the fanout is reported by kind:
    macro entry      the net enters an opaque macro (trace it separately there)
    output port      the net leaves the module (output-side; L2/06's export story)
    async pin        RESET_B/SET_B of a flop (a reset-assertion path, not a capture)
    clock/gate pin   the net is used as a clock or latch gate (it IS a clock; L2/05)
    capture NOSYNC   a data capture whose flop fails the two-flop predicate  <- findings

Same discipline as netgraph.py: unknown sky130 pins abort the run; macro pins are
never guessed at - a macro is an explicit hole, reported as such.

Usage: synccheck.py <gate-level.v> <port|net> ...   (bus ports expand via their declaration)
"""
import re
import sys
import collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from netgraph import OUT, PWR, IN, SEQ, PHYS  # the declared pin/cell tables

KEYWORDS = {'module', 'endmodule', 'input', 'output', 'inout', 'wire', 'assign',
            'supply0', 'supply1', 'reg', 'parameter', 'localparam', 'defparam'}
DATA_PINS = {'D', 'D_N', 'SCD'}
CLOCK_PINS = {'CLK', 'CLK_N', 'GATE', 'GATE_N'}
ASYNC_PINS = {'RESET_B', 'SET_B'}
BUFINV = re.compile(r'__(buf|inv|clkbuf|clkinv|dlybuf|dlygate|dlymetal|clkdly)')


def parse(path):
    txt = open(path, errors='replace').read()
    # port declarations with optional bus range
    decls = {}
    for d, rng, names in re.findall(
            r'\b(input|output|inout)\s*(\[[0-9]+:[0-9]+\])?\s*([^;]+);', txt):
        for n in names.split(','):
            decls[n.strip().lstrip('\\')] = (d, rng.strip() or None)
    insts = []
    for m in re.finditer(r'\b([A-Za-z_]\w*)\s+(\\?\S+?)\s*\(\s*(\.[^;]*?)\)\s*;', txt, re.S):
        cell, name, body = m.groups()
        if cell in KEYWORDS:
            continue
        pins = [(p, n.strip()) for p, n in re.findall(r'\.(\w+)\s*\(\s*([^)]*?)\s*\)', body)]
        insts.append((cell, name, pins))
    return insts, decls


def expand(port, decls):
    if port in decls and decls[port][1]:
        hi, lo = map(int, decls[port][1][1:-1].split(':'))
        return [f'{port}[{i}]' for i in range(min(hi, lo), max(hi, lo) + 1)]
    return [port]


def expand_expr(expr):
    """Expand a net expression - possibly a concatenation and/or bus slices -
    into individual bit nets."""
    out = []
    for part in expr.strip().lstrip('{').rstrip('}').split(','):
        part = part.strip()
        m = re.fullmatch(r'(\\?[^\s\[]+)\s*\[(\d+):(\d+)\]', part)
        if m:
            base, hi, lo = m.group(1), int(m.group(2)), int(m.group(3))
            out += [f'{base}[{i}]' for i in range(min(hi, lo), max(hi, lo) + 1)]
        elif part:
            out.append(part)
    return out


class Net:
    __slots__ = ('readers', 'driver')

    def __init__(self):
        self.readers = []   # (kind, cell, inst, pin) kind in {sky, macro}
        self.driver = None


def build(insts):
    nets = collections.defaultdict(Net)
    outs_of = {}          # inst -> [output nets]
    pins_of = {}          # inst -> {pin: net}
    unknown = collections.Counter()
    for cell, name, pins in insts:
        sky = cell.startswith('sky130')
        pins_of[name] = dict(pins)
        if sky:
            if PHYS.search(cell):
                continue
            o = []
            for p, net in pins:
                if p in PWR or p == 'DIODE':
                    continue
                if p in OUT:
                    o.append(net)
                    nets[net].driver = (cell, name, p)
                elif p in IN:
                    nets[net].readers.append(('sky', cell, name, p))
                else:
                    unknown[p] += 1
            outs_of[name] = o
        else:
            # opaque macro: every pin is an endpoint, direction unknown.
            # Macro connections may be concatenations {a, b[3:0], ...}: expand to bits.
            for p, net in pins:
                for n in expand_expr(net):
                    nets[n].readers.append(('macro', cell, name, p))
    if unknown:
        print('!! UNCLASSIFIED sky130 PINS - fix netgraph.py tables first:', dict(unknown))
        sys.exit(1)
    return nets, outs_of, pins_of


def chase_buffers(nets, outs_of, net):
    """Follow a net through single-fanout buffer/inverter stages; return the final
    net and the number of stages crossed, or (None, n) if the chain branches."""
    hops = 0
    while True:
        rs = nets[net].readers
        if len(rs) != 1:
            return net, hops
        kind, cell, inst, pin = rs[0]
        if kind == 'sky' and BUFINV.search(cell) and not SEQ.search(cell):
            o = outs_of.get(inst, [])
            if len(o) == 1:
                net, hops = o[0], hops + 1
                continue
        return net, hops


def clk_root(nets, pins_of, net):
    """Walk a clock net upward through buffer/inverter drivers to the tree root,
    so that two leaves of one clock tree compare equal."""
    seen = set()
    while net not in seen:
        seen.add(net)
        d = nets[net].driver
        if not d:
            return net
        cell, inst, pin = d
        if BUFINV.search(cell) and not SEQ.search(cell):
            src = [n for p, n in pins_of[inst].items() if p in IN and p not in PWR]
            if len(src) == 1:
                net = src[0]
                continue
        return net
    return net


def sync_verdict(nets, outs_of, pins_of, inst, cell):
    """Is flop `inst` the head of a two-flop synchroniser?"""
    clk1 = next((pins_of[inst].get(c) for c in CLOCK_PINS if c in pins_of[inst]), None)
    clk1 = clk_root(nets, pins_of, clk1) if clk1 else None
    loads = []
    for q in outs_of.get(inst, []):
        qn, _ = chase_buffers(nets, outs_of, q)
        loads += [(qn, r) for r in nets[qn].readers]
    if len(loads) != 1:
        return False, f'stage-1 Q drives {len(loads)} loads'
    (qn, (kind, c2, i2, p2)) = loads[0]
    if kind != 'sky' or not SEQ.search(c2) or p2 not in DATA_PINS:
        return False, f'stage-1 Q load is {c2.split("__")[-1]}.{p2}, not a flop D'
    clk2 = next((pins_of[i2].get(c) for c in CLOCK_PINS if c in pins_of[i2]), None)
    clk2 = clk_root(nets, pins_of, clk2) if clk2 else None
    if clk1 != clk2:
        return False, f'stage-2 clock {clk2} differs from stage-1 clock {clk1}'
    return True, f'2-flop on clk {clk1}'


def trace(nets, outs_of, pins_of, decls, start):
    seen = {start}
    frontier = [start]
    hits = collections.defaultdict(list)
    while frontier:
        net = frontier.pop()
        base = net.split('[')[0]
        if base in decls and decls[base][0] in ('output', 'inout') and net != start:
            hits['output port'].append(net)
        for kind, cell, inst, pin in nets[net].readers:
            if kind == 'macro':
                hits['macro entry'].append(f'{cell}.{pin}')
            elif SEQ.search(cell):
                if pin in DATA_PINS:
                    ok, why = sync_verdict(nets, outs_of, pins_of, inst, cell)
                    hits['capture SYNC' if ok else 'capture NOSYNC'].append(
                        f'{inst} ({cell.split("__")[-1]}) - {why}')
                elif pin in CLOCK_PINS:
                    hits['clock/gate pin'].append(f'{inst}.{pin}')
                elif pin in ASYNC_PINS:
                    hits['async pin'].append(f'{inst}.{pin}')
                else:
                    hits['other seq pin'].append(f'{inst}.{pin} ({cell})')
            else:
                for o in outs_of.get(inst, []):
                    if o not in seen:
                        seen.add(o)
                        frontier.append(o)
    return hits, len(seen)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    path, ports = sys.argv[1], sys.argv[2:]
    insts, decls = parse(path)
    nets, outs_of, pins_of = build(insts)
    print(f'{path}: {len(insts):,} instances, tracing {len(ports)} port group(s)\n')
    for port in ports:
        bits = expand(port, decls)
        # aggregate identical verdicts across bus bits for readability
        agg = collections.defaultdict(list)
        for b in bits:
            if not nets[b].readers:
                agg['(unconnected)'].append((b, ''))
                continue
            hits, reach = trace(nets, outs_of, pins_of, decls, b)
            for k, v in hits.items():
                for x in sorted(set(v)):
                    agg[k].append((b, x))
        print(f'== {port} ({len(bits)} bit(s))')
        for k in sorted(agg):
            entries = agg[k]
            uniq = collections.Counter(x for _, x in entries)
            nbits = len({b for b, _ in entries})
            print(f'   {k}: {len(entries)} hits over {nbits} bit(s)')
            for x, c in uniq.most_common(12):
                print(f'      {c:3}x {x}')
        print()


if __name__ == '__main__':
    main()
