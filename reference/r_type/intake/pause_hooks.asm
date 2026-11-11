; Original pause is Caps Shift+1, resume Caps Shift+2 (8B77 path, GAME PAUSED at C49A).
; Fold the last published frame once; holding pause repeats its native CALL.
        MACRO PAUSE_ENTRY label,value
label:
        call 0xC2C5
        push af
        ld a,r
        ld (pause_r),a
        ld a,value
        ld (pause_mode),a
        pop af
        jp pause_common
        ENDM
        PAUSE_ENTRY pause_enter,1
        PAUSE_ENTRY pause_leave,0
pause_common:
        call hook_save
        ld (pause_sp),sp
        ld sp,0x3D00
        ld bc,0x243B
        ld a,7
        out (c),a
        inc b
        in a,(c)
        and 3
        ld (pause_speed),a
        nextreg 7,3
        dec b
        ld a,0x56
        out (c),a
        inc b
        in a,(c)
        ld (pause_mmu6),a
        ld a,(pause_mode)
        or a
        jr z,.resume
        ld a,(pause_active)
        or a
        jr nz,.finish
        inc a
        ld (pause_active),a
        nextreg 0x56,45
        ld hl,0x4000
        ld de,0xC000
        ld bc,6912
        call move
        call fold_foreground
        nextreg 0x6B,0
        jr .finish
.resume:
        xor a
        ld (pause_active),a
        nextreg 0x56,45
        ld hl,0xC000
        ld de,0x4000
        ld bc,6912
        call move
        nextreg 0x6B,0x8B
.finish:
        ld a,(pause_mmu6)
        nextreg 0x56,a
        call hook_load
        push af
        ld a,(pause_speed)
        nextreg 7,a
        ld a,(pause_r)
        and 128
        ld (.bit+1),a
        ld a,(pause_r)
        sub 8
        and 127
.bit:   or 0
        ld r,a
        pop af
        ld sp,(pause_sp)
        ret
fold_foreground:
        nextreg 0x56,44
        nextreg 0x50,40
        ld hl,0x148
        ld (pause_map),hl
        ld hl,0xC000
        ld iy,source_rows
        ld c,20
.row:   ld e,(iy+0)
        ld d,(iy+1)
        inc iy
        inc iy
        ld b,32
.cell:  ld a,(hl)
        or a
        jr z,.next
        push bc
        push de
        push hl
        ld hl,(pause_map)
        ld a,(hl)
        inc hl
        ld b,(hl)
        ld l,a
        ld a,b
        and 1
        ld h,a
        DUP 3
        add hl,hl
        EDUP
        ld bc,0xC00
        add hl,bc
        ld a,d
        sub 0x20
        ld d,a
        DUP 8
        ld a,(de)
        or (hl)
        ld (de),a
        inc hl
        inc d
        EDUP
        pop hl
        push hl
        ld bc,640
        add hl,bc
        ld b,(hl)
        pop hl
        push hl
        ld a,h
        sub 0x68
        ld h,a
        ld (hl),b
        pop hl
        pop de
        pop bc
.next:
        push hl
        ld hl,(pause_map)
        inc hl
        inc hl
        ld (pause_map),hl
        pop hl
        inc hl
        inc e
        djnz .cell
        push hl
        ld hl,(pause_map)
        ld a,l
        add a,16
        ld l,a
        jr nc,.map_ok
        inc h
.map_ok:
        ld (pause_map),hl
        pop hl
        dec c
        jp nz,.row
        nextreg 0x50,0xFF
        ret
pause_mode: db 0
pause_r: db 0
pause_sp: dw 0
pause_mmu6: db 0
pause_speed: db 0

pause_map: dw 0

pause_active: db 0
