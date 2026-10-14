# Catalogue every distinct graphic of every frame (table 0xE290, up to 220 frames) present in memory at the end
# of any RZX frame. Output JSON: {frame: [{flags, height, addr, data(hex: header + rows), first, frames}]}.
# Usage: python gfxcat.py RZX OUT.json
import sys, json, hashlib, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import skoolkit.rzxplay as rz
NF = 220                                # table entries 0xE290-0xE5FF (0xE600 = temp descriptor)
cat, last, n = {}, [None], [0]
def frames_now(m):
    for i in range(NF):
        e = 0xE290 + 4 * i
        fl, h, a = m[e], m[e + 1], m[e + 2] | m[e + 3] << 8
        w = fl & 31
        if w and h and 0x5B00 <= a < 0x10000 - w * h:
            yield i, fl, h, a, bytes(m[a:a + 1 + w * h])
nf = rz.RZXTracer.next_frame
def next_frame(self):
    n[0] += 1
    m = self.simulator.memory
    key = hashlib.md5(bytes(m[0xE290:0xE290 + 4 * NF]) + bytes(m[0xAB00:0xDB00])).digest()
    if key != last[0]:
        last[0] = key
        for i, fl, h, a, d in frames_now(m):
            v = cat.setdefault(i, {}).setdefault(d, {'flags': fl, 'height': h, 'addr': a, 'first': n[0], 'changes': 0})
            v['changes'] += 1
    return nf(self)
rz.RZXTracer.next_frame = next_frame
try:
    rz.main(['--quiet', '--no-screen', '--fps', '0', sys.argv[1]])
except SystemExit:
    pass
out = {i: [dict(v, data=d.hex()) for d, v in vs.items()] for i, vs in sorted(cat.items())}
json.dump(out, open(sys.argv[2], 'w'), indent=0)
multi = {i: len(v) for i, v in out.items() if len(v) > 1}
print(n[0], 'frames;', len(out), 'figure frames;', sum(len(v) for v in out.values()), 'variants; with >1:', multi)
