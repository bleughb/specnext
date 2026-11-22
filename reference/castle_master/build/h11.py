p='cm11_glue.asm'
s=open(p,encoding='latin-1').read()
a="setup:\n        nextreg 0x12,PG_LA/2\n"
assert s.count(a)==1
s=s.replace(a,"""setup:
        ld a,(scr_on)                   ; a loading screen (m2_build --screen): it is the image's own screen, so
        or a                            ; it shows as soon as bank 5 loads, whatever the loader; held here 4.4 s
        jr z,2F                         ; (9 x 65,536 x 26 T at 3.5 MHz), then the game's screen back from 0xE000
        nextreg 0x07,0
        ld e,9
        ld bc,0
1:      dec bc
        ld a,b
        or c
        jr nz,1B
        dec e
        jr nz,1B
        ld hl,0xE000
        ld de,0x4000
        ld bc,6912
        ldir
2:      nextreg 0x12,PG_LA/2
""")
a="setup_end:\n"
assert s.count(a)==1
s=s.replace(a,"scr_on: db 0                            ; 1 = the stub bank's upper page holds the game's screen (m2_build)\nsetup_end:\n")
open(p,'w',encoding='latin-1').write(s)
