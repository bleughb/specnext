; Accelerate the four unchanged figure producers; their saved native time becomes
; credit for the later copier/colour-preparation window, rather than speeding play.
fast_setup:
        push bc
        push de
        push hl
        ld bc,0x243B
        ld a,7
        out (c),a
        inc b
        in a,(c)
        and 3
        ld (fast_speed),a
        nextreg 7,3
        HLIB_IFF_DI
        jp po,.off
        ld a,1
        ld (fast_iff),a
        ei
        jr .latched
.off:   xor a
        ld (fast_iff),a
.latched:
        call hlib_pace_open
        ld hl,10                 ; three saves, CALLfast_setup, entry PUSHAF
        add hl,sp
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld (fast_return+1),de
        ld de,fast_leave
        ld (hl),d
        dec hl
        ld (hl),e
        pop hl
        pop de
        pop bc
        ret
fast_leave:
        push af
        ld a,r
        ld (fast_r),a
        pop af
        call hook_save
        ld (fast_sp),sp
        ld sp,0x3D00
        call hlib_pace_tick
        ld hl,(HLIB_V_PACE+2)
        push hl
        ld a,104
        call hlib_mul8
        ld a,(fast_speed)
        ld b,a
        or a
        jr z,.scaled
.shift: srl h
        rr l
        djnz .shift
.scaled:
        ld a,(fast_iff)
        or a
        jr nz,.credit
        pop de
        xor a
        call hlib_pace_wait
        jr .restore
.credit:
        pop de
        DUP 4
        sla e
        rl d
        EDUP
        or a
        sbc hl,de
        jr nc,.positive
        ld hl,0
.positive:
        ld de,(fast_credit)
        add hl,de
        jr nc,.store
        ld hl,0xFFFF
.store: ld (fast_credit),hl
        xor a
        ld (HLIB_V_PACE+10),a
.restore:
        call hook_load
        push af
        ld a,(fast_speed)
        nextreg 7,a
        ld a,(fast_r)
        and 128
        ld (.bit+1),a
        ld a,(fast_r)
        sub 7
        and 127
.bit:   or 0
        ld r,a
        pop af
        ld sp,(fast_sp)
fast_return:
        jp 0
fast_speed: db 0
fast_iff: db 0
fast_r: db 0
fast_sp: dw 0
fast_credit: dw 0
