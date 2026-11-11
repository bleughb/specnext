; 256 direct-mapped RAM entries: full 36-byte content key, complete 128-byte pattern.
; The RAM cache is independent of the 128 hardware pattern slots. No shown slot is evicted.
        MACRO KEYBYTE
        ld (de),a
        inc de
        ld b,a
        xor c
        rlca
        ld c,a
        ex af,af'
        or b
        ex af,af'
        ENDM
cache_key:
        xor a
        ld (cache_hash),a
        ex af,af'
        xor a
        ex af,af'
        ld de,cache_scratch
        ld a,(dyn_y)
        ld b,a
        ld a,(dyn_x)
        ld c,a
        call cache_cell
        ld a,(dyn_y)
        ld b,a
        ld a,(dyn_x)
        inc a
        ld c,a
        call cache_cell
        ld a,(dyn_y)
        inc a
        ld b,a
        ld a,(dyn_x)
        ld c,a
        call cache_cell
        ld a,(dyn_y)
        inc a
        ld b,a
        ld a,(dyn_x)
        inc a
        ld c,a
        call cache_cell
        ex af,af'
        ld (cache_nonzero),a
        ex af,af'
        ret
cache_cell:
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
        jp z,.blank
        cp 0xDC
        jp nc,.blank
        push hl
        ld l,a
        ld h,text_owners/256
        ld a,(hl)
        pop hl
        or a
        jp nz,.blank
        ld a,h
        sub 6
        ld h,a
        ld a,(hl)
        and 0x47
        ; Ink key does not make an all-zero bitmap block visible.
        ld (de),a
        inc de
        ld b,a
        ld a,(cache_hash)
        xor b
        rlca
        ld c,a
        ld a,h
        sub 0x78
        DUP 3
        add a,a
        EDUP
        add a,0x60
        ld h,a
        DUP 8
        ld a,(hl)
        KEYBYTE
        inc h
        EDUP
        ld a,c
        ld (cache_hash),a
        ret
.blank: xor a
        DUP 9
        ld (de),a
        inc de
        EDUP
        ld a,(cache_hash)
        rlca                       ; nine zero bytes rotate hash nine times
        ld (cache_hash),a
        ret
cache_descriptor:
        ld a,(cache_hash)
        ld b,a
        and 0x80
        rlca
        add a,52
        nextreg 0x50,a
        ld a,b
        and 127
        ld h,a
        ld l,0
        srl h
        rr l
        srl h
        rr l
        ret
cache_data:
        ld a,(cache_hash)
        ld b,a
        and 0xC0
        rlca
        rlca
        add a,48
        nextreg 0x50,a
        ld a,b
        and 63
        ld h,a
        ld l,0
        srl h
        rr l
        ret
cache_lookup:
        call cache_descriptor
        ld a,(hl)
        or a
        ret z
        inc hl
        ld de,cache_scratch
        ld b,36
.compare:
        ld a,(de)
        cp (hl)
        jr nz,.miss
        inc hl
        inc de
        djnz .compare
        call cache_data
        ld de,(dyn_dest)
        ld bc,128
        call move
        ld a,1
        ld (dyn_nonzero),a
        scf
        ret
.miss:  or a
        ret
cache_store:
        call cache_descriptor
        ld (hl),1
        inc hl
        ex de,hl
        ld hl,cache_scratch
        ld bc,36
        ldir
        call cache_data
        ex de,hl
        ld hl,(dyn_dest)
        ld bc,128
        call move
        ret
cache_hash: db 0
cache_nonzero: db 0
cache_scratch: ds 36,0
