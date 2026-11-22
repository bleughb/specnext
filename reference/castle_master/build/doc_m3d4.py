p='C:/1NEXT/nexclash/games/castle_master.md'
s=open(p,encoding='utf-8',newline='').read()
def rep(a,b):
    global s
    assert s.count(a)==1,a
    s=s.replace(a,b)
rep("(m3_sim --prof; 524 redraws): geometry 27 %, game 18, span set-up 13,","(m3_sim --prof): geometry 27 %, game 18, span 13,")
rep("switch, R, K on hardware,","switch, R,")
rep(" 6 user rounds (hardware: M2 runs,\n  original pace; \"Start M3\"):"," 6 user rounds:\n ")
rep("~12 user rounds\n  (photos; CSpect):","~12 user rounds:\n ")
open(p,'w',encoding='utf-8',newline='').write(s)
