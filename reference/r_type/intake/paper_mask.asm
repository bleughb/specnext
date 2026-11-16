; Foreground classification captured before the copier consumes owner flags.
; Only shadow ULA paper is changed; ISR-mutated source attributes are never restored.
mask_init:
        nextreg 0x56,44
        ld a,0x24
        ld (mem_prog+7),a
        ld hl,dyn_zero
        ld (mem_src),hl
        ld hl,0xC000
        ld (mem_dst),hl
        ld hl,640
        ld (mem_len),hl
        ld hl,mem_prog
        ld bc,(mem_end-mem_prog)*256+0x6B
        otir
        ld a,0x14
        ld (mem_prog+7),a
        ret
mask_cell:
        push af
        push hl
        ld a,h
        add a,0x42
        ld h,a
        ld (hl),1
        pop hl
        pop af
        ret
clean_paper:
        nextreg 0x56,44
        IFDEF RT_POSTCLEAR
        ; Keep the exact original figure attributes for a native ULA pause view.
        ld hl,0x5800
        ld de,0xC280
        ld bc,640
        call move
        ld hl,0xC000
        ld iy,source_rows
        ld c,20
.row:   ld e,(iy+0)
        ld a,(iy+1)
        sub 0x20
        ld d,a
        inc iy
        inc iy
        ld b,32
.cell:  ld a,(hl)
        or a
        jr z,.next
        push de
        xor a
        DUP 8
        ld (de),a
        inc d
        EDUP
        pop de
        push hl
        ld a,h
        sub 0x68
        ld h,a
        ld a,(hl)
        and 0xC7
        ld (hl),a
        pop hl
.next:  inc hl
        inc e
        djnz .cell
        dec c
        jr nz,.row
        ret
        ELSE
        ld hl,0xC000
        ld de,0x5800
        ld bc,640
.loop:  ld a,(hl)
        or a
        jr z,.next
        ld a,(de)
        and 0xC7
        ld (de),a
.next:  inc hl
        inc de
        dec bc
        ld a,b
        or c
        jr nz,.loop
        ret
        ENDIF
