p='C:/1NEXT/nexclash/games/castle_master.md'
s=open(p,encoding='utf-8',newline='').read()
nl='\r\n' if '\r\n' in s else chr(10)
def rep(a,b):
    global s
    a=a.replace('\n',nl); b=b.replace('\n',nl)
    assert s.count(a)==1,a
    s=s.replace(a,b)
rep("stage 2 (build): M3d on hardware","stage 2 (build): M3e on hardware")
rep("State: M3d on hardware (user 2026-11-22: castle_master_m3d_05.nex)","State: M3d on hardware (user 2026-11-22); M3e: its .nxc loads there")
rep("castle_master.z80 (extracted from the RZX), C:\dev\castlemaster\castle.rzx","castle_master.z80 (from the RZX); RZX + tape: nxc_out\\")
rep("Start with: the colour cycle as palette + the switch, the M3b block's \"Open\" list","Start with: the colour cycle as palette, the M3b block's \"Open\" list")
rep("three headerless blocks): single load, not needed.","three headerless blocks): single load; the .nxc's target.")
rep("colour off (player option) = all indices -> the area's ink / paper (original\n  look); ISR cycle","colour off: M3e; ISR cycle")
rep("colour cycle, switch, R,","colour cycle, R,")
rep("- M0 side checks (m0_misc.py)","""- M3e (2026-11-22; castle_master_m3d_07.nex, cm11_*.asm; CSpect; on hardware (user) its .nxc loads). Colour off:
  col_on = 0 (renderer page; m2_build --mono): setpal gives every face the area's ink. Loading screen (tape
  offset 513) = the image's own screen, the game's kept in the stub bank (0xE000) and put back by setup after
  4.4 s (a NEX header screen: CSpect closes, JNext skips it). .nxc (jattree/nxc, tape target): toggle Original
  colours; trainers 49471,0 and 49135-7 (unplayed). Refused on the Next = an old dot/NEXCLASH on the card.
- M0 side checks (m0_misc.py)""")
rep("stage 2 M3c / M3d (profile, DDMA benchmark, speed pass, dissolve), ~6 h, ~350 tool calls:\n  +12 % views.","stage 2 M3c-e (profile, DDMA benchmark, speed pass, dissolve, screen, .nxc), ~9 h, ~600 tool\n  calls: +12 % views.")
open(p,'w',encoding='utf-8',newline='').write(s)
