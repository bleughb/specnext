NL = chr(10)
P = 'C:/1NEXT/nexclash/games/castle_master.md'
s = open(P, encoding='utf-8', newline='').read()
crlf = (chr(13) + NL) in s
s = s.replace(chr(13) + NL, NL)

def rep(a_start, a_end, new):
    global s
    i = s.index(a_start)
    j = s.index(a_end, i) + len(a_end)
    assert s.count(a_start) == 1, a_start
    s = s[:i] + new + s[j:]

rep('- DMA / DDMA evaluation (docs/DDMA.md; estimates)', 'Not built yet.' + NL,
    '- DMA / DDMA (measured 2026-11-21, CSpect 4.5.9, blitbench_02.nex: 192 x 64 block, us a byte at 28 MHz): LDIR' + NL
    + '  0.76, zxnDMA 0.18-0.21, DDMA 2D copy 0.18 (skips the row gaps), PUSH fill 0.20, DDMA constant fill 0.07; a' + NL
    + "  job's set-up = 11-26 us. Dither rules the constant fill out, a pattern-row copy = PUSH's speed, per-row jobs" + NL
    + '  lose: only the view copy gains (zxnDMA: M3c). JNext 1.3.0 has no DDMA.' + NL)
rep('- E1 PASS (e1_maths.asm, e1_check_full.log)', '4 mutants FAIL (Lessons).' + NL,
    "- E1 PASS (e1_maths.asm, e1_check_full.log): Z80N versions of the game's maths 0xA1FD, 0xA253, 0xA348, 0xA2C1" + NL
    + '  (MUL D,E; unrolled division): all 682,956 recorded inputs + random equal; maths 9.7 % -> 4.5 % of T. 4' + NL
    + '  mutants FAIL (Lessons). Not in the build (the game maths = ~2 % of an M3 update).' + NL)
a = '- M0 side checks (m0_misc.py)'
assert s.count(a) == 1
blk = ('- M3c (speed pass 2026-11-21: more views, same pace; local castle_master_m3d_01-03.nex from cm7_*.asm, NOT' + NL
       + '  on hardware: m3b stays the confirmed build). Profile (m3_sim --prof, m3_calls.py; 524 redraws): geometry' + NL
       + '  27 %, game 18 %, span set-up 13 %, PUSH fill 12 %, waits 7 % (flip 4), maths 7 % (div32 4), overlay 5 %,' + NL
       + '  copy 3 %. Changes: div32 8 bits a step, divisor negated (1,967 -> 970 T), proj1 the same; span: the PUSH' + NL
       + '  run from an end of either parity; copy by zxnDMA in 8-row chunks (LDIR when the line & 255 is 238-255 /' + NL
       + '  0-3: the DMA hides the frame interrupt); in-between flips deferred into the next view\'s object loop' + NL
       + '  (flipdef / flipchk / flipfl; the final view waits as before). Views a redraw 6.67 -> 7.46; pace median' + NL
       + '  +0.69, max +1.95. m3_sim also checks: flip line, raster into the shown bank, views drawn = shown;' + NL
       + '  mutants g-j. Pointer colour now set at the flip (ov_ptrc; states 1405, 2099 failed before).' + NL)
s = s.replace(a, blk + a)
a = ' views a second in a moving update: median 11.5-29 (two runs), 10 %' + NL + '  10, 90 % 31-36;'
assert s.count(a) == 1, s.count(a)
s = s.replace(a, ' ~11-29 views a second moving;')
a = 'colour cycle, switch, DMA, R, K on hardware,'
assert s.count(a) == 1
s = s.replace(a, 'colour cycle, switch, R, K on hardware,')
a = '  18 mutants, NEX, JNext.' + NL
assert s.count(a) == 1
s = s.replace(a, a + '- 2026-11-21, stage 2 M3c (profile, DDMA benchmark, speed pass), ~4 h, ~150 tool calls, 1 user round' + NL
              + '  (autonomous): 3 numbered builds, +12 % views.' + NL)
a = 'State: M3b (overlays) PASS in simulator + JNext, on hardware (user); rest of M3 open'
assert s.count(a) == 1
s = s.replace(a, 'State: M3b on hardware (user); M3c speed pass PASS in simulator, not on hardware')
a = 'heaviest outdoor view ~10 views a second: DMA'
assert s.count(a) == 1
s = s.replace(a, 'm3d_03 + blitbench_02 on hardware')
a = "a helper named dis.py shadows the stdlib `dis` (twice)"
assert s.count(a) == 1
s = s.replace(a, "a helper named dis.py shadows the stdlib `dis` (3 times)")
if crlf:
    s = s.replace(NL, chr(13) + NL)
open(P, 'w', encoding='utf-8', newline='').write(s)
print(len(s.encode('utf-8')), 'bytes', 'crlf' if crlf else 'lf')
