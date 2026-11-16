; Resolve while the original source page is already mapped. Slot6 code leaves
; native slot2 untouched; the original ISR never accesses slot6.
cell_resolve:
        push af
        push bc
        push de
        push hl
        ld hl,0xFFFF
        ld (cell_group),hl
        ld a,2
        ld (cell_case),a
        ld a,0
        ld (cell_ci),a
        ld a,(0x7A9C)
        dec a
        cp 0xDB
        jp nc,.done
        inc a
        ld l,a
        ld h,text_owners/256
        ld a,(hl)
        or a
        jr z,.figure
        ld a,3
        ld (cell_case),a
        jp .done
.figure:
        ld hl,(cell_src)
        inc hl
        ld de,cell_raw
        DUP 8
        ldi
        EDUP
        ld hl,(cell_owner)
        ld a,h
        sub 6
        ld h,a
        ld a,(hl)
        and 0x47
        ld e,a
        and 7
        ld d,a
        ld a,e
        rlca
        rlca
        and 1
        add a,a
        add a,a
        add a,a
        or d
        ld hl,cell_inks
        add hl,a
        ld a,(hl)
        ld (cell_ci),a
        nextreg 0x56,56
        call resolve_code
        nextreg 0x50,0xFF
        ld a,(plot_mmu6)
        nextreg 0x56,a
.done:  pop hl
        pop de
        pop bc
        pop af
        ret
cell_group: dw 0xFFFF
cell_case: db 2
cell_ci: db 0
cell_raw: ds 8,0
cell_inks: db 8,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
