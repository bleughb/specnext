; Static, preexpanded4bpp cost trial. BC=cell; IY=quadrant, stage page mapped6.
spritepaint_cell:
        ld a,b
        and 7
        rrca
        rrca
        rrca
        or c
        ld l,a
        ld a,b
        srl a
        srl a
        srl a
        add a,0x7E
        ld h,a
        ld a,(hl)
        or a
        ret z
        cp 0xDC
        ret nc
        push hl
        ld l,a
        ld h,text_owners/256
        ld a,(hl)
        pop hl
        or a
        ret nz
        ld a,h
        sub 0x7E
        ld h,a
        add hl,hl
        add hl,hl
        nextreg 0x50,51
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld a,(hl)
        inc hl
        ld c,(hl)
        nextreg 0x50,a
        ld a,(dyn_nonzero)
        or c
        ld (dyn_nonzero),a
        ex de,hl
        push iy
        pop de
        DUP 8,row
        DUP 4
        ldi
        EDUP
        IF row<7
        add de,4
        ENDIF
        EDUP
        ret
spritepaint_setup:
        nextreg 0x43,0x20
        nextreg 0x40,0
        ld hl,spritepaint_palette
        ld b,16
.pal:   ld a,(hl)
        inc hl
        nextreg 0x41,a
        djnz .pal
        nextreg 0x43,0
        nextreg 0x4B,0
        ret
spritepaint_palette:
        db 0xE3,0x02,0xA0,0xA2,0x14,0x16,0xB4,0xB6
        db 0,0x03,0xE0,0xE7,0x1C,0x1F,0xFC,0xFF
        INCLUDE "cell_plot.asm"
