; Castle Master M3: the renderer inside the game, original pace, in-between views (included by cmr.asm when M3 is
; defined; cm2_glue.asm is M2's).
;
; Memory states as M2 (plain = alt ROM + the game's RAM; renderer = pages PG_C0 / PG_C1, work RAM, Layer 2 window).
; New in M3:
;   - The game's own redraw (0x855E .. 0x859F: its geometry, sort, raster into its buffer, the copy to its screen)
;     runs at 28 MHz inside a pace window (hlib_pace's line clock). Its original time = K x its 28 MHz time (m_k).
;   - The time that frees draws in-between views: camera from the last shown view to the new one, on Layer 2, then
;     the new view itself, shown when the original would have shown it (h_show: m3_show).
;   - Three Layer 2 banks: shown, being drawn, and the last update's own view (the copy source when the game's
;     raster does not clear: its buffer keeps the last picture).
;   - The interrupt handler and the sound routine always run at 3.5 MHz, their time left out of the window
;     (hlib_pace_hold / _resume); the printer ticks the clock (it runs with interrupts off).
; Clock state and flags live in the game's IM 2 table 0xFE00-0xFEFE (only 0xFEFF / 0xFF00 are read: the bus gives
; 0xFF), visible in both states.

PG_C0   EQU 32                          ; 16K bank 16: renderer code
PG_C1   EQU 33
PG_W0   EQU 34                          ; 16K bank 17: work RAM
PG_W1   EQU 35
PG_LA   EQU 36                          ; Layer 2 A: 16K banks 18-20 (8K pages 36-41)
PG_LB   EQU 42                          ; Layer 2 B: 16K banks 21-23 (8K pages 42-47)
PG_LC   EQU 48                          ; Layer 2 C: 16K banks 24-26 (8K pages 48-53)
R_STACK EQU 0x7FFE
GAME_ISR EQU 0xC01F
G       EQU 0x4000                      ; the game's 0x4000-0x7FFF seen at 0x8000-0xBFFF (pages 10 / 11 in slots 4 / 5)
SHARED  EQU 0x3600                      ; alt ROM 0x3600-0x3CFF: the game reads the ROM only at 0x0000-0x00FF and never
                                        ; executes it (m3b_rom.py, all 167,134 frames); 0x386E-0x3CFF is 0xFF anyway
INISR   EQU 29518                       ; bit 7: inside the game's interrupt handler
VP      EQU 0xFE40                      ; hlib_pace's state (26 bytes); +10 = window open = the game's block at 28 MHz
m_sk    EQU VP+27                       ; an interrupt came during a main-line reading: it reads again
m_add   EQU VP+33                       ; that reading adds its lines (ptick) or drops them (prest)
m_k     EQU VP+28                       ; K x 16: the block's original time per unit of its 28 MHz time
m_ni    EQU VP+26                       ; interrupts held in the window so far
m_wait  EQU VP+30                       ; the game waits on its handler: the clock is stopped
m_hf    EQU VP+31                       ; this interrupt's wrapper holds the clock
m_spd   EQU VP+32                       ; the main line's CPU speed (written before each NR 0x07 it sets):
                                        ; the plain-state wrapper puts it back
m_last  EQU VP+29                       ; the clock's last reading was taken at an interrupt (a frame before the next)
m_pc    EQU VP+40                       ; 1 = the portcullis rises over a view shown in colour (h_off .. its end;
                                        ; in the IM 2 table: 0xFD in the image, the CPU reads only 0xFEFF)
    IFNDEF K16
K16     EQU 108                         ; JNext 1.3.0: 6.75 (m3_jnext.py, plain against M3, 7 updates); the host model: 128
    ENDIF
HLIB_V_PACE EQU VP
HLIB_PACE_NL EQU 312

        INCLUDE "hlib_iff.asm"

; ---- work RAM (after cmr.asm's) --------------------------------------------------------------------------------
        ORG ram_end
g_sp:     ds 2                          ; the game's SP while the renderer runs
isr_sp:   ds 2                          ; the renderer's SP during an interrupt
l2shown:  ds 1                          ; first 8K page of the Layer 2 bank on screen
l2last:   ds 1                          ; the bank with the last update's own view (= l2shown until an in-between view)
in_attr:  ds 1                          ; (27353): the area's view attribute
fin_ok:   ds 1                          ; fin_g holds a view
fin_g:    ds 15                         ; in_cam .. in_gcnt as at the game's geometry call
fin_r:    ds 4                          ; in_sky, in_mount, in_lflag, in_lcol as at the game's raster call
prev_ok:  ds 1
prev:     ds 15                         ; fin_g of the last update shown
tw_on:    ds 1                          ; an in-between view is being drawn
tw_ys:    ds 1                          ; its yaw's sin, cos; its pitch's sin, cos
tw_yc:    ds 1
tw_ps:    ds 1
tw_pc:    ds 1
tw_hadj:  ds 2
tw_madj:  ds 1
tw_d:     ds 6                          ; camera delta x, y, z
tw_dy:    ds 1                          ; yaw, pitch delta (5-degree units, signed)
tw_dp:    ds 1
tw_f:     ds 1
tw_n:     ds 1                          ; in-between views drawn in this update
t_fast:   ds 2                          ; the block's 28 MHz time (lines)
t_tgt:    ds 2                          ; its original time (lines): the new view goes on screen then
t_tw:     ds 2                          ; an in-between view's time, as last measured
t_fin:    ds 2                          ; the final view's
t_t0:     ds 2
t_h0:     ds 2                          ; the clock's held total when the window opened
ov_s:     ds 2688                       ; M3b: the buffer as the raster left it (the marker taken out)
ov_nz:    ds 84                         ; sprite k's pattern has opaque pixels
ov_new:   ds 84                         ; the buffer differs from ov_s under sprite k (ov_scan)
ov_sx:    ds 1                          ; the sprite ov_up builds: column 0-11, band 0-6, k = 12 x band + column
ov_sy:    ds 1
ov_k:     ds 1
ov_or:    ds 1                          ; its masks ORed: nonzero = opaque somewhere
ov_k54:   ds 1                          ; cur54 / cur55 around ov_in .. ov_out
ov_k55:   ds 1
ov_rb:    ds 1                          ; ov_cur: the rectangle's bottom row, its sprite columns and bands
ov_sx0:   ds 1
ov_sx1:   ds 1
ov_sy0:   ds 1
ov_sy1:   ds 1
; M3b fixed overlays (hardware runs 2-3): the shape (C bits) in one colour, white or black by the brightness of the
; Layer 2 view under it (ov_lum), whatever the screen says; T bits clear (Layer 2 shows: no edge). ov_fr0 = the
; centre sight (0xCF45's XOR plus), ov_fr1 = the pointer (0xCDD2's masked cursor: C = its shape, T = the rest of
; its mask). Record: +0 0 = off / 3 = white / 4 = black (the sprite palette's), +1 first row (>= 0), +2 last row
; (<= 111), +3 first byte column (signed; two bytes wide), +4 base (row r's bytes at base + 4 r: C, T, C, T), +6 9 rows
ov_fr0:   ds 42
ov_fr1:   ds 42
ov_r:     ds 1                          ; ov_upf: the buffer row
ov_tt:    ds 1                          ; ov_fwk -> ov_bytef: the T bits
ov_fc:    ds 1                          ; ov_fwk: this record's colour
facecur:  ds 16                         ; setpal: the 16 face colours in use (facepal, or the area's ink: col_on = 0)
dis_n:    ds 1                          ; the colour dissolve: passes left (4-1), this pass's table row x 4
dis_t:    ds 1
ov_lumt:  ds 256                        ; Layer 2 pixel byte -> its colour's brightness 0-62 (setpal; 68 used)
ov_lpg:   ds 1                          ; ov_lum: the bank's first page, first x, rows
ov_lx:    ds 1
ov_lc:    ds 1
fl_skip:  ds 1                          ; object records until flipchk looks at the raster line
fl_pend:  ds 1                          ; an in-between view waits for its flip (flipdef)
dma_st:   ds 1                          ; 0 not looked at yet, 1 CPU copies, 2 DMA
dma_pk:   ds 15                         ; the DMA program (source at +3, destination at +10)
m2_ram_end:
          ASSERT m2_ram_end <= 0x7F00

; ---- renderer-state code (page PG_C0) --------------------------------------------------------------------------
        ORG code_end

; isr_full: an interrupt while the renderer runs. SP may be inside Layer 2 (PUSH fill): nothing is pushed there.
isr_full:
        ld (isr_sp),sp
        ld sp,(g_sp)
        push af
        push bc
        push de
        push hl
        nextreg 0x52,10
        nextreg 0x53,11
        nextreg 0x54,4
        nextreg 0x55,5
        call isr_pre
        nextreg 0x07,0
        call GAME_ISR                   ; returns with EI
        di
        nextreg 0x07,3
        call isr_post
        nextreg 0x52,PG_W0
        nextreg 0x53,PG_W1
        ld a,(cur54)
        nextreg 0x54,a
        ld a,(cur55)
        nextreg 0x55,a
        pop hl
        pop de
        pop bc
        pop af
        ld sp,(isr_sp)
        ei
        ret

; stage: the game's inputs -> the renderer's in_* (the game's 0x4000-0x7FFF read through slots 4-5)
stage:
        ld a,10
        ld (cur54),a
        nextreg 0x54,a
        ld a,11
        ld (cur55),a
        nextreg 0x55,a
        ld hl,27309+G
        ld de,in_cam
        ld bc,6
        ldir
        ld a,(27319+G)
        ld (in_yaw),a
        ld a,(27318+G)
        ld (in_pitch),a
        ld a,(27325+G)
        ld (in_cull),a
        ld hl,(29494+G)
        ld (in_alist),hl
        ld a,(29496+G)
        ld (in_acnt),a
        ld hl,(27345+G)
        ld (in_glist),hl
        ld a,(27344+G)
        ld (in_gcnt),a
        ld a,(27402+G)
        ld (in_sky),a
        ld a,(27343+G)
        ld (in_mount),a
        ld a,(27391+G)
        ld (in_lflag),a
        ld a,(27353+G)
        ld (in_attr),a
        ld a,5
        ld (cur55),a
        nextreg 0x55,a
        ld a,(41970)                    ; the bolt's column as the game last drew it
        ld (in_lcol),a
        ret

; m3_begin (0x855E): the view's inputs as the game's own geometry finds them; the window opens = 28 MHz from here
m3_begin:
        call stage
        ld hl,in_cam
        ld de,fin_g
        ld bc,15
        ldir
        ld a,1
        ld (fin_ok),a
m3_open:
        call popen
        ld hl,(VP+14)
        ld (t_h0),hl
        ret

; m3_mid (0x8599, 0xB635): the raster's inputs; a redraw without the geometry call opens the window here
m3_mid:
        call stage
        ld hl,in_sky
        ld de,fin_r
        ld bc,4
        ldir
        ld a,(VP+10)
        or a
        jp z,m3_open
        jp ptick

; m3_show (after the game's 0x9F19 / 0xA38D): in-between views while the original would still be drawing, then
; the new view at the original's time
m3_show:
        ld a,(fin_ok)
        or a
        jp z,m3_end
        xor a
        ld (tw_n),a
        ld hl,0
        ld (t_tgt),hl
        ld a,(VP+10)
        or a
        jp z,.final
        call ptick
        ld hl,(VP+2)
        call ktgt
        call isradj
        ld (t_tgt),hl
        call enow
        ld (t_fast),hl
        ld hl,(t_fin)
        ld (t_tw),hl
        call tw_setup
        or a
        jr z,.final
.loop:  call ptick
        call enow
        ld de,(t_tw)
        add hl,de                       ; when this view would be on screen
        jr c,.final
        push hl
        ld de,(t_fin)
        add hl,de
        jr c,.fpop
        ld de,(t_tgt)
        or a
        sbc hl,de
        jr nc,.fpop                     ; no room before the final view
        pop hl
        ld de,(t_fast)
        or a
        sbc hl,de
        push hl                         ; num = show time - block time
        ld hl,(t_tgt)
        ld de,(t_fin)
        or a
        sbc hl,de
        ld de,(t_fast)
        or a
        sbc hl,de                       ; den = target - final's time - block time
        pop de
        jr c,.final
        call frac
        jr c,.final
        ld (tw_f),a
        call enow
        ld (t_t0),hl
        call tw_view
        call render_geom
        call flipfl                     ; the view before this one on screen before its bank can be chosen again
        call raster
        call flipdef
        ld hl,tw_n
        inc (hl)
        call ptick
        call enow
        ld de,(t_t0)
        or a
        sbc hl,de
        ld (t_tw),hl
        ld de,(t_fin)                   ; the final view costs at least what an in-between view of the same
        or a                            ; scene did (t_fin may come from another area or the first update)
        sbc hl,de
        jp c,.loop
        add hl,de
        ld (t_fin),hl
        jp .loop
.fpop:  pop hl
.final: xor a
        ld (tw_on),a
        ld (tw_madj),a
        ld l,a
        ld h,a
        ld (tw_hadj),hl
        ld hl,fin_g
        ld de,in_cam
        ld bc,15
        ldir
        ld hl,fin_r
        ld de,in_sky
        ld bc,4
        ldir
        call ov_scan                    ; what the copy put over the raster (its time is the final view's)
        ld a,(VP+10)
        or a
        jr z,1F
        call ptick
        call enow
        ld (t_t0),hl
1:      call render_geom
        call flipfl
        ld a,(nfull)
        or a
        jr nz,2F
        ld a,(in_sky)
        or a
        call z,l2copy
2:      call raster
        call setpal
        ld a,(VP+10)
        or a
        jp z,m3_fl3
        call ptick
        call enow
        ld de,(t_t0)
        or a
        sbc hl,de
        ld e,l                          ; + 1/8 and the flip's line wait: the next update's estimate
        ld d,h
        ld b,3
4:      srl d
        rr e
        djnz 4B
        add hl,de
        ld de,24
        add hl,de
        ld (t_fin),hl
        call waittgt
m3_fl3: ld a,(m_pc)                     ; 2 = the dissolve brings this view on (m3_dshow): no flip yet
        cp 2
        jp z,m3_end
        call ov_sightc                  ; the sight white or black over the new view
        call ov_ptrc
        call ov_flip                    ; the overlay sprites with the new view
        call flip
        ld a,(l2shown)
        ld (l2last),a
        call nexth
        ld hl,fin_g
        ld de,prev
        ld bc,15
        ldir
        ld a,1
        ld (prev_ok),a
m3_end: xor a
        ld (VP+10),a                    ; the window closes: r_leave gives the game its 3.5 MHz back
        ret

; m3_pshow (h_off, the portcullis at BEGIN): the final view only, at the original's time; m_pc = 1 if one was drawn
m3_pshow:
        ld a,(fin_ok)
        or a
        jr nz,1F
        ld (m_pc),a
        jp m3_wait_end
1:      ld a,1
        ld (m_pc),a
m3_pgo: xor a
        ld (tw_n),a
        ld hl,0
        ld (t_tgt),hl
        ld a,(VP+10)
        or a
        jp z,m3_show.final
        call ptick
        ld hl,(VP+2)
        call ktgt
        call isradj
        ld (t_tgt),hl
        jp m3_show.final

; m3_dshow (h_off1, (0x7349) = 1: the view goes on by the dissolve): the final view drawn in the hidden bank at the
; original's time. Layer 2 on = the last view is on it: m_pc = 2, the dissolve runs on Layer 2 (dis_pal, dis_pass)
; and m3_dfin shows the bank. Layer 2 off (a non-view screen before): as the portcullis, m_pc = 1.
m3_dshow:
        ld a,(fin_ok)
        or a
        jr nz,1F
        ld (m_pc),a
        jp m3_wait_end
1:      HLIB_IFF_DI
        push af
        ld bc,0x243B
        ld a,0x69
        out (c),a
        inc b
        in a,(c)
        ld c,a
        pop af
        HLIB_IFF_EI
        bit 7,c
        jp z,m3_pshow
        ld a,2
        ld (m_pc),a
        jp m3_pgo
; m3_dfin: after the dissolve. 2: the hidden bank (the same picture now) becomes the view shown, as a final view's
; flip; then, and for 1, the palettes and every overlay sprite from the screen as it is now (ov_pstep)
m3_dfin:
        ld a,(m_pc)
        cp 2
        push af
        xor a
        ld (m_pc),a
        pop af
        call z,m3_fl3
        jp ov_pstep
; dis_pal (h_diss): the area's colours as 0xB347 has just set them; 4 passes to come
dis_pal:
        ld a,4
        ld (dis_n),a
        call ov_in
        ld a,(27353+G)
        ld (in_attr),a
        call ov_out
        jp setpal
; dis_pass (h_dpass, before each of the game's 4 passes ends): the same bytes on Layer 2. The game copies bytes
; c, c + 4 .. c + 20 of each row, c from its table 0xB65E (pass, row & 3); here 8 pixels a byte from the hidden
; bank (slot 5) to the bank on screen (slot 4).
dis_tab: db 0,2,1,3, 1,3,0,2, 3,1,2,0, 2,0,3,1
dis_pass:
        call ov_in
        ld a,(dis_n)
        dec a
        and 3
        ld (dis_n),a
        add a,a
        add a,a
        ld (dis_t),a
        ld a,(in_l2page)
        inc a
        ld c,a
        ld a,(l2shown)
        inc a
        ld b,a
        ld ixl,4
.ch:    ld a,c
        ld (cur55),a
        nextreg 0x55,a
        ld a,b
        ld (cur54),a
        nextreg 0x54,a
        push bc
        ld a,ixl
        cp 1
        ld b,32
        jr nz,1F
        ld b,16
1:      ld h,0xA0
.row:   push bc
        ld a,h
        and 3
        ld e,a
        ld a,(dis_t)
        add a,e
        ld de,dis_tab
        add de,a
        ld a,(de)
        add a,a
        add a,a
        add a,a
        add a,32
        ld l,a
        ld d,h
        res 5,d
        ld e,l
        ld a,6
.by:    DUP 8
        ldi
        EDUP
        add hl,24
        add de,24
        dec a
        jr nz,.by
        pop bc
        inc h
        djnz .row
        pop bc
        inc b
        inc c
        dec ixl
        jr nz,.ch
        jp ov_out

; ov_pstep: a portcullis step over the view in colour (h_w77p): in_attr = (27353) now, setpal, the sight's colour
; over the bank shown, every sprite (ov_all)
ov_pstep:
        call ov_in
        ld a,(27353+G)
        ld (in_attr),a
        call ov_out
        call setpal
        ld a,(l2shown)
        call ov_sightp
; ov_all: every overlay sprite rebuilt from the screen
ov_all: call ov_in
        xor a
        ld (ov_sy),a
.ly:    xor a
        ld (ov_sx),a
.lx:    call ov_up
        ld hl,ov_sx
        inc (hl)
        ld a,(hl)
        cp 12
        jr c,.lx
        ld hl,ov_sy
        inc (hl)
        ld a,(hl)
        cp 7
        jr c,.ly
        jp ov_out

; m3_wait_end: a non-view screen's block: its original time, then the window closes
m3_wait_end:
        ld a,(VP+10)
        or a
        ret z
        call ptick
        ld hl,(VP+2)
        call ktgt
        call isradj
        ld (t_tgt),hl
        call waittgt
        jp m3_end

; waittgt: until the window has lasted t_tgt lines (gives up after 262,144 polls: no line counter)
waittgt:
        ld b,4
        ld de,0
1:      push bc
        push de
        call ptick
        call enow
        ld de,(t_tgt)
        or a
        sbc hl,de
        pop de
        pop bc
        ret nc
        dec de
        ld a,d
        or e
        jr nz,1B
        djnz 1B
        ret

; enow: HL = the window's real lines so far: its counted lines + the handler's time held out of them
enow:
        ld hl,(VP+14)
        ld de,(t_h0)
        or a
        sbc hl,de
        ld de,(VP+2)
        add hl,de
        ret

; isradj: HL = the block's original main-line time (lines) -> its real time with the handler: the handler's
; lines per interrupt h as measured in this window, T frames = HL / (312 - h), + h x T
isradj:
        push hl
        ld hl,(VP+14)
        ld de,(t_h0)
        or a
        sbc hl,de
        ld a,(m_ni)
        or a
        jr z,.none
        ld c,a
        ld b,0
        ld e,b
1:      or a
        sbc hl,bc
        jr c,2F
        inc e
        ld a,e
        cp HLIB_PACE_NL/2
        jr c,1B
2:      ld a,e                          ; A = the handler's lines a frame
        or a
        jr z,.none
        ld hl,HLIB_PACE_NL
        ld d,0
        sbc hl,de
        ld b,h
        ld c,l
        pop hl
        push hl
        ld de,0
3:      or a
        sbc hl,bc
        jr c,4F
        inc de
        jr 3B
4:      ld h,d                          ; HL = T frames
        ld l,e
        ld d,l
        ld e,a
        mul d,e
        push de
        ld d,h
        ld e,a
        mul d,e
        ld h,e
        ld l,0
        pop de
        add hl,de                       ; h x T
        pop de
        add hl,de
        ret nc
        ld hl,0xFFFF
        ret
.none:  pop hl
        ret

; ktgt: HL = lines at 28 MHz -> HL = HL x (m_k) / 16, at most 0xFFFF
ktgt:
        ld a,(m_k)
        ld c,a
        ld d,l
        ld e,c
        mul d,e
        push de
        ld d,h
        ld e,c
        mul d,e
        pop hl
        ld a,h
        add a,e
        ld h,a
        ld a,d
        adc a,0
        cp 0x10
        jr nc,.sat
        ld b,4
1:      srl a
        rr h
        rr l
        djnz 1B
        ret
.sat:   ld hl,0xFFFF
        ret

; frac: DE = num, HL = den (signed) -> A = 256 x num / den (0-255); carry = not inside (den <= 0, num >= den)
frac:
        bit 7,h
        jr nz,.no
        bit 7,d
        jr nz,.no
        push hl
        or a
        sbc hl,de
        pop hl
        jr c,.no
        jr z,.no
1:      ld a,h
        or a
        jr z,2F
        srl h
        rr l
        srl d
        rr e
        jr 1B
2:      ld a,e
        cp l
        jr c,3F
        ld a,255
        or a
        ret
3:      ld h,l
        ld bc,0x0800
4:      add a,a
        jr c,5F
        cp h
        jr c,6F
5:      sub h
        scf
        jr 7F
6:      or a
7:      rl c
        djnz 4B
        ld a,c
        or a
        ret
.no:    scf
        ret

; tw_setup: A = 1 when in-between views apply: the last view's area, a camera that moved a step or turned
tw_setup:
        ld a,(prev_ok)
        or a
        ret z
        ld hl,fin_g+8                   ; cull flag, the area's two lists
        ld de,prev+8
        ld b,7
1:      ld a,(de)
        cp (hl)
        jr nz,.no
        inc hl
        inc de
        djnz 1B
        ld ix,fin_g
        ld iy,tw_d
        ld bc,0x0300                    ; C = any change
2:      ld l,(ix+0)
        ld h,(ix+1)
        ld e,(ix+prev-fin_g)
        ld d,(ix+prev-fin_g+1)
        or a
        sbc hl,de
        ld (iy+0),l
        ld (iy+1),h
        ld a,l
        or h
        or c
        ld c,a
        ld a,h                          ; |delta| < 1024: a step, not a jump
        add a,4
        cp 8
        jr nc,.no
        inc ix
        inc ix
        inc iy
        inc iy
        djnz 2B
        ld a,(prev+6)
        ld e,a
        ld a,(fin_g+6)
        call .ang
        jr c,.no
        ld (tw_dy),a
        or c
        ld c,a
        ld a,(prev+7)
        ld e,a
        ld a,(fin_g+7)
        call .ang
        jr c,.no
        ld (tw_dp),a
        or c
        ret z
        ld a,1
        ret
.no:    xor a
        ret
.ang:   sub e                           ; A = the short way round, -8 .. 8 units; carry = further
        jr nc,3F
        add a,72
3:      cp 36
        jr c,4F
        sub 72
4:      ld d,a
        add a,8
        cp 17
        ccf
        ld a,d
        ret

; tw_view: the inputs of the in-between view at (tw_f) / 256 of the way
tw_view:
        ld hl,fin_g
        ld de,in_cam
        ld bc,15
        ldir
        ld ix,prev
        ld iy,tw_d
        ld de,in_cam
        ld b,3
1:      push bc
        push de
        ld l,(iy+0)
        ld h,(iy+1)
        call smulf
        ld e,(ix+0)
        ld d,(ix+1)
        add hl,de
        pop de
        ex de,hl
        ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        ex de,hl
        inc ix
        inc ix
        inc iy
        inc iy
        pop bc
        djnz 1B
        ld a,(tw_dy)
        ld e,a
        ld a,(prev+6)
        call .fine
        ld (in_yaw),a
        ld a,c
        rrca
        rrca
        and 1
        ld (tw_madj),a
        ld a,(in_yaw)
        call sc_fine
        ld (tw_ys),a
        ld a,b
        ld (tw_yc),a
        ld a,(tw_dp)
        ld e,a
        ld a,(prev+7)
        call .fine
        ld (in_pitch),a
        ld a,c                          ; the horizon: 11 rows a unit
        ld d,a
        ld e,11
        mul d,e
        ld a,e
        rrca
        rrca
        rrca
        and 31
        ld l,a
        ld h,0
        ld (tw_hadj),hl
        ld a,(in_pitch)
        call sc_fine
        ld (tw_ps),a
        ld a,b
        ld (tw_pc),a
        ld a,1
        ld (tw_on),a
        ret
.fine:  ld l,a                          ; A = from (units), E = delta (units, signed) -> A = unit, C = eighths
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        push hl
        ld a,e
        add a,a
        add a,a
        add a,a
        ld l,a
        rla
        sbc a,a
        ld h,a
        call smulf
        pop de
        add hl,de
        bit 7,h
        jr z,2F
        ld de,576
        add hl,de
2:      ld de,576
        or a
        sbc hl,de
        jr nc,3F
        add hl,de
3:      ld a,l
        and 7
        ld c,a
        srl h
        rr l
        srl h
        rr l
        srl h
        rr l
        ld a,l
        ret

; smulf: HL (signed) x (tw_f) / 256 -> HL
smulf:
        ld a,(tw_f)
        ld c,a
        ld a,h
        or a
        push af
        jp p,1F
        xor a
        sub l
        ld l,a
        sbc a,a
        sub h
        ld h,a
1:      ld d,l
        ld e,c
        mul d,e
        ld b,d
        ld d,h
        ld e,c
        mul d,e
        ld l,b
        ld h,0
        add hl,de
        pop af
        ret p
        xor a
        sub l
        ld l,a
        sbc a,a
        sub h
        ld h,a
        ret

; sc_fine: A = unit 0-71, C = eighths -> A = sin, B = cos between the game's table entries
sc_fine:
        ld l,a
        ld h,0
        add hl,hl
        ld de,sincos
        add hl,de
        call .one
        push af
        inc hl
        call .one
        ld b,a
        pop af
        ret
.one:   ld e,(hl)
        inc hl
        inc hl
        ld a,(hl)
        dec hl
        dec hl
        sub e
        ld d,a
        xor a
        ld b,c
        inc b
        jr 2F
1:      add a,d
2:      djnz 1B
        sra a
        sra a
        sra a
        add a,e
        ret

; tw_matrix: matrix's first part with the in-between view's sin / cos (cmr.asm "matrix" jumps here)
tw_matrix:
        ld hl,ident64
        ld de,ymat
        ld bc,9
        ldir
        ld a,(tw_ys)
        ld (ymat+6),a
        neg
        ld (ymat+2),a
        ld a,(tw_yc)
        ld (ymat+0),a
        ld (ymat+8),a
        ld hl,ident64
        ld de,pmat
        ld bc,9
        ldir
        ld a,(tw_ps)
        ld (pmat+5),a
        neg
        ld (pmat+7),a
        ld a,(tw_pc)
        ld (pmat+4),a
        ld (pmat+8),a
        ld ix,pmat
        ld iy,ymat
        ld de,ytmp
        call mat3
        ld hl,ytmp
        ld de,ymat
        ld bc,9
        ldir
        jp matrix_tail

; flip: the bank just drawn goes on screen, outside the view's lines (32-143): no tear
flip:
        ld de,4096
1:      push de
        call hlib_now
        pop de
        ld a,h
        or a
        jr nz,2F                        ; line 256+
        ld a,l
        cp 30
        jr c,2F
        cp 144
        jr nc,2F
        dec de
        ld a,d
        or e
        jr nz,1B
2:
flip_do:
        ld a,(in_l2page)
        ld (l2shown),a
        srl a
        nextreg 0x12,a
        nextreg 0x69,0x80
        nextreg 0x15,1                  ; the overlay sprites over it (SLU)
        ret

; flipdef: an in-between view is drawn. Outside the view's lines it goes on screen now; inside them the flip
; waits (fl_pend) while the next view's geometry runs: flipchk at each object record shows it once the
; raster has left the view, flipfl (before anything writes Layer 2 again) waits for that as flip does.
; The bank to draw next (nexth) is chosen when the flip happens.
flipdef:
        call flip_in
        jr nc,flip_go
        neg
        add a,144
        rrca
        rrca
        rrca
        and 31
        inc a
        ld (fl_skip),a                  ; the first look after (lines to go) / 8 records, then every 3rd
        ld a,1
        ld (fl_pend),a
        ret
flip_go:
        xor a
        ld (fl_pend),a
        call flip_do
        jp nexth
flipchk:
        push hl
        ld hl,fl_skip
        dec (hl)
        jr z,1F
        pop hl
        ret
1:      ld (hl),3
        push bc
        push de
        call flip_in
        call nc,flip_go
        pop de
        pop bc
        pop hl
        ret
flipfl:
        ld a,(fl_pend)
        or a
        ret z
        xor a
        ld (fl_pend),a
        call flip
        jp nexth
; flip_in: CF = the raster is inside the view's lines (30-143)
flip_in:
        call hlib_now
        ld a,h
        or a
        ret nz                          ; line 256+ (CF = 0)
        ld a,l
        cp 30
        ccf
        ret nc
        cp 144
        ret
        
; nexth: the bank to draw next = neither the one on screen nor the last update's view
nexth:
        ld a,(l2shown)
        call .nx
        ld hl,l2last
        cp (hl)
        call z,.nx
        ld (in_l2page),a
        ret
.nx:    add a,6
        cp PG_LC+6
        ret c
        ld a,PG_LA
        ret

; l2copy: view lines 32-143, pixels 32-223, the last update's view -> the bank being drawn (source in slot 5)
l2copy:
        ld a,(l2last)
        inc a
        ld c,a
        ld a,(in_l2page)
        inc a
        ld b,a
        ld ixl,4
1:      ld a,c
        ld (cur55),a
        nextreg 0x55,a
        ld a,b
        ld (cur54),a
        nextreg 0x54,a
        push bc
        ld a,ixl
        cp 1
        ld a,32
        jr nz,2F
        ld a,16
2:      ld hl,0xA020
        ld de,0x8020
        rrca
        rrca
        rrca                            ; chunks of 8 rows
3:      push af
        call l2chunk
        add hl,0x0800
        add de,0x0800
        pop af
        dec a
        jr nz,3B
        pop bc
        inc b
        inc c
        dec ixl
        jr nz,1B
        ld a,5
        ld (cur55),a
        nextreg 0x55,a
        ret

; l2chunk: 8 view rows (7 x 256 + 192 bytes: the columns between the rows are the same in every bank, never
; drawn) from HL to DE, both kept. By DMA (0.18 us a byte at 28 MHz against LDIR's 0.86: TECHNIQUES 1.0) unless
; the core is older than 3.00, hardware IM 2 is on, or the frame interrupt may fall inside the transfer: the
; CPU cannot see its pulse while the DMA holds the bus. The line's low byte 238-255 or 0-3 = the interrupt's
; lines (248 VGA, 256 HDMI at 50 Hz) and the chunk's 6 lines before them: those chunks go by LDIR.
l2chunk:
        push hl
        push de
        ld a,(dma_st)
        or a
        call z,dma_det
        dec a
        jr z,.cpu                       ; 1 = CPU only
        ld (dma_pk+3),hl
        ld (dma_pk+10),de
        HLIB_IFF_DI                     ; the handler's clock selects registers on the same port
        push af
        ld bc,0x243B
        ld a,0x1F
        out (c),a
        inc b
        in a,(c)
        ld c,a
        pop af
        HLIB_IFF_EI
        ld a,c
        add a,18
        cp 22
        jr c,.cpu
        ld hl,dma_pk
        ld bc,15*256+0x6B
        otir
        pop de
        pop hl
        ret
.cpu:   ld a,8
1:      ld bc,192
        ldir
        add hl,64
        add de,64
        dec a
        jr nz,1B
        pop de
        pop hl
        ret
; dma_det: the first use. A = dma_st = 2 (DMA) or 1 (CPU); the program's fixed bytes to work RAM
dma_det:
        push hl
        push de
        ld hl,dma_pk0
        ld de,dma_pk
        ld bc,15
        ldir
        HLIB_IFF_DI
        push af
        ld bc,0x243B
        ld a,0x01
        out (c),a
        inc b
        in a,(c)
        ld d,a                          ; core version, major << 4 | minor
        dec b
        ld a,0xC0
        out (c),a
        inc b
        in a,(c)
        ld e,a
        pop af
        HLIB_IFF_EI
        ld a,d
        inc a
        jr z,.no
        dec a
        cp 0x30
        jr c,.no
        bit 0,e
        jr nz,.no
        ld a,2
        jr .set
.no:    ld a,1
.set:   ld (dma_st),a
        pop de
        pop hl
        ret
dma_pk0:
        db 0x83,0xC3,0x7D               ; disable, reset, WR0: A -> B, address + length follow
        dw 0,7*256+192
        db 0x14,0x10,0xAD               ; both memory, incrementing; continuous, B's address follows
        dw 0
        db 0x82,0xCF,0x87               ; stop at the end, load, enable

; setpal: Layer 2 palette. Pixel byte = 2 x code + the original bit: bit 0 clear = the area's paper; set = the
; face's colour (codes 0-15, PLACEHOLDER table) or the area's ink (16-33: sky / ground, mountains, bolt).
setpal:
        nextreg 0x43,0x10
        nextreg 0x40,0
        ld a,(in_attr)
        ld c,a
        and 0x40
        rrca
        rrca
        rrca
        ld b,a
        ld a,c
        and 7
        or b
        ld hl,ula16
        add hl,a
        ld e,(hl)
        ld a,c
        rrca
        rrca
        rrca
        and 7
        or b
        ld hl,ula16
        add hl,a
        ld d,(hl)
        push de
        ld hl,facepal
        ld de,facecur
        ld bc,16
        ldir
        pop de
        ld a,(col_on)                   ; 0 = the original's look: every face in the area's ink
        or a
        jr nz,7F
        ld hl,facecur
        ld b,16
6:      ld (hl),e
        inc hl
        djnz 6B
7:      ld hl,facecur
        ld b,16
1:      ld a,d
        nextreg 0x41,a
        ld a,(hl)
        inc hl
        nextreg 0x41,a
        djnz 1B
        ld b,18
2:      ld a,d
        nextreg 0x41,a
        ld a,e
        nextreg 0x41,a
        djnz 2B
        nextreg 0x43,0x20               ; sprite palette: 1 = the area's paper, 2 = its ink (the overlays)
        nextreg 0x40,1
        ld a,d
        nextreg 0x41,a
        ld a,e
        nextreg 0x41,a
        ld a,(col_on)                   ; 3 = white, 4 = black: the fixed overlays (ov_fr0 / ov_fr1); with the
        or a                            ; colours off, the area's ink and paper
        jr z,8F
        nextreg 0x41,0xFF
        nextreg 0x41,0x00
        jr 9F
8:      ld a,e
        nextreg 0x41,a
        ld a,d
        nextreg 0x41,a
9:
        push ix                         ; ov_lumt: each Layer 2 pixel byte's brightness, as the colours above
        ld ix,facecur
        ld hl,ov_lumt
        ld b,16
3:      ld a,d
        call lumc
        ld (hl),a
        inc hl
        ld a,(ix+0)
        inc ix
        call lumc
        ld (hl),a
        inc hl
        djnz 3B
        ld b,18
4:      ld a,d
        call lumc
        ld (hl),a
        inc hl
        ld a,e
        call lumc
        ld (hl),a
        inc hl
        djnz 4B
        pop ix
        ret
; lumc: A = RRRGGGBB -> 3 R + 5 G + 2 B (0-62)
lumc:   push bc
        push de
        ld c,a
        and 3
        add a,a
        ld b,a
        ld a,c
        rrca
        rrca
        and 7
        ld e,a
        add a,a
        add a,a
        add a,e
        add a,b
        ld b,a
        ld a,c
        rlca
        rlca
        rlca
        and 7
        ld e,a
        add a,a
        add a,e
        add a,b
        pop de
        pop bc
        ret

ula16:  db 0x00,0x02,0xA0,0xA2,0x14,0x16,0xB4,0xB6      ; the ULA's colours as RRRGGGBB
        db 0x00,0x03,0xE0,0xE2,0x1C,0x1F,0xFC,0xFF      ; bright (magenta 0xE2: 0xE3 is the transparent colour)

        MACRO RGB332 red, green, blue
        db ((red >> 5) << 5) | ((green >> 5) << 2) | (blue >> 6)
        ENDM
col_on: db 1                            ; 1 = colours, 0 = the original's look (the .nxc's colour set pokes it)
facepal:                                ; PLACEHOLDER (the user's palette later): colour index 1..16
        RGB332 40,40,48
        RGB332 150,150,160
        RGB332 196,120,70
        RGB332 120,160,90
        RGB332 90,130,200
        RGB332 210,190,120
        RGB332 170,90,90
        RGB332 110,110,120
        RGB332 225,225,230
        RGB332 200,160,60
        RGB332 80,170,170
        RGB332 150,110,190
        RGB332 100,140,70
        RGB332 220,140,160
        RGB332 60,90,150
        RGB332 180,200,220
; ---- M3b overlays ----------------------------------------------------------------------------------------------
; A grid of 84 sprites (12 x 7, 16 x 16, 4-bit; sprite k = pattern k = 12 x band + column) covers the view (pixels
; 32-223, lines 32-143) over Layer 2 and carries what the game draws over its own raster. A pixel is opaque where
; the screen differs from the raster's output (ov_s: the buffer at the copy, the centre marker taken out): the
; marker, the cursor. Buffer writes the copy has not shown (the handler's printer) stay out, as on the screen.
; Opaque = the area's ink where the screen's bit is set, its paper where clear (sprite palette 1 / 2; 0 = clear).

; ov_in / ov_out: the game's 0x4000-0x7FFF in slots 4-5 (at +G), then slots 4-5 back as they were (read from the
; registers: after r_enter they hold the game's pages 4 / 5 while cur54 / cur55 may still name others). The reads
; with interrupts off: the handler's clock selects the line registers on the same port.
ov_in:  HLIB_IFF_DI
        push af                         ; P/V for HLIB_IFF_EI (IN / DEC change it)
        ld bc,0x243B
        ld a,0x54
        out (c),a
        inc b
        in a,(c)
        ld (ov_k54),a
        dec b
        ld a,0x55
        out (c),a
        inc b
        in a,(c)
        ld (ov_k55),a
        pop af
        HLIB_IFF_EI
        ld a,10
        ld (cur54),a
        nextreg 0x54,a
        ld a,11
        ld (cur55),a
        nextreg 0x55,a
        ret
ov_out: ld a,(ov_k54)
        ld (cur54),a
        nextreg 0x54,a
        ld a,(ov_k55)
        ld (cur55),a
        nextreg 0x55,a
        ret

; ov_cap: before the copy (sites 0x859C, 0xB638): ov_s = the buffer; its time is not the block's
ov_cap: ld a,(VP+10)
        or a
        call nz,ptick
        call ov_in
        ld hl,0x5CBC+G
        ld de,ov_s
        ld bc,2688
        ldir
        xor a
        ld (ov_fr0),a                   ; the sight: on below if this view has it
        ld (ov_fr1),a                   ; the pointer: the copy wipes it, the show (0x9F3C CALL 0xB63D) redraws it
        ld a,(27405+G)                  ; the raster XORs the centre marker in at its end (0x9F0B .. 0x9F15)
        or a
        jr nz,1F
        ld a,(27409+G)
        or a
        jr z,1F
        ld hl,ov_mkrec
        ld de,ov_fr0
        ld bc,6+7*4
        ldir
        ld hl,ov_s+53*24+11             ; take it out again (0xCF45: rows 53-59, bytes 11-12)
        ld de,24
        ld b,3
2:      ld a,(hl)
        xor 1
        ld (hl),a
        add hl,de
        djnz 2B
        ld a,(hl)
        xor 0x0E
        ld (hl),a
        inc hl
        ld a,(hl)
        xor 0xE0
        ld (hl),a
        dec hl
        ld b,3
3:      add hl,de
        ld a,(hl)
        xor 1
        ld (hl),a
        djnz 3B
1:      call ov_out
        ld a,(VP+10)
        or a
        ret z
        jp prest

; ov_scan: ov_new(k) = 1 where the buffer (as copied) differs from ov_s under sprite k
ov_scan:
        call ov_in
        ld hl,0x5CBC+G
        ld de,ov_s
        ld iy,ov_new
        ld c,7
.band:  ld b,16
.row:   push bc
        push iy
        ld b,12
.sp:    ld a,(de)
        xor (hl)
        inc hl
        inc de
        ld c,a
        ld a,(de)
        xor (hl)
        inc hl
        inc de
        or c
        jr z,1F
        ld (iy+0),1
1:      inc iy
        djnz .sp
        pop iy
        pop bc
        djnz .row
        push de
        ld de,12
        add iy,de
        pop de
        dec c
        jr nz,.band
        jp ov_out

; ov_flip: before the new view is shown: every sprite with a new difference or opaque pixels rebuilt
ov_flip:
        call ov_in
        ld hl,ov_new
        ld de,ov_nz
        xor a
        ld (ov_sy),a
.ly:    xor a
        ld (ov_sx),a
.lx:    ld a,(de)
        or (hl)
        jr z,1F
        ld (hl),0
        push hl
        push de
        call ov_up
        pop de
        pop hl
1:      inc hl
        inc de
        ld a,(ov_sx)
        inc a
        ld (ov_sx),a
        cp 12
        jr c,.lx
        ld a,(ov_sy)
        inc a
        ld (ov_sy),a
        cp 7
        jr c,.ly
        jp ov_out

; ov_cur: after the game's cursor draw (0xCDD2) or restore (0xCECD): the sprites over its rectangle. Descriptor
; (copied to VP+34 by cur_d): x (pixel, 1-based), y (bottom row = 111 - y; rows go up), width (bytes), rows | flag
ov_cur: ld a,(VP+10)
        or a
        call nz,ptick                   ; its time is not the block's
        call ov_in
        call ov_ptr
        ld a,(VP+35)
        ld b,a
        ld a,111
        sub b                           ; the bottom row in 8 bits as the game finds it (y >= 250: rows 112+)
        jp m,.out                       ; bit 7: all above the view
        ld (ov_rb),a
        ld c,a
        ld a,(VP+37)
        and 127
        jr z,.out
        ld b,a
        ld a,c
        sub b
        inc a                           ; top row, may be negative (>= -126)
        jp p,1F
        xor a
1:      cp 112
        jr nc,.out                      ; all below the view
        swapnib
        and 15
        ld (ov_sy0),a
        ld a,(ov_rb)
        cp 112
        jr c,5F
        ld a,111                        ; the grid's last row
5:      swapnib
        and 15
        ld (ov_sy1),a
        ld a,(VP+34)
        dec a
        ld c,a
        srl c
        cp 192
        jr c,2F
        set 7,c
2:      sra c
        sra c                           ; C = the first byte column as the game finds it (signed)
        ld a,(VP+36)
        add a,c                         ; + width: the last column (one more for the pixel shift)
        jp m,.out                       ; all left of the view
        cp 24
        jr c,3F
        ld a,23
3:      srl a
        ld (ov_sx1),a
        ld a,c
        bit 7,a
        jr z,4F
        xor a
4:      srl a
        ld (ov_sx0),a
        ld a,(ov_sy0)
.ly:    ld (ov_sy),a
        ld a,(ov_sx0)
.lx:    ld (ov_sx),a
        call ov_up
        ld a,(ov_sx)
        inc a
        ld b,a
        ld a,(ov_sx1)
        cp b
        ld a,b
        jr nc,.lx
        ld a,(ov_sy)
        inc a
        ld b,a
        ld a,(ov_sy1)
        cp b
        ld a,b
        jr nc,.ly
.out:   call ov_out
        ld a,(VP+10)
        or a
        ret z
        jp prest

; ov_up: sprite (ov_sx, ov_sy)'s pattern from the screen, the buffer and ov_s, uploaded; ov_nz(k) set
ov_up:  ld a,(ov_sy)
        ld c,a
        add a,a
        add a,c
        add a,a
        add a,a
        ld c,a
        ld a,(ov_sx)
        add a,c
        ld (ov_k),a
        srl a
        jr nc,1F
        or 0x80
1:      ld bc,0x303B
        out (c),a                       ; pattern k: slot k / 2, + 128 bytes when k is odd
        ld a,(ov_sy)
        swapnib
        ld d,a
        ld e,24
        mul d,e
        ld a,(ov_sx)
        add a,a
        add de,a                        ; its first byte's offset in the buffer
        ld iy,ov_s
        add iy,de
        ld a,(ov_sy)
        swapnib
        add a,32
        ld d,a
        ld a,(ov_sx)
        swapnib
        add a,32
        ld e,a
        pixelad                         ; HL = its first screen byte (0x4000-based)
        xor a
        ld (ov_or),a
        call ov_fhit
        jp nz,ov_upf                    ; a fixed overlay (sight, pointer) touches this sprite
        ld b,16
.row:   push hl
        ld a,h
        add a,high G
        ld h,a
        ld a,(hl)
        inc l
        ld c,(hl)
        call ov_byte
        inc iy
        ld a,c
        call ov_byte
        ld de,23
        add iy,de
        pop hl
        pixeldn
        djnz .row
ov_upz: ld a,(ov_k)
        ld hl,ov_nz
        add hl,a
        ld a,(ov_or)
        ld (hl),a
        ret

; ov_byte: A = a screen byte, IY = its ov_s byte (the raster's) -> 4 bytes of 4-bit pixels to port 0x5B: opaque
; where they differ. DE, HL lost
ov_byte:
        ld e,a
        xor (iy+0)                      ; screen ^ the raster's
        jr z,.z
        ld d,a
        ld hl,ov_or
        or (hl)
        ld (hl),a
        ld a,d
        and 0xF0
        ld l,a
        ld a,e
        swapnib
        and 15
        or l
        ld l,a
        ld h,high ov_ta
        ld a,(hl)
        out (0x5B),a
        inc h
        ld a,(hl)
        out (0x5B),a
        ld a,d
        swapnib
        and 0xF0
        ld l,a
        ld a,e
        and 15
        or l
        ld l,a
        dec h
        ld a,(hl)
        out (0x5B),a
        inc h
        ld a,(hl)
        out (0x5B),a
        ret
.z:     out (0x5B),a
        out (0x5B),a
        out (0x5B),a
        out (0x5B),a
        ret

; ov_fhit: Z = no fixed overlay record touches sprite (ov_sx, ov_sy). A, B lost
ov_fhit:
        push hl
        ld hl,ov_fr0
        call .one
        jr nz,1F
        ld hl,ov_fr1
        call .one
1:      pop hl
        ret
.one:   ld a,(hl)                       ; on
        or a
        ret z
        inc hl
        ld a,(ov_sy)
        swapnib                         ; the sprite's first row
        ld b,a
        add a,15
        cp (hl)
        jr c,.no                        ; its last row above the first
        inc hl
        ld a,(hl)
        cp b
        jr c,.no                        ; the last above its first row
        inc hl
        ld a,(ov_sx)
        add a,a
        sub (hl)                        ; its first column - the record's (signed)
        inc a
        cp 3
        jr nc,.no                       ; -1, 0, 1: the two bytes overlap
        or 1
        ret
.no:    xor a
        ret

; ov_fwk: A = byte column, (ov_r) = buffer row -> D = white bits, E = black bits, (ov_tt) = clear bits (the pointer
; over the sight: it is drawn on the screen after the view). A lost
ov_fwk: push hl
        push bc
        ld c,a
        ld de,0
        xor a
        ld (ov_tt),a
        ld hl,ov_fr0
        call .one
        push de
        ld a,(ov_tt)
        push af
        ld de,0
        xor a
        ld (ov_tt),a
        ld hl,ov_fr1
        call .one
        ld a,(ov_tt)
        or d
        or e
        cpl
        ld b,a                          ; not the pointer's pixels
        pop af                          ; the sight's clear bits
        and b
        ld hl,ov_tt
        or (hl)
        ld (hl),a
        pop hl                          ; H, L = the sight's white, black
        ld a,b
        and h
        or d
        ld d,a
        ld a,b
        and l
        or e
        ld e,a
        pop bc
        pop hl
        ret
.one:   ld a,(hl)
        or a
        ret z
        ld (ov_fc),a
        inc hl
        ld a,(ov_r)
        cp (hl)
        ret c                           ; above its first row
        inc hl
        ld b,a
        ld a,(hl)
        cp b
        ret c                           ; below its last row
        inc hl
        ld a,c
        sub (hl)
        cp 2
        ret nc                          ; not its column 0 or 1
        inc hl
        push de
        add a,a
        ld e,(hl)
        inc hl
        ld d,(hl)
        add de,a                        ; base + 2 x column
        ld l,b
        ld h,0
        add hl,hl
        add hl,hl
        add hl,de                       ; + 4 x row
        pop de
        ld b,(hl)                       ; C bits
        inc hl
        ld a,(hl)                       ; T bits
        ld hl,ov_tt
        or (hl)
        ld (hl),a
        ld a,(ov_fc)
        cp 3
        ld a,b
        jr nz,1F
        or d
        ld d,a
        ret
1:      or e
        ld e,a
        ret

; ov_upf: ov_up's rows when a fixed overlay touches the sprite (HL = first screen byte, IY = its ov_s byte)
ov_upf: ld a,(ov_sy)
        swapnib
        ld (ov_r),a
        ld b,16
.row:   push bc
        push hl
        ld a,h
        add a,high G
        ld h,a
        ld a,(hl)
        inc l
        ld c,(hl)
        push bc                         ; C = the second screen byte
        push af
        ld a,(ov_sx)
        add a,a
        call ov_fwk
        pop af
        call ov_bytef
        inc iy
        ld a,(ov_sx)
        add a,a
        inc a
        call ov_fwk
        pop bc
        ld a,c
        call ov_bytef
        ld de,23
        add iy,de
        ld hl,ov_r
        inc (hl)
        pop hl
        pixeldn
        pop bc
        djnz .row
        jp ov_upz

; ov_bytef: ov_byte with D = white bits, E = black bits (palette 3 / 4, opaque), (ov_tt) = clear bits over the
; rule. BC, DE, HL lost
ov_bytef:
        ld c,a                          ; C = screen
        ld a,(ov_tt)
        or d
        or e
        ld a,c
        jp z,ov_byte                    ; no fixed pixels in this byte
        xor (iy+0)
        ld b,a                          ; B = screen ^ the raster's
        or d
        or e
        ld hl,ov_or
        or (hl)
        ld (hl),a
        ld l,4
.o:     call .px
        swapnib
        ld h,a
        call .px
        or h
        out (0x5B),a
        dec l
        jr nz,.o
        ret
.px:    ld a,3                          ; the next pixel (bit 7 of D, E, (ov_tt), B, C; all shifted)
        sla d
        jr c,.w
        ld a,4
        sla e
        jr c,.k
        push hl
        ld hl,ov_tt
        sla (hl)
        pop hl
        jr c,.c
        sla b
        jr nc,.t
        ld a,1
        sla c
        adc a,0                         ; paper 1, ink 2
        ret
.c:     sla b
.t:     sla c
        xor a
        ret
.w:     sla e
.k:     push hl
        ld hl,ov_tt
        sla (hl)
        pop hl
        sla b
        sla c
        ret

; ov_ptr: the pointer record (VP+38 from cur_p: 0 = another object, the record stays (the thrown rock 0x8078
; flies while the pointer is drawn); desc + 1 = the pointer's restore: none; desc = its draw: built from it).
; The game's draw (0xCE5A ..): shift s = (x - 1) AND 7, masks at (desc + 6 + 2 s), shapes at (desc + 22 + 2 s),
; 2 bytes a row from the bottom row (111 - y) up; screen = screen AND mask OR shape
ov_ptr: ld hl,(VP+38)
        ld a,h
        or l
        ret z
        xor a
        ld (ov_fr1),a
        bit 0,l
        ret nz
        ld a,(VP+36)
        cp 2
        ret nz                          ; (the game's four cursors are 2 bytes wide, 3-9 rows)
        ld a,(VP+37)
        and 127
        ret z
        cp 10
        ret nc
        ld (ov_r),a
        ld c,a
        ld a,(VP+35)
        ld b,a
        ld a,111
        sub b                           ; the bottom row in 8 bits (as ov_cur)
        ret m                           ; above the view
        ld (ov_fr1+2),a
        sub c
        inc a                           ; the top row (signed)
        ld (ov_fr1+1),a
        ld e,a
        ld d,0
        bit 7,a
        jr z,1F
        dec d
1:      ld hl,0
        or a
        sbc hl,de
        add hl,hl
        add hl,hl
        ld de,ov_fr1+6
        add hl,de
        ld (ov_fr1+4),hl                ; base = the data - 4 x top
        ld a,(ov_fr1+1)
        bit 7,a
        jr z,2F
        xor a
        ld (ov_fr1+1),a
2:      cp 112
        ret nc                          ; below the view
        ld a,(ov_fr1+2)
        cp 112
        jr c,3F
        ld a,111
        ld (ov_fr1+2),a
3:      ld a,(VP+34)
        dec a
        ld e,a
        srl e
        cp 192
        jr c,4F
        set 7,e
4:      sra e
        sra e
        ld hl,ov_fr1+3
        ld (hl),e                       ; the first byte column (signed, as ov_cur)
        and 7
        add a,a
        add a,6
        ld hl,(VP+38)
        add hl,a
        push hl
        call ov_gw                      ; DE = this shift's mask
        pop hl
        push de
        ld a,16
        add hl,a
        call ov_gw                      ; DE = its shape
        pop hl
        ld a,(ov_r)
        ld b,a
        dec a
        add a,a
        add a,a
        push hl
        ld hl,ov_fr1+6
        add hl,a
        push hl
        pop ix                          ; the record's bottom row
        pop hl
5:      push bc
        call ov_gb
        ld c,a
        ex de,hl
        call ov_gb
        ex de,hl
        ld (ix+0),a                     ; C = shape
        or c
        cpl
        ld (ix+1),a                     ; T = NOT (mask OR shape)
        inc hl
        inc de
        call ov_gb
        ld c,a
        ex de,hl
        call ov_gb
        ex de,hl
        ld (ix+2),a
        or c
        cpl
        ld (ix+3),a
        inc hl
        inc de
        ld bc,-4
        add ix,bc
        pop bc
        djnz 5B
        ld a,(l2shown)                  ; its brightness: rows as the record, 16 pixels from its first column
ov_ptrl:
        ld d,a
        ld a,(ov_fr1+3)
        bit 7,a
        jr z,6F
        xor a                           ; (column -1: from x 0)
6:      add a,a
        add a,a
        add a,a
        ld e,a
        ld a,(ov_fr1+1)
        ld b,a
        ld a,(ov_fr1+2)
        sub b
        inc a
        ld c,a
        ld a,d
        call ov_lum
        ld (ov_fr1),a
        ret
; ov_ptrc: the pointer drawn inside a show took its colour from the view then on screen: again from the bank
; just drawn (before ov_flip), as the sight's
ov_ptrc:
        ld a,(ov_fr1)
        or a
        ret z
        call ov_in
        ld a,(in_l2page)
        call ov_ptrl
        jp ov_out

; ov_sightc: the sight's colour from the bank just drawn (before ov_flip: in_l2page); ov_sightp: from bank A
ov_sightc:
        ld a,(in_l2page)
ov_sightp:
        ld c,a
        ld a,(ov_fr0)
        or a
        ret z
        push bc
        call ov_in
        pop bc
        ld a,c
        ld e,88
        ld bc,50*256+13
        call ov_lum
        ld (ov_fr0),a
        jp ov_out

; ov_lum: A = the Layer 2 bank's first page, B = first row, C = rows (1-60), E = first x (clamped to 176) -> A = 4
; (black) if the 16 x C pixels' brightness (ov_lumt) averages 34 or more, else 3 (white). After ov_in (slot 4
; used, back to page 10). BC, DE, HL lost
ov_lum: ld (ov_lpg),a
        ld a,e
        cp 177
        jr c,2F
        ld a,176
2:      ld (ov_lx),a
        ld a,c
        ld (ov_lc),a
        ld de,0                         ; the sum
.row:   push bc
        ld a,b
        add a,32                        ; the line
        ld c,a
        rlca
        rlca
        rlca
        and 7
        ld hl,ov_lpg
        add a,(hl)
        ld (cur54),a
        nextreg 0x54,a
        ld a,c
        and 31
        or 0x80
        ld h,a
        ld a,(ov_lx)
        add a,32
        ld l,a
        ld b,16
3:      ld a,(hl)
        inc l
        push hl
        ld hl,ov_lumt
        add hl,a
        ld a,(hl)
        pop hl
        add a,e
        ld e,a
        adc a,d
        sub e
        ld d,a
        djnz 3B
        pop bc
        inc b
        dec c
        jr nz,.row
        ld a,10
        ld (cur54),a
        nextreg 0x54,a
        push de
        ld a,(ov_lc)
        ld d,a
        ld e,34*16/8                    ; the threshold: 34 x 16 pixels x rows (/ 8: in 8 bits)
        mul d,e
        ex de,hl
        add hl,hl
        add hl,hl
        add hl,hl
        pop de
        ex de,hl
        or a
        sbc hl,de                       ; sum - threshold
        ld a,3
        ret c
        inc a
        ret

; ov_gw / ov_gb: the game's word (DE) / byte (A) at HL, after ov_in (0x4000-0x7FFF at +G; 0x8000-0xBFFF paged in
; for the read, cur54 written before each NEXTREG)
ov_gw:  call ov_gb
        ld e,a
        inc hl
        call ov_gb
        ld d,a
        dec hl
        ret
ov_gb:  ld a,h
        cp 0xC0
        jr nc,.d
        cp 0x80
        jr nc,.p
        push hl
        add a,high G
        ld h,a
        ld a,(hl)
        pop hl
        ret
.d:     ld a,(hl)
        ret
.p:     push hl
        rlca
        rlca
        rlca
        and 7                           ; 4 or 5: the game's page there
        ld (cur54),a
        nextreg 0x54,a
        ld a,h
        and 0x1F
        or 0x80
        ld h,a
        ld a,(hl)
        push af
        ld a,10
        ld (cur54),a
        nextreg 0x54,a
        pop af
        pop hl
        ret

; ov_mkrec: ov_fr0 when the view has the centre sight (rows 53-59, bytes 11-12: the plus; its colour: ov_sightc)
ov_mkrec:
        db 3,53,59,11
        dw ov_fr0+6-53*4
        db 0x01,0x00,0x00,0x00          ; row 53
        db 0x01,0x00,0x00,0x00
        db 0x01,0x00,0x00,0x00
        db 0x0E,0x00,0xE0,0x00          ; row 56
        db 0x01,0x00,0x00,0x00
        db 0x01,0x00,0x00,0x00
        db 0x01,0x00,0x00,0x00          ; row 59

; ov_ta / ov_tb: index = mask nibble x 16 + screen nibble (4 pixels each) -> two bytes of two 4-bit pixels:
; 0 = transparent (mask clear), 1 = paper (screen clear), 2 = ink
        ALIGN 256
ov_ta:
ov_i = 0
        DUP 256
        db ((ov_i >> 7) & 1) * (1 + ((ov_i >> 3) & 1)) * 16 + ((ov_i >> 6) & 1) * (1 + ((ov_i >> 2) & 1))
ov_i = ov_i + 1
        EDUP
ov_tb:
ov_i = 0
        DUP 256
        db ((ov_i >> 5) & 1) * (1 + ((ov_i >> 1) & 1)) * 16 + ((ov_i >> 4) & 1) * (1 + (ov_i & 1))
ov_i = ov_i + 1
        EDUP
glue_end:
        ASSERT glue_end <= SHARED

; ---- shared block: the same bytes in the alt ROM and in page PG_C1 (isr_e's target apart) ----------------------
        ORG SHARED
h_geom:                                 ; site 0x855E, CALL 0x8D4F
        call r_enter
        call m3_begin
        call r_leave
        jp 0x8D4F
h_rast:                                 ; sites 0x8599, 0xB635, CALL 0x9EA3
        call r_enter
        call m3_mid
        call r_leave
        jp 0x9EA3
h_show:                                 ; site 0x859C, CALL 0x9F19: its copy to the screen = the new view's time
        push af
        ld a,(0x7349)
        or a
        jr nz,h_off
        pop af
        call ov_capw                    ; ov_s: the buffer as the raster left it
        call 0x9F19
h_on:   call r_enter
        call m3_show
        call r_leave
        ret
h_off:  ld a,(0x7349)
        cp 1
        jr z,h_off1
        pop af                          ; 2+: the portcullis rises over this view (0x9F39 -> 0xCFC2; at BEGIN):
        call ov_capw                    ; hardware run 3: in colour from the start. ov_s = the view's buffer,
        call r_enter                    ; the view on Layer 2 at the original's time (m3_pshow), the sprites off
        call m3_pshow                   ; until its first step (h_w77p: the screen is the view under the bars
        call r_leave                    ; from then on)
        nextreg 0x69,0                  ; Layer 2 and the sprites wait for the first step: the show sets the area's
        nextreg 0x15,0                  ; colours first (0x9F24 CALL 0xB347: (27353) was the menu's at the raster)
        call 0x9F19
        push af
        xor a
        ld (m_pc),a
        pop af
        ret
h_off1: pop af                          ; (0x7349) = 1: this view goes to the screen by the dissolve 0xB66E (0x9F35;
        call ov_capw                    ; the drawbridge, a new area). The view into the hidden bank at the
        call r_enter                    ; original's time (m3_dshow); the dissolve then runs on Layer 2 as well
        call m3_dshow                   ; (m_pc = 2: h_diss, h_dpass), or, from a screen without Layer 2, in the
        call r_leave                    ; original's look with Layer 2 off (m_pc = 1, as the portcullis)
        push af
        ld a,(m_pc)
        cp 2
        jr z,1F
        nextreg 0x69,0
        nextreg 0x15,0
1:      pop af
        call 0x9F19
h_dshow:
        push af
        ld a,(m_pc)
        or a
        jr z,2F
        call r_enter
        call m3_dfin
        call r_leave
        nextreg 0x69,0x80
        nextreg 0x15,1
2:      pop af
        ret
h_dpass:                                ; site 0xB6E4 (POP AF / DEC A / JR NZ,0xB678): a pass of the dissolve is done
        ld a,(m_pc)
        cp 2
        jr nz,1F
        call r_enter
        call dis_pass
        call r_leave
1:      pop af
        dec a
        jp nz,0xB678
        jp 0xB6E8
h_flip:                                 ; site 0xB638, CALL 0xA38D
        call ov_capw
        call 0xA38D
        jp h_on

; h_snd_in / h_snd_out: the sound routine 0xC683 (interrupts off from 0xC68B to 0xC7F3) at 3.5 MHz, its time
; left out of the window. Sites 0xC68B (DI / DEC A / SLA A) and 0xC7F2 (POP AF / EI / POP BC; DE, HL follow).
h_snd_in:
        di
        push af
        call snd_q
        jr z,1F
        call ptick                      ; the window counted up to here
        xor a
        ld (m_spd),a
        nextreg 0x07,0
1:      pop af
        dec a
        sla a
        ret
h_snd_out:
        call snd_q
        jr z,1F
        ld a,3
        ld (m_spd),a
        nextreg 0x07,3
        call prest                      ; the window goes on from now: the sound's time is not in it
1:      pop hl
        pop af
        pop bc
        ei
        jp (hl)
snd_q:  ld a,(INISR)                    ; Z = inside the interrupt handler (its wrapper holds), or no window
        cpl
        and 0x80
        ret z
        ld a,(VP+10)
        or a
        ret

; h_prn / h_prn_out: the printer 0xCA4E keeps interrupts off for a whole string (0xCA56 .. 0xCBFE): one can be
; lost even at 28 MHz, and two readings a lost frame apart would hide it. So the clock ticks at its entry and its
; exit. Sites 0xCA4E (PUSH IX / PUSH IY -> JP h_prn) and 0xCBFF (POP AF / POP BC / POP DE -> JP h_prn_out:
; AF, BC, DE, HL are popped next, so they are free here).
h_prn_out:
        ld a,(INISR)
        rla
        jr c,1F
        ld a,(VP+10)
        or a
        call nz,ptick
1:      pop af
        pop bc
        pop de
        jp 0xCC02
h_prn:
        push af
        ld a,(INISR)
        rla
        jr c,1F
        ld a,(VP+10)
        or a
        jr z,1F
        push bc
        push de
        push hl
        call ptick
        pop hl
        pop de
        pop bc
1:      pop af
        push ix
        push iy
        jp 0xCA52

; h_w77 / h_w4a: the game's 14 waits on the interrupt handler (LD A,(nn) / OR A / JR cc,self: 0x7377 counts
; down, 0x734A is set) are real time, at any CPU speed: the window's clock stops for them.
h_w77:  call wait_in
1:      ld a,(0x7377)
        or a
        jr nz,1B
        jr wait_out
h_w4a:  call wait_in
1:      ld a,(0x734A)
        or a
        jr z,1B
wait_out:
        push af
        ld a,(VP+10)
        or a
        jr z,1F
        push bc
        push de
        push hl
        call prest                      ; the window goes on from now (m_wait cleared with the reading)
        pop hl
        pop de
        pop bc
1:      pop af
        ret
wait_in:
        push af
        ld a,(VP+10)
        or a
        jr z,1F
        push bc
        push de
        push hl
        call ptick
        pop hl
        pop de
        pop bc
        ld a,1
        ld (m_wait),a                   ; the interrupt wrapper leaves the clock alone during the wait
1:      pop af
        ret

; ptick: the window's lines brought up to now, from the main line
; popen: open the window; the opening reading and the window flag together (an interrupt between them
; would take no reading, and the next one a frame on would count one line)
popen:  HLIB_IFF_DI
        push af
        xor a
        ld (m_last),a
        ld (m_ni),a
        call hlib_pace_open
        pop af
        HLIB_IFF_EI
        ret
ptick:  ld a,1
        jr 1F
; prest: the window goes on from now (the time since the last reading is dropped); m_wait cleared
prest:  xor a
1:      ld (m_add),a
; the reading is committed with interrupts off; an interrupt during it (one that ticked, or one skipped in a
; wait) means the reading may be from before it: read again. AF, BC, DE, HL lost.
.r:     xor a
        ld (m_sk),a
        ld de,(VP)
        ld bc,(VP+18)
        call hlib_since_c               ; HL = lines since the last reading; +22 / +24 = this reading
        HLIB_IFF_DI
        push af
        ld a,(m_sk)
        or a
        jr nz,.again
        ld (m_last),a                   ; the last reading is the main line's
        ld (m_wait),a
        ld a,(m_add)
        or a
        jr z,2F
        ld de,(VP+2)
        add hl,de
        ld (VP+2),hl
2:      ld hl,(VP+22)
        ld (VP),hl
        ld hl,(VP+24)
        ld (VP+18),hl
        pop af
        HLIB_IFF_EI
        ret
.again: pop af
        HLIB_IFF_EI
        jr .r

; isr_pre / isr_post: around the game's handler, interrupts off, 28 MHz: the handler's time is left out of the
; window; the clock ticks once a frame even when the main line does not
isr_pre:
        xor a
        ld (m_hf),a
        ld a,(VP+10)
        or a
        ret z
        ld a,1
        ld (m_sk),a                     ; a main-line reading under way reads again
        ld a,(m_wait)
        or a
        ret nz
        call isr_tick
        ld a,1
        ld (m_last),a
        ld (m_hf),a
        ld hl,m_ni
        inc (hl)
        jp hlib_pace_hold
; isr_tick: hlib_pace_tick for readings a frame apart: after a reading at the last interrupt, a line difference
; under half a frame is a frame more (hlib_since takes it for under a frame)
isr_tick:
        call hlib_line
        push hl
        ld de,(VP)
        or a
        sbc hl,de
        jr nc,1F
        ld de,HLIB_PACE_NL
        add hl,de
1:      ld a,(m_last)
        or a
        jr z,2F
        ld de,HLIB_PACE_NL/2
        or a
        sbc hl,de
        add hl,de
        jr nc,2F
        ld de,HLIB_PACE_NL
        add hl,de
2:      ex de,hl
        ld hl,(VP+14)
        ld bc,(VP+18)
        ld (VP+18),hl
        or a
        sbc hl,bc                       ; held since the last reading
        ex de,hl
        or a
        sbc hl,de
        jr nc,3F
        ld hl,0
3:      ld de,(VP+2)
        add hl,de
        ld (VP+2),hl
        pop hl
        ld (VP),hl
        ret
isr_post:
        ld a,(m_hf)
        or a
        ret z
        jp hlib_pace_resume

; isr_p: an interrupt in the plain state (0xFDFD jumps to isr_e)
isr_p:
        push af
        push bc
        push de
        push hl
        nextreg 0x07,3
        call isr_pre
        nextreg 0x07,0
        call GAME_ISR                   ; returns with EI
        di
        nextreg 0x07,3
        call isr_post
        ld a,(m_spd)                    ; the interrupted code's speed (not the window's: an
        nextreg 0x07,a                  ; interrupt in r_enter comes before the window opens)
        pop hl
        pop de
        pop bc
        pop af
        ei
        ret

; r_enter: CALLed in the plain state. Every register onto the game's stack (11 words), then the renderer state
; at 28 MHz; returns to its caller there. The game's IFF is kept.
r_enter:
        ex (sp),hl                      ; HL = the return address
        push af
        push bc
        push de
        push ix
        push iy
        exx
        push bc
        push de
        push hl
        exx
        ex af,af'
        push af
        ex af,af'
        ld a,3
        ld (m_spd),a
        nextreg 0x07,3
        HLIB_IFF_DI
        nextreg 0x51,PG_C1
        nextreg 0x50,PG_C0
        nextreg 0x52,PG_W0
        nextreg 0x53,PG_W1
        ld (g_sp),sp
        ld sp,R_STACK
        HLIB_IFF_EI
        jp (hl)

; r_leave: CALLed in the renderer state; returns to its caller in the plain state with the game's registers,
; at 28 MHz while the window is open, else at 3.5 MHz
r_leave:
        pop hl
        HLIB_IFF_DI
        ld sp,(g_sp)
        nextreg 0x52,10
        nextreg 0x53,11
        nextreg 0x54,4
        nextreg 0x55,5
        nextreg 0x50,0xFF
        nextreg 0x51,0xFF
        HLIB_IFF_EI
        ld a,(VP+10)
        or a
        jr nz,1F
        ld (m_spd),a
        nextreg 0x07,0
1:      ex af,af'
        pop af
        ex af,af'
        exx
        pop hl
        pop de
        pop bc
        exx
        pop iy
        pop ix
        pop de
        pop bc
        pop af
        ex (sp),hl
        ret

        INCLUDE "hlib_pace.asm"

; h_cdraw / h_crest: the game's cursor drawn on the screen (0xCDD2) / its background put back (0xCECD); both keep
; every register. Sites: PUSH IX / PUSH IY, PUSH IX / PUSH HL -> JP. Then the overlay sprites over its rectangle.
h_cdraw:
        push de
        ld de,0
        call cur_p                      ; the pointer's draw: ov_ptr reads its masks and shapes
        pop de
        call cur_d
        call 1F
        jp cur_post
1:      push ix
        push iy
        jp 0xCDD6
h_crest:
        push de
        ld de,1
        call cur_p                      ; the pointer's restore: no pointer record
        pop de
        call cur_d
        call 1F
        jp cur_post
1:      push ix
        push hl
        jp 0xCED0
; h_diss: the dissolve copier 0xB66E (buffer -> screen in 4 passes; from 0x9F35 non-view, 0xBCE5 area change,
; 0xC93E, 0xCA44 transition; m3b_dissolve.py: 9 calls in the recording come with Layer 2 on): the original's look,
; Layer 2 and the sprites off until the next view. Site PUSH IX / PUSH IY / PUSH HL -> JP.
h_diss: push af
        ld a,(m_pc)
        cp 2
        jr z,1F
        nextreg 0x69,0
        nextreg 0x15,0
        jr 2F
1:      call r_enter                    ; the dissolve of a view over the last one on Layer 2: in colour
        call dis_pal
        call r_leave
2:      pop af
        push ix
        push iy
        push hl
        jp 0xB673
; h_portc: the portcullis 0xCFC2 (masked sprites straight onto the screen: dropped at a death from 0xA0A4, risen
; at BEGIN from 0x9F39; hardware run 2: under Layer 2 it showed as broken bars on black). At BEGIN (m_pc = 1) over
; the view in colour, its bars as overlay sprites (h_w77p); else as h_diss, the original's look until the next view.
; Site PUSH IX / PUSH IY -> JP (the carry picks the path: kept).
h_portc:
        push af
        ld a,(m_pc)
        cp 1
        jr z,1F
        nextreg 0x69,0
        nextreg 0x15,0
1:      pop af
        push ix
        push iy
        jp 0xCFC6
; h_w77p: the portcullis's waits (sites 0xCFE9 / 0xD00F, after each step 0xD028): over a view in colour, the
; palettes from the area's colours now, every overlay sprite rebuilt from the screen (ov_pstep), Layer 2 and the
; sprites on; then the wait as h_w77
h_w77p: push af
        ld a,(m_pc)
        cp 1
        jr nz,1F
        call r_enter
        call ov_pstep
        call r_leave
        nextreg 0x69,0x80
        nextreg 0x15,1
1:      pop af
        jp h_w77
cur_p:  push hl                         ; VP+38 = HL + DE if HL is the pointer's descriptor (0x7F20: loaded at
        push af                         ; 0xB402 / 0xB461 / 0xB645), else 0 (another object: ov_ptr keeps the record)
        ld a,h
        cp 0x7F
        jr nz,1F
        ld a,l
        cp 0x20
        jr nz,1F
        add hl,de
        jr 2F
1:      ld hl,0
2:      ld (VP+38),hl
        pop af
        pop hl
        ret
cur_d:  push hl                         ; the descriptor (HL: x, y, width, rows) -> VP+34 (read here: it may be
        push de                         ; anywhere in the game's RAM)
        push bc
        ld de,VP+34
        ld bc,4
        ldir
        pop bc
        pop de
        pop hl
        ret
cur_post:
        call r_enter
        call ov_cur
        call r_leave                    ; (CALLed: it takes its return address from the renderer's stack)
        ret                             ; to the cursor routine's caller
ov_capw:
        call r_enter
        call ov_cap
        call r_leave
        ret

isr_e:  jp isr_full                     ; (the alt ROM's copy: JP isr_p)
shared_end:
        ASSERT shared_end + 20 <= 0x3D00
        DISPLAY "shared block bytes: ",/D,shared_end-SHARED," glue end ",/H,glue_end
        SAVEBIN "cm12_page.bin",0x0000,0x4000
        ORG isr_e
        jp isr_p
        SAVEBIN "cm12_rom.bin",SHARED,shared_end-SHARED

; ---- start-up (the converter's stub calls it: 0xD000, 3.5 MHz, interrupts off, the game's RAM in slots 2-5) -----
        ORG 0xD000
setup:
        ld a,(scr_on)                   ; a loading screen (m2_build --screen): it is the image's own screen, so
        or a                            ; it shows as soon as bank 5 loads, whatever the loader; not held (cm12):
        jr z,2F                         ; the game's screen comes straight back from 0xE000
        ld hl,0xE000
        ld de,0x4000
        ld bc,6912
        ldir
2:      nextreg 0x12,PG_LA/2
        nextreg 0x70,0                  ; 256 x 192
        nextreg 0x16,0
        nextreg 0x17,0
        nextreg 0x71,0
        nextreg 0x14,0xE3
        nextreg 0x1C,1                  ; clip index of Layer 2 back to 0
        nextreg 0x18,32                 ; the view: x 32-223, y 32-143 (row 112 = line 144 stays hidden)
        nextreg 0x18,223
        nextreg 0x18,32
        nextreg 0x18,143
        ld a,PG_LA+1
        call set_clr4
        ld a,PG_LB+1
        call set_clr4
        ld a,PG_LC+1
        call set_clr4
        call setup_spr
        nextreg 0x54,4
        ret                             ; (the clock's bytes at VP: zero, K at m_k - in the image, m2_build.py)
; setup_spr: the M3b sprite grid (m3_sim runs this part alone)
setup_spr:
        nextreg 0x4B,0                  ; 4-bit index 0 transparent
        nextreg 0x15,0                  ; off until a view is on screen (SLU: sprites over Layer 2)
        nextreg 0x1C,2                  ; sprite clip index back to 0: the view
        nextreg 0x19,32
        nextreg 0x19,223
        nextreg 0x19,32
        nextreg 0x19,143
        xor a
        ld bc,0x303B
        out (c),a                       ; pattern slot 0 and sprite 0
        ld de,84*128
5:      xor a
        out (0x5B),a                    ; patterns 0-83 transparent
        dec de
        ld a,d
        or e
        jr nz,5B
        xor a
        ld bc,0x303B
        out (c),a
        ld d,0                          ; sprite k = 12 x band + column: pattern k at (64 + 16 column, 64 + 16 band)
        ld c,64
6:      ld b,64
        ld e,12
7:      ld a,b
        out (0x57),a
        ld a,c
        out (0x57),a
        xor a
        out (0x57),a
        ld a,d
        srl a
        or 0xC0                         ; visible, 5th byte
        out (0x57),a
        ld a,d
        rrca
        rrca
        and 0x40
        or 0x80                         ; 4-bit, N6 = k & 1
        out (0x57),a
        inc d
        ld a,b
        add a,16
        ld b,a
        dec e
        jr nz,7B
        ld a,c
        add a,16
        ld c,a
        cp 64+7*16
        jr c,6B
        ld b,44*4                       ; sprites 84-127: 4-byte records, invisible
8:      xor a
        out (0x57),a
        djnz 8B
        ret
set_clr4: ld b,4
1:      nextreg 0x54,a
        push af
        push bc
        ld hl,0x8000
        ld de,0x8001
        ld bc,0x1FFF
        ld (hl),l
        ldir
        pop bc
        pop af
        inc a
        djnz 1B
        ret
scr_on: db 0                            ; 1 = the stub bank's upper page holds the game's screen (m2_build)
setup_end:
        SAVEBIN "cm12_setup.bin",0xD000,setup_end-0xD000
