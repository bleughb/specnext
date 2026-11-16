; Four original CALL/zero-guard/prefix blocks become NEXTREG28/JP7 bytes.
; The original shared helper remains intact for every other caller.
cell_inline_n:
        ld a,0x2A
        jr cell_entry
cell_inline_h:
        ld a,0x91
        jr cell_entry
cell_inline_v:
        ld a,0xFD
        jr cell_entry
cell_inline_hv:
        ld a,0x57
        jr cell_entry
