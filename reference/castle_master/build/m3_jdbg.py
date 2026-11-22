import os, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
W = r'C:/1NEXT/castle_master_work/'
os.environ['NEXCLASH_JNEXT'] = r'C:/1NEXT/jnext-1.3.0-windows-x64/jnext.exe'
from nexclash import jnext
from m2_lib import syms
S = syms('cm3')
nex = W + 'castle_master_m3.nex'
frames = int(sys.argv[1]) if len(sys.argv) > 1 else 1100
sc = jnext.Script(jnext.start_frame(nex))
sc.rule(jnext.counters())
sc.start_line(nex)
prof = dict(jnext.GENERIC)
sc.start_keys(prof)
sc.frame_input(jnext.schedule(prof, frames, 1))
VP = 0xFE40
def m16(a):
    return '${mem[%d]} ${mem[%d]}' % (a, a + 1)
st = 'EL=%s HELD=%s LAST=%s OPEN=${mem[%d]} K=${mem[%d]} ML=${mem[%d]}' % (m16(VP + 2), m16(VP + 14), m16(VP), VP + 10, VP + 28, VP + 29)
for tag, ad, extra in (('B0', 0x855E, ''), ('B1', 0x859C, ''), ('B2', 0x859F, ''), ('SHOW', S['m3_show'], ''),
                       ('WT', S['waittgt'], ' FAST=%s TGT=%s FIN=%s' % (m16(S['t_fast']), m16(S['t_tgt']), m16(S['t_fin']))),
                       ('FL', S['flip'], ''), ('IP', S['isr_p'], ''), ('IF', S['isr_full'], ''), ('IT', S['isr_tick'], ''),
                       ('MID', S['m3_mid'], ''), ('OPEN', S['popen'], '')):
    sc.rule('on execute %d do\n  log "%s F=${FRAME} C=${CYCLE} %s%s"\nend\n' % (ad, tag, st, extra))
sc.exit_at(frames)
out = W + 'm3_jdbg'
p = jnext.launch(nex, sc.text(), out, frames, jnext.card(r'C:/1NEXT/cspect-next-2gb.img'))
p.wait(timeout=3600)
c0 = None
for line in open(os.path.join(out, 'run.log')):
    if ' F=' not in line:
        continue
    parts = line.split()
    i = [k for k, x in enumerate(parts) if x.startswith('F=')][0]
    tag, f = parts[i - 1], int(parts[i].split('=')[1])
    if f < 1015:
        continue
    c = int(parts[i + 1].split('=')[1])
    c0 = c0 or c
    print(tag, f, '%.2f' % ((c - c0) / 559104), ' '.join(parts[i + 2:]))
