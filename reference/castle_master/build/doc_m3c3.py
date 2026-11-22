import re, textwrap
NL = chr(10)
P = 'C:/1NEXT/nexclash/games/castle_master.md'
s = open(P, encoding='utf-8', newline='').read()
WS = '[ ' + NL + ']+'

def sub(old, new):
    global s
    pat = WS.join(re.escape(w) for w in old.split())
    m = list(re.finditer(pat, s))
    assert len(m) == 1, (len(m), old[:50])
    a, b = m[0].span()
    i = s.rfind(NL + '- ', 0, a) + 1
    j = s.find(NL + '- ', b)
    k = s.find(NL + NL, b)
    j = min(x for x in (j, k) if x >= 0)
    text = ' '.join((s[i:a] + new + s[b:j]).split())
    s = s[:i] + NL.join(textwrap.wrap(text, 111, subsequent_indent='  ', break_long_words=False, break_on_hyphens=False)) + s[j:]

sub('(speed pass 2026-11-21: more views, same pace; local castle_master_m3d_01-03.nex', '(speed pass 2026-11-21; castle_master_m3d_01-03.nex')
sub('Profile (m3_sim --prof, m3_calls.py; 524 redraws): geometry 27 %, game 18, span set-up 13, PUSH fill 12, waits 7 (flip 4), maths 7 (div32 4), overlay 5, copy 3: profile first (the copy, guessed at half a view, was 3 %).',
    'Profile (m3_sim --prof; 524 redraws): geometry 27 %, game 18, span set-up 13, PUSH fill 12, waits 7, maths 7, overlay 5, copy 3.')
sub('(flipdef / flipchk / flipfl; the final view waits as before)', '(flipdef / flipchk / flipfl)')
sub('pace median +0.69, max +1.95.', 'pace median +0.69.')
sub('(ov_ptrc; states 1405, 2099)', '(ov_ptrc)')
sub('DDMA 2D copy 0.18 (skips the row gaps),', 'DDMA 2D copy 0.18,')
sub("a job's set-up = 11-26 us.", '')
sub('(22 of 5,000; 1 of 4,000)', '')
sub('(bolt: 688 bytes at pitch 4, 172 recorded)', '')
sub('(callers 0x6A8C, 0x6A96, 0x8519, 0xBD49)', '')
sub('(castle_master_work: cm2_glue.asm in cmr.asm, m2_lib / m2_sim / m2_build / m2_jnext / m2_mutants)', '(cm2_glue.asm in cmr.asm; m2_* tools)')
sub('E1 maths, DMA: not in the build yet.', 'E1 maths: not in the build.')
sub("Z80N versions of the game's maths 0xA1FD, 0xA253, 0xA348, 0xA2C1 (MUL D,E; unrolled division): all 682,956 recorded inputs + random equal; maths 9.7 % -> 4.5 % of T. 4 mutants FAIL (Lessons). Not in the build (the game maths = ~2 % of an M3 update).",
    "Z80N versions of the game's maths 0xA1FD, 0xA253, 0xA348, 0xA2C1 = the originals on all recorded inputs + random; 4 mutants FAIL (Lessons); not in the build (~2 % of an M3 update).")
open(P, 'w', encoding='utf-8', newline='').write(s)
print(len(s.encode('utf-8')), 'bytes')
