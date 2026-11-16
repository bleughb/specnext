; Same live graphic identity as the measured full census. Owner88 is never globally excluded.
        MACRO TEXT_ENTRY label,after,flipped
label:
        push af
        ld a,r
        ld (text_r),a
        IFDEF RT_FASTPLOTS
        call fast_setup
        ENDIF
        IFDEF RT_CELL
        call plot_setup
        ENDIF
        call classify_text
        pop af
        push bc
        push de
        IF flipped
        ld b,0x5D
        ELSE
        exx
        ENDIF
        jp after
        ENDM
        TEXT_ENTRY text_8cfd,0x8D00,0
        TEXT_ENTRY text_8d65,0x8D69,1
        TEXT_ENTRY text_8dd3,0x8DD6,0
        TEXT_ENTRY text_8e29,0x8E2D,1
classify_text:
        push bc
        push de
        push hl
        ld c,0
        ld a,h
        cp 0xCA
        jr nz,.done
        ld a,l
        cp 0xFF
        jr nz,.done
        ld a,d
        cp 21
        jr nz,.done
        ld a,e
        cp 24
        jr nz,.done
        ld de,text_signature
        ld b,34
.compare:
        ld a,(de)
        cp (hl)
        jr nz,.done
        inc de
        inc hl
        djnz .compare
        inc c
.done:  ld a,(0x7A9C)
        ld l,a
        ld h,text_owners/256
        ld (hl),c
        pop hl
        pop de
        pop bc
        ld a,(text_r)
        and 128
        ld (.bit+1),a
        ld a,(text_r)
        IFDEF RT_CELL
        sub 10                ; extra LD A,(plot_speed) / NEXTREG after LD R
        ELSE
        sub 7                 ; entry JP/PUSH/LDAR4; return RET/POP/JP3
        ENDIF
        and 127
.bit:   or 0
        ld r,a
        IFDEF RT_CELL
        ld a,(plot_speed)
        nextreg 7,a
        ENDIF
        ret
text_r: db 0
text_signature:
        db 0x05,0x00,0x7E,0x18,0x18,0x18,0x18,0x18,0x18,0x05,0x00,0x41,0x41,0x41,0x7F,0x41,0x41,0x41,0x05,0x00,0x1F,0x31,0x61,0x41,0x7F,0x41,0x41,0x05,0x00,0x61,0x71,0x79,0x5D,0x4F

        IFDEF RT_CELL
; Latch once per original plot call; its cell writers inherit this clock.
plot_setup:
        push bc
        ld bc,0x243B
        ld a,7
        out (c),a
        inc b
        in a,(c)
        and 3
        ld (plot_speed),a
        nextreg 7,3
        IFDEF RT_RESOLVED
        dec b
        ld a,0x56
        out (c),a
        inc b
        in a,(c)
        ld (plot_mmu6),a
        ENDIF
        HLIB_IFF_DI
        ld a,0
        jp po,.off
        inc a
        ld (plot_iff),a
        ei
        jr .done
.off:   ld (plot_iff),a
.done:  pop bc
        ret
plot_iff: db 1
plot_speed: db 0
        IFDEF RT_RESOLVED
plot_mmu6: db 0
        ENDIF
        ENDIF
