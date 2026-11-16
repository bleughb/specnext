; Cost-only static-texture stress trial. First frozen frame has an independent
; RGB oracle; later frames measure copying/clearing cost, not correct live art.
paint_setup:
        nextreg 0x69,0
        nextreg 0x70,0
        nextreg 0x12,32
        nextreg 0x13,35
        nextreg 0x43,0x10
        nextreg 0x40,0
        nextreg 0x41,0xE3
        xor a
.pal:   nextreg 0x41,a
        inc a
        cp 0xE3
        jr nz,.pal
        inc a
.last:  nextreg 0x41,a
        inc a
        jr nz,.last
        nextreg 0x43,0
        ret
paint_prepare:
        ld a,1
        ld (irq_slot2_active),a
        ld a,(paint_index)
        or a
        ld iy,paint_dirty
        jr z,.dirty
        ld iy,paint_dirty+640
.dirty: ld hl,0x0148
        ld (paint_tile),hl
        ld hl,0
        ld (paint_desc),hl
        xor a
        ld (paint_y),a
.row:   xor a
        ld (paint_x),a
.cell:  nextreg 0x50,40
        ld hl,(paint_tile)
        ld a,(hl)
        inc hl
        or (hl)
        jr z,.empty
        xor a
        ld (hl),a
        dec hl
        ld (hl),a
        ld (iy+0),1
        nextreg 0x50,51
        ld hl,(paint_desc)
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld (paint_source),de
        inc hl
        ld a,(hl)
        ld (paint_page),a
        inc hl
        ld a,(hl)
        ld (paint_flip),a
        inc hl
        ld a,(hl)
        ld (paint_skip),a
        jr .draw
.empty:
        ld a,(iy+0)
        or a
        jp z,paint_next
        ld (iy+0),0
        ld hl,0
        ld (paint_source),hl
        xor a
        ld (paint_flip),a
        inc a
        ld (paint_skip),a
        ld a,101
        ld (paint_page),a
.draw:  ld a,(paint_y)
        srl a
        srl a
        ld hl,paint_hidden
        add a,(hl)
        nextreg 0x52,a
        ld a,(paint_y)
        and 3
        DUP 3
        add a,a
        EDUP
        add a,0x40
        ld d,a
        ld a,(paint_x)
        DUP 3
        add a,a
        EDUP
        ld e,a
        ld a,(paint_page)
        nextreg 0x50,a
        ld hl,(paint_source)
        ld a,(paint_flip)
        and 3
        add a,a
        ld c,a
        ld b,0
        push hl
        ld hl,paint_offsets
        add hl,bc
        ld c,(hl)
        inc hl
        ld b,(hl)
        pop hl
        add hl,bc
        push hl
        ld a,(paint_flip)
        and 3
        add a,a
        ld l,a
        ld h,0
        ld bc,paint_functions
        add hl,bc
        ld c,(hl)
        inc hl
        ld b,(hl)
        ld (paint_dispatch+1),bc
        pop hl
        ld a,(paint_skip)
paint_dispatch:
        jp paint_normal
paint_normal:
        DUP 8
        ldix
        EDUP
        add de,248
        DUP 8
        ldix
        EDUP
        add de,248
        DUP 8
        ldix
        EDUP
        add de,248
        DUP 8
        ldix
        EDUP
        add de,248
        DUP 8
        ldix
        EDUP
        add de,248
        DUP 8
        ldix
        EDUP
        add de,248
        DUP 8
        ldix
        EDUP
        add de,248
        DUP 8
        ldix
        EDUP
        jp paint_done
paint_mirror:
        DUP 8
        lddx
        EDUP
        add hl,16
        add de,248
        DUP 8
        lddx
        EDUP
        add hl,16
        add de,248
        DUP 8
        lddx
        EDUP
        add hl,16
        add de,248
        DUP 8
        lddx
        EDUP
        add hl,16
        add de,248
        DUP 8
        lddx
        EDUP
        add hl,16
        add de,248
        DUP 8
        lddx
        EDUP
        add hl,16
        add de,248
        DUP 8
        lddx
        EDUP
        add hl,16
        add de,248
        DUP 8
        lddx
        EDUP
        jp paint_done
paint_vertical:
        DUP 8
        ldix
        EDUP
        add hl,-16
        add de,248
        DUP 8
        ldix
        EDUP
        add hl,-16
        add de,248
        DUP 8
        ldix
        EDUP
        add hl,-16
        add de,248
        DUP 8
        ldix
        EDUP
        add hl,-16
        add de,248
        DUP 8
        ldix
        EDUP
        add hl,-16
        add de,248
        DUP 8
        ldix
        EDUP
        add hl,-16
        add de,248
        DUP 8
        ldix
        EDUP
        add hl,-16
        add de,248
        DUP 8
        ldix
        EDUP
        jp paint_done
paint_both:
        DUP 8
        lddx
        EDUP
        add de,248
        DUP 8
        lddx
        EDUP
        add de,248
        DUP 8
        lddx
        EDUP
        add de,248
        DUP 8
        lddx
        EDUP
        add de,248
        DUP 8
        lddx
        EDUP
        add de,248
        DUP 8
        lddx
        EDUP
        add de,248
        DUP 8
        lddx
        EDUP
        add de,248
        DUP 8
        lddx
        EDUP
        jp paint_done
paint_done:
        nextreg 0x52,42
        nextreg 0x50,40
paint_next:
        ld a,(paint_x)
        and 7
        jr nz,$+5
        RT_DEBT_TICK
        inc iy
        ld hl,(paint_desc)
        ld bc,6
        add hl,bc
        ld (paint_desc),hl
        ld hl,(paint_tile)
        inc hl
        inc hl
        ld (paint_tile),hl
        ld hl,paint_x
        inc (hl)
        ld a,(hl)
        cp 32
        jp nz,paint_prepare.cell
        ld hl,(paint_tile)
        ld bc,16
        add hl,bc
        ld (paint_tile),hl
        ld hl,paint_y
        inc (hl)
        ld a,(hl)
        cp 20
        jp nz,paint_prepare.row
        ld a,(paint_hidden)
        srl a
        ld (paint_next_bank),a
        ld a,(paint_hidden)
        xor 6
        ld (paint_hidden),a
        ld a,(paint_index)
        xor 1
        ld (paint_index),a
        nextreg 0x52,42
        ld a,0
        ld (irq_slot2_active),a
        nextreg 0x50,0xFF
        ret
paint_offsets: dw 0,7,56,63
paint_functions: dw paint_normal,paint_mirror,paint_vertical,paint_both
paint_hidden: db 70
paint_index: db 0
paint_x: db 0
paint_y: db 0
paint_tile: dw 0
paint_desc: dw 0
paint_source: dw 0
paint_page: db 0
paint_flip: db 0
paint_skip: db 0
paint_dirty: ds 1280,0
