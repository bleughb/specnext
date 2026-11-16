live_lookup:
        push hl
        push bc
        push iy
        ld a,1
        ld (irq_slot2_active),a
        nextreg 0x50,56
        call live_lookup_code
        nextreg 0x52,42
        ld a,0
        ld (irq_slot2_active),a
        nextreg 0x50,0xFF
        ld a,(dyn_page)
        nextreg 0x56,a
        pop iy
        pop bc
        pop hl
        ret
