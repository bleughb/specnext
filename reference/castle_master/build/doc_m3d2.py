p='C:/1NEXT/nexclash/games/castle_master.md'
s=open(p,encoding='utf-8',newline='').read()
def rep(a,b):
    global s
    assert s.count(a)==1,a
    s=s.replace(a,b)
i=s.index("- M3d (2026-11-22"); j=s.index("- M0 side checks (m0_misc.py)")
s=s[:i]+"""- M3d (2026-11-22; castle_master_m3d_05.nex, cm9_*.asm; on hardware (user): good). Views shown by the dissolve
  ((0x7349) = 1 at 0x859C: the drawbridge) stayed in the original look. Now drawn hidden (m3_dshow), 0xB66E's
  passes repeated on Layer 2 (site 0xB6E4 h_dpass), then flipped: +3 frames. m3_sim: 18 / 18 such views.
"""+s[j:]
rep("- 2026-11-21 / 22, stage 2 M3c / M3d (profile, DDMA benchmark, speed pass; dissolve in colour, hardware), ~6 h,\n  ~350 tool calls, mostly autonomous: +12 % views.",
    "- 2026-11-21 / 22, stage 2 M3c / M3d (profile, DDMA benchmark, speed pass, dissolve), ~6 h, ~350 tool calls:\n  +12 % views.")
rep("no DDMA. Hardware (user) = CSpect within 3 lines.","no DDMA. Hardware = CSpect.")
rep("0xCECD; rows in 8 bits). Sprites go with Layer 2; the dissolve 0xB66E turns both off (views: M3d). Hooks from 0x3600 (m3b_rom.py). After hardware runs 1-2 (user's choices):",
    "0xCECD; rows in 8 bits). Sprites go with Layer 2; the dissolve 0xB66E turns both off (views: M3d). Hooks\n  from 0x3600 (m3b_rom.py). After hardware runs 1-2 (user's choices):")
rep("in-between flips deferred into the next view's object loop (flipdef / flipchk\n  / flipfl).","in-between flips deferred into the next view's object loop (flipchk).")
rep("sprite grid, cursor / dissolve / portcullis sites, fixed sight + pointer, host tests,\n  18 mutants, NEX, JNext.","sprite grid, cursor / dissolve / portcullis sites, fixed sight + pointer, 18 mutants.")
open(p,'w',encoding='utf-8',newline='').write(s)
