for n in ('cm11.asm','cm11_cmr.asm','cm11_glue.asm'):
    s=open(n,encoding='latin-1',newline='').read().replace('cm11','cm12')
    if n.endswith('glue.asm'):
        i=s.index("ld a,(scr_on)"); j=s.index("        nextreg 0x07,0",i); k=s.index("        ld hl,0xE000",j)
        assert 'dec e' in s[j:k] and k-j<400
        s=s[:j]+s[k:]
        b="it shows as soon as bank 5 loads, whatever the loader; held here 4.4 s"
        assert s.count(b)==1
        s=s.replace(b,"it shows as soon as bank 5 loads, whatever the loader; not held (cm12):")
    open(n.replace('cm11','cm12'),'w',encoding='latin-1',newline='').write(s)
