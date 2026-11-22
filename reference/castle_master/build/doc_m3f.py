p='C:/1NEXT/nexclash/games/castle_master.md'
s=open(p,encoding='utf-8',newline='').read()
n=chr(13)+chr(10) if chr(13)+chr(10) in s else chr(10)
bs=chr(92)
L=s.split(n)
assert L[171].startswith('- M3e (2026-11-22') and L[176-1].startswith('  shows the tape')
new=["- M3e (2026-11-22; castle_master_m3d_08.nex, cm12_*.asm; on hardware from its .nxc 1.1 (user)). col_on = 0",
"  (m2_build --mono): every face in the area's ink. Loading screen (tape offset 513) = the image's screen; setup",
"  puts the game's back (a NEX header screen: CSpect closes, JNext skips it). .nxc (jattree/nxc, tape target):",
"  toggle Original colours, 2 trainers (unplayed); build_screen=513: the loader shows the tape's screen from",
"  ENTER (nxc branch build-screen). Refused on the Next: update dot/NEXCLASH."]
L[171:176]=new
s=n.join(L)
a="RZX + tape: nxc_out"+bs
assert s.count(a)==1
s=s.replace(a,"RZX + tape: nxc_out_1.1"+bs)
open(p,'w',encoding='utf-8',newline='').write(s)
