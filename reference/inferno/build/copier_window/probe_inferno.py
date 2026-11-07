"""Inferno probe: (A) who writes DC00-FFFF during gameplay, (B) where the game is paced.

Usage: python probe_inferno.py NEXCLASH_DIR LEVEL [STOP]  -> prints JSON summary.
Gameplay = after the first execution of 0x8F7C (the per-update scenery hook site).
"""
import collections
import json
import sys

sys.path.insert(0, sys.argv[1])
from nexclash.simrun import run  # noqa: E402

UPDATE_PC = 0x8F7C
REF = sys.argv[1] + '/../specnext/reference/inferno/'


class Probe:
    def __init__(self):
        self.active = False
        self.frame = 0
        self.sim = None
        # A: writes
        self.wpc = {}                      # pc -> [count, lo, hi, first_frame, last_frame]
        self.waddr = collections.Counter()  # 256-byte page -> writes
        # B: pacing
        self.t_total = 0
        self.t_halt = 0
        self.pc_t = collections.Counter()
        self.updates = []                  # (frame, T since previous update, halt T, interrupts)
        self.u_t = self.u_halt = self.u_int = self.u_idle = 0
        self.flag_writers = collections.Counter()
        self.t0 = self.t9907 = self.tcopy = None
        self.fg = []          # (frame, foreground T 8F7C->9907, slack T 9907->next interrupt, copier T)
        self.cur = None
        self.tabs = 0

    def on_sim(self, sim):
        self.sim = sim

    def on_frame(self, n):
        self.frame = n

    def on_interrupt(self, sim, prev_pc):
        if self.active:
            self.u_int += 1
        if self.cur is not None and self.t9907 is not None:
            self.cur[2] = self.tabs - self.t9907
            self.fg.append(tuple(self.cur))
            self.cur, self.t9907 = None, None

    def before(self, pc):
        T = self.tabs
        if pc == UPDATE_PC:
            self.cur, self.t0, self.t9907 = [self.frame, None, None, 0], T, None
        elif pc == 0x9790 and self.cur is not None:
            self.tcopy = T
        elif pc == 0x9907 and self.cur is not None and self.t9907 is None:
            if self.tcopy is not None:
                self.cur[3] = T - self.tcopy
                self.tcopy = None
            self.cur[1] = T - self.t0
            self.t9907 = T
        if pc == UPDATE_PC:
            if self.active:
                self.updates.append((self.frame, self.u_t, self.u_halt, self.u_int, self.u_idle))
            self.active = True
            self.u_t = self.u_halt = self.u_int = self.u_idle = 0

    def after(self, pc, dt):
        self.tabs += dt
        if not self.active:
            return
        self.t_total += dt
        self.u_t += dt
        self.pc_t[pc] += dt
        if pc == 0x9989:
            self.u_idle += dt
        if self.sim.memory[pc] == 0x76 and self.sim.registers[24] == pc:   # still on HALT
            self.t_halt += dt
            self.u_halt += dt

    def on_write(self, a, v, pc, mem):
        if a == 0x998E:
            self.flag_writers['0x%04X=%d' % (pc, v)] += 1
        if not self.active or a < 0xDC00:
            return
        e = self.wpc.get(pc)
        if e is None:
            self.wpc[pc] = [1, a, a, self.frame, self.frame]
        else:
            e[0] += 1
            e[1] = min(e[1], a)
            e[2] = max(e[2], a)
            e[4] = self.frame
        self.waddr[a >> 8] += 1


def main():
    level = sys.argv[2]
    stop = int(sys.argv[3]) if len(sys.argv) > 3 else None
    p = Probe()
    n = run(REF + 'Inferno%s.z80' % level, [REF + 'Inferno%s.rzx' % level], p, stop=stop)
    ts = sorted(u[1] for u in p.updates)
    ints = collections.Counter(u[3] for u in p.updates)
    idle = sorted(u[4] for u in p.updates)
    busy = sorted(u[1] - u[4] for u in p.updates)
    q = lambda v: {'min': v[0], 'p1': v[len(v) // 100], 'p10': v[len(v) // 10], 'median': v[len(v) // 2], 'max': v[-1]} if v else None
    zero = sum(1 for v in idle if v == 0)
    fg = p.fg
    out_fg = {'n': len(fg), 'foreground_T': q(sorted(f[1] for f in fg)), 'slack_T': q(sorted(f[2] for f in fg)),
              'copier_T': q(sorted(f[3] for f in fg))}
    for ms in (0.5, 1, 2, 5, 10, 15, 20):
        x = ms * 3500
        out_fg['updates_slipping_a_frame_at_%gms' % ms] = round(sum(1 for f in fg if f[2] < x) / len(fg), 4) if fg else None
    out = {
        'pacing': out_fg,
        'idle_T_per_update': q(idle), 'busy_T_per_update': q(busy), 'updates_with_zero_idle': zero,
        'flag_998E_writers': dict(p.flag_writers),
        'level': level, 'frames': n, 'updates': len(p.updates),
        'T_per_update': {'min': ts[0], 'median': ts[len(ts) // 2], 'p90': ts[len(ts) * 9 // 10], 'max': ts[-1]}
        if ts else None,
        'halt_share': p.t_halt / p.t_total if p.t_total else None,
        'interrupts_per_update': dict(sorted(ints.items())),
        'top_pcs_by_T': [['0x%04X' % pc, t, round(t / p.t_total, 4)] for pc, t in p.pc_t.most_common(25)],
        'writes_DC00_FFFF_pages': {'0x%02X00' % k: v for k, v in sorted(p.waddr.items())},
        'writers': {'0x%04X' % pc: {'count': e[0], 'lo': '0x%04X' % e[1], 'hi': '0x%04X' % e[2],
                                    'first_frame': e[3], 'last_frame': e[4]}
                    for pc, e in sorted(p.wpc.items(), key=lambda kv: -kv[1][0])},
    }
    print(json.dumps(out, indent=1))


main()
