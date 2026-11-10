; R-Type feasibility: original copier into a shadow slot2; staged commit.
; Synthetic graphics, original audio at native speed; no sprite engine.
; Uses the pinned assembler and shared DMA capability gate. RAM code/packets.
        DEVICE ZXSPECTRUMNEXT
MODE    EQU 0x3800
ROW     EQU MODE+1
SLOT    EQU MODE+2
COUNT   EQU MODE+3
DSRC    EQU MODE+4
DDST    EQU MODE+6
NL      EQU 311
HLIB_V_PACE EQU 0x3820
HLIB_PACE_NL EQU NL
        ORG 0x2000
entry:  di
        ld sp,0x3FF0
        nextreg 8,0x80
        nextreg 0x57,1
        ld a,0x84
        ld i,a
        im 2
        nextreg 3,0xA3
        nextreg 0x64,0
        nextreg 7,3
        nextreg 0xC0,0
        nextreg 0x15,1
        ld a,1
        call hlib_dma_init
initial_mode:
        ld a,0
        ld (MODE),a
.trial:
.pv:    call hlib_now
        ld de,170
        or a
        sbc hl,de
        jr nc,.pv
.pw:    call hlib_now
        ld de,170
        or a
        sbc hl,de
        jr c,.pw
        call prepare
        ld a,(MODE)
        ld (hlib_dma_policy),a
.v:     call hlib_now
        ld de,150
        or a
        sbc hl,de
        jr nc,.v
.w:     call hlib_now
        ld de,150
        or a
        sbc hl,de
        jr c,.w
tail_begin:
        di
        ; Forced sentinel at a proven ISR-written star-state byte. The negative
        ; control removes only tail_copy and must lose this runtime change.
        ld hl,0xDB64
        inc (hl)
        nextreg 0x52,10
        ld hl,0xDB00
        ld de,0x5B00
        ld bc,1280
tail_copy:
        call move
        ld bc,64
        ld (mem_len),bc
.wait:  call hlib_now
        ld de,160
        or a
        sbc hl,de
        jr c,.wait
pstart: ld bc,0x303B
        xor a
        out (c),a
        call hlib_dma_backend
        or a
        jr z,.acpu
        ld hl,attrs
        ld (io_src),hl
        ld hl,525
        ld (io_len),hl
        ld hl,0x57
        ld (io_dst),hl
        ld hl,io_prog
        ld bc,(io_end-io_prog)*256+0x6B
        otir
        ld hl,0x5B
        ld (io_dst),hl
        jr .adone
.acpu:  ld hl,attrs
        ld d,105
        ld c,0x57
.a:     ld b,5
        otir
        dec d
        jr nz,.a
.adone: xor a
        ld (ROW),a
        ld (SLOT),a
rstart: ld a,(SLOT)
        cp 105
        jr nc,.zero
        ld b,a
        ld a,105
        sub b
        cp 16
        jr c,.n
        ld a,16
.n:     ld (COUNT),a
        ld a,b
        srl a
        ld bc,0x303B
        out (c),a
        ld a,(SLOT)
        and 63
        ld l,a
        ld h,0
        DUP 7
        add hl,hl
        EDUP
        ld de,0xC000
        add hl,de
        ld a,(SLOT)
        cp 64
        ld a,40
        jr c,.pg
        inc a
.pg:    nextreg 0x56,a
        ld a,(COUNT)
        ld d,a
        and 1
        ld e,a
        ld a,d
        srl a
        ld d,a
        call hlib_dma_backend
        or a
        jr nz,.dma
        ld c,0x5B
.cpu:   call hlib_dma_sprite.cpu
        dec d
        jr nz,.cpu
        ld a,e
        or a
        jr z,.done
        call hlib_dma_sprite.cpu ; padded unused half: visible patterns still exactly105
        jr .done
.dma:   ld (io_src),hl
        ld a,(COUNT)
        ld l,a
        ld h,0
        DUP 7
        add hl,hl
        EDUP
        ld (io_len),hl
        ld hl,io_prog
        ld bc,(io_end-io_prog)*256+0x6B
        otir
.done:  ld a,(COUNT)
        ld hl,SLOT
        add a,(hl)
        ld (hl),a
.zero:  nextreg 0x56,42
        ld a,(ROW)
        ld l,a
        and 3
        ld h,0
        rrca
        rrca
        ld e,a
        ld a,l
        and 12
        add a,a
        or 0x40
        ld d,a
        ld h,a
        set 7,h
        ld l,e
        ld (DSRC),hl
        ld (DDST),de
        call hlib_dma_backend
        cp 2
        jr z,.ddma
        ld a,8
.row:   push af
        call hlib_dma_backend
        or a
        jr nz,.rowdma
        ld bc,64
        call copy64
        jr .next
.rowdma:
        ld (mem_src),hl
        ld (mem_dst),de
        push hl
        push de
        ld hl,mem_prog
        ld bc,(mem_end-mem_prog)*256+0x6B
        otir
        pop de
        pop hl
        ld bc,64
        add hl,bc
        ex de,hl
        add hl,bc
        ex de,hl
.next:  ld bc,192
        add hl,bc
        ex de,hl
        add hl,bc
        ex de,hl
        pop af
        dec a
        jr nz,.row
        jr .attrs
.ddma:  ld (hlib_dma_rect_src),hl
        ld (hlib_dma_rect_dst),de
        ld hl,8
        ld (hlib_dma_rect_rows),hl
        ld hl,256
        ld (hlib_dma_rect_astride),hl
        ld (hlib_dma_rect_bstride),hl
        ld hl,hlib_dma_rect_prog
        ld bc,(hlib_dma_rect_end-hlib_dma_rect_prog)*256+0x6B
        otir
.attrs: ld a,(ROW)
        ld l,a
        ld h,0
        DUP 6
        add hl,hl
        EDUP
        ld de,0x5800
        add hl,de
        ex de,hl
        ld hl,0x8000
        add hl,de
        call hlib_dma_backend
        or a
        jr nz,.atdma
        ld bc,64
        call copy64
        jr rend
.atdma: ld (mem_src),hl
        ld (mem_dst),de
        ld hl,mem_prog
        ld bc,(mem_end-mem_prog)*256+0x6B
        otir
rend:   ld hl,ROW
        inc (hl)
        ld a,(hl)
        cp 10
        jp c,rstart
pend:   jp finish
finish: ei
        jr finish

io_prog: db 0x83,0xC3,0x7D
io_src: dw 0
io_len: dw 0
        db 0x14,0x28,0xAD
io_dst: dw 0x005B
        db 0x82,0xCF,0x87
io_end:
mem_prog: db 0x83,0xC3,0x7D
mem_src: dw 0
mem_len: dw 64
        db 0x14,0x10,0xAD
mem_dst: dw 0
        db 0x82,0xCF,0x87
mem_end:
copy64:
        DUP 64
        ldi
        EDUP
        ret
; Prototype only: no pattern generation, no text classification.
prepare:
        nextreg 0x56,43
        ld hl,0x6000
        ld de,0xC000
        ld bc,8192
        call move
        nextreg 0x56,42
        ld hl,0x4000
        ld de,0xC000
        ld bc,8192
        call move
        call clear_figures
        nextreg 0x52,42
shadow_ready:
        ei
        call 0x8842
        nextreg 0x56,43
        ld hl,0xC000
        ld de,0x6000
        ld bc,4096
        call move
        ld hl,0xD000
        ld de,0x7000
        ld a,8
.restore:
        push af
        push hl
        push de
        ld bc,128
        call move
        pop de
        pop hl
        inc h
        inc d
        pop af
        dec a
        jr nz,.restore
        nextreg 0x56,42
prep_end:
        ret
move:
        push hl
        push de
        push bc
        call hlib_dma_backend
        or a
        pop bc
        pop de
        pop hl
        jr nz,.dma
        ldir
        ret
.dma:   ld (mem_src),hl
        ld (mem_dst),de
        ld (mem_len),bc
        ld hl,mem_prog
        ld bc,(mem_end-mem_prog)*256+0x6B
        otir
        ret
clear_figures:
        ld iy,source_rows
        ld hl,0x7E00
        ld c,20
.row:   ld e,(iy+0)
        ld d,(iy+1)
        inc iy
        inc iy
        ld b,32
.cell:  ld a,(hl)
        or a
        jr z,.skip
        cp 0xDC
        jr nc,.skip
        push bc
        push de
        xor a
        ld b,8
.bits:  ld (de),a
        inc d
        djnz .bits
        pop de
        pop bc
.skip:  inc hl
        inc e
        djnz .cell
        dec c
        jr nz,.row
        ret
source_rows:
        DUP 20,j
        dw 0x6000+((j&24)<<8)+((j&7)<<5)
        EDUP

; Original BE26 replaces PUSH IX / PUSH IY. The snapshot PC BE24 is untouched.
irq_in:
        push ix
        push iy
        push hl
        ld bc,0x243B
        ld a,7
        out (c),a
        inc b
        in a,(c)
        ld (irq_speed),a
        nextreg 7,0
        call hlib_pace_hold
        jp 0xBE2B
; BE52 replaces POP AF / EX AF,AF' / POP HL.
irq_out:
        call hlib_pace_resume
        ld a,(irq_speed)
        nextreg 7,a
        pop af
        ex af,af'
        pop hl
        jp 0xBE55
irq_speed: db 0
        INCLUDE "../../../../nexclash/asm/lib/hlib_dma.asm"
        INCLUDE "../../../../nexclash/asm/lib/hlib_pace.asm"
attrs:
        DUP 105,i
        db (32+(i%16)*16)&255,32+(i/16)*16,(32+(i%16)*16)/256,0xC0+(i/2),0x80+(i%2)*64
        EDUP
        SAVEBIN "rtshadow_code.bin",entry,$-entry
