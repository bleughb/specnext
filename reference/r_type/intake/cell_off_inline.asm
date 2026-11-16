; Native DI UI keeps the original helper and remaining row loop at caller speed.
cell_off_inline:
        pop af
        ld (cell_kind),a
        ld (cell_sp),sp
        ld sp,0x3D00
        ld a,(plot_speed)
        ld (cell_off_speed+3),a
        nextreg 7,a
        call 0x8EA2
        push af
        nextreg 7,3
        push hl
        ld a,(cell_kind)
        cp 0x2A
        jr z,.n
        cp 0x91
        jr z,.h
        cp 0xFD
        jr z,.v
        ld hl,0x8E5B
        ld (cell_off_jump+1),hl
        ld a,22
        ld (cell_off_span),a
        pop hl
        pop af
        add a,7
        jr .repair
.n:     ld hl,0x8D2E
        ld (cell_off_jump+1),hl
        ld a,22
        ld (cell_off_span),a
        pop hl
        pop af
        ld d,a
        jr .repair
.h:     ld hl,0x8D95
        ld (cell_off_jump+1),hl
        ld a,23
        ld (cell_off_span),a
        pop hl
        pop af
        ld d,a
        ld c,(hl)
        jr .repair
.v:     ld hl,0x8E01
        ld (cell_off_jump+1),hl
        ld a,22
        ld (cell_off_span),a
        pop hl
        pop af
        add a,7
.repair:
        push af
        ld a,(0x8EB1)
        or a
        ld a,0
        jr z,.force
        inc a
.force: ld (cell_off_force+1),a
        ld a,(cell_off_span)
cell_off_force:
        add a,0
        ld (cell_off_add+1),a
        ld a,(cell_r)
        and 128
        ld (cell_off_bit+1),a
        ld a,(cell_r)
cell_off_add:
        add a,0
        sub 14                 ; inline capture8; POP/LDSP/NEXTREG/JP6
        and 127
cell_off_bit:
        or 0
        ld r,a
        pop af
        ld sp,(cell_sp)
cell_off_speed:
        nextreg 7,0
cell_off_jump:
        jp 0
cell_off_span: db 0
