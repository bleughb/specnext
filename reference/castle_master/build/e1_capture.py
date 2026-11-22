"""Castle Master E1 step 1: every call to the maths routines over the RZX, with inputs and outputs.

Routines (leaf, no memory writes but the stack):
  0xA1FD  A(s8) * HL(s16)      -> AHL (s24)      keeps BC DE
  0xA253  HL(s16) * DE(s16)    -> DEHL (s32)     keeps AF BC
  0xA2C1  AHL(s24) / DE(s16)   -> AHL quot, DE   keeps BC BC'
  0xA348  H(s8) * L(s8)        -> HL (s16)       keeps AF BC DE
Writes e1_calls.json: per routine, {input key: [count, all 16 main+alt regs in, all 16 out]} for each unique
full register input (so any register a caller might read afterwards is captured), plus totals and the
call sites (return addresses) seen.
Usage: python -I e1_capture.py [--stop N]
"""
import argparse, collections, json, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun

ENTRIES = (0xA1FD, 0xA253, 0xA2C1, 0xA348)
REGS = list(range(8)) + list(range(16, 24))   # A F B C D E H L, A' F' B' C' D' E' H' L'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=3000)
    ap.add_argument('-o', default=r'C:/1NEXT/castle_master_work/e1_calls.json')
    a = ap.parse_args()
    st = {'sim': None}
    pending = []                                # (routine, entry SP, return address, regs in, frame-free)
    calls = {e: {} for e in ENTRIES}
    total = collections.Counter()
    sites = {e: collections.Counter() for e in ENTRIES}
    odd = collections.Counter()

    class H:
        def on_sim(self, sim):
            st['sim'] = sim

        def before(self, pc):
            sim = st['sim']
            R = sim.registers
            if pending:
                rt, sp0, ret, rin = pending[-1]
                if pc == ret and R[12] == (sp0 + 2) & 0xFFFF:
                    pending.pop()
                    rout = tuple(R[i] for i in REGS)
                    d = calls[rt]
                    k = rin
                    if k in d:
                        d[k][0] += 1
                        if d[k][1] != rout:
                            odd[rt] += 1
                    else:
                        d[k] = [1, rout]
                    total[rt] += 1
                    sites[rt][ret] += 1
            if pc in ENTRIES:
                m = sim.memory
                sp = R[12]
                pending.append((pc, sp, m[sp] | m[(sp + 1) & 0xFFFF] << 8, tuple(R[i] for i in REGS)))
                if len(pending) > 8:
                    odd['deep'] += 1
                    del pending[0]

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=a.stop)
    out = {'%04X' % e: {'calls': total[e], 'unique': len(calls[e]),
                        'sites': {'%04X' % s: n for s, n in sorted(sites[e].items())},
                        'cases': [[list(k), v[0], list(v[1])] for k, v in calls[e].items()]}
           for e in ENTRIES}
    out['odd'] = dict(odd)
    out['stop'] = a.stop
    json.dump(out, open(a.o, 'w'))
    for e in ENTRIES:
        print('%04X calls %d unique inputs %d sites %d' % (e, total[e], len(calls[e]), len(sites[e])))
    print('odd', dict(odd))
    return 0 if not odd else 1


if __name__ == '__main__':
    sys.exit(main())
