live_lookup_code:
resolved_render_code:
        ld a,(hl)
        ld (resolved_owner),a
        ld a,h
        sub 6
        ld h,a
        ld a,(hl)
        and 0x47
        ld e,a
        and 7
        ld d,a
        ld a,e
        and 0x40
        jr z,.dark
        ld a,d
        or 8
        ld d,a
.dark:  ld a,d
        or a
        jr nz,.ink
        ld a,8
.ink:   ld (resolved_ink),a
        ld a,h
        sub 0x78
        ld h,a
        DUP 3
        add hl,hl
        EDUP
        set 6,h
        nextreg 0x52,50
        inc hl
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,d
        and e
        inc a
        jp z,live_miss
        ld (resolved_group),de
        inc hl
        ld a,(hl)
        ld (resolved_flip),a
        inc hl
        ld a,(resolved_ink)
        cp (hl)
        jp nz,live_miss
        inc hl
        ld a,(resolved_owner)
        cp (hl)
        jp nz,live_miss
        inc hl
        ld a,(0x719C)
        cp (hl)
        jp nz,live_miss
        ld a,d
        and 128
        jp z,live_hit           ; complete transparent texture needs no copy
        ld hl,dyn_nonzero
        or (hl)
        ld (hl),a
        ld a,d
        and 0x3F
        ld d,a
        cp 0x22
        jp c,.valid
        jp nz,live_miss
        ld a,e
        cp 0x40
        jp nc,live_miss
.valid: ld a,d
        add a,a
        add a,a
        ld b,a
        ld a,e
        rlca
        rlca
        and 3
        or b
        add a,119
        nextreg 0x52,a
        ld a,e
        and 63
        ld l,a
        ld h,0
        DUP 7
        add hl,hl
        EDUP
        set 6,h
        ld a,(resolved_flip)
        and 3
        DUP 5
        rlca
        EDUP
        add hl,a
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
live_hit:
        scf
        ret
live_miss:
        or a
        ret
resolved_owner: db 0
resolved_ink: db 0
resolved_group: dw 0
resolved_flip: db 0
