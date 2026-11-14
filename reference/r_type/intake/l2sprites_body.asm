; R-Type prototype step 2: figures as hardware sprites (included by l2scroll.asm).
;
; Every figure the game draws goes through one of four plotters (8CFD normal,
; 8D65 mirrored, 8DD3 upside down, 8E29 both) with HL = graphic, B/C = row/column,
; D/E = height/width in 8x8 cells. A graphic is a row-major stream of cells: one
; attribute byte then eight pixel bytes, or the single byte 36 for an empty cell.
; Each plot is recorded here; its graphic is converted once into 16x16 4bpp
; patterns (2x2 cells each, colour index = ink + 8*bright, paper transparent) and
; cached by graphic address and ink override (8EB1). The game's flips become the
; sprite mirror flags. The native plotter still runs for the owner/collision maps;
; the copier's figure copy to the ULA is skipped while sprites are on (8886).
; All sprites recorded since the previous copier call are published at 8842.
CELLW   EQU 17                  ; cells kept per row (16 + one empty)
CELLH   EQU 21
MAXENT  EQU 64
MAXSPR  EQU 128

spr_setup:
        nextreg 0x43,0x20       ; edit the first sprite palette
        nextreg 0x40,0
        ld hl,col_tab
        ld b,16
.p:     ld a,(hl)
        nextreg 0x41,a
        inc hl
        djnz .p
        nextreg 0x43,0
        nextreg 0x4B,0          ; colour index 0 is transparent
        nextreg 0x1C,2          ; reset sprite clip index
        nextreg 0x19,8
        nextreg 0x19,247
        nextreg 0x19,0
        nextreg 0x19,159
        nextreg 0x15,0x44       ; Layer 2 over sprites over ULA; sprite 0 on top; hidden
        ret

; A level (or life) has just been drawn: empty cache, sprites on.
spr_start:
        xor a
        ld (next_slot),a
        ld (cache_n),a
        ld (spr_n),a
        ld (spr_ovf),a
        ld a,MAXSPR
        ld (spr_prev),a         ; the next publication hides every stale sprite
        ld a,1
        ld (spr_on),a
        nextreg 0x15,0x45
        ret

; ---- plotter entries: record, then the displaced instructions -----------------
plot_n: xor a
        call spr_record
        push bc
        push de
        exx
        jp 0x8D00
plot_h: ld a,1
        call spr_record
        push bc
        push de
        ld b,0x5D
        jp 0x8D69
plot_v: ld a,2
        call spr_record
        push bc
        push de
        exx
        jp 0x8DD6
plot_hv:
        ld a,3
        call spr_record
        push bc
        push de
        ld b,0x5D
        jp 0x8E2D

; 8886 replaces LD A,H / ADD A,20: skip the eight-byte figure copy to the ULA.
spr_gate:
        ld a,(spr_on)
        or a
        jp nz,0x88A9
        ld a,h
        add a,0x20
        jp 0x8889

; ---- record one plot: A = flip, HL/BC/DE as the plotter receives them ---------
spr_record:
        ld (r_flip),a
        ld a,(spr_on)
        or a
        ret z
        ld a,(0x8EBF)
        cp 0x60
        ret nz                  ; the plotter is drawing scenery straight to the ULA
        push hl
        push de
        push bc
        push ix
        ld (r_src),hl
        ld (r_w),de             ; r_w = E, r_h = D
        ld (r_col),bc           ; r_col = C, r_row = B
        ld a,(0x8EB1)
        ld (r_ink),a
        ld a,e
        dec a
        cp 16
        jr nc,.out
        ld a,d
        dec a
        cp 20
        jr nc,.out
        ld a,e
        inc a
        srl a
        ld (nx),a
        ld a,d
        inc a
        srl a
        ld (ny),a
        call cache_find
        jr z,.have
        call convert
        jr c,.out
.have:  call emit
.out:   pop ix
        pop bc
        pop de
        pop hl
        ret

; Z and IX = entry when cached; NZ and IX = first free entry otherwise.
cache_find:
        ld ix,cache
        ld a,(cache_n)
        or a
        jr z,.miss
        ld b,a
        ld hl,(r_src)
        ld a,(r_ink)
        ld c,a
        ld de,16
.l:     ld a,(ix+0)
        cp l
        jr nz,.n
        ld a,(ix+1)
        cp h
        jr nz,.n
        ld a,(ix+2)
        cp c
        ret z
.n:     add ix,de
        djnz .l
.miss:  or 1
        ret

; ---- convert the graphic at r_src into patterns; carry = no room --------------
convert:
        ld a,(cache_n)
        cp MAXENT
        jp nc,.fail
        ld a,(spr_ovf)
        or a
        jp nz,.fail
        ld hl,celltab
        ld de,celltab+1
        ld bc,CELLW*CELLH*2-1
        ld (hl),0
        ldir
        ld hl,(r_src)
        ld a,(r_h)
        ld b,a
        ld de,celltab
.row:   push bc
        push de
        ld a,(r_w)
        ld b,a
.col:   ld a,(hl)
        cp 0x36
        jr z,.skip
        ld a,l
        ld (de),a
        inc de
        ld a,h
        ld (de),a
        inc de
        ld a,9
        add hl,a
        jr .next
.skip:  inc de
        inc de
        inc hl
.next:  djnz .col
        pop de
        ld a,CELLW*2
        add de,a
        pop bc
        djnz .row
        ld hl,(r_src)
        ld (ix+0),l
        ld (ix+1),h
        ld a,(r_ink)
        ld (ix+2),a
        ld a,(next_slot)
        ld (ix+3),a
        ld (c_slot),a
        push ix
        pop hl
        ld a,5
        add hl,a
        ld b,10
        xor a
.clr:   ld (hl),a
        inc hl
        djnz .clr
        ld (t_idx),a
        ld hl,celltab
        ld (rowbase),hl
        ld a,(ny)
        ld b,a
.ty:    push bc
        ld hl,(rowbase)
        ld (tp),hl
        ld a,(nx)
        ld b,a
.tx:    push bc
        ld hl,(tp)
        call do_tile
        jr c,.full
        call nz,set_bit
        ld hl,(tp)
        ld a,4
        add hl,a
        ld (tp),hl
        ld hl,t_idx
        inc (hl)
        pop bc
        djnz .tx
        ld hl,(rowbase)
        ld a,CELLW*4
        add hl,a
        ld (rowbase),hl
        pop bc
        djnz .ty
        ld a,(c_slot)
        ld (next_slot),a
        ld hl,cache_n
        inc (hl)
        or a
        ret
.full:  pop bc
        pop bc
.fail:  ld a,1
        ld (spr_ovf),a
        ld hl,stat_drop
        inc (hl)
        scf
        ret

; HL = cell-pointer pair of the tile's top row. Z = empty; NZ = uploaded; C = full.
do_tile:
        ld de,tl
        ld bc,4
        ldir
        ld a,CELLW*2-4
        add hl,a
        ld bc,4
        ldir
        ld hl,tl
        ld b,8
        xor a
.z:     or (hl)
        inc hl
        djnz .z
        ret z
        ld a,(c_slot)
        cp 128
        jr nc,.ovf
        ld bc,0x303B
        ld e,a
        srl a
        bit 0,e
        jr z,.s
        or 0x80
.s:     out (c),a               ; pattern, upper or lower 128 bytes
        ld hl,(tl)
        ld (ea),hl
        ld hl,(tr)
        ld (eb),hl
        call half
        ld hl,(bl)
        ld (ea),hl
        ld hl,(br)
        ld (eb),hl
        call half
        ld hl,c_slot
        inc (hl)
        or 1
        ret
.ovf:   xor a
        inc a
        scf
        ret

half:   xor a
.l:     ld (e_line),a
        ld de,(ea)
        call emit_cell
        ld de,(eb)
        call emit_cell
        ld a,(e_line)
        inc a
        cp 8
        jr nz,.l
        ret

; Four pattern bytes (eight pixels) of one cell line. DE = cell or 0.
emit_cell:
        ld a,d
        or e
        jr z,.blank
        ld a,(r_ink)
        or a
        jr nz,.at
        ld a,(de)
.at:    ld c,a
        and 7
        ld b,a
        ld a,c
        rrca
        rrca
        rrca
        and 8
        or b
        ld (.lo+1),a
        rlca
        rlca
        rlca
        rlca
        ld (.hi+1),a
        ld a,(e_line)
        inc a
        ex de,hl
        add hl,a
        ld c,(hl)
        ld b,4
.pair:  ld e,0
        sla c
        jr nc,.q1
.hi:    ld e,0
.q1:    sla c
        ld a,e
        jr nc,.q2
.lo:    or 0
.q2:    out (0x5B),a
        djnz .pair
        ret
.blank: xor a
        out (0x5B),a
        out (0x5B),a
        out (0x5B),a
        out (0x5B),a
        ret

; HL = bitmap byte, A = mask for tile t_idx of entry IX.
bit_addr:
        ld a,(t_idx)
        ld c,a
        rrca
        rrca
        rrca
        and 0x1F
        add a,5
        push ix
        pop hl
        add hl,a
        ld a,c
        and 7
        ld b,a
        inc b
        ld a,0x80
.r:     rlca
        djnz .r
        ret
set_bit:
        call bit_addr
        or (hl)
        ld (hl),a
        ret

; ---- sprite attributes for the cached entry IX at r_row/r_col -----------------
emit:   ld a,(ix+3)
        ld (c_slot),a
        xor a
        ld (t_idx),a
        ld c,a                  ; tile row
.ty:    ld b,0                  ; tile column
.tx:    push bc
        call bit_addr
        and (hl)
        jp z,.next
        pop bc
        push bc
        ld a,b
        add a,a
        ld d,a
        ld a,(r_flip)
        and 1
        ld a,d
        jr z,.nh
        ld a,(r_w)
        sub 2
        sub d
.nh:    ld hl,r_col
        add a,(hl)
        inc a                   ; column + 1: 0..31 are on or beside the screen
        cp 32
        jr nc,.adv
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,24
        add hl,de
        ld (e_x),hl
        ld a,c
        add a,a
        ld d,a
        ld a,(r_flip)
        and 2
        ld a,d
        jr z,.nv
        ld a,(r_h)
        sub 2
        sub d
.nv:    ld hl,r_row
        add a,(hl)
        inc a
        cp 21
        jr nc,.adv
        add a,a
        add a,a
        add a,a
        add a,24
        ld (e_y),a
        ld a,(spr_n)
        cp MAXSPR
        jr nc,.adv
        ld l,a
        ld h,0
        ld e,l
        ld d,h
        add hl,hl
        add hl,hl
        add hl,de
        ld de,spr_list
        add hl,de
        ld a,(e_x)
        ld (hl),a
        inc hl
        ld a,(e_y)
        ld (hl),a
        inc hl
        ld a,(r_flip)
        ld d,a
        and 1
        rlca
        rlca
        rlca
        ld e,a                  ; X mirror
        ld a,d
        and 2
        add a,a
        or e                    ; Y mirror
        ld d,a
        ld a,(e_x+1)
        and 1
        or d
        ld (hl),a
        inc hl
        ld a,(c_slot)
        ld d,a
        srl a
        or 0xC0                 ; visible, fifth byte follows
        ld (hl),a
        inc hl
        ld a,d
        rrca
        rrca
        and 0x40
        or 0x80                 ; 4bpp, pattern half
        ld (hl),a
        ld hl,spr_n
        inc (hl)
.adv:   ld hl,c_slot
        inc (hl)
.next:  ld hl,t_idx
        inc (hl)
        pop bc
        inc b
        ld a,(nx)
        cp b
        jp nz,.tx
        inc c
        ld a,(ny)
        cp c
        jp nz,.ty
        ret

; ---- 8842: show everything recorded since the previous copier call ------------
spr_publish:
        ld a,(spr_on)
        or a
        ret z
        ld bc,0x303B
        xor a
        out (c),a               ; from sprite 0
        ld hl,spr_list
        ld c,0x57
        ld a,(spr_n)
        or a
        jr z,.hide
        ld d,a
.s:     outinb
        outinb
        outinb
        outinb
        outinb
        dec d
        jr nz,.s
.hide:  ld a,(spr_n)
        ld e,a
        ld a,(spr_prev)
        sub e
        jr c,.done
        jr z,.done
        ld d,a
        xor a
.h:     out (c),a
        out (c),a
        out (c),a
        out (c),a               ; invisible: four bytes only
        dec d
        jr nz,.h
.done:  ld a,(spr_n)
        ld (spr_prev),a
        ld hl,stat_max
        cp (hl)
        jr c,.nm
        ld (hl),a
.nm:    xor a
        ld (spr_n),a
        ld a,(spr_ovf)
        or a
        ret z
        xor a                   ; no room this update: start the cache again
        ld (spr_ovf),a
        ld (next_slot),a
        ld (cache_n),a
        ld hl,stat_flush
        inc (hl)
        ret

spr_on:   db 0
spr_n:    db 0
spr_prev: db 0
spr_ovf:  db 0
next_slot: db 0
cache_n:  db 0
stat_flush: db 0
stat_drop: db 0
stat_max: db 0
r_src:    dw 0
r_w:      db 0
r_h:      db 0
r_col:    db 0
r_row:    db 0
r_flip:   db 0
r_ink:    db 0
nx:       db 0
ny:       db 0
c_slot:   db 0
t_idx:    db 0
e_line:   db 0
e_x:      dw 0
e_y:      db 0
rowbase:  dw 0
tp:       dw 0
tl:       dw 0
tr:       dw 0
bl:       dw 0
br:       dw 0
ea:       dw 0
eb:       dw 0
spr_list: ds MAXSPR*5
cache:    ds MAXENT*16
celltab:  ds CELLW*CELLH*2
