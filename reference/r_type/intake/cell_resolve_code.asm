; Outputs only private cell_group/cell_case. Each outcome has a fixed CPU cost;
; the raw guard checks all8 bytes so its miss position cannot change that cost.
resolve_code:
        ld hl,(cell_src)
        ld a,h
        sub 0xA0
        cp 0x40
        sbc a,a
        ld c,a
        ld a,(0x719C)
        sub 48
        cp 10
        sbc a,a
        and c
        jp z,resolve_bounds
        ld a,(0x719C)
        sub 48
        add a,a
        add a,a
        add a,64
        ld b,a
        ld a,h
        DUP 4
        rrca
        EDUP
        and 3
        xor 2                  ; high nibbles A..D -> source pages0..3
        add a,b
        nextreg 0x50,a
        ld a,h
        and 15
        ld h,a
        add hl,hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,d
        or e
        jp z,resolve_empty
        ld a,d
        DUP 3
        srl a
        EDUP
        add a,104
        nextreg 0x50,a
        ld a,d
        and 7
        ld h,a
        ld l,e
        add hl,hl
        add hl,hl
        ld de,cell_raw
        ld b,8
        ld c,0
.raw:   ld a,(de)
        xor (hl)
        or c
        ld c,a
        inc de
        inc hl
        djnz .raw
        ld a,c
        or a
        jp nz,resolve_raw
        ld a,(hl)
        inc hl
        bit 7,a
        jr nz,.multi
        ld b,a
        ld a,(cell_ci)
        cp b
        jp nz,resolve_ink
        ld a,0
        ld (cell_case),a
        jr .id
.multi: ld a,(cell_ci)
        add a,a
        add hl,a
        ld a,1
        ld (cell_case),a
.id:    ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,d
        and e
        inc a
        jr z,.invalid
        ld (cell_group),de
        ret
.invalid:
        ld a,(cell_case)
        or a
        ld a,7
        jr nz,.case
        ld a,9
.case:  ld (cell_case),a
        ret
resolve_bounds:
        ld a,4
        ld (cell_case),a
        ret
resolve_empty:
        ld a,5
        ld (cell_case),a
        ret
resolve_ink:
        ld a,6
        ld (cell_case),a
        ret
resolve_raw:
        ld a,8
        ld (cell_case),a
        ret
