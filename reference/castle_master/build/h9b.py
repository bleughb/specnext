p='cm9_glue.asm'
s=open(p,encoding='latin-1').read()
a="        ld a,(m_pc)                     ; 2 = the dissolve brings this view on (m3_dshow): no flip yet\n        cp 2\n        jp z,m3_end\nm3_fl3: call ov_sightc"
assert s.count(a)==1
s=s.replace(a,"m3_fl3: ld a,(m_pc)                     ; 2 = the dissolve brings this view on (m3_dshow): no flip yet\n        cp 2\n        jp z,m3_end\n        call ov_sightc")
open(p,'w',encoding='latin-1').write(s)
