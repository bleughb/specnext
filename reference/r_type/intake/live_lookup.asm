; Temporary slot0 code at1000 avoids DivMMC entry addresses. Slot2 supplies
; descriptor/hash/texture data; IRQ wrapper redirects native screen accesses.
live_lookup_code:
        ; Caller has already classified the native owner and text identity.
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
        cp 0x40
        jp c,live_miss
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
        ; Original canonical source may be in the displaced C000 game page.
        ld a,(hook_mmu6)
        nextreg 0x56,a
        ld hl,(live_source)
        ld d,12
        ld e,l
        mul d,e
        add hl,de
        ld a,(live_level)
        ld b,a
        ld c,a
        add hl,bc
        ld a,(live_ink)
        ld e,a
        DUP 4
        rlca
        EDUP
        or e
        ld e,a
        ld a,(live_ink)
        ld d,a
        add hl,de
        ld a,h
        and 0x3F
        ld h,a
        ld (live_hash),hl
live_probe:
        ld hl,(live_hash)
        ld a,h
        srl a
        add a,64
        nextreg 0x52,a
        ld a,h
        and 1
        ld h,a
        DUP 4
        add hl,hl
        EDUP
        set 6,h
        ld a,(hl)
        inc hl
        or (hl)
        jp z,live_table_miss
        dec hl
        ld de,(live_source)
        ld a,(hl)
        cp e
        jp nz,live_next
        inc hl
        ld a,(hl)
        cp d
        jp nz,live_next
        inc hl
        ld a,(live_level)
        cp (hl)
        jp nz,live_next
        inc hl
        ld a,(live_ink)
        cp (hl)
        jp nz,live_next
        inc hl
        inc de
        ld b,8
.check: ld a,(de)
        cp (hl)
        jp nz,live_next
        inc de
        inc hl
        djnz .check
        ; Entry+12 group ID; entry+14 any opaque output pixel.
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld a,(dyn_nonzero)
        or (hl)
        ld (dyn_nonzero),a
        ld a,d
        add a,a
        add a,a
        ld b,a
        ld a,e
        DUP 2
        rlca
        EDUP
        and 3
        or b
        add a,96
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
live_next:  ld hl,(live_hash)
        inc hl
        ld a,h
        and 0x3F
        ld h,a
        ld (live_hash),hl
        jp live_probe
live_table_miss:
live_miss:
        or a
        ret
live_index: dw 0
live_source: dw 0
live_hash: dw 0
live_owner: db 0
live_ink: db 0
live_level: db 0
live_flip: db 0
