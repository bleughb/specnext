p='C:/1NEXT/nexclash/games/castle_master.md'
s=open(p,encoding='utf-8',newline='').read()
def rep(a,b):
    global s
    assert s.count(a)==1,a
    s=s.replace(a,b)
rep("A Next set to 60 Hz: a black flash at load (the stub's switch to 50 Hz); none at 50 Hz.","A 60 Hz Next: a black flash at load (the stub's switch to 50 Hz).")
rep("9 mutants, NEX, JNext 8,000 frames.","9 mutants.")
rep("cm3_glue.asm, host test, NEX, JNext.","cm3_glue.asm.")
rep("cm9_*.asm; on hardware (user): good). Views","cm9_*.asm). Views")
open(p,'w',encoding='utf-8',newline='').write(s)
