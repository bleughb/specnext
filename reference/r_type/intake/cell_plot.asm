; Bounded trial: accelerate only successful 8x8 cell writers, retaining exact
; original helper and row instructions. Fixed spans permit CPU-cycle accounting
; without counting added wrapper work as original work. Not yet pace-enabled.
        IFDEF RT_INLINE
        INCLUDE "cell_inline.asm"
        ENDIF
cell_entry:
        ; Original code is fixed at 3.5MHz; latch inherited clock at plot entry.
        ; The cell gate will assert this contract in integrated JNext checks.
        IFNDEF RT_INLINE
        nextreg 7,3
        ENDIF
        push af
        ld a,r
        ld (cell_r),a
        ld a,(plot_iff)
        or a
        IFDEF RT_INLINE
        jp z,cell_off_inline
        ELSE
        jp z,cell_off
        ENDIF
        ld a,(plot_speed)
        ld (cell_restore_speed+3),a
        pop af
        ld (cell_src),hl
        ld (cell_owner),de
        ld (cell_sp),sp
        ld sp,0x3D00
        push af
        push bc
        push hl
        IFDEF RT_INLINE
        ld (cell_kind),a
        ELSE
        ld hl,(cell_sp)
        ld a,(hl)
        ld (cell_kind),a
        ENDIF
        ld a,(0x8EB1)
        or a
        ld a,0
        jr z,.native
        inc a
.native:
        ld (cell_override),a
        pop hl
        pop bc
        pop af
        ld a,(0x7A9C)
        call 0x8EA5
        IFDEF RT_RESOLVED
        call cell_resolve
        ENDIF
        push af
        push hl
        ld a,(cell_kind)
        cp 0x2A
        jp z,.normal
        cp 0x91
        jp z,.horizontal
        cp 0xFD
        jp z,.vertical
        cp 0x57
        jp z,.both
.invalid:
        di
        halt
        jr .invalid
.normal:
        ld hl,0x8D4C
        call cell_target
        ld a,51                ; original helper + JP Z + complete row body M1
        ld (cell_span),a
        xor a
        ld (cell_flip),a
        pop hl
        pop af
        ld d,a
        DUP 7
        ld a,(hl)
        ld (de),a
        inc hl
        inc d
        EDUP
        ld a,(hl)
        ld (de),a
        jp cell_done
.horizontal:
        ld hl,0x8DBA
        call cell_target
        ld a,59
        ld (cell_span),a
        ld a,1
        ld (cell_flip),a
        pop hl
        pop af
        ld d,a
        DUP 7
        ld c,(hl)
        ld a,(bc)
        ld (de),a
        inc hl
        inc d
        EDUP
        ld c,(hl)
        ld a,(bc)
        ld (de),a
        jp cell_done
.vertical:
        ld hl,0x8E10
        call cell_target
        ld a,75
        ld (cell_span),a
        ld a,2
        ld (cell_flip),a
        pop hl
        pop af
        add a,7
        ld d,a
        ld ixl,7
.vloop: ld a,(hl)
        ld (de),a
        inc hl
        dec d
        dec ixl
        jp nz,.vloop
        ld a,(hl)
        ld (de),a
        jp cell_done
.both:
        ld hl,0x8E6C
        call cell_target
        ld a,83
        ld (cell_span),a
        ld a,3
        ld (cell_flip),a
        pop hl
        pop af
        add a,7
        ld d,a
        ld ixl,7
.bloop: ld c,(hl)
        ld a,(bc)
        ld (de),a
        inc hl
        dec d
        dec ixl
        jp nz,.bloop
        ld c,(hl)
        ld a,(bc)
        ld (de),a
cell_done:
        push af
        push bc
        push de
        push hl
        ; Descriptor is tied to the successful owner write, not a bounding box.
        IFDEF RT_RESOLVED
        nextreg 0x50,50
        ld hl,(cell_owner)
        ld a,h
        sub 0x7E
        ld h,a
        DUP 3
        add hl,hl
        EDUP
        ld de,(cell_src)
        ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        ld de,(cell_group)
        ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        ld a,(cell_flip)
        ld (hl),a
        inc hl
        ld a,(cell_ci)
        ld (hl),a
        inc hl
        ld de,(cell_owner)
        ld a,(de)
        ld (hl),a
        inc hl
        ld a,(0x719C)
        ld (hl),a
        nextreg 0x50,0xFF
        ELSE
        nextreg 0x50,50
        ld de,(cell_owner)
        ld a,d
        sub 0x7E
        ld d,a
        ld h,d
        ld l,e
        add hl,hl
        add hl,de
        add hl,hl              ; 6 * index
        ld de,(cell_src)
        ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        ld a,(cell_flip)
        ld (hl),a
        inc hl
        ld de,(cell_owner)
        ld a,d
        sub 6
        ld d,a
        ld a,(de)              ; actual effective attribute, including override
        ld (hl),a
        inc hl
        ld de,(cell_owner)
        ld a,(de)
        ld (hl),a
        inc hl
        ld a,(0x719C)
        ld (hl),a
        nextreg 0x50,0xFF
        ENDIF
        ; Exact saved CPU cycles in 28MHz units, including this bookkeeping.
        ; Timer quantisation and new wrapper work never become native-time credit.
        ld a,(cell_override)
        add a,a
        add a,a
        ld hl,cell_flip
        add a,(hl)
        IFDEF RT_RESOLVED
        ld b,a
        ld a,(cell_case)
        add a,a
        add a,a
        add a,a
        add a,b
        ENDIF
        add a,a
        ld l,a
        ld h,cell_savings/256
        ld e,(hl)
        inc l
        ld d,(hl)
        IFDEF RT_RESOLVED
        ld a,d
        add a,a
        sbc a,a
        ld (cell_adc+1),a
        ENDIF
        ld hl,(cell_credit)
        add hl,de
        ld (cell_credit),hl
        ld a,(cell_credit+2)
cell_adc:
        adc a,0
        ld (cell_credit+2),a
        pop hl
        pop de
        pop bc
        pop af
        push af
        ld a,(cell_override)
        ld (cell_add+1),a
        ld a,(cell_span)
cell_add:
        add a,0
        ld (cell_add_r+1),a
        ld a,(cell_r)
        and 128
        ld (cell_bit+1),a
        ld a,(cell_r)
cell_add_r:
        add a,0
        IFDEF RT_INLINE
        sub 13                 ; capture8; tail6; original CALL adds1 to span
        ELSE
        sub 12                 ; capture6; tail6
        ENDIF
        and 127
cell_bit:
        or 0
        ld (cell_restore_r+1),a
cell_restore_r:
        ld a,0
        ld r,a
        pop af
        ld sp,(cell_sp)
cell_restore_speed:
        nextreg 7,0
        IFDEF RT_INLINE
cell_return:
        jp 0
        ELSE
        ret
        ENDIF
cell_target:
        IFDEF RT_INLINE
        ld (cell_return+1),hl
        ret
        ELSE
        ; Replace the helper's popped return word with the row-end continuation.
        push de
        ex de,hl
        ld hl,(cell_sp)
        ld (hl),e
        inc hl
        ld (hl),d
        pop de
        ret
        ENDIF
cell_r: db 0
cell_speed: db 0
cell_sp: dw 0
cell_src: dw 0
cell_owner: dw 0
cell_kind: db 0
cell_page: db 0
cell_flip: db 0
cell_override: db 0
cell_span: db 0

; Generated constants are checked against complete original/hook invocations.
        ALIGN 256
cell_savings:
        IFDEF RT_RESOLVED
        IFDEF RT_INLINE
        INCLUDE "cell_inline_costs.asm"
        ELSE
        INCLUDE "cell_resolved_costs.asm"
        ENDIF
        ELSE
        dw 657,1005,1604,1989,707,1055,1654,2039
        ENDIF
cell_credit: ds 3,0
cell_lines: dw 0
cell_budget:
        ld hl,(cell_credit)
        ld a,(cell_credit+2)
        IFDEF RT_RESOLVED
        ld c,a
        and 128
        ld (cell_budget_sign),a
        ld a,c
        jr z,.magnitude
        ld b,a
        ex de,hl
        ld hl,0
        or a
        sbc hl,de
        ld a,0
        sbc a,b
.magnitude:
        ENDIF
        ld e,0
        ld b,24
.div:   add hl,hl
        rla
        rl e
        ld d,a
        ld a,e
        sub 114                ; 228 native T per line * 8 / 16
        jr c,.small
        ld e,a
        inc l
.small: ld a,d
        djnz .div
        or a
        jp nz,cell_entry.invalid
        IFDEF RT_RESOLVED
        ld a,e
        ld (cell_remainder),a
        ld a,(cell_budget_sign)
        or a
        jr nz,.negative
        ENDIF
        ld (cell_lines),hl
        ld a,e
        ld (cell_credit),a
        xor a
        ld (cell_credit+1),a
        ld (cell_credit+2),a
        ret
        IFDEF RT_RESOLVED
.negative:
        ld de,0
        ld (cell_lines),de
        call hlib_debt_add
        ld a,(cell_remainder)
        neg
        ld (cell_credit),a
        sbc a,a
        ld (cell_credit+1),a
        ld (cell_credit+2),a
        ret
cell_budget_sign: db 0
cell_remainder: db 0
        ENDIF

; A native DI plot keeps its original helper/rows and contributes no time credit.
cell_off:
        ld a,(plot_speed)
        ld (.speed+3),a
        ld a,(cell_r)
        and 128
        ld (.bit+1),a
        ld a,(cell_r)
        sub 10                 ; capture +6; POP/LD A/NEXTREG/JP +5; prefix1
        and 127
.bit:   or 0
        ld r,a
        pop af
        ld a,(0x7A9C)
.speed: nextreg 7,0
        jp 0x8EA5

        IFDEF RT_RESOLVED
        INCLUDE "cell_resolve_bridge.asm"
        ENDIF

        IFDEF RT_INLINE
        INCLUDE "cell_off_inline.asm"
        ENDIF
