live_lookup_code:
direct_lookup_code:
        ld a,(hl)
        ld (live_owner),a
        push hl
        ld a,h
        sub 0x7E
        ld h,a
        ld (live_index),hl
        pop hl
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
.ink:   ld (live_ink),a
        ld a,(0x719C)
        ld (live_level),a
        sub 48
        cp 10
        jp nc,live_miss
        nextreg 0x52,50
        ld de,(live_index)
        ld h,d
        ld l,e
        add hl,hl
        add hl,de
        add hl,hl
        set 6,h
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,d
        cp 0xA0
        jp c,live_miss
        cp 0xE0
        jp nc,live_miss
        ld (live_source),de
        inc hl
        ld a,(hl)
        ld (live_flip),a
        inc hl
        inc hl
        ld a,(live_owner)
        cp (hl)
        jp nz,live_miss
        inc hl
        ld a,(live_level)
        cp (hl)
        jp nz,live_miss
        ld a,(hook_mmu6)
        nextreg 0x56,a
        ld a,(live_level)
        sub 48
        add a,a
        add a,a
        add a,64
        ld b,a
        ld a,d
        DUP 4
        rrca
        EDUP
        and 3
        xor 2                  ; high nibbles A..D -> source pages0..3
        add a,b
        nextreg 0x52,a
        ld a,d
        and 15
        ld h,a
        ld l,e
        add hl,hl
        set 6,h
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,d
        or e
        jp z,live_miss
        ld a,d
        DUP 3
        srl a
        EDUP
        add a,104
        nextreg 0x52,a
        ld a,d
        and 7
        ld h,a
        ld l,e
        add hl,hl
        add hl,hl
        set 6,h
        ld de,(live_source)
        inc de
        ld b,8
.check: ld a,(de)
        cp (hl)
        jp nz,live_miss
        inc de
        inc hl
        djnz .check
        ld a,(hl)
        inc hl
        bit 7,a
        jr nz,.multi
        ld b,a
        ld a,(live_ink)
        cp b
        jp nz,live_miss
        jr .id
.multi: ld a,(live_ink)
        add a,a
        add hl,a
.id:    ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,d
        cp 0xFF
        jp z,live_miss
        and 128
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
        DUP 2
        rlca
        EDUP
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
        ld a,(live_flip)
        and 3
        DUP 5
        rlca
        EDUP
        add hl,a
        ld a,(dyn_page)
        nextreg 0x56,a
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
live_index: dw 0
live_source: dw 0
live_owner: db 0
live_ink: db 0
live_level: db 0
live_flip: db 0
