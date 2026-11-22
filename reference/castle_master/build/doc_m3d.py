p='C:/1NEXT/nexclash/games/castle_master.md'
s=open(p,encoding='utf-8',newline='').read()
def rep(a,b):
    global s
    assert s.count(a)==1,a
    s=s.replace(a,b)
rep("stage 2 (build): M3b on hardware","stage 2 (build): M3d on hardware")
rep("State: M3b on hardware (user); M3c speed pass PASS in simulator, not on hardware","State: M3d on hardware (user 2026-11-22: castle_master_m3d_05.nex)")
rep("; K on hardware (6.75 = JNext); m3d_03 + blitbench_02 on hardware","; K on hardware (6.75 = JNext)")
rep("no DDMA.","no DDMA. Hardware (user) = CSpect within 3 lines.")
rep("the dissolve 0xB66E (9 calls under Layer 2: 0xBCE5,\n  0xCA44) turns both off.","the dissolve 0xB66E turns both off (views: M3d).")
rep("castle_master_m3d_01-03.nex from cm7_*.asm, NOT on hardware (m3b is)). Profile","castle_master_m3d_01-03.nex from cm7_*.asm). Profile")
rep("- M0 side checks (m0_misc.py)","""- M3d (2026-11-22; castle_master_m3d_05.nex, cm9_*.asm; on hardware (user): good). A view shown by the dissolve
  ((0x7349) = 1 at 0x859C -> 0x9F35: the drawbridge) stayed in the original look until the next move. Now drawn
  hidden (m3_dshow), 0xB66E's 4 passes repeated on Layer 2 (site 0xB6E4 h_dpass, table 0xB65E), then flipped;
  from a screen without Layer 2: original look, colour at the end. +3 frames. m3_sim: 18 / 18 such views.
- M0 side checks (m0_misc.py)""")
rep("- 2026-11-21, stage 2 M3c (profile, DDMA benchmark, speed pass), ~4 h, ~150 tool calls, autonomous: +12 % views.",
    "- 2026-11-21 / 22, stage 2 M3c / M3d (profile, DDMA benchmark, speed pass; dissolve in colour, hardware), ~6 h,\n  ~350 tool calls, mostly autonomous: +12 % views.")
open(p,'w',encoding='utf-8',newline='').write(s)
