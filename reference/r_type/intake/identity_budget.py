"""Bounded plot-identity review using the retained corpus and original peak replay.

No renderer, intake census or emulator dependency. Reconstructs source artwork
with the existing native decoder; traces only 100 peak updates after a cached
RZX cut. Generated snapshots/packed artwork remain outside Git. CPU estimates
are hypotheses, not natural-pace measurements or new timing credit constants.
"""
import collections
import gzip
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3] / 'nexclash'
sys.path[:0] = [str(ROOT)]
from nexclash import rzx, z80tonex as Z
from live_assets import reconstruct
from skoolkit.z80 import get_timing

WORK = Path('/workspace/work/r_type_review')
FLIPS = {0x8CFD: 0, 0x8D65: 1, 0x8DD3: 2, 0x8E29: 3}


def instruction_cost(m, r):
    """SkoolKit CPU timings with the live condition; never include IRQ CPU."""
    pc = r[24]
    op = m[pc]
    cost = get_timing(SimpleNamespace(operation='instruction',
        bytes=[m[(pc+i)&65535] for i in range(4)]))
    if isinstance(cost, tuple):
        if op == 0x10:
            taken = r[2] != 1
        else:
            cc = ((op >> 3) & 3) if op in (0x20, 0x28, 0x30, 0x38) else ((op >> 3) & 7)
            mask = (64, 64, 1, 1, 4, 4, 128, 128)[cc]
            taken = bool(r[1] & mask) == bool(cc & 1)
        cost = cost[0 if taken else 1]
    return cost


def packed(plot, cells):
    """Include attributes and transparent markers: they control source traversal."""
    byxy = {(x, y): cells[key] for x, y, key in plot['cells']}
    data = bytearray()
    for y in range(plot['h'] // 8):
        for x in range(plot['w'] // 8):
            c = byxy.get((x, y))
            data.extend(bytes([c['attribute']]) + bytes(c['bits']) if c else b'\x36')
    return bytes(data)


def sources(corpus):
    cache = WORK / 'decoded.bin'
    if cache.exists():
        data = cache.read_bytes()
        assert len(data) == 10 * 65536
        images = [data[i:i+65536] for i in range(0, len(data), 65536)]
    else:
        snap = Z.Z80Snapshot(str(HERE.parent / 'Rtype.z80'))
        images = reconstruct(snap, dict(unpack_levels=[49,50,51,52,53,54,55,56,49]))
        cache.write_bytes(b''.join(images))
    recipes = {}
    signatures = {}
    for key, p in corpus['plots'].items():
        data = packed(p, corpus['cells'])
        addr = p['address']
        hits = [i for i, image in enumerate(images) if image[addr:addr+len(data)] == data]
        assert hits, ('packed source not reconstructed', key)
        recipes[key] = hits
        signatures.setdefault((p['level'], addr, p['w']//8, p['h']//8), set()).add(data)
    writes = set(json.loads((HERE / 'isr-footprint.json').read_text())['writes'])
    addresses = {p['address']+i for p in corpus['plots'].values()
                 for i in range(len(packed(p, corpus['cells'])))}
    assert not writes & addresses, 'retained ISR writes packed source'
    # Exact matching, with no hash-only acceptance. Every byte mutation must miss.
    negatives = 0
    for variants in signatures.values():
        for data in variants:
            for i in range(len(data)):
                changed = bytearray(data)
                changed[i] ^= 1
                assert bytes(changed) not in variants
                negatives += 1
    return signatures, dict(plots=len(recipes), reconstructed_plots=len(recipes),
        packed_variants=sum(map(len, signatures.values())),
        ambiguous_entry_keys=sum(len(v)>1 for v in signatures.values()),
        source_address_count=len(addresses), isr_source_write_intersection=0,
        one_bit_mutations_rejected=negatives,
        decoded_sha256=hashlib.sha256(b''.join(images)).hexdigest())


def peak(signatures):
    cut = WORK / 'peak.rzx'
    if not cut.exists():
        assert rzx.cut(str(HERE.parent / 'Rtype.rzx'), 29404, 1200, str(cut)) == 1200
    rows = []
    row = None
    active = None
    plot_states = {}

    class Done(Exception):
        pass

    def at(pc, sim):
        nonlocal row, active
        r, m = sim.registers, sim.memory
        if pc == 0x8649:
            if row is not None:
                rows.append(row)
                if len(rows) == 100:
                    raise Done
            row = collections.Counter()
            active = None
            return
        if row is None:
            return
        if pc in FLIPS:
            addr = r[6]*256+r[7]
            h, w = r[4] or 256, r[5] or 256
            assert h <= 32 and w <= 32
            ptr = addr
            n = 0
            for _ in range(w*h):
                a = m[ptr]
                ptr += 1
                if a != 0x36:
                    n += 1
                    ptr += 8
            data = bytes(m[a] for a in range(addr, ptr))
            key = (m[0x719C], addr, w, h)
            known = data in signatures.get(key, ())
            active = dict(known=known, owner=m[0x7A9C])
            row['plots'] += 1
            row['known_plots' if known else 'unknown_plots'] += 1
            row['packed_bytes'] += len(data)
            row['nonblank_cells'] += n
            row['known_packed_bytes' if known else 'unknown_packed_bytes'] += len(data)
            # Small real states for later ABI tests; no second capture pass.
            if pc not in plot_states:
                plot_states[pc] = dict(pc=pc, frame=29404+sim.tracer.frame_index,
                    banks=[list(b) for b in m.banks], registers=list(r))
        elif pc == 0x8EA2:
            assert active is not None
            row['successful_cells'] += 1
            if active['known'] and 0 < m[0x7A9C] < 0xDC:
                row['known_successful_cells'] += 1
            else:
                row['fallback_successful_cells'] += 1
        if active is not None and 0x8CFD <= pc < 0x8F1F:
            cost = instruction_cost(m, r)
            row['original_plot_T'] += cost
            # Already accelerated by the current cell hook: helper, JP Z, rows.
            if (0x8EA2 <= pc < 0x8EC2 or pc in (0x8D2A,0x8D91,0x8DFD,0x8E57)
                or any(lo <= pc < hi for lo,hi in ((0x8D2D,0x8D4C),
                    (0x8D93,0x8DBA),(0x8DFF,0x8E10),(0x8E59,0x8E6C)))):
                row['already_accelerated_T'] += cost
            # All four outer exits are RET Z; helper RETs have a deeper SP.
            if pc in (0x8D56,0x8DC4,0x8E1A,0x8E76) and r[1]&64:
                active = None

    try:
        frames, desync = rzx.trace(str(cut), [0x8649, *range(0x8CFD,0x8F1F)], at)
    except Done:
        desync = None
    assert desync is None and len(rows) == 100, (len(rows), desync)
    (WORK / 'plot-states.json').write_text(json.dumps(list(plot_states.values())))
    return rows


def validate_counter():
    """Check cycle/condition accounting against isolated native executions."""
    from skoolkit.simulator import Simulator
    from irq_equivalence import Memory
    results = []
    for state in json.loads((WORK / 'plot-states.json').read_text()):
        for seed in (0,127,128,255):
            m = Memory(state, b'')
            sim = Simulator(m)
            sim.registers[:] = state['registers']
            r = sim.registers
            r[15] = seed
            start, sp = r[25], r[12]
            ret = m[sp] | m[sp+1]<<8
            total = 0
            count = 0
            m1 = 0
            while r[24] != ret or r[12] != (sp+2)&65535:
                total += instruction_cost(m,r)
                m1 += 2 if m[r[24]] in (0xCB,0xDD,0xED,0xFD) else 1
                sim.opcodes[m[r[24]]]()
                count += 1
                assert count < 100000
            assert total == r[25]-start
            assert r[15] == (seed&128)|((seed+m1)&127)
            results.append(dict(pc=hex(state['pc']), R=seed, T=total, M1=m1))
    assert {int(c['pc'],16) for c in results} == set(FLIPS)
    return results


def run():
    WORK.mkdir(exist_ok=True)
    corpus = json.loads(gzip.decompress((HERE / 'continuation/assets.json.gz').read_bytes()))
    signatures, source_result = sources(corpus)
    rows = peak(signatures)
    counter_cases = validate_counter()
    totals = sum(rows, collections.Counter())
    # Retained complete cell CPU costs: basic 657 versus resolved -946 fast T.
    # Their difference includes resolver + larger metadata + signed accounting.
    # It is an optimistic ceiling, NOT an isolated resolver measurement.
    ceiling_t = totals['known_successful_cells'] * (657 - (-946))
    # Sequential exact byte guard: LD A,(DE), CP (HL), JP NZ, INC DE/HL,
    # DJNZ = 49 T/byte (final loop exit is cheaper). Allow 600 T/plot setup,
    # 80 T/successful ID selection; final integration may require more.
    guard_t = totals['known_packed_bytes']*49 + totals['plots']*600
    selection_t = totals['known_successful_cells']*80
    baseline = json.loads((HERE / 'continuation/resolved-pace.json').read_text())
    phase = baseline['result']['phases'][0][1]
    required_ms = (phase['build_s'] - 1.02*phase['orig_s'])*1000/100
    estimate = dict(required_saving_ms_per_update=required_ms,
        optimistic_ceiling_ms_per_update=ceiling_t/28000/100,
        sequential_guard_ms_per_update=guard_t/28000/100,
        id_selection_ms_per_update=selection_t/28000/100,
        estimated_net_ms_per_update=(ceiling_t-guard_t-selection_t)/28000/100,
        assumptions='28MHz CPU only; no IRQ/debt/phase/publication benefit assumed; '
                    'current complete cell-cost difference is an optimistic ceiling; '
                    '600T plot setup + 49T packed byte + 80T successful ID selection',
        scope='Original RZX 100 peak updates; not JNext natural trajectory or a pace pass')
    extra_native = totals['original_plot_T'] - totals['already_accelerated_T']
    estimate['combined_writer_extra_native_T'] = extra_native
    estimate['combined_writer_extra_acceleration_ms_per_update'] = extra_native*7/28000/100
    estimate['combined_writer_estimated_net_ms_per_update'] = (
        ceiling_t-guard_t-selection_t+extra_native*7)/28000/100
    estimate['illustrative_combined_writer_residual_fast_T_per_update'] = (
        ceiling_t-guard_t-selection_t+extra_native*7)/100-required_ms*28000
    estimate['combined_writer_limit'] = ('Illustrative CPU estimate from a different trajectory, '
        'not a whole-route budget or implementation gate. Price all retained/replaced work, '
        'IRQ, accounting and publication first. No assembled combined writer yet.')
    result = dict(scope=__doc__, source=source_result, peak_totals=dict(totals),
                  updates=100, estimates=estimate, counter_cases=counter_cases,
                  per_update=[dict(r) for r in rows])
    out = HERE / 'continuation/identity-budget.json'
    out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'per_update'}, indent=2))


if __name__ == '__main__':
    run()
