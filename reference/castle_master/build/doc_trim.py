p='C:/1NEXT/nexclash/games/castle_master.md'
s=open(p,encoding='utf-8',newline='').read()
def rep(a,b):
    global s
    assert s.count(a)==1,a
    s=s.replace(a,b)
rep(" (the clock's rules decide where ticks must come from)","")
rep("(stub, tail, alt ROM fill: the build's memory plan depends on all three)","(stub, tail, alt ROM fill)")
rep("0xB62C (108, the same list again)","0xB62C (108, same list)")
open(p,'w',encoding='utf-8',newline='').write(s)
