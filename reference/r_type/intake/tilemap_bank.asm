; Relocate immutable bank7 assets to physical bank24. Original bank1/3/4/6 reads
; keep their original paging instruction; bank7 reads use a temporary slot0 alias.
; Return to 8F24, which still restores the native 7FFD latch to bank1.
bank_read:
        ld (bank_value),a
        push af
        ld a,r
        ld (bank_r),a
        push bc
        push hl
        ld a,(bank_value)
        and 7
        cp 7
        jr z,.alias
        ld a,(bank_value)
        out (c),a
        ld e,(hl)
        jr .done
.alias: ld a,h
        and 0x20
        DUP 5
        rrca
        EDUP
        add a,48
        nextreg 0x50,a
        res 7,h
        res 6,h
        res 5,h
        ld e,(hl)
        nextreg 0x50,0xFF
.done:  pop hl
        pop bc
        ld a,(bank_r)
        and 128
        ld (.bit+1),a
        ld a,(bank_r)
        sub 4                   ; entry captured R0+5; POP/JP2; original span3
        and 127
.bit:   or 0
        ld r,a
        pop af
        jp 0x8F24
bank_value: db 0
bank_r: db 0
