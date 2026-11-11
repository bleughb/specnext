; 40x32 map at 0000, 512 x 8-byte glyphs at 0C00 in bank7 lower BRAM.
; 0 is a blank transparent glyph. Figure cells use independently coloured 1-bit glyphs.
dynamic_patterns:
        nextreg 0x56,40
        ld a,0x24
        ld (mem_prog+7),a
        ld hl,dyn_zero
        ld (mem_src),hl
        ld hl,0xC000
        ld (mem_dst),hl
        ld hl,8192
        ld (mem_len),hl
        ld hl,mem_prog
        ld bc,(mem_end-mem_prog)*256+0x6B
        otir
        ld a,0x14
        ld (mem_prog+7),a
        ld hl,1
        ld (tile_count),hl
        ld hl,0xCC08
        ld (tile_dest),hl
        ld hl,0xC148             ; (4*40+4)*2, aligned to ULA paper at32,32
        ld (tile_map),hl
        ld iy,source_rows
        ld ix,0x7E00
        xor a
        ld (tile_row),a
.row:   ld e,(iy+0)
        ld d,(iy+1)
        inc iy
        inc iy
        ld a,32
        ld (tile_col),a
.cell:  ld a,(ix+0)
        or a
        jp z,.next
        cp 0xDC
        jp nc,.next
        ld l,a
        ld h,text_owners/256
        ld a,(hl)
        or a
        jp nz,.next
        ; Skip all-zero bitmaps before assigning a glyph.
        push de
        ld h,d
        ld l,e
        xor a
        DUP 8
        or (hl)
        inc h
        EDUP
        pop de
        or a
        jr z,.next
        ld hl,(tile_count)
        ld a,h
        cp 2
        jp nc,tile_overflow
        push de
        ld bc,(tile_map)
        ld a,l
        ld (bc),a
        inc bc
        ld a,h
        ld (tile_high),a
        ; Attribute is source ink/bright as a text-mode palette group.
        push ix
        pop hl
        ld a,h
        sub 6
        ld h,a
        ld a,(hl)
        and 0x47
        ld l,a
        and 7
        ld h,a
        ld a,l
        and 0x40
        jr z,.normal
        ld a,h
        or 8
        ld h,a
.normal:
        ld a,h
        or a
        jr nz,.colour
        ld a,8
.colour:
        add a,a
        ld h,a
        ld a,(tile_high)
        or h
        ld (bc),a
        pop de
        ; Gather a nonlinear ZX cell directly; no bit expansion.
        push de
        ld h,d
        ld l,e
        ld de,(tile_dest)
        DUP 8
        ld a,(hl)
        ld (de),a
        inc de
        inc h
        EDUP
        ld (tile_dest),de
        pop de
        ld hl,(tile_count)
        inc hl
        ld (tile_count),hl
.next:  inc e
        inc ix
        ld hl,(tile_map)
        inc hl
        inc hl
        ld (tile_map),hl
        ld hl,tile_col
        dec (hl)
        jp nz,.cell
        ld hl,(tile_map)
        ld bc,16
        add hl,bc
        ld (tile_map),hl
        ld hl,tile_row
        inc (hl)
        ld a,(hl)
        cp 20
        jp nc,.ready
        IFDEF RT_PACE
        push de
        push ix
        push iy
        RT_DEBT_TICK
        pop iy
        pop ix
        pop de
        ENDIF
        jp .row
.ready:
        IFDEF RT_PAINT
        call paint_call_prepare
        ENDIF
        nextreg 0x56,42
        ret
tile_overflow:
        di
        halt
        jr tile_overflow

tile_setup:
        IFDEF RT_PAINT
        call paint_call_setup
        ENDIF
        nextreg 0x15,0
        nextreg 0x6B,0
        nextreg 0x6E,0x80
        nextreg 0x6F,0x8C
        nextreg 0x4C,0
        nextreg 0x14,0xE3
        nextreg 0x2F,0
        nextreg 0x30,0
        nextreg 0x31,0
        nextreg 0x1C,8
        nextreg 0x1B,16
        nextreg 0x1B,143
        nextreg 0x1B,32
        nextreg 0x1B,191
        nextreg 0x43,0x30
        nextreg 0x40,0
        ld hl,tile_palette
        ld b,32
.pal:   ld a,(hl)
        nextreg 0x41,a
        inc hl
        djnz .pal
        nextreg 0x43,0
        ret

tile_publish:
        ; Native bank7 game assets must be relocated before this is enabled.
        nextreg 0x56,40
        nextreg 0x50,14
        ld hl,0xC000
        ld de,0
        ld bc,7168
        call move
        nextreg 0x50,0xFF
        nextreg 0x6B,0x8B
        IFDEF RT_PAINT
        ld a,(paint_next_bank)
        nextreg 0x12,a
        nextreg 0x69,0x80
        ENDIF
        ld bc,64
        ld (mem_len),bc
        ret

tile_count: dw 1
tile_dest: dw 0
tile_map: dw 0
tile_row: db 0
tile_col: db 0
tile_high: db 0
dyn_zero: db 0
        ALIGN 256
text_owners: ds 256,0
tile_palette:
        db 0xE3,0,0xE3,2,0xE3,0xA0,0xE3,0xA2
        db 0xE3,0x14,0xE3,0x16,0xE3,0xB4,0xE3,0xB6
        db 0xE3,0,0xE3,3,0xE3,0xE0,0xE3,0xE7
        db 0xE3,0x1C,0xE3,0x1F,0xE3,0xFC,0xE3,0xFF

        INCLUDE "tilemap_bank.asm"

        INCLUDE "pause_hooks.asm"

        IFDEF RT_FASTPLOTS
        INCLUDE "fast_plots.asm"
        ENDIF

        IFDEF RT_CELL
        INCLUDE "cell_plot.asm"
        ENDIF

        IFDEF RT_PAINT
        INCLUDE "paint_bridge.asm"
        ENDIF
