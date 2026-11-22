import re, textwrap
NL = chr(10)
P = 'C:/1NEXT/nexclash/games/castle_master.md'
s = open(P, encoding='utf-8', newline='').read()
WS = '[ ' + NL + ']+'

def sub(old, new, wrap=None):
    """old: text matched with any whitespace between words; new: replacement (re-wrapped as a bullet when wrap)"""
    global s
    pat = WS.join(re.escape(w) for w in old.split())
    m = list(re.finditer(pat, s))
    assert len(m) == 1, (len(m), old[:50])
    a, b = m[0].span()
    if wrap:                                    # re-wrap the whole bullet that contains the match
        i = s.rfind(NL + '- ', 0, a) + 1
        j = s.find(NL + '- ', b)
        k = s.find(NL + NL, b)
        j = min(x for x in (j, k) if x >= 0)
        text = ' '.join((s[i:a] + new + s[b:j]).split())
        lines = textwrap.wrap(text, 111, subsequent_indent='  ', break_long_words=False, break_on_hyphens=False)
        s = s[:i] + NL.join(lines) + s[j:]
    else:
        s = s[:a] + new + s[b:]

# the M3c block, tighter
i = s.index('- M3c (speed pass 2026-11-21')
j = s.index('- M0 side checks (m0_misc.py)')
blk = ("- M3c (speed pass 2026-11-21: more views, same pace; local castle_master_m3d_01-03.nex from cm7_*.asm, NOT on "
       "hardware: m3b stays the confirmed build). Profile (m3_sim --prof, m3_calls.py; 524 redraws): geometry 27 %, "
       "game 18, span set-up 13, PUSH fill 12, waits 7 (flip 4), maths 7 (div32 4), overlay 5, copy 3: profile "
       "first (the copy, guessed at half a view, was 3 %). Changes: div32 and proj1 by 8-bit steps with the divisor "
       "negated (1,967 -> 970 T); span's PUSH run from an end of either parity; copy by zxnDMA in 8-row chunks "
       "(LDIR when the line & 255 is 238-255 / 0-3: the DMA hides the frame interrupt); in-between flips deferred "
       "into the next view's object loop (flipdef / flipchk / flipfl; the final view waits as before). Views a "
       "redraw 6.67 -> 7.46; pace median +0.69, max +1.95. m3_sim also checks the flip's line, raster into the "
       "shown bank, views drawn = shown; mutants g-j. Pointer colour set at the flip (ov_ptrc; states 1405, 2099).")
s = s[:i] + NL.join(textwrap.wrap(blk, 111, subsequent_indent='  ', break_long_words=False, break_on_hyphens=False)) + NL + s[j:]
sub('- 2026-11-21, stage 2 M3c (profile, DDMA benchmark, speed pass), ~4 h, ~150 tool calls, 1 user round (autonomous): 3 numbered builds, +12 % views.',
    '- 2026-11-21, stage 2 M3c (profile, DDMA benchmark, speed pass), ~4 h, ~150 tool calls, autonomous: +12 % views.')
sub("Two line readings one frame apart (handler to handler) differ by 0 or 311 by jitter: a tick taken only in the interrupt wrapper lost half the frames. Rule: after a reading at an interrupt, a difference under half a frame is a frame more.",
    "Two line readings a frame apart differ by 0 or 311 by jitter: after a reading at an interrupt, a difference under half a frame is a frame more.", wrap=True)
sub("A long interrupts-off span (sound, 0.5 s) must be ticked before and re-read after, not held (hold / resume are modulo a frame). The game's waits on its handler inside the window are real time: 14 loops found by their byte pattern after redraws showed +28 frames late. An interrupt that skips its reading (a main-line one under way, the window half open) loses a frame: let it read; commit",
    "A long interrupts-off span (sound, 0.5 s) is ticked before and re-read after, not held. The game's 14 waits on its handler inside the window are real time (+28 frames until found). An interrupt must not skip its reading; commit", wrap=True)
sub("also run the build's code along the recording. That test must enter the hooks themselves: with the pointer filter and the NEXTREGs modelled in the test, two mutants in them passed.",
    "also run the build's code, hooks included, along the recording (with the hooks modelled in the test, two mutants passed).", wrap=True)
sub("The host harness poked the same bytes, so only JNext showed it (the clock ran on table bytes).",
    "Only JNext showed it (the harness poked the same bytes).", wrap=True)
sub("0x8D4F sectors 2k T, 0x9776 12k, 0x9D8A sort median 42k (max 662k), raster (clear 82k + fill ~41k) 17.5 % of all T, copy 52k;",
    "sort 0x9D8A median 42k T (max 662k), raster 17.5 % of all T, copy 52k;", wrap=True)
sub("; 15 on another path (-2.2 .. -0.9)", "")
open(P, 'w', encoding='utf-8', newline='').write(s)
print(len(s.encode('utf-8')), 'bytes; longest line', max(len(l) for l in s.split(NL)))
