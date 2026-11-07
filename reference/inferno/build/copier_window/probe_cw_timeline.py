"""Inferno copier window: per-update timeline of a FULL original recording (milestone 2).

Usage: python probe_cw_timeline.py NEXCLASH_DIR LEVEL OUT.json [STOP]   (reference = NEXCLASH_DIR/../specnext/reference/inferno)
       python probe_cw_timeline.py --summary tl1.json ... tl6.json      (window model -> JSON on stdout)

Replays InfernoLEVEL.rzx from InfernoLEVEL.z80 (Python simulator, uncontended T) and records, for
every copier update (8F92 -> 9907): the T of 8F92, 9790 and 9907, every accepted interrupt, the
416 head OUT values (change count, first value, cell-1 change), the port FE value before the head,
G (tiles >= 16 in the 13 head rows, from the tile map), 998E and the bytes at 9907 (the never-read
rule: PUSH DE / PUSH HL overwrite the 4 bytes below SP first) and SP at 9907. summarize() turns
these into lost/handled IRQs, late level changes, slack
and free time. No game data is written; the JSON holds numbers only.
"""
import json
import sys
from pathlib import Path

if sys.argv[1:2] != ['--summary']:
    sys.path.insert(0, sys.argv[1])
    from nexclash.simrun import run  # noqa: E402

HEAD_OUT, ENTRY, HEAD, LIMIT = 0x97C5, 0x8F92, 0x9790, 0x9907


class Timeline:
    def __init__(self):
        self.sim, self.t = None, 0
        self.irqs, self.updates, self.cur, self.port = [], [], None, None
        self.frame_t, self.last_irq = [], None

    def on_sim(self, sim):
        self.sim = sim

    def on_interrupt(self, sim, prev_pc):
        if self.last_irq is not None:
            self.frame_t.append(self.t - self.last_irq)
        self.last_irq = self.t
        self.irqs.append(self.t)

    def before(self, pc):
        m = self.sim.memory
        op = m[pc]
        if op == 0xD3 and m[(pc + 1) & 0xFFFF] == 0xFE:
            v = self.sim.registers[0]
            if self.cur is not None and self.cur.get('t9790') is not None and pc == HEAD_OUT:
                self.cur['outs'].append(v)
            else:
                self.port = v
        if pc == ENTRY:
            self.cur = {'t8F92': self.t, 'port': self.port, 'outs': [], 't9790': None, 'irq0': len(self.irqs)}
        elif pc == HEAD and self.cur is not None and self.cur['t9790'] is None:
            self.cur['t9790'] = self.t
            self.cur['G'] = sum(m[0x9F7E - 2 * k] >= 16 for k in range(416))
            self.cur['flag'] = m[0x998E]
        elif pc == LIMIT and self.cur is not None and self.cur['t9790'] is not None:
            c = self.cur
            outs = c.pop('outs')
            c['t9907'] = self.t
            c['sp'] = self.sim.registers[12]
            c['code9907'] = m[0x9907] << 8 | m[0x9908]
            c['flag'] = max(c['flag'], m[0x998E])
            c['n_outs'] = len(outs)
            c['changes'] = sum(1 for i, v in enumerate(outs) if i == 0 or v != outs[i - 1])
            c['first'] = outs[0] if outs else None
            c['cell1'] = len(outs) > 1 and outs[1] != outs[0]
            c['last'] = outs[-1] if outs else None
            self.updates.append(c)
            self.port = outs[-1] if outs else self.port
            self.cur = None

    def after(self, pc, dt):
        self.t += dt


def main():
    ref, level, out = Path(sys.argv[1]) / '../specnext/reference/inferno', sys.argv[2], Path(sys.argv[3])
    stop = int(sys.argv[4]) if len(sys.argv) > 4 else None
    tl = Timeline()
    frames = run(str(ref / ('Inferno%s.z80' % level)), [str(ref / ('Inferno%s.rzx' % level))], tl, stop=stop)
    keys = ('t8F92', 't9790', 't9907', 'irq0', 'G', 'changes', 'n_outs', 'first', 'cell1', 'port', 'sp', 'code9907', 'flag')
    out.write_text(json.dumps({'level': level, 'frames': frames, 'irqs': tl.irqs,
                               'frame_t': {'n': len(tl.frame_t), 'min': min(tl.frame_t, default=0),
                                           'max': max(tl.frame_t, default=0),
                                           'mean': sum(tl.frame_t) / max(1, len(tl.frame_t))},
                               'keys': keys, 'updates': [[u.get(k) for k in keys] for u in tl.updates]}) + '\n')
    print(level, frames, len(tl.updates))


if __name__ == '__main__' and sys.argv[1:2] != ['--summary']:
    main()


def summarize(paths, entry=(14, 139), busy=(16534, 46.62, 14.23), tol=32):
    """Window model over the recorded updates. entry: DI span (start after 8F92, length) of the
    milestone-2 window from the checks; busy: T = a + b*changes + c*G fitted on the quick states."""
    import statistics
    out = {}
    for p in paths:
        d = json.loads(Path(p).read_text())
        k = {n: i for i, n in enumerate(d['keys'])}
        irqs, ups = d['irqs'], d['updates']
        import bisect
        c = {'updates': len(ups), 'IRQs inside 8F92..9907': 0, 'updates with an IRQ in the window': 0,
             'IRQs lost in the entry DI span': 0, 'updates with a late level change (cell 0/1)': 0,
             'slack below tolerance': 0, 'code at 9907 not PUSH DE/PUSH HL': 0, '998E set in the head': 0,
             'SP at 9907 outside A1F0..A6FE': 0, 'n_outs != 416': 0}
        free, slack = [], []
        for u in ups:
            t0, t9907 = u[k['t8F92']], u[k['t9907']]
            i = bisect.bisect_left(irqs, t0)
            inside = []
            while i < len(irqs) and irqs[i] < t9907:
                inside.append(irqs[i] - t0)
                i += 1
            if i < len(irqs):
                slack.append(irqs[i] - t9907)
                if irqs[i] - t9907 < tol:
                    c['slack below tolerance'] += 1
            c['IRQs inside 8F92..9907'] += len(inside)
            lost = [x for x in inside if entry[0] <= x <= entry[0] + entry[1] - 32]
            c['IRQs lost in the entry DI span'] += len(lost)
            if len(inside) > len(lost):
                c['updates with an IRQ in the window'] += 1
            if (u[k['first']] != u[k['port']]) or u[k['cell1']]:
                c['updates with a late level change (cell 0/1)'] += 1
            c['code at 9907 not PUSH DE/PUSH HL'] += u[k['code9907']] != 0xD5E5
            c['998E set in the head'] += bool(u[k['flag']])
            c['SP at 9907 outside A1F0..A6FE'] += not 0xA1F0 <= u[k['sp']] <= 0xA6FE
            c['n_outs != 416'] += u[k['n_outs']] != 416
            head = t9907 - u[k['t9790']] - 94 * sum(1 for x in inside if x >= 17)
            free.append(head - (busy[0] + busy[1] * u[k['changes']] + busy[2] * u[k['G']]))
        free.sort()
        q = lambda v, f: round(v[min(len(v) - 1, int(f * len(v)))] / 3500, 3)
        c['free ms (min/p1/median)'] = [q(free, 0), q(free, .01), q(free, .5)]
        c['frames'] = d['frames']
        out[d['level']] = c
    return out


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--summary':
    print(json.dumps(summarize(sys.argv[2:]), indent=1))
