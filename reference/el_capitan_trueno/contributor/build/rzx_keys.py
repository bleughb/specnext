# Keys pressed in the RZX: for every keyboard port read (low byte 0xFE), the keys whose bits read 0,
# collected per frame; prints frame ranges with the keys held (FIRST..LAST window).
# Usage: python rzx_keys.py RZX FIRST LAST
import sys
sys.path.insert(0, 'lib')
import skoolkit.rzxplay as rz

ROWS = {0xFE: ['CAPS', 'Z', 'X', 'C', 'V'], 0xFD: ['A', 'S', 'D', 'F', 'G'], 0xFB: ['Q', 'W', 'E', 'R', 'T'],
        0xF7: ['1', '2', '3', '4', '5'], 0xEF: ['0', '9', '8', '7', '6'], 0xDF: ['P', 'O', 'I', 'U', 'Y'],
        0xBF: ['ENTER', 'L', 'K', 'J', 'H'], 0x7F: ['SPACE', 'SYM', 'M', 'N', 'B']}
F, L = int(sys.argv[2]), int(sys.argv[3])
n = [0]
held = {}
rp, nf = rz.RZXTracer.read_port, rz.RZXTracer.next_frame


def read_port(self, registers, port):
    v = rp(self, registers, port)
    if F <= n[0] <= L and port & 0xFF == 0xFE:
        hi = port >> 8
        for row, keys in ROWS.items():
            if hi & ~row & 0xFF == 0 or hi == row:
                for b, k in enumerate(keys):
                    if not v & (1 << b) and hi == row:
                        held.setdefault(n[0], set()).add(k)
    return v


def next_frame(self):
    n[0] += 1
    return nf(self)


rz.RZXTracer.read_port, rz.RZXTracer.next_frame = read_port, next_frame
try:
    rz.main(['--quiet', '--no-screen', '--fps', '0', '--stop', str(L + 1), sys.argv[1]])
except SystemExit:
    pass
runs = []
for f in sorted(held):
    k = ' '.join(sorted(held[f]))
    if runs and runs[-1][2] == k and f - runs[-1][1] <= 2:
        runs[-1][1] = f
    else:
        runs.append([f, f, k])
for a, b, k in runs:
    print('%d-%d: %s' % (a, b, k))
