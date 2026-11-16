; Slot6 code runs on a private stack; neither an original C000 stack nor its
; return word can disappear when page56 is mapped. IRQs keep native ROM/MMU.
paint_call_setup:
        ld hl,paint_setup
        jr paint_call
paint_call_prepare:
        ld hl,paint_prepare
paint_call:
        ld (paint_jump+1),hl
        ld (paint_call_sp),sp
        ld sp,0x3C80
        ld bc,0x243B
        ld a,0x56
        out (c),a
        inc b
        in a,(c)
        ld (paint_call_m6),a
        nextreg 0x56,56
paint_jump:
        call paint_setup
        ld a,(paint_call_m6)
        nextreg 0x56,a
        ld sp,(paint_call_sp)
        ret
paint_call_sp: dw 0
paint_call_m6: db 0
paint_next_bank: db 32
