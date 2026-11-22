p='C:/1NEXT/nexclash/games/castle_master.md'
s=open(p,encoding='utf-8',newline='').read()
bs=chr(92)
def rep(a,b):
    global s
    assert s.count(a)==1,a
    s=s.replace(a,b)
rep("RZX + tape: nxc_out_1.1"+bs,"RZX + tape: nxc_out"+bs)
rep(" Refused on the Next: update dot/NEXCLASH.","")
rep("on hardware from its .nxc 1.1 (user)","hardware, from .nxc 1.1 (user)")
rep("every face in the area's ink","faces in the area's ink")
open(p,'w',encoding='utf-8',newline='').write(s)
