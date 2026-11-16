; R-Type feasibility only: full 105-pattern publication, no game hooks.
; Uses the pinned assembler and shared DMA capability gate. RAM code/packets.
        DEVICE ZXSPECTRUMNEXT
MODE    EQU 0xB100
ROW     EQU MODE+1
SLOT    EQU MODE+2
COUNT   EQU MODE+3
DSRC    EQU MODE+4
DDST    EQU MODE+6
NL      EQU 311
HLIB_V_PACE EQU 0xB120
HLIB_PACE_NL EQU NL
        DEFINE HLIB_PACE_LEAN
        ORG 0x8000
entry:  di
        ld sp,0xBFF0
        nextreg 8,0x80
        ld bc,0x7FFD
        ld a,0x10
        out (c),a
        nextreg 3,0xA3
        nextreg 7,3
        nextreg 0xC0,0
        nextreg 0x15,1
        ld a,1
        call hlib_dma_init
initial_mode:
        ld a,0
        ld (MODE),a
.trial: ld a,(MODE)
        ld (hlib_dma_policy),a
.v:     call hlib_line
        ld de,160
        or a
        sbc hl,de
        jr nc,.v
.w:     call hlib_line
        ld de,160
        or a
        sbc hl,de
        jr c,.w
pstart: ld bc,0x303B
        xor a
        out (c),a
        ld hl,attrs
        ld d,105
        ld c,0x57
.a:     ld b,5
        otir
        dec d
        jr nz,.a
        xor a
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
finish: jr finish

io_prog: db 0x83,0xC3,0x7D
io_src: dw 0
io_len: dw 0
        db 0x14,0x28,0xAD
        dw 0x005B
        db 0x82,0xCF,0x87
io_end:
mem_prog: db 0x83,0xC3,0x7D
mem_src: dw 0
        dw 64
        db 0x14,0x10,0xAD
mem_dst: dw 0
        db 0x82,0xCF,0x87
mem_end:
copy64:
        DUP 64
        ldi
        EDUP
        ret
        INCLUDE "../../../../nexclash/asm/lib/hlib_dma.asm"
        INCLUDE "../../../../nexclash/asm/lib/hlib_pace.asm"
attrs:
        DUP 105,i
        db (32+(i%16)*16)&255,32+(i/16)*16,(32+(i%16)*16)/256,0xC0+(i/2),0x80+(i%2)*64
        EDUP
        SAVEBIN "rtpub_code.bin",entry,$-entry
