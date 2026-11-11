; Whole-copier diagnostic. Private stack avoids scribbling live game RAM.
; Initial IFF is recorded before DI; source copier executes with original registers.
; Return R tracks the actual copier M1 span. IRQ R consumers still need supplied-R proof.
hook_entry:
        push af
        ld a,r
        ld (hook_r_entry),a
        and 0x80
        ld (hook_r_bit+1),a
        ; Latch the caller's clock before the brief IFF latch. Expensive register
        ; saving runs with IRQs enabled on a valid game/private stack.
        push bc
        ld bc,0x243B
        ld a,7
        out (c),a
        inc b
        in a,(c)
        and 3
        ld (hook_speed),a
        nextreg 7,3
        pop bc
        HLIB_IFF_DI
        jp po,.off
        ld a,1
        ld (hook_iff),a
        pop af
        ei
        jr .saved
.off:   xor a
        ld (hook_iff),a
        pop af
.saved: call hook_save
        ld (hook_sp),sp
        ld sp,0x3D00
        ld bc,0x243B
        ld a,0x56
        out (c),a
        inc b
        in a,(c)
        ld (hook_mmu6),a
        nextreg 7,3
        ld a,(hook_iff)
        or a
        jp z,hook_off_copy
        IFDEF RT_PACE
        call hlib_pace_open
        RT_NEST_OPEN
        ENDIF
        ei
.safe:
        IFDEF RT_PACE
        RT_DEBT_TICK
        ENDIF
        call hlib_now
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
        IFDEF RT_BULKULA
.bulk_wait:
        RT_DEBT_TICK
        call hlib_now
        ld de,150
        or a
        sbc hl,de
        jr c,.bulk_wait
        IFDEF RT_TILEMAP
        ld de,45               ; tail starts below195; measure publication <247
        ELSE
        ld de,30               ; larger111-pattern sprite payload
        ENDIF
        or a
        sbc hl,de
        jr nc,.bulk_wait
        jp tail_begin
        ELSE
.prev:
        IFDEF RT_PACE
        RT_DEBT_TICK
        ENDIF
        call hlib_now
        ld de,150
        or a
        sbc hl,de
        jr nc,.prev
.wait:
        IFDEF RT_PACE
        RT_DEBT_TICK
        ENDIF
        call hlib_now
        ld de,150
        or a
        sbc hl,de
        jr c,.wait
        jp tail_begin
        ENDIF
hook_finish:
        IFDEF RT_CELL
        call cell_budget
        ENDIF
        IFDEF RT_PACE
        xor a
        RT_NEST_CLOSE
        ENDIF
        di
        ld a,(hook_mmu6)
        nextreg 0x56,a
        ld a,(hook_speed)
        nextreg 7,a
        IFDEF RT_PACE
        ei
        ld c,a
pace_k:
        ld a,104
        IFDEF RT_CREDIT
        call hlib_pace_tick
        ld hl,(HLIB_V_PACE+2)
        ld a,104
        call hlib_mul8
        ld a,(hook_speed)
        ld b,a
        or a
        jr z,.copy_scaled
.copy_scale:
        srl h
        rr l
        djnz .copy_scale
.copy_scaled:
        IFDEF RT_FASTPLOTS
        ld de,(fast_credit)
        ENDIF
        IFDEF RT_CELL
        ld de,(cell_lines)
        ENDIF
        add hl,de
        jr nc,.copy_target
        ld hl,0xFFFF
.copy_target:
        IFDEF RT_FASTPLOTS
        ld de,0
        ld (fast_credit),de
        ENDIF
        xor a
        call hlib_pace_wait
        ELSE
        call hlib_pace_waitk
        ENDIF
        nextreg 7,3
.return_safe:
        call hlib_now
        ld de,242
        or a
        sbc hl,de
        jr c,.return_ready
        ld de,7
        or a
        sbc hl,de
        jr c,.return_safe
.return_ready:
        di
        ENDIF
        call hook_load
restore_control:
        nop
        nop
        nop
        nop
        push af
        ld a,(hook_iff)
        or a
        jr z,.iff_off
        ei
.iff_off:
        IFDEF RT_PACE
        ld a,(hook_speed)
        nextreg 7,a
        ENDIF
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
hook_off_copy:
        ; DI callers cannot wait for native IRQs. Run the unmodified copier,
        ; expose its original ULA and return DI. Recording verification classifies callers.
        call hook_load
        jp hook_copy_start
hook_off_finish:
        IFDEF RT_TILEMAP
        nextreg 0x6B,0
        ELSE
        nextreg 0x15,0
        ENDIF
        ld a,(hook_mmu6)
        nextreg 0x56,a
        ld a,(hook_speed)
        nextreg 7,a
        call hook_load
        jp restore_control
hook_unsupported:
        di
        halt
        jr hook_unsupported
original_copy:
        ld ix,0x8080
        jp 0x8846

hook_setup:
        IFNDEF RT_TILEMAP
        IFDEF RT_CELL
        call spritepaint_setup
        ENDIF
        ENDIF
        nextreg 0x64,0
        IFDEF RT_TILEMAP
        call tile_setup
        ELSE
        nextreg 0x15,1
        ENDIF
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

        INCLUDE "text_classifier.asm"

        INCLUDE "paper_mask.asm"
