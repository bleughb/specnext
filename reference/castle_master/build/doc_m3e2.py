p='C:/1NEXT/nexclash/games/castle_master.md'
s=open(p,encoding='utf-8',newline='').read()
nl='\r\n' if '\r\n' in s else chr(10)
bs=chr(92)
def rep(a,b):
    global s
    a=a.replace('\n',nl); b=b.replace('\n',nl)
    assert s.count(a)==1,a
    s=s.replace(a,b)
i=s.index("- M3e (2026-11-22"); j=s.index("- M0 side checks (m0_misc.py)")
s=s[:i]+("""- M3e (2026-11-22; castle_master_m3d_07.nex, cm11_*.asm; CSpect; its .nxc loads on hardware (user)). col_on = 0
  (m2_build --mono): every face in the area's ink. Loading screen (tape offset 513) = the image's screen, the
  game's put back from the stub bank by setup after 4.4 s (a NEX header screen: CSpect closes, JNext skips it).
  .nxc (jattree/nxc; tape target): toggle Original colours, 2 trainers. Refused on the Next: update dot/NEXCLASH.
""").replace('\n',nl)+s[j:]
rep("- Palette: index 1-16 + area paper; colour off: M3e; ISR cycle = same switch with the ISR's attribute. Placeholder until the user's palette.",
    "- Palette: index 1-16 + area paper; colour off: M3e; ISR cycle = same switch with the ISR's attribute.\n  Placeholder until the user's palette.")
rep("- Pipeline costs (15k frames): sort 0x9D8A median 42k T (max 662k), raster 17.5 % of all T, copy 52k; walking\n  ~2.4M T a step, maths ~20 %, no wait anywhere.\n","")
rep("helped: pacing_census on the main loop 0x8542 showed event-driven renders of 2-52\n  frames and no frame wait, which set the speed question.","helped: pacing_census on 0x8542 showed event-driven renders, no frame wait.")
rep("must restore;\n  the ISR's R reads are cosmetic (E5: 229 blink-delay bytes).","must restore.")
s=s.replace("nxc_out"+bs+bs,"nxc_out"+bs)
open(p,'w',encoding='utf-8',newline='').write(s)
