; Scan fixed 16x16 blocks; each visible source cell supplies its own ink.
; Pattern capacity checked before any candidate write. Unused attributes hidden.
; text_owners is supplied by the observed per-plot identity classifier, not owner88.
dynamic_patterns:
        IFDEF RT_FULL_LUT
        ; Classic game keeps slot0 mapped to ROM (FF); only this generator pages it.
        ; Avoid an interruptible select/read pair while native IRQ wrappers select NextRegs.
        ld a,0xFF
        ld (dyn_mmu0),a
        ENDIF
        ; Two linear zero fills replace writes for hundreds of empty cells.
        ; Ordinary DMA fixed source; restores the shared memory packet mode.
        ld a,0x24
        ld (mem_prog+7),a
        ld hl,dyn_zero
        ld (mem_src),hl
        ld hl,8192
        ld (mem_len),hl
        ld hl,0xC000
        ld (mem_dst),hl
        nextreg 0x56,40
        ld hl,mem_prog
        ld bc,(mem_end-mem_prog)*256+0x6B
        otir
        nextreg 0x56,41
        ld hl,mem_prog
        ld bc,(mem_end-mem_prog)*256+0x6B
        otir
        ld a,0x14
        ld (mem_prog+7),a
        xor a
        ld (dyn_count),a
        ld (dyn_y),a
        ld hl,attrs
        ld de,attrs+1
        ld bc,524
        ld (hl),a
        ldir
.scan: nop
.y:     xor a
        ld (dyn_x),a
.x:     ld a,(dyn_count)
        cp MAXFIG
        jr c,.capacity
        ; A full bank can still have empty blocks. Use a spare candidate page.
        nextreg 0x56,44
        IFDEF RT_LIVEPAINT
        ld a,44
        ld (dyn_page),a
        ENDIF
        ld iy,0xC000
        jr .candidate
.capacity:
        cp 64
        ld b,40
        jr c,.page
        inc b
.page:  and 63
        ld h,a
        ld l,0
        srl h
        rr l
        ld a,h
        or 0xC0
        ld h,a
        push hl
        pop iy
        ld a,b
        IFDEF RT_LIVEPAINT
        ld (dyn_page),a
        ENDIF
        nextreg 0x56,a
.candidate:
        ld (dyn_dest),iy
        xor a
        ld (dyn_nonzero),a
        IFDEF RT_CACHE
        call cache_key
        ld a,(cache_nonzero)
        or a
        jp z,.next
        call cache_lookup
        jp c,.commit
        ENDIF
        ld a,(dyn_y)
        ld b,a
        ld a,(dyn_x)
        ld c,a
        call dynamic_cell
        ld iy,(dyn_dest)
        ld de,4
        add iy,de
        ld a,(dyn_y)
        ld b,a
        ld a,(dyn_x)
        inc a
        ld c,a
        call dynamic_cell
        ld iy,(dyn_dest)
        ld de,64
        add iy,de
        ld a,(dyn_y)
        inc a
        ld b,a
        ld a,(dyn_x)
        ld c,a
        call dynamic_cell
        ld iy,(dyn_dest)
        ld de,68
        add iy,de
        ld a,(dyn_y)
        inc a
        ld b,a
        ld a,(dyn_x)
        inc a
        ld c,a
        call dynamic_cell
        IFDEF RT_CACHE
        call cache_store
        ENDIF
.commit:
        ld a,(dyn_nonzero)
        or a
        jr z,.next
        ld a,(dyn_count)
        cp MAXFIG
        jp nc,dyn_overflow
        ld l,a
        ld h,0
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,de
        ld de,attrs
        add hl,de
        ld a,(dyn_x)
        add a,a
        add a,a
        add a,a
        add a,32
        ld (hl),a
        inc hl
        ld a,(dyn_y)
        add a,a
        add a,a
        add a,a
        add a,32
        ld (hl),a
        inc hl
        ld a,(dyn_x)
        cp 28
        ld a,0
        adc a,0
        xor 1
        ld (hl),a
        inc hl
        ld a,(dyn_count)
        srl a
        or 0xC0
        ld (hl),a
        inc hl
        ld a,(dyn_count)
        and 1
        rrca
        rrca
        or 0x80
        ld (hl),a
        ld hl,dyn_count
        inc (hl)
.next:
        IFDEF RT_PACE
        RT_DEBT_TICK
        ENDIF
        ld hl,dyn_x
        inc (hl)
        inc (hl)
        ld a,(hl)
        cp 32
        jp c,.x
        ld hl,dyn_y
        inc (hl)
        inc (hl)
        ld a,(hl)
        cp 20
        jp c,.y
        nextreg 0x56,42
        IFDEF RT_FULL_LUT
        ld a,(dyn_mmu0)
        nextreg 0x50,a
        ENDIF
        ret

dyn_overflow:
        ld a,1
        ld (dyn_failed),a
        di
        halt
        jr dyn_overflow

; BC = cell (y,x). IY = quadrant. Read only the nonlinear bitmap.
dynamic_cell:
        IFDEF RT_PREPAINT
        jp spritepaint_cell
        ELSE
        ld a,b
        and 7
        rrca
        rrca
        rrca
        or c
        ld l,a
        ld a,b
        srl a
        srl a
        srl a
        add a,0x7E
        ld h,a
        ld a,(hl)
        or a
        jp z,.blank
        cp 0xDC
        jp nc,.blank
        push hl
        ld l,a
        ld h,text_owners/256
        ld a,(hl)
        pop hl
        or a
        jp nz,.blank
        IFDEF RT_LIVEPAINT
        call live_lookup
        ret c
        ENDIF
        ld a,h
        sub 6
        ld h,a
        ld a,(hl)
        and 0x47
        ld c,a
        and 7
        jr nz,.ink
        ld a,c
        or 0x40
        ld c,a
.ink:
        IFDEF RT_FULL_LUT
        ld a,c
        and 7
        add a,a
        add a,a
        ld (dyn_colour),a
        ld a,c
        and 0x40
        ld a,46
        jr z,.lutpage
        inc a
.lutpage:
        nextreg 0x50,a
        ld a,h
        sub 0x78
        DUP 3
        add a,a
        EDUP
        add a,0x60
        ld h,a
        ; Source HL / accumulator C in main set; output DE in alternate set.
        ; Unroll eight rows so bitmap expansion has no index-register or memory counter cost.
        push iy
        exx
        pop de
        exx
        ld c,0
        DUP 8
        ld a,(hl)
        ld b,a
        or c
        ld c,a
        ld a,b
        inc h
        exx
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        ld a,(dyn_colour)
        or h
        ld h,a
        DUP 4
        ldi
        EDUP
        ld a,e
        add a,4
        ld e,a
        jr nc,$+3
        inc d
        exx
        EDUP
        ld a,(dyn_nonzero)
        or c
        ld (dyn_nonzero),a
        ret
        ELSE
.ink:   ld a,c
        and 7
        DUP 5
        add a,a
        EDUP
        ld c,a
        ld a,(hl)
        and 0x40
        jr nz,.bright
        ld a,c
        or a
        ld a,expand_lut/256
        jr nz,.table
.bright:
        ld a,expand_lut/256+1
.table: ld (dyn_table_h),a
        ld a,h
        sub 0x78
        DUP 3
        add a,a
        EDUP
        add a,0x60
        ld h,a
        push hl
        pop ix
        ld de,8
        ld a,8
        ld (dyn_lines),a
.bits:  ld a,(ix+0)
        ld b,a
        ld hl,dyn_nonzero
        or (hl)
        ld (hl),a
        ld a,b
        DUP 4
        rrca
        EDUP
        and 15
        add a,a
        or c
        ld l,a
        ld a,(dyn_table_h)
        ld h,a
        ld a,(hl)
        ld (iy+0),a
        inc l
        ld a,(hl)
        ld (iy+1),a
        ld a,b
        and 15
        add a,a
        or c
        ld l,a
        ld a,(hl)
        ld (iy+2),a
        inc l
        ld a,(hl)
        ld (iy+3),a
        inc ixh
        add iy,de
        ld hl,dyn_lines
        dec (hl)
        jr nz,.bits
        ret
        ENDIF
.blank: ret

        ENDIF
dyn_colour: db 0
dyn_mmu0: db 0xFF
dyn_zero: db 0
dyn_count: db 0
dyn_x: db 0
dyn_y: db 0
dyn_dest: dw 0
dyn_nonzero: db 0
dyn_lines: db 0
dyn_table_h: db 0
dyn_failed: db 0
        ALIGN 256
text_owners: ds 256,0
        IFDEF RT_CACHE
        INCLUDE "pattern_cache.asm"
        ENDIF
        IFNDEF RT_FULL_LUT
        ALIGN 512
expand_lut:
        DUP 16,col
        DUP 16,bits
        db ((col*((bits>>3)&1))<<4)|(col*((bits>>2)&1))
        db ((col*((bits>>1)&1))<<4)|(col*(bits&1))
        EDUP
        EDUP

        ENDIF

        IFDEF RT_PREPAINT
        INCLUDE "spritepaint_cell.asm"
        ENDIF

        IFDEF RT_LIVEPAINT
dyn_page: db 40
        INCLUDE "live_bridge.asm"
        INCLUDE "spritepaint_cell.asm"
        ENDIF
