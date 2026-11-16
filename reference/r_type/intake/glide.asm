; R-Type sprite build (L2_GLIDE): figures glide between the game's steps, in play and on the title.
;
; The game moves every figure in whole 8x8 cells, once per update (3 frames in play, 4-9 on the
; title). Each figure plot is tagged with the object that drew it: the IY register (enemy slots
; 8501.., the ship, shots) plus its order among that object's plots this update. At publish, a
; figure that was also drawn last update and moved at most 4 cells (across, down or both) is shown
; 1/P of the way from its old place, P = the frames the last update took (2..8); the interrupt
; moves it on 1/P each frame (8.8 fixed point), arriving where the game put it as the next update
; is due. Game logic, collisions and timing are untouched; only sprite positions shown change.
;
; Lives in page GLIDE_PG (bank 13 high half) at 0x0100, mapped into slot 0 while it runs.
; Entry points: 0100 record (after a figure's sprites are emitted), 0103 publish (before the
; sprite list goes out), 0106 frame (from the interrupt).

        MMU 0,GLIDE_PG
        ORG 0x0100              ; not 0000: the tests break there to catch a reset
glide_start:
        jp g_record
        jp g_publish
        jp g_frame

MAXF    EQU 64                  ; figures per update
FENT    EQU 16                  ; 0-1 IY, 2 order (object), 3 first sprite, 4 sprites, 5 column, 6 row,
                                ; 7 order (object + graphic), 8-9 graphic, 10 colour override (8EB1)
MENT    EQU 13                  ; 0 sprite, 1-2 x, 3 y, 4 attr 2 without x bit 8, 5-6 x offset, 7-8 y offset,
                                ; 9-10 x step, 11-12 y step (8.8, signed)

; ---- after a figure's sprites are in spr_list (save_n .. spr_n-1) ----------------------------
g_record:
        ld a,(g_cur_n)
        cp MAXF
        ret nc
        push bc
        push de
        push hl
        push ix
        push iy
        pop de                  ; DE = IY of the object drawing
        ld bc,0                 ; C = order among its figures, B = among those of this graphic
        ld a,(g_cur_n)
        or a
        jr z,.add
        ld (g_tmp),a
        ld ix,g_cur
.s:     ld a,(ix+0)
        cp e
        jr nz,.n
        ld a,(ix+1)
        cp d
        jr nz,.n
        inc c
        ld a,(r_src)
        cp (ix+8)
        jr nz,.n
        ld a,(r_src+1)
        cp (ix+9)
        jr nz,.n
        inc b
.n:     push de
        ld de,FENT
        add ix,de
        pop de
        ld hl,g_tmp
        dec (hl)
        jr nz,.s
.add:   ld a,(g_cur_n)
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        push de
        ld de,g_cur
        add hl,de
        pop de
        push hl
        pop ix
        ld (ix+0),e
        ld (ix+1),d
        ld (ix+2),c
        ld (ix+7),b
        ld a,(save_n)
        ld (ix+3),a
        ld c,a
        ld a,(spr_n)
        sub c
        ld (ix+4),a
        ld a,(r_col)
        ld (ix+5),a
        ld a,(r_row)
        ld (ix+6),a
        ld a,(r_src)
        ld (ix+8),a
        ld a,(r_src+1)
        ld (ix+9),a
        ld a,(r_ink)
        ld (ix+10),a
        ld hl,g_cur_n
        inc (hl)
        pop ix
        pop hl
        pop de
        pop bc
        ret

; ---- before spr_list is published ------------------------------------------------------------
g_publish:
        push iy
        xor a
        ld (g_mov_n),a
        ld (g_k),a
        ld a,(hk_last)          ; P = frames the last update took (hook page, every interrupt)
        cp 2
        jp c,.done              ; one frame or none: nothing to spread
        cp 9
        jr c,.pk
        ld a,8
.pk:    ld (g_p),a
        dec a
        ld (g_kn),a
        ld a,(g_p)
        ld hl,g_recip
        add hl,a
        ld a,(hl)
        ld (g_r),a
        ld a,(g_cur_n)
        or a
        jp z,.done
        ld ix,g_cur
        ld b,a
.e:     push bc
        ld a,(ix+4)
        or a
        jp z,.nx                ; no sprites (drawn on the ULA)
        ld a,(g_prev_n)
        or a
        jp z,.nx
        ld b,a                  ; same object, same graphic, same order among those
        ld iy,g_prev
.f1:    ld a,(iy+0)
        cp (ix+0)
        jr nz,.n1
        ld a,(iy+1)
        cp (ix+1)
        jr nz,.n1
        ld a,(iy+8)
        cp (ix+8)
        jr nz,.n1
        ld a,(iy+9)
        cp (ix+9)
        jr nz,.n1
        ld a,(iy+7)
        cp (ix+7)
        jr z,.found
.n1:    ld de,FENT
        add iy,de
        djnz .f1
        ld a,(g_prev_n)         ; else (a new animation frame): same object, same order
        ld b,a
        ld iy,g_prev
.f2:    ld a,(iy+0)
        cp (ix+0)
        jr nz,.n2
        ld a,(iy+1)
        cp (ix+1)
        jr nz,.n2
        ld a,(iy+2)
        cp (ix+2)
        jr z,.found
.n2:    ld de,FENT
        add iy,de
        djnz .f2
        jp .nx
.found:                         ; IY = the same figure last update
        ld a,(ix+10)            ; a flashing figure (colour override) steps as the original:
        or (iy+10)              ; flash frames and effects sharing an object pair up wrongly
        jp nz,.nx
        ld a,(ix+5)
        sub (iy+5)
        ld hl,g_ax
        call axis
        jp c,.nx
        ld a,(ix+6)
        sub (iy+6)
        ld hl,g_ay
        call axis
        jp c,.nx
        ld hl,(g_ax+2)
        ld a,h
        or l
        ld hl,(g_ay+2)
        or h
        or l
        jp z,.nx                ; did not move
        ld a,(ix+3)             ; each of its sprites
        ld c,a
        ld b,(ix+4)
.sp:    push bc
        ld a,(g_mov_n)
        cp MAXSPR
        jp nc,.spx
        ld l,c                  ; HL = spr_list + 5 * sprite
        ld h,0
        ld e,l
        ld d,h
        add hl,hl
        add hl,hl
        add hl,de
        ld de,spr_list
        add hl,de
        push hl
        ld a,(g_mov_n)          ; IY = mov record
        ld e,a
        ld d,MENT
        mul d,e
        ld iy,g_mov
        add iy,de
        pop hl
        ld (iy+0),c
        ld a,(hl)               ; target x (9 bits), y, attr 2
        ld (iy+1),a
        inc hl
        ld a,(hl)
        ld (iy+3),a
        inc hl
        ld a,(hl)
        and 1
        ld (iy+2),a
        ld a,(hl)
        and 0xFE
        ld (iy+4),a
        dec hl
        dec hl
        ld de,(g_ax)            ; offsets and steps
        ld (iy+5),e
        ld (iy+6),d
        ld de,(g_ay)
        ld (iy+7),e
        ld (iy+8),d
        ld de,(g_ax+2)
        ld (iy+9),e
        ld (iy+10),d
        ld de,(g_ay+2)
        ld (iy+11),e
        ld (iy+12),d
        call g_pos              ; the position shown now -> spr_list
        ld (hl),e
        inc hl
        ld (hl),c
        inc hl
        ld a,(iy+4)
        or d
        ld (hl),a
        ld hl,g_mov_n
        inc (hl)
.spx:   pop bc
        inc c
        dec b
        jp nz,.sp
.nx:    ld de,FENT
        add ix,de
        pop bc
        dec b
        jp nz,.e
        ld a,(g_kn)
        ld (g_k),a
.done:  xor a
        ld (g_miss),a           ; steps skipped before this publish belong to the old moves
        ld hl,g_cur             ; this update becomes the previous one
        ld de,g_prev
        ld bc,MAXF*FENT
        ldir
        ld a,(g_cur_n)
        ld (g_prev_n),a
        xor a
        ld (g_cur_n),a
        pop iy
        ret

; IY = mov record -> E = x low, D = x bit 8, C = y: target + offset rounded to whole pixels.
g_pos:  push hl
        ld l,(iy+5)
        ld h,(iy+6)
        ld de,0x80
        add hl,de
        ld a,h                  ; whole pixels, signed
        ld e,a
        rlca
        sbc a,a
        ld d,a
        ld l,(iy+1)
        ld h,(iy+2)
        add hl,de
        push hl
        ld l,(iy+7)
        ld h,(iy+8)
        ld de,0x80
        add hl,de
        ld a,h
        add a,(iy+3)
        ld c,a
        pop de
        ld a,d
        and 1
        ld d,a
        pop hl
        ret

; A = signed move in cells, HL = 4 bytes: offset now, step per frame (both 8.8, signed).
; Shown now: 1/P of the way, so offset = -(distance - step). Carry if more than 4 cells.
axis:   push hl
        ld (hl),0
        inc hl
        ld (hl),0
        inc hl
        ld (hl),0
        inc hl
        ld (hl),0
        pop hl
        or a
        ret z
        ld c,0
        bit 7,a
        jr z,.p
        neg
        dec c                   ; C = FF: negative
.p:     cp 5
        ccf
        ret c
        add a,a
        add a,a
        add a,a                 ; pixels (8..32)
        ld b,a
        push hl
        ld d,a
        ld a,(g_r)
        ld e,a
        mul d,e                 ; DE = step = pixels * 256 / P
        ld h,b
        ld l,0
        or a
        sbc hl,de               ; HL = distance still to go
        bit 0,c
        jr nz,.neg
        push de                 ; positive move: offset = -HL, step = +DE
        ex de,hl
        ld hl,0
        or a
        sbc hl,de
        ex de,hl                ; DE = offset
        pop hl                  ; HL = step
        jr .st
.neg:   push hl                 ; negative move: offset = +HL, step = -DE
        ld hl,0
        or a
        sbc hl,de               ; HL = step
        pop de                  ; DE = offset
.st:    ex (sp),hl              ; HL = destination; step on the stack
        ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        pop de
        ld (hl),e
        inc hl
        ld (hl),d
        or a
        ret

; ---- each interrupt: count frames; move the gliding sprites on --------------------------------
g_frame:
        ld a,(g_fr)
        inc a
        jr z,.k
        ld (g_fr),a
.k:     ld a,(g_k)
        or a
        ret z
        dec a
        ld (g_k),a
        ld a,(g_mov_n)
        or a
        ret z
        ld (g_cnt),a
        push bc
        push de
        push hl
        push iy
        ld iy,g_mov
.m:     ld a,(g_k)
        or a
        jr nz,.adv
        ld (iy+5),a             ; last frame: exactly where the game put it
        ld (iy+6),a
        ld (iy+7),a
        ld (iy+8),a
        jr .out
.adv:   ld l,(iy+5)
        ld h,(iy+6)
        ld e,(iy+9)
        ld d,(iy+10)
        add hl,de
        ld (iy+5),l
        ld (iy+6),h
        ld l,(iy+7)
        ld h,(iy+8)
        ld e,(iy+11)
        ld d,(iy+12)
        add hl,de
        ld (iy+7),l
        ld (iy+8),h
.out:   call g_pos
        ld h,c                  ; y
        ld bc,0x303B
        ld a,(iy+0)
        out (c),a
        ld c,0x57
        out (c),e
        out (c),h
        ld a,(iy+4)
        or d
        out (c),a
        ld de,MENT
        add iy,de
        ld hl,g_cnt
        dec (hl)
        jr nz,.m
        pop iy
        pop hl
        pop de
        pop bc
        ret

g_recip:  db 0,0,128,85,64,51,43,37,32     ; 256 / P
g_fr:     db 0
g_tmp:    db 0
g_p:      db 0
g_kn:     db 0
g_r:      db 0
g_cnt:    db 0
g_k:      db 0
g_cur_n:  db 0
g_prev_n: db 0
g_mov_n:  db 0
g_ax:     ds 4
g_ay:     ds 4
g_cur:    ds MAXF*FENT
g_prev:   ds MAXF*FENT
g_mov:    ds MAXSPR*MENT
glide_end:
        ASSERT glide_end <= 0x2000
; (the SAVEBIN is in l2sprites.asm / l2sprites_full.asm: the build reads output names from the top file)
