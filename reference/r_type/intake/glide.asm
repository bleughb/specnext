; R-Type sprite build, trial (L2_GLIDE, level 1 only): figures glide between the game's steps.
;
; The game moves every figure in whole 8x8 cells, once per update (3 frames). Each figure plot is
; tagged with the object that drew it: the IY register (enemy slots 8501.., the ship, shots) plus
; its order among that object's plots this update. At publish, a figure that was also drawn last
; update and moved at most 3 cells starts two thirds of the way back; the interrupt then steps it
; on a third each frame, so it arrives where the game put it two frames later. Game logic,
; collisions and timing are untouched; only sprite positions shown between updates change.
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
FENT    EQU 8                   ; 0-1 IY, 2 order, 3 first sprite, 4 sprites, 5 column, 6 row
MENT    EQU 9                   ; 0 sprite, 1-2 x, 3 y, 4 attr 2 without x bit 8, 5-6 step 1, 7-8 step 2

; ---- after a figure's sprites are in spr_list (save_n .. spr_n-1) ----------------------------
g_record:
        ld a,(0x719C)
        cp '1'
        ret nz                  ; trial: level 1 only
        ld a,(g_cur_n)
        cp MAXF
        ret nc
        push bc
        push de
        push hl
        push ix
        push iy
        pop de                  ; DE = IY of the object drawing
        push de
        pop iy
        ld c,0                  ; order among this object's figures
        ld a,(g_cur_n)
        or a
        jr z,.add
        ld b,a
        ld hl,g_cur
.s:     ld a,(hl)
        cp e
        jr nz,.n
        inc hl
        ld a,(hl)
        dec hl
        cp d
        jr nz,.n
        inc c
.n:     ld a,FENT
        add hl,a
        djnz .s
.add:   ld a,(g_cur_n)
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        push de
        ld de,g_cur
        add hl,de
        pop de
        ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        ld (hl),c
        inc hl
        ld a,(save_n)
        ld (hl),a
        inc hl
        ld b,a
        ld a,(spr_n)
        sub b
        ld (hl),a
        inc hl
        ld a,(r_col)
        ld (hl),a
        inc hl
        ld a,(r_row)
        ld (hl),a
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
        ld b,a
        ld hl,g_prev
.f:     ld a,(hl)
        cp (ix+0)
        jr nz,.fn
        inc hl
        ld a,(hl)
        dec hl
        cp (ix+1)
        jr nz,.fn
        inc hl
        inc hl
        ld a,(hl)
        dec hl
        dec hl
        cp (ix+2)
        jr z,.found
.fn:    ld a,FENT
        add hl,a
        djnz .f
        jp .nx
.found: push hl
        pop iy                  ; IY = the same figure last update
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
        ld a,(g_ax+3)
        ld c,a
        ld a,(g_ay+3)
        or c
        jp z,.nx                ; did not move
        ld a,(ix+3)             ; each of its sprites: start part of the way back
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
        ld a,(g_mov_n)          ; DE = mov record
        ld e,a
        ld d,MENT
        mul d,e
        push hl
        ld hl,g_mov
        add hl,de
        ex de,hl
        pop hl
        ld a,c
        ld (de),a               ; sprite
        inc de
        ld a,(g_ax)             ; x = x + start offset (9 bits)
        ld c,a
        rlca
        sbc a,a
        ld b,a                  ; BC = offset, sign extended
        push hl
        ld a,(hl)
        inc hl
        inc hl
        ld h,(hl)
        ld l,a
        ld a,h
        and 1
        ld h,a
        add hl,bc
        ld a,l
        ld (de),a
        inc de
        ld a,h
        and 1
        ld (de),a
        inc de
        ld b,a
        ld a,l
        pop hl
        ld (hl),a               ; x low
        inc hl
        ld a,(g_ay)             ; y = y + start offset
        add a,(hl)
        ld (hl),a
        ld (de),a
        inc de
        inc hl
        ld a,(hl)
        and 0xFE
        ld (de),a               ; attr 2 without x bit 8
        or b
        ld (hl),a
        inc de
        ld hl,g_ax+1
        ldi
        ld hl,g_ay+1
        ldi
        ld hl,g_ax+2
        ldi
        ld hl,g_ay+2
        ldi
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
.done:  ld hl,g_cur             ; this update becomes the previous one
        ld de,g_prev
        ld bc,MAXF*FENT
        ldir
        ld a,(g_cur_n)
        ld (g_prev_n),a
        xor a
        ld (g_cur_n),a
        pop iy
        ret

; A = signed move in cells, HL = 4 bytes: start offset, step 1, step 2, moved (0/1).
; Carry if more than 3 cells (a jump, not a move).
axis:   ld (hl),0
        inc hl
        ld (hl),0
        inc hl
        ld (hl),0
        inc hl
        ld (hl),0
        dec hl
        dec hl
        dec hl
        or a
        ret z
        ld c,0
        bit 7,a
        jr z,.p
        neg
        dec c                   ; C = FF: negative
.p:     cp 4
        ccf
        ret c
        push hl
        ld hl,g_two
        add hl,a
        ld d,(hl)               ; two thirds of the move (pixels)
        ld hl,g_one
        add hl,a
        ld e,(hl)               ; one third
        pop hl
        ld a,d                  ; start: two thirds back
        neg
        call .sg
        ld (hl),a
        inc hl
        ld a,d                  ; step 1: two thirds - one third
        sub e
        call .sg
        ld (hl),a
        inc hl
        ld a,e                  ; step 2: one third
        call .sg
        ld (hl),a
        inc hl
        ld (hl),1
        or a
        ret
.sg:    bit 0,c                 ; negate if the move was negative
        ret z
        neg
        ret
g_two:  db 0,5,11,16
g_one:  db 0,3,5,8

; ---- each interrupt: step the gliding sprites ------------------------------------------------
g_frame:
        ld a,(g_k)
        cp 2
        ret nc
        inc a
        ld (g_k),a
        ld a,(g_mov_n)
        or a
        ret z
        push bc
        push de
        push hl
        push ix
        ld e,a
        ld ix,g_mov
.m:     ld a,(g_k)
        cp 1
        ld a,(ix+5)
        ld d,(ix+6)
        jr z,.k1
        ld a,(ix+7)
        ld d,(ix+8)
.k1:    ld c,a                  ; x += step (9 bits)
        rlca
        sbc a,a
        ld b,a
        ld l,(ix+1)
        ld h,(ix+2)
        add hl,bc
        ld a,h
        and 1
        ld h,a
        ld (ix+1),l
        ld (ix+2),h
        ld a,(ix+3)
        add a,d
        ld (ix+3),a
        ld bc,0x303B
        ld a,(ix+0)
        out (c),a
        ld c,0x57
        out (c),l
        ld a,(ix+3)
        out (c),a
        ld a,(ix+4)
        or h
        out (c),a
        ld bc,MENT
        add ix,bc
        dec e
        jr nz,.m
        pop ix
        pop hl
        pop de
        pop bc
        ret

g_k:      db 2
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
