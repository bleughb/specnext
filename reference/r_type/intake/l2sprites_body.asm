; R-Type prototype step 2: figures as hardware sprites (included by l2scroll.asm).
;
; Every figure the game draws goes through one of four plotters (8CFD normal,
; 8D65 mirrored, 8DD3 upside down, 8E29 both) with HL = graphic, B/C = row/column,
; D/E = height/width in 8x8 cells. A graphic is a row-major stream of cells: one
; attribute byte then eight pixel bytes, or the single byte 36 for an empty cell.
; Each plot is recorded here; its graphic is converted once into 16x16 4bpp
; patterns (2x2 cells each, colour index = ink + 8*bright; black paper transparent,
; coloured paper drawn) and
; cached by graphic address and ink override (8EB1), with a checksum: the game
; rewrites some graphics in place and those are converted again into the same slots. The game's flips become the
; sprite mirror flags. The native plotter still runs for the owner/collision maps;
; the copier's figure copy to the ULA is skipped while sprites are on (8886).
; All sprites recorded since the previous copier call are published at 8842.
; A figure that does not fit (128 sprites, 128 patterns) is drawn natively on the
; ULA for that update. The cell hook flags only cells a sprite shows; the copier
; copies every other buffer cell natively, including cells produced outside the
; plotters (the level 3 battleship).
CELLW   EQU 17                  ; cells kept per row (16 + one empty)
CELLH   EQU 21
MAXENT  EQU 64
MAXSPR  EQU 128
FLAGMAP EQU 0x3A00              ; one byte per cell, same layout as the owner map 7E00
COOL    EQU 50                  ; updates between cache restarts
BUDGET  EQU 24                  ; tiles converted per update
CACHE_LIM EQU 128               ; pattern slots for cached graphics

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
        ld (spr_tight),a
        ld (spr_cool),a
        ld a,COOL
        ld (cool_len),a
        ld a,MAXSPR
        ld (spr_prev),a         ; the next publication hides every stale sprite
        ld a,1
        ld (spr_on),a
        nextreg 0x15,0x45
        ret

; ---- plotter entries: record, then the displaced instructions -----------------
plot_n: xor a
        call spr_record
        call .body
        jp spr_after
.body:  push bc
        push de
        exx
        jp 0x8D00
plot_h: ld a,1
        call spr_record
        call .body
        jp spr_after
.body:  push bc
        push de
        ld b,0x5D
        jp 0x8D69
plot_v: ld a,2
        call spr_record
        call .body
        jp spr_after
.body:  push bc
        push de
        exx
        jp 0x8DD6
plot_hv:
        ld a,3
        call spr_record
        call .body
        jp spr_after
.body:  push bc
        push de
        ld b,0x5D
        jp 0x8E2D

; The native plot has finished. A figure keeps its sprites only if every cell the
; plotter tried was drawn (8EC2 candidates = 8EA2 writes); otherwise another
; figure or the scenery owns part of it and the native ULA cells show it exactly.
spr_after:
        push af
        push hl
        ld a,(cur_serial)
        or a
        jr z,.x
        ld a,(emitted)
        or a
        jr z,.x
        ld a,(cand)
        ld hl,succ
        cp (hl)
        jr z,.ok
        ld hl,stat_part         ; partly hidden: whatever owns its missing cells
        inc (hl)                ; must be in front, so its sprites go behind all
        push bc                 ; others (published last)
        ld a,(save_n)
        ld c,a
        ld a,(spr_n)
        sub c
        jr z,.pe
        ld b,a
        ld a,c
        ld hl,spr_part
        add hl,a
.pm:    ld (hl),1
        inc hl
        djnz .pm
.pe:    pop bc
.ok:    ld a,(cur_serial)
        ld hl,plot_ok
        add hl,a
        ld (hl),1
.x:     xor a
        ld (cur_serial),a
        pop hl
        pop af
        ret

; 8EC2 replaces LD A,B / RRCA / RRCA: the plotter is testing one cell.
cand_hook:
        push hl
        ld hl,cand
        inc (hl)
        pop hl
        ld a,b
        rrca
        rrca
        jp 0x8EC5

; 8886 replaces LD A,H / ADD A,20: skip the eight-byte figure copy to the ULA.
spr_gate:
        ld a,(spr_on)
        or a
        jr z,.native
        push hl
        ld a,d
        add a,high(FLAGMAP)-0x7E
        ld h,a
        ld l,e
        ld a,(hl)               ; serial of the plot that drew this cell, or 0
        ld (hl),0               ; one use: other producers of buffer cells never set it
        or a
        jr z,.nat
        ld hl,plot_ok
        add hl,a
        ld a,(hl)
        or a
        pop hl
        jr z,.native
        xor a                   ; a sprite shows it: the ULA cell must be blank,
        ld (hl),a               ; or older pixels show in the figure's colours
        inc h
        ld (hl),a
        inc h
        ld (hl),a
        inc h
        ld (hl),a
        inc h
        ld (hl),a
        inc h
        ld (hl),a
        inc h
        ld (hl),a
        inc h
        ld (hl),a
        jp 0x88A9
.nat:   pop hl
.native:
        ld a,h
        add a,0x20
        jp 0x8889

; 8EA2 replaces LD A,(7A9C): a plotter is about to draw one cell (DE = its owner
; map byte). Remember whether that figure is shown by sprites or by the ULA.
cell_hook:
        push hl
        ld a,d
        add a,high(FLAGMAP)-0x7E
        ld h,a
        ld l,e
        ld a,(cur_serial)
        ld (hl),a
        ld hl,succ
        inc (hl)
        pop hl
        ld a,(0x7A9C)
        jp 0x8EA5

; ---- record one plot: A = flip, HL/BC/DE as the plotter receives them ---------
spr_record:
        ld (r_flip),a
        xor a
        ld (cur_serial),a
        ld (emitted),a
        ld (cand),a
        ld (succ),a
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
        ld a,(need_reset)
        or a
        jr z,.nr
        push de
        ld hl,plot_ok
        ld de,plot_ok+1
        ld bc,255
        ld (hl),0
        ldir
        pop de
        xor a
        ld (need_reset),a
        ld (serial),a
.nr:    ld a,(serial)
        inc a
        jr z,.out               ; more than 255 plots in one update: native
        ld (serial),a
        ld (cur_serial),a
        ld a,(spr_n)
        ld (save_n),a
        ld a,e
        dec a
        cp 16
        jr nc,.out
        ld a,d
        dec a
        cp 18                   ; at most 8 x 9 sprites: the entry bitmap is 72 bits
        jr nc,.out
        ld a,e
        inc a
        srl a
        ld (nx),a
        ld a,d
        inc a
        srl a
        ld (ny),a
        call stream_sum
        call cache_find
        jr z,.hit
        call convert
        jr c,.out
        jr .have
.hit:   ld hl,(r_sum)
        ld a,(ix+14)
        cp l
        jr nz,.stale
        ld a,(ix+15)
        cp h
        jr z,.have
.stale: call reconvert          ; the game rewrote this graphic in place
        jr c,.out
.have:  ld a,(spr_n)
        add a,(ix+4)
        jr c,.out
        cp MAXSPR+1
        jr nc,.out              ; no sprites left: the whole figure stays on the ULA
        call emit
        ld a,1
        ld (emitted),a
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
        jp nc,conv_fail
        ld a,(spr_ovf)
        or a
        jp nz,conv_keep
        ld a,(ny)               ; refuse before any work if it cannot fit even
        ld b,a                  ; with every tile used
        ld a,(nx)
        ld c,a
        ld a,(next_slot)
.need:  add a,c
        jp c,conv_fail
        djnz .need
        cp CACHE_LIM+1
        jp nc,conv_fail
        ld hl,next_slot         ; spread conversion work: at most BUDGET tiles an
        sub (hl)                ; update, or one figure of any size
        ld c,a                  ; tiles this figure may need
        ld a,(budget)
        cp BUDGET
        jr z,.first
        cp c
        jr c,conv_later
        sub c
        jr .spend
.first: xor a
.spend: ld (budget),a
        ld hl,(r_src)
        ld (ix+0),l
        ld (ix+1),h
        ld a,(r_ink)
        ld (ix+2),a
        ld a,(next_slot)
        ld (ix+3),a
        ld (c_slot),a
        ld a,CACHE_LIM
        ld (slot_lim),a
        call conv_core
        jp c,conv_fail
        ld a,(c_slot)
        ld (next_slot),a
        sub (ix+3)
        ld (ix+4),a             ; sprites this figure needs
        ld hl,cache_n
        inc (hl)
        or a
        ret
; Same entry, same pattern slots, new pixels. Carry = it no longer fits.
reconvert:
        ld hl,stat_re
        inc (hl)
        ld a,(ix+3)
        ld (c_slot),a
        add a,(ix+4)
        ld (slot_lim),a
        call conv_core
        ret nc
        ld (ix+0),0xFF          ; grew: forget it, a later plot converts it afresh
        ld (ix+1),0xFF
        scf
        ret
conv_fail:
        ld a,(spr_cool)
        or a
        jr z,.ask
        ld a,1                  ; restarted recently and still full: the figures
        ld (spr_tight),a        ; on screen need more than 128 patterns
        jr conv_keep
.ask:   ld a,1
        ld (spr_ovf),a
conv_keep:
        ld hl,stat_drop
        inc (hl)
conv_later:
        scf                     ; the figure is drawn natively this update
        ret

; Upload the graphic r_src into slots c_slot.. below slot_lim; bitmap and
; checksum into entry IX. Carry = out of slots.
conv_core:
        ld hl,(r_sum)
        ld (ix+14),l
        ld (ix+15),h
        call build_cells
        push ix
        pop hl
        ld a,5
        add hl,a
        ld b,9
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
        or a
        ret
.full:  pop bc
        pop bc
        scf
        ret

; celltab = pointers to the cells of the graphic r_src (0 = empty or absent).
build_cells:
        ld a,(r_h)              ; clear only the rows a tile can read: h+1
        inc a
        ld d,a
        ld e,CELLW*2
        mul d,e
        dec de
        ld b,d
        ld c,e
        ld hl,celltab
        ld de,celltab+1
        ld (hl),0
        ldir
        ld hl,(r_src)
        ld a,(r_h)
        ld b,a
        ld de,celltab
.r:   push bc
        push de
        ld a,(r_w)
        ld b,a
.c:   ld a,(hl)
        cp 0x36
        jr z,.k
        ld a,l
        ld (de),a
        inc de
        ld a,h
        ld (de),a
        inc de
        ld a,9
        add hl,a
        jr .n
.k:  inc de
        inc de
        inc hl
.n:  djnz .c
        pop de
        ld a,CELLW*2
        add de,a
        pop bc
        djnz .r
        ret

; DE and r_sum = sum of every byte of the graphic stream at r_src.
stream_sum:
        ld hl,(r_src)
        ld de,0
        ld a,(r_h)
        ld b,a
.row:   push bc
        ld a,(r_w)
        ld b,a
.col:   ld a,(hl)
        cp 0x36
        jr z,.one
        ld c,9
.s:     ld a,(hl)
        add de,a
        inc hl
        dec c
        jr nz,.s
        jr .next
.one:   add de,a
        inc hl
.next:  djnz .col
        pop bc
        djnz .row
        ld (r_sum),de
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
        ld hl,slot_lim
        cp (hl)
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

; Two cells of one tile half, line-major. Colours are worked out once per cell
; into four-byte tables (entry = pixel pair, bit 1 = left pixel).
half:   ld de,(ea)
        ld hl,tab_l
        call cell_tab
        ld de,(eb)
        ld hl,tab_r
        call cell_tab
        xor a
.l:     ld (e_line),a
        ld de,(ea)
        ld hl,tab_l
        call emit_line
        ld de,(eb)
        ld hl,tab_r
        call emit_line
        ld a,(e_line)
        inc a
        cp 8
        jr nz,.l
        ret

; HL = table for the cell DE (0 = blank). Index = ink + 8*bright; black paper is
; transparent, coloured paper drawn, black ink on coloured paper opaque black.
cell_tab:
        push hl
        ld bc,0                 ; B paper, C ink
        ld a,d
        or e
        jr z,.fill
        ld a,(r_ink)
        or a
        jr nz,.at
        ld a,(de)
.at:    ld l,a
        rrca
        rrca
        rrca
        ld h,a                  ; bits 0..2 paper, bit 3 bright
        and 7
        jr z,.pz
        ld a,h
        and 15
.pz:    ld b,a
        ld a,l
        and 7
        jr nz,.ic
        ld a,b
        or a
        jr z,.fill              ; black on black: nothing to show
        ld c,8
        jr .fill
.ic:    ld c,a
        ld a,h
        and 8
        or c
        ld c,a
.fill:  pop hl
        ld a,b
        rlca
        rlca
        rlca
        rlca
        ld e,a
        or b
        ld (hl),a               ; paper, paper
        inc hl
        ld a,e
        or c
        ld (hl),a               ; paper, ink
        inc hl
        ld a,c
        rlca
        rlca
        rlca
        rlca
        ld d,a
        or b
        ld (hl),a               ; ink, paper
        inc hl
        ld a,d
        or c
        ld (hl),a               ; ink, ink
        ret

; Four pattern bytes of line e_line of cell DE (or 0), table HL.
emit_line:
        ld a,d
        or e
        jr z,.blank
        push hl
        ld a,(e_line)
        inc a
        ex de,hl
        add hl,a
        ld c,(hl)
        pop hl
        ld b,4
.p:     xor a
        sla c
        rla
        sla c
        rla
        push hl
        add hl,a
        ld a,(hl)
        pop hl
        out (0x5B),a
        djnz .p
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
        jp nc,.adv
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
        jp nc,.adv
        add a,a
        add a,a
        add a,a
        add a,24
        ld (e_y),a
        ld a,(spr_n)
        cp MAXSPR
        jp nc,.adv
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
        ld a,(spr_n)
        ld hl,spr_part
        add hl,a
        ld (hl),0
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
        ld c,0x57
        xor a                   ; whole figures first (on top), then partly
        call .pass              ; hidden ones behind them
        ld a,1
        call .pass
        jr .hide
.pass:  ld (.want+1),a
        ld a,(spr_n)
        or a
        ret z
        ld d,a
        ld hl,spr_list
        ld ix,spr_part
.s:     ld a,(ix+0)
        inc ix
.want:  cp 0
        jr nz,.skip
        outinb
        outinb
        outinb
        outinb
        outinb
        dec d
        jr nz,.s
        ret
.skip:  ld a,5
        add hl,a
        dec d
        jr nz,.s
        ret
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
.nm:    ld a,BUDGET
        ld (budget),a
        ld a,1
        ld (need_reset),a
        xor a
        ld (spr_n),a
        ld a,(spr_cool)
        or a
        jr z,.c0
        dec a
        ld (spr_cool),a
.c0:    ld a,(spr_ovf)
        or a
        ret z
        ld a,(spr_tight)
        or a
        ld a,(cool_len)
        jr z,.len
        add a,a                 ; restarting did not make room last time: wait longer
        jr nc,.len
        ld a,255
.len:   ld (cool_len),a
        ld (spr_cool),a
        xor a                   ; no room this update: start the cache again
        ld (spr_tight),a
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
spr_cool: db 0
spr_tight: db 0
cool_len: db COOL
budget:   db BUDGET
tab_l:    ds 4
tab_r:    ds 4
cur_serial: db 0
serial:   db 0
need_reset: db 1
emitted:  db 0
cand:     db 0
succ:     db 0
save_n:   db 0
stat_part: db 0
stat_re:  db 0
slot_lim: db 128
r_sum:    dw 0
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
plot_ok:  ds 256
spr_part: ds MAXSPR
        ASSERT $ <= FLAGMAP
