p='cm10_glue.asm'
s=open(p,encoding='latin-1').read()
def rep(a,b):
    global s
    assert s.count(a)==1,a
    s=s.replace(a,b)
rep("dis_n:    ds 1 ","facecur:  ds 16                         ; setpal: the 16 face colours in use (facepal, or the area's ink: col_on = 0)\ndis_n:    ds 1 ")
rep("        ld d,(hl)\n        ld hl,facepal\n        ld b,16\n1:      ld a,d",
"""        ld d,(hl)
        push de
        ld hl,facepal
        ld de,facecur
        ld bc,16
        ldir
        pop de
        ld a,(col_on)                   ; 0 = the original's look: every face in the area's ink
        or a
        jr nz,7F
        ld hl,facecur
        ld b,16
6:      ld (hl),e
        inc hl
        djnz 6B
7:      ld hl,facecur
        ld b,16
1:      ld a,d""")
rep("        nextreg 0x41,0xFF               ; 3 = white, 4 = black: the fixed overlays (ov_fr0 / ov_fr1)\n        nextreg 0x41,0x00\n",
"""        ld a,(col_on)                   ; 3 = white, 4 = black: the fixed overlays (ov_fr0 / ov_fr1); with the
        or a                            ; colours off, the area's ink and paper
        jr z,8F
        nextreg 0x41,0xFF
        nextreg 0x41,0x00
        jr 9F
8:      ld a,e
        nextreg 0x41,a
        ld a,d
        nextreg 0x41,a
9:
""")
rep("        ld ix,facepal\n","        ld ix,facecur\n")
rep("facepal:                                ; PLACEHOLDER","col_on: db 1                            ; 1 = colours, 0 = the original's look (the .nxc's colour set pokes it)\nfacepal:                                ; PLACEHOLDER")
open(p,'w',encoding='latin-1').write(s)
