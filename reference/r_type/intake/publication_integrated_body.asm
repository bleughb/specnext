; Whole-copier diagnostic. Private stack avoids scribbling live game RAM.
; Initial IFF is recorded before DI; source copier executes with original registers.
; Return R tracks the actual copier M1 span. IRQ R consumers still need supplied-R proof.
hook_entry:
        push af
        ld a,r
        ld (hook_r_entry),a
        and 0x80
        ld (hook_r_bit+1),a
        ld a,i
        di
        jp po,.off
        ld a,1
        jr .iff
.off:   xor a
.iff:   ld (hook_iff),a
        pop af
        call hook_save
        ld (hook_sp),sp
        ld sp,0x3D00
        ld bc,0x243B
        ld a,0x56
        out (c),a
        inc b
        in a,(c)
        ld (hook_mmu6),a
        dec b
        ld a,7
        out (c),a
        inc b
        in a,(c)
        ld (hook_speed),a
        nextreg 7,3
        ld a,(hook_iff)
        or a
        jp z,hook_unsupported
        ei
.safe:  call hlib_now
        ld de,210
        or a
        sbc hl,de
        jr c,.ready
        ld de,39
        or a
        sbc hl,de
        jr c,.safe
.ready:
        di
        jp prepare
hook_wait:
integrated_policy:
        ld a,1
        ld (hlib_dma_policy),a
.prev:  call hlib_now
        ld de,150
        or a
        sbc hl,de
        jr nc,.prev
.wait:  call hlib_now
        ld de,150
        or a
        sbc hl,de
        jr c,.wait
        jp tail_begin
hook_finish:
        di
        ld a,(hook_mmu6)
        nextreg 0x56,a
        ld a,(hook_speed)
        nextreg 7,a
        call hook_load
restore_control:
        nop
        nop
        nop
        nop
        ei
        push af
        ld a,(hook_r_entry)
hook_r_add:
        add a,0
        sub 8               ; entry JP/PUSH/LDAR=4, final POP/LDSP/RET=4
        and 127
hook_r_bit:
        or 0
        ld r,a
        pop af
        ld sp,(hook_sp)
hook_return:
        ret
hook_unsupported:
        di
        halt
        jr hook_unsupported
original_copy:
        ld ix,0x8080
        jp 0x8846

hook_setup:
        nextreg 0x64,0
        nextreg 0x15,1
        ; DMA capability checked; fail closed instead of a late CPU publication.
        ld a,1
        call hlib_dma_init
        ld a,(hlib_dma_cap)
        or a
        jp z,hook_unsupported
        ret
hook_save:
        ld (hook_regs+6),hl
        ld (hook_regs+2),bc
        ld (hook_regs+4),de
        ld (hook_regs+8),ix
        ld (hook_regs+10),iy
        push af
        pop hl
        ld (hook_regs),hl
        ex af,af'
        push af
        pop hl
        ld (hook_regs+12),hl
        ex af,af'
        exx
        ld (hook_regs+14),bc
        ld (hook_regs+16),de
        ld (hook_regs+18),hl
        exx
        ret
hook_load:
        exx
        ld bc,(hook_regs+14)
        ld de,(hook_regs+16)
        ld hl,(hook_regs+18)
        exx
        ld hl,(hook_regs+12)
        push hl
        pop af
        ex af,af'
        ld hl,(hook_regs)
        push hl
        pop af
        ld bc,(hook_regs+2)
        ld de,(hook_regs+4)
        ld hl,(hook_regs+6)
        ld ix,(hook_regs+8)
        ld iy,(hook_regs+10)
        ret
hook_iff: db 0
hook_sp: dw 0
hook_mmu6: db 0
hook_speed: db 0
hook_r_entry: db 0
hook_r_start: db 0
hook_regs: ds 20,0
