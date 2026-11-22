; Castle Master M1: the Next-native renderer (Z80N), geometry part. Spec = the M0 port (m0_geom.py, m0_cube.py,
; m0_objects.py, m0_sort.py, m0_pipeline.py), itself equal to the game at all 5,233 recorded redraws.
; Assemble: sjasmplus --nologo --zxnext --sym=cmr.sym cmr.asm   (writes cmr.bin = 0x0000.. code + constants)
;
; Memory while the renderer runs (Next plan; the host harness m1_lib.py uses the same addresses):
;   0x0000-0x3FFF  this code + constant tables (read-only here; slots 0-1 on the Next)
;   0x4000-0x7FFF  work RAM: inputs, tables copied from the game at init, per-view and per-object data, output
;   0xC000-0xFFFF  world snapshot = the game's 0xC000-0xFFFF (object lists at their own addresses)
; Conventions: 16-bit values little-endian; "negative" = bit 15 of the wrapped result, as the original.
        DEVICE NOSLOT64K
        ORG 0x0000

        jp render_geom                  ; 0x0000: the whole geometry pipeline (inputs -> sorted list)

; ==== maths ====================================================================================================

; smul8x8: A (s8) * E (s8) -> HL (s16). Keeps BC. Unsigned MUL then the two sign corrections.
smul8x8:
        ld d,a
        ld l,e
        ld h,a
        mul d,e
        ld a,d
        bit 7,h
        jr z,1F
        sub l
1:      bit 7,l
        jr z,2F
        sub h
2:      ld h,a
        ld l,e
        ret

; smul8u8: A (s8) * E (u8) -> HL (s16). Keeps BC.
smul8u8:
        ld h,a
        ld l,e
        ld d,a
        mul d,e
        bit 7,h
        jr z,1F
        ld a,d
        sub l
        ld d,a
1:      ex de,hl
        ret

; umul16: HL * DE -> DEHL (unsigned 32). Destroys A, BC.
umul16:
        ld a,e                  ; yl
        ld c,d                  ; yh
        ld b,l                  ; xl (H = xh)
        ld d,b
        mul d,e                 ; xl*yl
        push de
        ld d,h
        ld e,a
        mul d,e                 ; xh*yl
        ld a,h
        ld h,d
        ld l,e
        ld d,b
        ld e,c
        mul d,e                 ; xl*yh
        add hl,de               ; cross (17 bits: carry)
        ld b,0
        rl b
        ld d,a
        ld e,c
        mul d,e                 ; xh*yh
        ld c,h
        ld a,l
        ex (sp),hl              ; HL = xl*yl
        add a,h
        ld h,a
        ld a,e
        adc a,c
        ld e,a
        ld a,d
        adc a,b
        ld d,a
        pop bc
        ret

; smul16: HL (s16) * DE (s16) -> DEHL (s32). Destroys A, BC.
smul16:
        ld (sm_x),hl
        ld (sm_y),de
        call umul16
        ex de,hl
        ld a,(sm_x+1)
        bit 7,a
        jr z,1F
        ld bc,(sm_y)
        or a
        sbc hl,bc
1:      ld a,(sm_y+1)
        bit 7,a
        jr z,2F
        ld bc,(sm_x)
        or a
        sbc hl,bc
2:      ex de,hl
        ret

; div32: DEHL (s32) / BC (s16) -> HL (s16) as 45740: magnitudes, quotient + 1 when remainder >= |divisor| / 2
; (floor), sign applied, low 16 bits; 0 when the dividend is 0. Destroys all but IY.
div32:
        ld a,d
        or e
        or h
        or l
        ret z                   ; HL = 0
        ld a,b
        or c
        jp z,div32_old          ; a zero divisor: as before
        ld a,d
        xor b
        ld (dv_sign),a          ; bit 7 = result negative
        bit 7,d
        jr z,1F
        xor a                   ; DEHL = -DEHL
        sub l
        ld l,a
        ld a,0
        sbc a,h
        ld h,a
        ld a,0
        sbc a,e
        ld e,a
        ld a,0
        sbc a,d
        ld d,a
1:      bit 7,b
        jr nz,2F
        xor a                   ; BC = -|divisor|
        sub c
        ld c,a
        sbc a,a
        sub b
        ld b,a
2:      push hl                 ; the low word
        ld hl,0                 ; remainder (< |divisor| <= 0x8000)
        ld a,d
        or a
        jr z,3F
        call dv8                ; a zero top byte leaves the remainder 0: skipped
        ld a,e
        call dv8
        jr 4F
3:      ld a,e
        or a
        call nz,dv8
4:      pop de
        ld a,d
        call dv8
        ld d,a
        ld a,e
        call dv8
        ld e,a                  ; DE = quotient (low 16 bits), HL = remainder
        xor a
        sub c
        ld c,a
        sbc a,a
        sub b
        ld b,a                  ; |divisor|
        srl b
        rr c
        or a
        sbc hl,bc               ; remainder - |d| / 2
        ex de,hl
        jr c,5F
        inc hl
5:      ld a,(dv_sign)
        rla
        ret nc
        xor a
        sub l
        ld l,a
        sbc a,a
        sub h
        ld h,a
        ret
; dv8: 8 bits of A into the remainder HL against BC = -|divisor| -> A = the 8 quotient bits
dv8:
        DUP 8
        add a,a
        adc hl,hl
        add hl,bc
        jr c,1F
        sbc hl,bc
        dec a
1:      inc a
        EDUP
        ret
div32_old:
        ld a,d
        xor b
        ld (dv_sign),a          ; bit 7 = result negative
        bit 7,d
        jr z,1F
        xor a                   ; DEHL = -DEHL
        sub l
        ld l,a
        ld a,0
        sbc a,h
        ld h,a
        ld a,0
        sbc a,e
        ld e,a
        ld a,0
        sbc a,d
        ld d,a
1:      bit 7,b
        jr z,2F
        xor a                   ; BC = -BC
        sub c
        ld c,a
        ld a,0
        sbc a,b
        ld b,a
2:      push hl
        pop ix                  ; dividend / quotient = DE:IX
        ld hl,0                 ; remainder
        ld a,32
.lp:    add ix,ix
        rl e
        rl d
        adc hl,hl
        or a
        sbc hl,bc
        jr nc,.one
        add hl,bc
        dec a
        jr nz,.lp
        jr .done
.one:   inc ix
        dec a
        jr nz,.lp
.done:  ex de,hl                ; DE = remainder
        ld h,b
        ld l,c
        srl h
        rr l                    ; HL = |d| / 2
        ex de,hl
        or a
        sbc hl,de               ; remainder - |d|/2
        push ix
        pop hl
        jr c,3F
        inc hl
3:      ld a,(dv_sign)
        bit 7,a
        ret z
        xor a
        sub l
        ld l,a
        sbc a,a
        sub h
        ld h,a
        ret

; ==== view matrix (0x9776) =====================================================================================

; mat3: (DE) = (IX) x (IY), 3x3 signed bytes; each element = round((4 * sum) / 256) as 41342 (16-bit sum).
mat3:
        ld (m3out),de
        ld c,3
.row:   ld b,3
        push iy
.col:   push bc
        ld a,(ix+0)
        ld e,(iy+0)
        call smul8x8
        push hl
        ld a,(ix+1)
        ld e,(iy+3)
        call smul8x8
        push hl
        ld a,(ix+2)
        ld e,(iy+6)
        call smul8x8
        pop de
        add hl,de
        pop de
        add hl,de
        add hl,hl
        add hl,hl
        ld a,h
        bit 7,l
        jr z,1F
        inc a
1:      ld hl,(m3out)
        ld (hl),a
        inc hl
        ld (m3out),hl
        inc iy
        pop bc
        djnz .col
        pop iy
        ld de,3
        add ix,de
        dec c
        jr nz,.row
        ret

matrix:
        IFDEF M3
        ld a,(tw_on)                    ; an in-between view: fine angles (cm3_glue.asm)
        or a
        jp nz,tw_matrix
        ENDIF
        ld hl,ident64
        ld de,ymat
        ld bc,9
        ldir
        ld a,(in_yaw)
        or a
        jr z,.noyaw
        call sincos_a           ; A = sin, B = cos
        ld (ymat+6),a
        neg
        ld (ymat+2),a
        ld a,b
        ld (ymat+0),a
        ld (ymat+8),a
.noyaw: ld a,(in_pitch)
        or a
        jr z,.nopit
        call sincos_a
        push af
        push bc
        ld hl,ident64
        ld de,pmat
        ld bc,9
        ldir
        pop bc
        pop af
        ld (pmat+5),a
        neg
        ld (pmat+7),a
        ld a,b
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
.nopit:
matrix_tail:
        ld ix,diagm
        ld iy,ymat
        ld de,mat
        jp mat3

sincos_a:                               ; A = angle -> A = sin, B = cos (table copied from 29337)
        ld l,a
        ld h,0
        add hl,hl
        ld de,sincos
        add hl,de
        ld a,(hl)
        inc hl
        ld b,(hl)
        ret

ident64: db 64,0,0, 0,64,0, 0,0,64
diagm:   db 40,0,0, 0,64,0, 0,0,32

; ==== sector limits (0x8D4F) and the per-object test (0x85C9) ==================================================

sector:
        ld hl,bounds
        ld b,6
        ld a,255
1:      ld (hl),a
        inc hl
        djnz 1B
        ld c,4                          ; h = 4, 3, 2, 1
.h:     ld a,(in_yaw)
        ld b,a
        ld a,c
        cp 3
        ld a,b
        jr c,.yp
        sub 8                           ; (yaw - 8) mod 72
        jr nc,.yd
        add a,72
        jr .yd
.yp:    add a,8                         ; (yaw + 8) mod 72
        cp 72
        jr c,.yd
        sub 72
.yd:    ld d,1
        cp 18
        jr c,.dd
        ld d,3
        cp 36
        jr c,.dd
        ld d,5
        cp 54
        jr c,.dd
        ld d,7
.dd:    ld a,(in_pitch)
        bit 0,c
        jr z,.pm
        add a,8
        cp 72
        jr c,.pd
        sub 72
        jr .pd
.pm:    sub 8
        jr nc,.pd
        add a,72
.pd:    cp 18
        jr nc,.p2
        inc d
        jr .ps
.p2:    cp 36
        jr nc,.p3
        ld a,d
        add a,5
        cp 9
        jr c,.p2s
        sub 8
.p2s:   ld d,a
        jr .ps
.p3:    cp 54
        jr nc,.ps
        ld a,d
        add a,4
        cp 9
        jr c,.p3s
        sub 8
.p3s:   ld d,a
.ps:    ld hl,secm-1
        ld a,d
        add hl,a
        ld e,(hl)
        ld hl,bounds
        ld ix,secv
        ld b,6
.si:    srl e
        jr nc,.sn
        ld a,(ix+0)
        ld (hl),a
.sn:    inc hl
        inc ix
        djnz .si
        dec c
        jp nz,.h
        ld ix,in_cam
        ld hl,bounds
        ld b,3
.ck:    ld e,(ix+0)
        ld d,(ix+1)
        ex de,hl
        add hl,hl
        add hl,hl
        ld c,h                          ; bits 6..13 of the camera coordinate
        ex de,hl
        ld a,(hl)
        cp 255
        jr nz,.ck2
        ld a,c
        inc a
        ld (hl),a
        jr .ck3
.ck2:   inc hl
        ld a,(hl)
        dec hl
        cp 255
        jr nz,.ck3
        inc hl
        ld (hl),c
        dec hl
.ck3:   inc hl
        inc hl
        inc ix
        inc ix
        djnz .ck
        ret

secm:   db 0x15,0x19,0x25,0x29,0x26,0x2A,0x16,0x1A      ; d = 1..8: which limits take secv
secv:   db 127,0,63,0,127,0

; secull: IX = object record -> carry set = outside the sector limits (skip)
secull:
        ld hl,bounds
        ld b,3
        push ix
.k:     ld a,(ix+1)
        ld c,a
        sub (hl)
        jr z,.k1
        jp p,.cull
.k1:    inc hl
        ld a,c
        add a,(ix+4)
        sub (hl)
        jp m,.cull
        inc hl
        inc ix
        djnz .k
        pop ix
        or a
        ret
.cull:  pop ix
        scf
        ret

; ==== bounding box (0x85C9 34313-34399) ========================================================================

        MACRO BBOXAX k
        ld d,(ix+1+k)
        ld e,64
        mul d,e
        ld hl,(in_cam+2*k)
        ex de,hl
        or a
        sbc hl,de
        ld (box+4*k),hl
        ld a,h
        or l
        jr z,1F
        bit 7,h
        jr nz,1F
        set 2*k,c
1:      ld d,(ix+4+k)
        ld e,64
        mul d,e
        add hl,de
        ld (box+4*k+2),hl
        bit 7,h
        jr z,2F
        set 2*k+1,c
2:
        ENDM

; bbox: IX = record -> box (min, max per axis, camera-relative words), side (bit 2k: min > 0, 2k+1: max < 0)
bbox:
        ld c,0
        BBOXAX 0
        BBOXAX 1
        BBOXAX 2
        ld a,c
        ld (side),a
        ret

; ==== transform (0x930F): V = bits 6..21 of the 24-bit sum M[r][c] * P[c] ======================================

        MACRO PROD ofs
        ld e,(iy+ofs)
        ld d,c
        mul d,e
        add hl,de
        jr nc,1F
        inc b
1:      ld e,(iy+ofs+1)
        ld d,c
        mul d,e
        ld a,h
        add a,e
        ld h,a
        ld a,b
        adc a,d
        ld b,a
        bit 7,c
        jr z,2F
        ld a,h
        sub (iy+ofs)
        ld h,a
        ld a,b
        sbc a,(iy+ofs+1)
        ld b,a
2:      bit 7,(iy+ofs+1)
        jr z,3F
        ld a,b
        sub c
        ld b,a
3:
        ENDM

        MACRO XROW r
        ld hl,0
        ld b,l
        ld a,(mat+3*r)
        or a
        jr z,4F
        ld c,a
        PROD 0
4:      ld a,(mat+3*r+1)
        or a
        jr z,5F
        ld c,a
        PROD 2
5:      ld a,(mat+3*r+2)
        or a
        jr z,6F
        ld c,a
        PROD 4
6:      add hl,hl
        rl b
        add hl,hl
        rl b
        ld (ix+2*r),h
        ld (ix+2*r+1),b
        ENDM

; xform: IY -> point (x, y, z words), IX -> vertex out (x, y, z words)
xform:
        XROW 0
        XROW 1
        XROW 2
        ret

; ==== outcode (0x93DE) and projection (0x9294) =================================================================

; outc: IX -> vertex -> A = code (31 = inside)
outc:
        ld e,(ix+4)
        ld d,(ix+5)
        ld c,31
        ld l,(ix+0)
        ld h,(ix+1)
        add hl,de
        bit 7,h
        jr z,1F
        res 4,c
1:      ld l,(ix+2)
        ld h,(ix+3)
        add hl,de
        bit 7,h
        jr z,2F
        res 3,c
2:      ld l,(ix+2)
        ld h,(ix+3)
        or a
        sbc hl,de
        bit 7,h
        jr nz,3F
        res 1,c
3:      ld l,(ix+0)
        ld h,(ix+1)
        or a
        sbc hl,de
        bit 7,h
        jr nz,4F
        res 2,c
4:      bit 7,d
        jr z,5F
        res 0,c
5:      ld a,c
        ret

; proj: IX -> vertex -> B = x (0..192), C = y (0..112, y up)
proj:
        ld e,(ix+4)
        ld d,(ix+5)
        ld a,d
        or e
        jr nz,1F
        ld bc,96*256+56
        ret
1:      ld l,(ix+0)
        ld h,(ix+1)
        ld a,96
        call proj1
        push af
        ld l,(ix+2)
        ld h,(ix+3)
        ld a,56
        call proj1
        ld c,a
        pop af
        ld b,a
        ret

; proj1: HL = p, DE = z (kept), A = half -> A = half + 96p/z (truncating), clamped to 0 / 2 * half
proj1:
        ld c,a
        bit 7,h
        jr z,.pos
        push hl
        add hl,de
        dec hl
        bit 7,h
        pop hl
        jr z,.div
        xor a
        ret
.pos:   push hl
        or a
        sbc hl,de
        bit 7,h
        pop hl
        jr nz,.div
        ld a,c
        add a,a
        ret
.div:   ld b,h                          ; sign of p
        bit 7,h
        jr z,1F
        xor a
        sub l
        ld l,a
        sbc a,a
        sub h
        ld h,a
1:      push bc
        push de
        ld d,c
        ld e,l
        mul d,e                         ; half * lo
        ld a,d
        ld l,e
        ld d,c
        ld e,h
        mul d,e                         ; half * hi
        add a,e
        ld h,a
        ld a,d
        adc a,0                         ; N = A:H:L (< 2^22)
        sla l
        rl h
        rla
        ld b,l                          ; the 7 low bits of N, top first
        ld l,h
        ld h,a                          ; HL = N >> 7 (< z: the quotient is below 128)
        pop de
        push de
        xor a
        sub e
        ld e,a
        sbc a,a
        sub d
        ld d,a                          ; DE = -z: ADD sets the carry when the remainder >= z
        ld a,b
        REPT 7
        add a,a
        adc hl,hl
        add hl,de
        jr c,1F
        sbc hl,de
        dec a
1:      inc a
        ENDR
        pop de
        pop bc
        bit 7,b
        jr nz,2F
        add a,c
        ret
2:      neg
        add a,c
        ret

; ==== edges, corners, facing and winding tests (0x8746, 0x91C2, 0x8A69, 0x9300) ================================

; estart / eend: A = edge ref (bit 7 = walked backwards) -> A = its start / end vertex in the current template
estart:
        ld c,a
        and 127
        add a,a
        inc a
        ld hl,(ctmpl)
        add hl,a
        bit 7,c
        jr z,1F
        inc hl
1:      ld a,(hl)
        ret
eend:
        ld c,a
        and 127
        add a,a
        inc a
        ld hl,(ctmpl)
        add hl,a
        bit 7,c
        jr nz,1F
        inc hl
1:      ld a,(hl)
        ret

vptr:                                   ; A = vertex index -> IX = vtx + 6A
        ld e,a
        ld d,6
        mul d,e
        ld ix,vtx
        add ix,de
        ret

codeof:                                 ; A = vertex index -> A = its outcode (keeps HL)
        push hl
        ld hl,codes
        add hl,a
        ld a,(hl)
        pop hl
        ret

; cdiv: HL = difference, DE = t, BC = divisor -> HL = div32(HL * DE, BC)
cdiv:
        ld (cl_dv),bc
        call smul16
        ld bc,(cl_dv)
        jp div32

        MACRO SUBHL pa, pb              ; HL = pa - pb (words)
        ld hl,(pa)
        ld de,(pb)
        or a
        sbc hl,de
        ENDM

        MACRO SUBW dst, pa, pb          ; dst = HL = pa - pb
        SUBHL pa, pb
        ld (dst),hl
        ENDM

        MACRO PUTPT bn                 ; IX = the end that was outside plane `bit` (cc0 tested)
        ld a,(cc0)
        bit bn,a
        ld ix,clp
        jr z,1F
        ld ix,clp+6
1:
        ENDM

        MACRO STW ofs, src              ; (ix+ofs) = word at src
        ld hl,(src)
        ld (ix+ofs),l
        ld (ix+ofs+1),h
        ENDM

        MACRO STNEG ofs, src            ; (ix+ofs) = -(word at src)
        ld hl,(src)
        xor a
        sub l
        ld (ix+ofs),a
        sbc a,a
        sub h
        ld (ix+ofs+1),a
        ENDM

        MACRO RECODE bn, ea, eb, op    ; set `bit` in both codes, clear it where (ea op eb) < 0
        ld hl,cc0
        set bn,(hl)
        ld hl,cc1
        set bn,(hl)
        ld hl,(clp+ea)
        ld de,(clp+eb)
        IF op == 0
        or a
        sbc hl,de
        ELSE
        add hl,de
        ENDIF
        bit 7,h
        jr z,1F
        ld hl,cc0
        res bn,(hl)
1:      ld hl,(clp+6+ea)
        ld de,(clp+6+eb)
        IF op == 0
        or a
        sbc hl,de
        ELSE
        add hl,de
        ENDIF
        bit 7,h
        jr z,2F
        ld hl,cc1
        res bn,(hl)
2:
        ENDM

        MACRO PLANETEST bn, skip       ; reject if both outside; to `skip` if both inside
        ld a,(cc0)
        ld b,a
        ld a,(cc1)
        ld c,a
        or b
        bit bn,a
        jp z,clrej
        ld a,b
        and c
        bit bn,a
        jp nz,skip
        ENDM

        MACRO QUOT num, nbase, res      ; res = div32((num1 - num0) * cl_t, cl_d) + nbase0
        SUBHL clp+6+num, clp+num
        ld de,(cl_t)
        ld bc,(cl_d)
        call cdiv
        ld de,(clp+nbase)
        add hl,de
        ld (res),hl
        ENDM

; clipedge (0x8746): P = clp+0 (x0, y0, z0), Q = clp+6, codes cc0 / cc1 -> carry set = rejected
clipedge:
        PLANETEST 0, cl_s1
        SUBW cl_d, clp+4, clp+10                ; d = z0 - z1
        ld hl,(clp+4)
        ld (cl_t),hl                            ; t = z0
        QUOT 0, 0, cl_n1                        ; nx
        QUOT 2, 2, cl_n2                        ; ny
        PUTPT 0
        STW 0, cl_n1
        STW 2, cl_n2
        ld (ix+4),0
        ld (ix+5),0
        RECODE 1, 4, 2, 0                       ; z - y < 0 -> clear bit 1
cl_s1:  PLANETEST 1, cl_s1d
        SUBW cl_d, clp+8, clp+2                 ; d = (y1 - y0) - z1 + z0
        ld de,(clp+10)
        or a
        sbc hl,de
        ld de,(clp+4)
        add hl,de
        ld (cl_d),hl
        SUBW cl_t, clp+4, clp+2                 ; t = z0 - y0
        QUOT 4, 4, cl_n1                        ; nz
        QUOT 0, 0, cl_n2                        ; nx
        PUTPT 1
        STW 0, cl_n2
        STW 2, cl_n1
        STW 4, cl_n1
cl_s1d: RECODE 2, 4, 0, 0                       ; z - x < 0 -> clear bit 2
        PLANETEST 2, cl_s2d
        SUBW cl_d, clp+6, clp+0                 ; d = (x1 - x0) - z1 + z0
        ld de,(clp+10)
        or a
        sbc hl,de
        ld de,(clp+4)
        add hl,de
        ld (cl_d),hl
        SUBW cl_t, clp+4, clp+0                 ; t = z0 - x0
        QUOT 4, 4, cl_n1                        ; nz
        QUOT 2, 2, cl_n2                        ; ny
        PUTPT 2
        STW 0, cl_n1
        STW 2, cl_n2
        STW 4, cl_n1
cl_s2d: RECODE 3, 4, 2, 1                       ; z + y < 0 -> clear bit 3
        PLANETEST 3, cl_s3d
        SUBW cl_d, clp+2, clp+8                 ; d = (y0 - y1) - z1 + z0
        ld de,(clp+10)
        or a
        sbc hl,de
        ld de,(clp+4)
        add hl,de
        ld (cl_d),hl
        ld hl,(clp+4)                           ; t = z0 + y0
        ld de,(clp+2)
        add hl,de
        ld (cl_t),hl
        QUOT 4, 4, cl_n1                        ; nz
        QUOT 0, 0, cl_n2                        ; nx
        PUTPT 3
        STW 0, cl_n2
        STNEG 2, cl_n1
        STW 4, cl_n1
cl_s3d: RECODE 4, 4, 0, 1                       ; z + x < 0 -> clear bit 4
        PLANETEST 4, cl_sdone
        SUBW cl_d, clp+0, clp+6                 ; d = (x0 - x1) - z1 + z0
        ld de,(clp+10)
        or a
        sbc hl,de
        ld de,(clp+4)
        add hl,de
        ld (cl_d),hl
        ld hl,(clp+4)                           ; t = z0 + x0
        ld de,(clp+0)
        add hl,de
        ld (cl_t),hl
        QUOT 4, 4, cl_n1                        ; nz
        QUOT 2, 2, cl_n2                        ; ny
        PUTPT 4
        STNEG 0, cl_n1
        STW 2, cl_n2
        STW 4, cl_n1
cl_sdone:
        or a
        ret
clrej:  scf
        ret

; edge: A = edge index -> carry set, B,C = p0 (x, y), D,E = p1; carry clear = nothing (cached per face)
edge:
        ld (eg_e),a
        ld hl,estate
        add hl,a
        ld a,(hl)
        or a
        jr z,.comp
        cp 1
        jr z,.none
        ld a,(eg_e)
        add a,a
        add a,a
        ld hl,epts
        add hl,a
        ld b,(hl)
        inc hl
        ld c,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld e,(hl)
        scf
        ret
.none:  or a
        ret
.comp:  push hl
        ld a,(eg_e)
        add a,a
        inc a
        ld hl,(ctmpl)
        add hl,a
        ld a,(hl)
        ld (eg_a),a
        inc hl
        ld a,(hl)
        ld (eg_b),a
        ld a,(eg_a)
        call codeof
        ld (cc0),a
        ld c,a
        ld a,(eg_b)
        call codeof
        ld (cc1),a
        ld b,a
        and c
        cp 31
        jr z,.both
        ld a,b
        or c
        cp 31
        jr nz,.nil
        ld a,(eg_a)
        call vptr
        push ix
        pop hl
        ld de,clp
        ld bc,6
        ldir
        ld a,(eg_b)
        call vptr
        push ix
        pop hl
        ld de,clp+6
        ld bc,6
        ldir
        call clipedge
        jr c,.nil
        ld ix,clp
        call proj
        push bc
        ld ix,clp+6
        call proj
        ld d,b
        ld e,c
        pop bc
        jr .store
.both:  ld a,(eg_a)
        call vptr
        call proj
        push bc
        ld a,(eg_b)
        call vptr
        call proj
        ld d,b
        ld e,c
        pop bc
.store: pop hl
        ld (hl),2
        ld a,(eg_e)
        add a,a
        add a,a
        ld hl,epts
        add hl,a
        ld (hl),b
        inc hl
        ld (hl),c
        inc hl
        ld (hl),d
        inc hl
        ld (hl),e
        scf
        ret
.nil:   pop hl
        ld (hl),1
        or a
        ret

addpt:                                  ; append (B, C) to the face being built
        ld hl,(pp)
        ld (hl),b
        inc hl
        ld (hl),c
        inc hl
        ld (pp),hl
        ld hl,np
        inc (hl)
        ret
lastpt:                                 ; D,E = the last point
        ld hl,(pp)
        dec hl
        ld e,(hl)
        dec hl
        ld d,(hl)
        ret
firstpt:                                ; D,E = the first point
        ld hl,(fp)
        inc hl
        ld d,(hl)
        inc hl
        ld e,(hl)
        ret

; corners (0x91C2): B,C = target (kept) -> appends the screen corners walked from the last point to it
corners:
        push bc
        call lastpt
        ld a,e
        ld l,1
        cp 112
        jr z,1F
        ld a,d
        ld l,2
        or a
        jr z,1F
        ld a,e
        ld l,3
        or a
        jr z,1F
        ld l,0
1:      ld a,b
        ld h,0
        cp 192
        jr z,2F
        ld a,c
        ld h,1
        cp 112
        jr z,2F
        ld a,b
        ld h,2
        or a
        jr z,2F
        ld h,3
2:
.lp:    ld a,l
        cp h
        jr z,.done
        push hl
        add a,a
        ld hl,cornt
        add hl,a
        ld b,(hl)
        inc hl
        ld c,(hl)
        call lastpt
        ld a,b
        cp d
        jr nz,3F
        ld a,c
        cp e
        jr z,.skip
3:      call firstpt
        ld a,b
        cp d
        jr nz,4F
        ld a,c
        cp e
        jr z,.skip
4:      call addpt
.skip:  pop hl
        inc l
        ld a,l
        and 3
        ld l,a
        jr .lp
.done:  pop bc
        ret

cornt:  db 192,112, 0,112, 0,0, 192,0

vsub:                                   ; (HL) = (IX) - (IY), 3 words; keeps IX, IY
        ld b,3
        push ix
        push iy
1:      ld a,(ix+0)
        sub (iy+0)
        ld (hl),a
        inc hl
        ld a,(ix+1)
        sbc a,(iy+1)
        ld (hl),a
        inc hl
        inc ix
        inc ix
        inc iy
        inc iy
        djnz 1B
        pop iy
        pop ix
        ret

        MACRO CROSS dst, pa, pb, pc, pd     ; dst (32) = a * b - c * d (words)
        ld hl,(pa)
        ld de,(pb)
        call smul16
        ld (dst),hl
        ld (dst+2),de
        ld hl,(pc)
        ld de,(pd)
        call smul16
        ld b,d
        ld c,e
        ex de,hl
        ld hl,(dst)
        or a
        sbc hl,de
        ld (dst),hl
        ld hl,(dst+2)
        sbc hl,bc
        ld (dst+2),hl
        ENDM

add16acc:                               ; (HL) in acc48 += DE, carry up to the top byte (mod 2^48)
        ld a,(hl)
        add a,e
        ld (hl),a
        inc hl
        ld a,(hl)
        adc a,d
        ld (hl),a
.c:     ret nc
        inc hl
        ld a,l
        cp low(acc48+6)
        ret z
        ld a,(hl)
        add a,1
        ld (hl),a
        jr .c

        MACRO MACC i, j
        ld d,(ix+i)
        ld a,(mac_v+j)
        ld e,a
        mul d,e
        ld hl,acc48+i+j
        call add16acc
        ENDM

; mac48: IX -> n (s32), DE = v (s16) -> acc48 += n * v (mod 2^48)
mac48:
        ld (mac_v),de
        MACC 0, 0
        MACC 0, 1
        MACC 1, 0
        MACC 1, 1
        MACC 2, 0
        MACC 2, 1
        MACC 3, 0
        MACC 3, 1
        ld a,(mac_v+1)
        bit 7,a
        jr z,1F
        ld hl,acc48+2                   ; v < 0: acc -= n << 16
        ld a,(hl)
        sub (ix+0)
        ld (hl),a
        inc hl
        ld a,(hl)
        sbc a,(ix+1)
        ld (hl),a
        inc hl
        ld a,(hl)
        sbc a,(ix+2)
        ld (hl),a
        inc hl
        ld a,(hl)
        sbc a,(ix+3)
        ld (hl),a
1:      bit 7,(ix+3)
        ret z
        ld hl,acc48+4                   ; n < 0: acc -= v << 32
        ld a,(mac_v)
        ld e,a
        ld a,(hl)
        sub e
        ld (hl),a
        inc hl
        ld a,(mac_v+1)
        ld e,a
        ld a,(hl)
        sbc a,e
        ld (hl),a
        ret

; facing (0x8A69): the face (f_refs, base template) -> A = 1 if dot >= 0 else 0; clears f_cover when the
; signs of the dot and of nz differ
facing:
        ld hl,(f_refs)
        ld a,(hl)
        push af
        call estart
        ld (fc_p1),a
        pop af
        call eend
        ld (fc_p2),a
        ld hl,(f_refs)
        inc hl
        ld a,(hl)
        call eend
        ld (fc_p3),a
        ld a,(fc_p2)
        call vptr
        push ix
        pop iy
        ld a,(fc_p1)
        call vptr
        ld hl,fc_d1
        call vsub
        ld a,(fc_p3)
        call vptr
        ld hl,fc_d3
        call vsub
        CROSS fc_n+0, fc_d1+2, fc_d3+4, fc_d1+4, fc_d3+2
        CROSS fc_n+4, fc_d1+4, fc_d3+0, fc_d1+0, fc_d3+4
        CROSS fc_n+8, fc_d1+0, fc_d3+2, fc_d1+2, fc_d3+0
        ld hl,acc48
        ld b,6
        xor a
1:      ld (hl),a
        inc hl
        djnz 1B
        ld a,(fc_p2)
        call vptr
        push ix
        pop iy                          ; IY = V[p2]
        ld ix,fc_n+0
        ld e,(iy+0)
        ld d,(iy+1)
        call mac48
        ld ix,fc_n+4
        ld e,(iy+2)
        ld d,(iy+3)
        call mac48
        ld ix,fc_n+8
        ld e,(iy+4)
        ld d,(iy+5)
        call mac48
        ld a,(acc48+5)
        ld b,a
        ld a,(fc_n+11)
        xor b
        bit 7,a
        jr z,2F
        xor a
        ld (f_cover),a
2:      bit 7,b
        ld a,0
        ret nz
        inc a
        ret

; winding (0x9300): every edge of the face (f_refs, f_n, current template): sign of end.x * start.y - end.y *
; start.x (>= 0 -> 1) = f_want -> carry set
winding:
        ld a,(f_n)
        ld b,a
        ld hl,(f_refs)
.w:     push bc
        push hl
        ld a,(hl)
        push af
        call estart
        ld (wd_s),a
        pop af
        call eend
        call vptr
        push ix
        ld a,(wd_s)
        call vptr
        push ix
        pop iy
        pop ix
        ld l,(ix+0)
        ld h,(ix+1)
        ld e,(iy+2)
        ld d,(iy+3)
        call smul16
        push de
        push hl
        ld l,(ix+2)
        ld h,(ix+3)
        ld e,(iy+0)
        ld d,(iy+1)
        call smul16
        ld b,d
        ld c,e
        ex de,hl
        pop hl
        or a
        sbc hl,de
        pop hl
        sbc hl,bc
        ld a,h
        rlca
        ccf
        ld a,0
        rla
        ld hl,f_want
        cp (hl)
        pop hl
        pop bc
        jr nz,.no
        inc hl
        djnz .w
        scf
        ret
.no:    or a
        ret

; ==== faces -> output record (0x9448's callers: no-clip 0x8C74, clip 0x8E88) ===================================
; In: nv, vtx, codes; f_tmpl (base edge template), f_back (mode 2), f_fl (face list: count, then colour slot, n,
; refs), cols[] (modes 0 / 1), f_mode, f_cb (mode 2), f_id; the record goes to (outp).
; Out: carry set = a record was written (outp moved past it).
faces:
        ld hl,codes
        ld a,(nv)
        ld b,a
        ld a,31
1:      and (hl)
        inc hl
        djnz 1B
        sub 31
        ld (f_clip),a
        jr z,2F
        ld hl,estate
        ld b,16
        xor a
3:      ld (hl),a
        inc hl
        djnz 3B
2:      xor a
        ld (f_cnt),a
        ld (f_idx),a
        ld hl,(outp)
        inc hl
        inc hl
        ld (wp),hl
        ld hl,(f_fl)
        ld a,(hl)
        ld (f_left),a
        inc hl
        ld (f_ptr),hl
.face:  ld a,(f_left)
        or a
        jp z,.end
        dec a
        ld (f_left),a
        ld hl,(f_ptr)
        inc hl
        ld a,(hl)
        ld (f_n),a
        inc hl
        ld (f_refs),hl
        add hl,a
        ld (f_ptr),hl
        ld hl,(f_tmpl)
        ld (ctmpl),hl
        ld a,(f_mode)
        cp 2
        ld a,1
        jr z,4F
        ld hl,cols
        ld a,(f_idx)
        add hl,a
        ld a,(hl)
4:      ld (f_col),a
        ld hl,f_idx
        inc (hl)
        or a
        jp z,.face
        ld a,1
        ld (f_cover),a
        ld a,(f_clip)
        or a
        call nz,phase_a
        ld a,(f_mode)
        or a
        jr z,.m0
        call facing
        ld (f_want),a
        ld b,a
        ld a,(f_mode)
        cp 1
        jr nz,.m2
        ld a,b
        or a
        jp nz,.face
        jr .m0
.m2:    ld a,b
        or a
        ld a,(f_cb)
        jr z,5F
        swapnib
        ld hl,(f_back)
        ld (ctmpl),hl
        ld hl,f_want
        ld (hl),0
5:      and 15
        ld (f_col),a
        jp z,.face
.m0:    ld a,(f_clip)
        or a
        jr nz,.clip
        ld hl,(wp)                      ; no clip: the projected start of each edge
        ld a,(f_col)
        swapnib
        ld b,a
        ld a,(f_n)
        or b
        ld (hl),a
        inc hl
        ld (wp),hl
        ld a,(f_n)
        ld b,a
        ld hl,(f_refs)
.nc:    push bc
        push hl
        ld a,(hl)
        call estart
        call vptr
        call proj
        ld hl,(wp)
        ld (hl),b
        inc hl
        ld (hl),c
        inc hl
        ld (wp),hl
        pop hl
        inc hl
        pop bc
        djnz .nc
        ld hl,f_cnt
        inc (hl)
        jp .face
.clip:  ld a,(f_n)
        cp 2
        jr nz,6F
        ld a,1
6:      ld (f_nn),a
        ld hl,(wp)
        ld (fp),hl
        inc hl
        ld (pp),hl
        xor a
        ld (np),a
        ld a,(f_nn)
        ld b,a
        ld hl,(f_refs)
.cl:    push bc
        push hl
        ld a,(hl)
        ld (f_r),a
        and 127
        call edge
        jr nc,.cln
        ld a,(f_r)
        bit 7,a
        jr z,1F
        push bc
        push de
        pop bc
        pop de
1:      ld (cl_p1),de
        ld a,(np)
        or a
        jr z,2F
        push bc
        call lastpt
        pop bc
        ld a,b
        cp d
        jr nz,3F
        ld a,c
        cp e
        jr z,4F
3:      call corners
2:      call addpt
4:      ld de,(cl_p1)
        ld a,b
        cp d
        jr nz,5F
        ld a,c
        cp e
        jr z,.cln
5:      ld b,d
        ld c,e
        call addpt
.cln:   pop hl
        inc hl
        pop bc
        djnz .cl
        ld a,(np)
        cp 2
        jr c,.few
        jr nz,.close
        ld a,(f_nn)
        cp 1
        jr z,.emitc
.close: call firstpt
        push de
        call lastpt
        pop bc
        ld a,b
        cp d
        jr nz,7F
        ld a,c
        cp e
        jr nz,7F
        ld hl,(pp)
        dec hl
        dec hl
        ld (pp),hl
        ld hl,np
        dec (hl)
        jr .emitc
7:      call corners
.emitc: ld hl,(fp)
        ld a,(f_col)
        swapnib
        ld b,a
        ld a,(np)
        or b
        ld (hl),a
        ld hl,(pp)
        ld (wp),hl
        ld hl,f_cnt
        inc (hl)
        jp .face
.few:   ld a,(f_nn)
        cp 1
        jp z,.face
        ld a,(f_cover)
        or a
        jp z,.face
        ld a,(f_mode)
        or a
        jr nz,.wind
        call facing
        ld (f_want),a
        ld a,(f_cover)
        or a
        jp z,.face
.wind:  call winding
        jp nc,.face
        ld hl,(wp)                      ; the full-screen face: the record ends here
        ld a,(f_col)
        swapnib
        or 4
        ld (hl),a
        inc hl
        ex de,hl
        ld hl,cornt
        ld bc,8
        ldir
        ld (wp),de
        ld hl,f_cnt
        inc (hl)
        ld a,(hl)
        or 0x80
        jr .hdr
.end:   ld a,(f_cnt)
        or a
        ret z
.hdr:   ld hl,(outp)
        ld b,a
        ld a,(f_id)
        ld (hl),a
        inc hl
        ld (hl),b
        ld hl,(wp)
        ld (outp),hl
        scf
        ret

; phase_a (0x8E88 before the facing test): the face covers the screen only if every other edge has both ends
; outside and their codes share no inside plane
phase_a:
        ld a,(f_n)
        inc a
        srl a
        ld b,a
        ld c,30
        ld hl,(f_refs)
.k:     push hl
        ld a,(hl)
        and 127
        add a,a
        inc a
        ld hl,(ctmpl)
        add hl,a
        ld a,(hl)
        call codeof
        cp 31
        jr z,.hit
        and c
        ld c,a
        inc hl
        ld a,(hl)
        call codeof
        cp 31
        jr z,.hit
        and c
        ld c,a
        pop hl
        inc hl
        inc hl
        djnz .k
        ld a,c
        or a
        ret z
        jr .no
.hit:   pop hl
.no:    xor a
        ld (f_cover),a
        ret

; ==== object builders (0x85C9 dispatch; 0x97F9 cube, 0x9CB8 rectangle, 0x9953 pyramids, 0x9C22 polygons) =======

        MACRO AV k, r
        ld a,(mat+3*r+k)
        ld e,(ix+4+k)
        call smul8u8
        ld (av+6*k+2*r),hl
        ENDM

avecs:                                  ; A_k = M column k * size_k (IX = record)
        AV 0,0
        AV 0,1
        AV 0,2
        AV 1,0
        AV 1,1
        AV 1,2
        AV 2,0
        AV 2,1
        AV 2,2
        ret

        MACRO VADD dst, src, vec
        ld hl,(src)
        ld de,(vec)
        add hl,de
        ld (dst),hl
        ld hl,(src+2)
        ld de,(vec+2)
        add hl,de
        ld (dst+2),hl
        ld hl,(src+4)
        ld de,(vec+4)
        add hl,de
        ld (dst+4),hl
        ENDM

origin:                                 ; vtx[0] = transform of the box minimum (IX = record, kept)
        ld hl,(box+0)
        ld (tp+0),hl
        ld hl,(box+4)
        ld (tp+2),hl
        ld hl,(box+8)
        ld (tp+4),hl
        push ix
        ld iy,tp
        ld ix,vtx
        call xform
        pop ix
        ret

allcodes:                               ; codes[] for nv vertices -> A = OR of them (IX kept)
        push ix
        ld a,(nv)
        ld b,a
        ld ix,vtx
        ld hl,codes
        ld c,0
1:      push bc
        push hl
        call outc
        pop hl
        ld (hl),a
        inc hl
        pop bc
        or c
        ld c,a
        ld de,6
        add ix,de
        djnz 1B
        ld a,c
        pop ix
        ret

        MACRO CCOL k
        ld a,(ix+9+k)
        and 15
        bit 2*k,c
        jr nz,1F
        xor a
1:      ld (cols+2*k),a
        ld a,(ix+9+k)
        swapnib
        and 15
        bit 2*k+1,c
        jr nz,2F
        xor a
2:      ld (cols+2*k+1),a
        ENDM

b_cube:
        call origin
        call avecs
        VADD vtx+6, vtx, av
        VADD vtx+12, vtx+6, av+6
        VADD vtx+18, vtx, av+6
        VADD vtx+24, vtx, av+12
        VADD vtx+30, vtx+6, av+12
        VADD vtx+36, vtx+12, av+12
        VADD vtx+42, vtx+18, av+12
        ld a,8
        ld (nv),a
        call allcodes
        cp 31
        ret nz
        ld a,(side)
        ld c,a
        CCOL 0
        CCOL 1
        CCOL 2
        ld hl,tmpl
        ld (f_tmpl),hl
        ld hl,tmpl+25
        ld (f_fl),hl
        xor a
        ld (f_mode),a
        call faces
        jp emit

vadd3:                                  ; (HL) = (IX) + (IY), 3 words
        ld b,3
1:      ld a,(ix+0)
        add a,(iy+0)
        ld (hl),a
        inc hl
        ld a,(ix+1)
        adc a,(iy+1)
        ld (hl),a
        inc hl
        inc ix
        inc ix
        inc iy
        inc iy
        djnz 1B
        ret

b_rect:
        call origin
        call avecs
        ld a,(side)
        ld c,a
        ld a,(ix+4)
        or a
        jr nz,1F
        ld hl,av+12                     ; size x = 0: u = A2, v = A1
        ld de,av+6
        jr 3F
1:      ld a,(ix+5)
        or a
        jr nz,2F
        ld hl,av+0                      ; size y = 0: u = A0, v = A2
        ld de,av+12
        srl c
        srl c
        jr 3F
2:      ld hl,av+6                      ; else: u = A1, v = A0
        ld de,av+0
        srl c
        srl c
        srl c
        srl c
3:      ld (r_u),hl
        ld (r_v),de
        bit 0,c
        ld a,(ix+9)
        jr z,4F
        and 15
        ld hl,tmpl+292
        jr 5F
4:      swapnib
        and 15
        ld hl,tmpl+283
5:      ld (f_tmpl),hl
        or a
        ret z
        ld (cols),a
        push ix
        ld ix,vtx
        ld iy,(r_u)
        ld hl,vtx+6
        call vadd3                      ; V1 = O + u
        ld ix,vtx+6
        ld iy,(r_v)
        ld hl,vtx+12
        call vadd3                      ; V2 = V1 + v
        ld ix,vtx+12
        ld iy,(r_u)
        ld hl,vtx+18
        call vsub                       ; V3 = V2 - u
        pop ix
        ld a,4
        ld (nv),a
        call allcodes
        cp 31
        ret nz
        ld hl,rectfl
        ld (f_fl),hl
        xor a
        ld (f_mode),a
        call faces
        jp emit

rectfl: db 1, 0, 4, 0,1,2,3
pflc:   db 1, 0, 0, 0,1,2,3,4,5
linefl: db 1, 0, 2, 0,1

        MACRO INS dsti, basei, k        ; vals[dsti] = vals[basei] + inset k * 64
        ld d,(ix+12+k)
        ld e,64
        mul d,e
        ld hl,(box+2*basei)
        add hl,de
        ld (box+2*dsti),hl
        ENDM

b_pyr:
        ld a,(b_type)
        cp 5
        ret z                           ; type 5: not in the game's data (M0)
        INS 6,0,0
        INS 7,0,2
        INS 8,2,0
        INS 9,2,2
        INS 10,4,1
        INS 11,4,3
        INS 12,2,1
        INS 13,2,3
        ld b,0
        ld a,(ix+12)
        cp (ix+14)
        jr nz,1F
        set 1,b
1:      ld a,(ix+13)
        cp (ix+15)
        jr nz,2F
        set 0,b
2:      ld a,b                          ; pyrsel: (point count, edge template, face list) per apex shape
        add a,a
        add a,a
        add a,b
        ld hl,pyrsel
        add hl,a
        ld a,(hl)
        ld (nv),a
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld (f_tmpl),de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld (f_fl),de
        ld a,(b_type)                   ; point sources: pyrsrc + (type - 4) * 24
        sub 4
        ld e,a
        ld d,24
        mul d,e
        ld hl,pyrsrc
        add hl,de
        ld (py_src),hl
        push ix
        ld ix,vtx
        ld a,(nv)
        ld b,a
.pt:    push bc
        ld hl,(py_src)
        ld de,tp
        ld b,3
.ax:    ld a,(hl)
        inc hl
        push hl
        add a,a
        ld hl,box
        add hl,a
        ldi
        ldi
        inc bc
        inc bc
        pop hl
        djnz .ax
        ld (py_src),hl
        ld iy,tp
        call xform
        ld de,6
        add ix,de
        pop bc
        djnz .pt
        pop ix
        call allcodes
        cp 31
        ret nz
        ld hl,cols                      ; face f: low / high nibble of colour byte f / 2
        ld b,3
        push ix
.cb:    ld a,(ix+9)
        ld c,a
        and 15
        ld (hl),a
        inc hl
        ld a,c
        swapnib
        and 15
        ld (hl),a
        inc hl
        inc ix
        djnz .cb
        pop ix
        ld a,1
        ld (f_mode),a
        call faces
        jp emit

pyrsel: db 8
        dw tmpl+202, tmpl+227           ; apex x and z differ: 27688 / 27713
        db 6
        dw tmpl+106, tmpl+125           ; z equal: 27592 / 27611
        db 6
        dw tmpl+154, tmpl+173           ; x equal: 27640 / 27659
        db 5
        dw tmpl+62, tmpl+79             ; both equal: 27548 / 27565

; per type 4..9: 8 points x (x, y, z) source = index into vals (box words 0-5, then xmn+i0, xmn+i2, ymn+i0,
; ymn+i2, zmn+i1, zmn+i3, ymn+i1, ymn+i3)
pyrsrc: db 0,2,5, 0,2,4, 0,3,4, 0,3,5, 1,8,11, 1,9,10, 1,8,10, 1,9,11           ; 4
        db 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0,  0,0,0,  0,0,0,  0,0,0            ; 5 (absent)
        db 0,2,4, 0,2,5, 1,2,5, 1,2,4, 6,3,10, 7,3,11, 6,3,11, 7,3,10           ; 6
        db 1,3,4, 1,3,5, 0,3,5, 0,3,4, 7,2,10, 6,2,11, 7,2,11, 6,2,10           ; 7
        db 0,3,4, 0,2,4, 1,2,4, 1,3,4, 6,13,5, 7,12,5, 6,12,5, 7,13,5           ; 8
        db 0,2,5, 0,3,5, 1,3,5, 1,2,5, 6,12,4, 7,13,4, 6,13,4, 7,12,4           ; 9

b_poly:
        ld a,(b_type)
        sub 8
        ld (nv),a
        push ix
        pop hl
        ld de,10
        add hl,de                       ; HL -> first point
        push ix
        ld ix,vtx
        ld b,a
.pt:    push bc
        ld c,0
.ax:    ld d,(hl)
        inc hl
        ld e,64
        mul d,e
        push hl
        ld hl,in_cam
        ld a,c
        add hl,a
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ex de,hl
        or a
        sbc hl,de
        ex de,hl
        ld hl,tp
        ld a,c
        add hl,a
        ld (hl),e
        inc hl
        ld (hl),d
        pop hl
        inc c
        inc c
        ld a,c
        cp 6
        jr nz,.ax
        push hl
        ld iy,tp
        call xform
        pop hl
        ld de,6
        add ix,de
        pop bc
        djnz .pt
        pop ix
        call allcodes
        cp 31
        ret nz
        ld a,(nv)
        cp 2
        jr nz,1F
        ld a,(ix+9)                     ; a line: one colour, mode 0
        and 15
        ld (cols),a
        ld hl,tmpl+264
        ld (f_tmpl),hl
        ld hl,linefl
        ld (f_fl),hl
        xor a
        ld (f_mode),a
        call faces
        jp emit
1:      push af                         ; polygons: two-sided, mode 2
        ld hl,pflc
        ld de,pfl
        ld bc,9
        ldir
        pop af
        ld (pfl+2),a
        ld hl,tmpl+269
        ld de,tmpl+276
        cp 3
        jr z,2F
        ld hl,tmpl+283
        ld de,tmpl+292
        cp 4
        jr z,2F
        ld hl,tmpl+301
        ld de,tmpl+312
2:      ld (f_tmpl),hl
        ld (f_back),de
        ld hl,pfl
        ld (f_fl),hl
        ld a,(ix+9)
        ld (f_cb),a
        ld a,2
        ld (f_mode),a
        call faces
        jp emit

; emit: carry set (a record was written) -> list entry (record pointer, box)
emit:
        ret nc
        ld hl,(entp)
        ld de,(b_start)
        ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        ex de,hl
        ld hl,box
        ld bc,12
        ldir
        ld hl,(listp)
        ld bc,(entp)
        ld (hl),c
        inc hl
        ld (hl),b
        inc hl
        ld (listp),hl
        inc de
        inc de
        ld (entp),de
        ld hl,nrec
        inc (hl)
        ret

; build: IX = object record
build:
        ld a,(ix+0)
        bit 6,a
        ret nz
        and 15
        ret z
        cp 2
        ret z
        ld (b_type),a
        ld a,(in_cull)
        or a
        jr nz,1F
        call secull
        ret c
1:      call bbox
        ld a,(ix+7)
        ld (f_id),a
        ld hl,(outp)
        ld (b_start),hl
        ld a,(b_type)
        cp 1
        jp z,b_cube
        cp 3
        jp z,b_rect
        cp 10
        jp c,b_pyr
        jp b_poly

; ==== depth sort (0x9D8A) ======================================================================================

; axcode: IX -> a (min, max), IY -> b (min, max) words -> A = 0, 1 or 2 (m0_sort.axis_code)
axcode:
        ld l,(ix+0)
        ld h,(ix+1)
        ld e,(iy+2)
        ld d,(iy+3)
        or a
        sbc hl,de
        bit 7,h
        jr z,1F
        ld l,(iy+0)
        ld h,(iy+1)
        ld e,(ix+2)
        ld d,(ix+3)
        or a
        sbc hl,de
        bit 7,h
        jr z,1F
        xor a
        ret
1:      ld a,(ix+1)
        xor (ix+3)
        bit 7,a
        jr z,2F
        ld a,1
        ret
2:      ld a,(iy+1)
        xor (iy+3)
        bit 7,a
        jr z,3F
        ld a,2
        ret
3:      ld a,(iy+1)
        xor (ix+1)
        bit 7,a
        jr z,4F
        xor a
        ret
4:      ld l,(iy+0)
        ld h,(iy+1)
        ld e,(ix+0)
        ld d,(ix+1)
        or a
        sbc hl,de
        ld a,h
        or l
        jr nz,5F
        ld l,(iy+2)
        ld h,(iy+3)
        ld e,(ix+2)
        ld d,(ix+3)
        or a
        sbc hl,de
        ld a,h
        xor (iy+3)
        bit 7,a
        ld a,2
        ret nz
        dec a
        ret
5:      ld a,h
        xor (iy+1)
        bit 7,a
        ld a,1
        ret z
        inc a
        ret

; ordered: DE = entry a, BC = entry b -> carry set = keep (no axis 1, some axis 2)
ordered:
        ld hl,2
        add hl,de
        push hl
        pop ix
        ld hl,2
        add hl,bc
        push hl
        pop iy
        ld c,0
        ld b,3
.ax:    push bc
        call axcode
        pop bc
        cp 1
        jr z,.no
        or c
        ld c,a
        ld de,4
        add ix,de
        add iy,de
        djnz .ax
        ld a,c
        or a
        ret z
        scf
        ret
.no:    or a
        ret

sort:                                   ; bubble sort as 0x9D8A. ordered(a, b) depends on the two entries only and
        ld a,(nrec)                     ; the order can cycle, so results are cached: s_mat[a * 32 + b] = view
        cp 2                            ; stamp (s_gen, a multiple of 4, never 0) + 1 keep / 2 swap; entries are
        ret c                           ; 16 bytes from a page start, index = offset / 16; index >= 32: no cache
        dec a
        ld (s_passes),a
        ld a,(s_gen)
        add a,4
        jr nz,1F
        ld hl,s_mat                     ; stamp wrapped: clear the cache
        ld de,s_mat+1
        ld bc,1023
        ld (hl),a
        ldir
        ld a,4
1:      ld (s_gen),a
.pass:  xor a
        ld (s_swapped),a
        ld a,(nrec)
        dec a
        ld b,a
        ld hl,list
.cmp:   push bc
        push hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld c,(hl)
        inc hl
        ld b,(hl)
        ld a,d
        sub high entries
        cp 2
        jr nc,.direct
        ld a,b
        sub high entries
        cp 2
        jr nc,.direct
        rrca                            ; cache address: b's index
        rrca
        rrca
        rrca
        and 16
        ld l,a
        ld a,c                          ; sort key b low
        swapnib
        and 15
        or l
        ld l,a
        ld a,e
        add a,a
        and 0xE0
        or l
        ld l,a
        ld a,e
        rlca
        and 1
        ld h,a
        ld a,d
        sub high entries
        add a,a
        or h
        add a,high s_mat
        ld h,a
        ld a,(s_gen)
        xor (hl)
        cp 4
        jr nc,.miss
        rra                             ; cached: bit 0 = keep
        jr .have
.miss:  push hl
        call ordered
        pop hl
        ld a,(s_gen)
        jr nc,2F
        inc a
        ld (hl),a
        scf
        jr .have
2:      add a,2
        ld (hl),a
        or a
        jr .have
.direct:
        call ordered
.have:  pop hl
        jr c,.keep
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld c,(hl)
        inc hl
        ld b,(hl)
        ld (hl),d
        dec hl
        ld (hl),e
        dec hl
        ld (hl),b
        dec hl
        ld (hl),c
        ld a,1
        ld (s_swapped),a
.keep:  inc hl
        inc hl
        pop bc
        dec b
        jp nz,.cmp
        ld a,(s_swapped)
        or a
        ret z
        ld hl,s_passes
        dec (hl)
        jp nz,.pass
        ret

; ==== the pipeline =============================================================================================

objlist:                                ; HL = first record, A = count
        or a
        ret z
        ld b,a
1:      push bc
        push hl
          IFDEF M3
        ld a,(fl_pend)
        or a
        call nz,flipchk                 ; a view waiting for its flip (the glue's flipdef)
          ENDIF
        push hl
        pop ix
        call build
        pop hl
        push hl
        ld de,8
        add hl,de
        ld a,(hl)
        pop hl
        add hl,a
        pop bc
        djnz 1B
        ret

render_geom:
        call matrix
        ld a,(in_cull)
        or a
        call z,sector
        xor a
        ld (nrec),a
        ld hl,outbuf
        ld (outp),hl
        ld hl,entries
        ld (entp),hl
        ld hl,list
        ld (listp),hl
        ld hl,(in_alist)
        ld a,(in_acnt)
        call objlist
        ld hl,(in_glist)
        ld a,(in_gcnt)
        call objlist
        call sort
        ld a,(nrec)                     ; full-screen records (the game's 29523)
        ld b,a
        ld c,0
        or a
        jr z,2F
        ld hl,entries
1:      push hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        ex de,hl
        inc hl
        bit 7,(hl)
        jr z,3F
        inc c
3:      pop hl
        ld de,16
        add hl,de
        djnz 1B
2:      ld a,c
        ld (nfull),a
        ret

; ==== raster (0x9EA3: clear 0xA3F4, filler 0x9484, span 0x9696) -> Layer 2 ====================================
; Spec = m1_raster.py (equal to the game's view buffer at all redraws). The view = Layer 2 lines 32 + r (r = 0..112,
; the game's buffer row; r = 112 is its y = 0 overrun row, below the 112-line view) and x 32 + p (p = 0..191).
; Window: MMU slot 4 (0x8000-0x9FFF, NR 0x54), one 8K page = 32 lines; in_l2page = the page of line 0.
; Pixel byte = 2 * code + the original's bit: code 0-15 face colour nibble, 16 + c sky / ground fill of pattern c,
; 32 mountains, 33 lightning. The palette decides what the player sees (colour / original ink-paper / flat).
L2WIN   EQU 0x8000
PAT     EQU 53825                       ; dither patterns: 4 rows per colour at (colour - 1) * 4 (world snapshot)

; rcol: A = colour (pattern), C = code -> r_patp (as the game's 29664), rtile (4 rows x 8 pixel values),
; r_p8 (1 = a row's pattern does not repeat every 4 pixels: colour 0 only), the RAM jump r_jp
rcol:
        dec a
        add a,a
        add a,a
        ld hl,PAT
        add hl,a
        ld (r_patp),hl
        ld a,c
        add a,a
        ld c,a                          ; C = 2 * code (bit clear)
        ld a,0xC3
        ld (r_jp),a
        ld a,high pbeg
        ld (r_jp+2),a
        xor a
        ld (r_p8),a
        ld de,rtile
        ld b,4
1:      ld a,(hl)
        inc hl
        push hl
        ld l,a
        swapnib
        cp l
        jr z,2F
        ld a,1
        ld (r_p8),a
2:
        DUP 8
        sla l
        ld a,c
        adc a,0
        ld (de),a
        inc e
        EDUP
        pop hl
        djnz 1B
        ret

; l2map: A = row & 0xE0, HL = l2cur -> that 32-line page into the window. Keeps BC, DE.
l2map:
        ld (hl),a
        dec hl
        rlca
        rlca
        rlca
        add a,(hl)
        ld (cur54),a                    ; first: an interrupt stub puts (cur54) back in the window
        nextreg 0x54,a
        ret

; l2row: A = row (0..112) -> HL = its pixel 0 in the window (page mapped). Keeps DE, B.
l2row:
        ld c,a
        and 0xE0
        ld hl,l2cur
        cp (hl)
        call nz,l2map
        ld a,c
        and 31
        or high L2WIN
        ld h,a
        ld l,32
        ret

; span: H, D = the two ends (x bytes) -> pixels max(lo, 1) - 1 .. hi - 1 of row (r_row) in pattern row (r_y) & 3,
; then the row moves up one. An end >= 193 drops the span and its row advance (0x9696).
; 16 pixels and more: PUSH fill, 5.5 T a pixel, SP inside Layer 2 with interrupts ON. Safe if an interrupt's entry
; writes only its 2-byte return address at SP (the M2 stub must switch stacks first): those 2 bytes are always
; pixels this span still writes (the next PUSH, or the 2-3 leftmost pixels written last, after SP is restored).
span:
        ld a,h
        cp 193
        ret nc
        ld a,d
        cp 193
        ret nc
        cp h
        jr nc,1F                        ; D >= H: lo = H, hi = D
        ld d,h
        ld h,a
1:      ld a,h
        or a
        jr z,2F
        dec a
2:      ld e,a                          ; E = first pixel, D = end (exclusive)
        ld hl,r_row
        ld a,(hl)
        dec (hl)
        cp 113
        ret nc                          ; not a view row (never with clipped points)
        ld c,a
        ld a,d
        sub e
        ret z
        ld b,a                          ; B = pixels
        ld a,c
        and 0xE0
        ld hl,l2cur
        cp (hl)
        call nz,l2map
        ld a,c
        and 31
        or high L2WIN
        ld h,a
        ld a,e
        add a,32
        ld l,a                          ; HL = first pixel
        ld a,(r_p8)
        or a
        jr nz,.p8
        ld a,(r_y)
        and 3
        add a,a
        add a,a
        add a,a
        add a,low rtile
        ld c,a                          ; C = low byte of the pattern row's 8 values
        ld a,b
        cp 16
        jr nc,.push
        push hl                         ; short: B, C, D, E = values of pixels end & 3 .., unrolled LD (HL),r
        ld a,d
        and 3
        add a,c
        ld l,a
        ld h,high rtile
        ld a,b
        ld b,(hl)
        inc l
        ld c,(hl)
        inc l
        ld d,(hl)
        inc l
        ld e,(hl)
        add a,a
        neg
        add a,low ufend
        ld l,a
        ld h,high ufend
        ex (sp),hl                      ; HL = first pixel, (SP) = entry into the unrolled run
        ret                             ; ... whose RET returns to our caller
.push:  ld (r_sp),sp                    ; B = pixels (>= 16), C = pattern row, D = end, E = first, HL = first pixel
        ld a,d
        add a,32
        ld e,l                          ; E = the first pixel's low byte (= first, mod 4)
        ld l,a
        ld sp,hl                        ; SP = the end (odd or even)
        ld l,e                          ; HL = first pixel
        ld a,b
        srl a
        cpl
        add a,low pend + 2              ; pixels / 2 - 1 PUSHes fill m .. end, m = first + 2 (+ 1: odd count);
        ld (r_jp+1),a                   ; the 2-3 pixels below m come last
        ld a,b
        and 1
        add a,e
        add a,2
        and 3
        add a,c
        ld c,a                          ; values of pixels m, m + 1 (DE) and m + 2, m + 3 (BC)
        rr b                            ; CF = odd count, kept to the end (LD, INC, EX do not change it)
        ld b,high rtile
        ld a,(bc)
        ld e,a
        inc c
        ld a,(bc)
        ld d,a
        inc c
        ld a,(bc)
        inc c
        ex af,af'
        ld a,(bc)
        ld b,a
        ex af,af'
        ld c,a
        sbc a,a                         ; bit 0 = 3 pixels below m
        jp r_jp
.p8:    push hl                         ; period 8: the first 8 pixels from the tile, then LDIR 8 behind
        ld a,(r_y)
        and 3
        add a,a
        add a,a
        add a,a
        ld c,a
        ld a,e
        and 7
        add a,c
        ld de,rtile
        add de,a
        push bc
        ld a,b
        cp 9
        jr c,4F
        ld a,8
4:      ld b,a
5:      ld a,(de)
        ld (hl),a
        inc l
        ld a,e
        inc a
        xor e
        and 7
        xor e
        ld e,a
        djnz 5B
        pop bc
        pop hl
        ld a,b
        sub 8
        ret c
        ret z
        ld c,a
        ld b,0
        ld d,h
        ld a,l
        add a,8
        ld e,a
        ldir
        ret

        ALIGN 256
pbeg:                                   ; 96 PUSHes: BC, DE repeating; the last (DE) lands on pixel m
        DUP 48
        push bc
        push de
        EDUP
pend:   ld sp,(r_sp)
        rra
        jr nc,1F
        ld (hl),d                       ; 3 pixels below m
        inc l
1:      ld (hl),c
        inc l
        ld (hl),b
        ret
ufill:                                  ; 16 pixels: B, C, D, E repeating
        DUP 4
        ld (hl),b
        inc l
        ld (hl),c
        inc l
        ld (hl),d
        inc l
        ld (hl),e
        inc l
        EDUP
ufend:  ret
        ASSERT high pbeg == high ufend

; rslope: A = dx low byte, CF = borrow (dx = A - 256), C = dy + 1 (2..113)
;   -> HL = 45740(dx * 256, -(dy + 1)): magnitude rounded half up, negative when dx > 0. Keeps IX, IY, D.
rslope:
        jr nc,1F
        neg
        jr .mag
1:      or a
        jr z,.zero
        call .mag
        xor a
        sub l
        ld l,a
        sbc a,a
        sub h
        ld h,a
        ret
.zero:  ld hl,0
        ret
.mag:   ld h,a                          ; HL = A * 256 / C, 16 restoring steps, remainder in A
        ld l,0
        xor a
        ld b,16
2:      add hl,hl
        rla
        cp c
        jr c,3F
        sub c
        inc l
3:      djnz 2B
        ld b,a
        ld a,c
        srl a
        ld e,a
        ld a,b
        cp e
        ret c
        inc hl
        ret

; rface: HL = a face's points (x, y pairs), A = its header (colour << 4 | n) -> HL = after the points (0x9484)
; While it runs: HL' = left x (8.8), BC' = left slope, IX = right x, DE' = right slope, IYL / IYH = the y where
; the left / right chain's edge ends; chain pointers r_lp (the game's IY, backwards) / r_rp (its IX, forwards).
rface:
        push af
        push hl
        swapnib
        and 15
        ld c,a
        call rcol
        pop hl
        pop af
        and 15
        ld (r_n),a
        ld (r_cnt),a
        jr z,1F
        add a,a
        ld c,a
        ld b,0
        ld de,r_pts
        push hl
        ldir                            ; the points twice (as 29666)
        pop hl
        ld c,a
        ldir
1:      ld (r_q),hl
        ld a,(r_n)
        cp 2
        jp z,rline
        ld hl,r_pts+1                   ; lowest vertex (the last of ties)
        ld c,(hl)
        ld d,h
        ld e,l
        sub 1
        jr c,2F
        jr z,2F
        ld b,a
        ld a,c
3:      inc hl
        inc hl
        cp (hl)
        jr c,4F
        ld a,(hl)
        ld d,h
        ld e,l
4:      djnz 3B
        ld c,a
2:      dec de                          ; DE = x of the lowest vertex
        ld a,c
        ld (r_y),a
        neg
        add a,112
        ld (r_row),a
        ld h,d
        ld l,e
        dec hl
        dec hl
        ld (r_rp),hl
        inc hl
        inc hl
        inc hl
        ld a,(hl)
        ld iyh,a
        ld a,(r_n)
        inc a
        add a,a
        ex de,hl
        add hl,a
        ld (r_lp),hl
        dec hl
        ld a,(hl)
        ld iyl,a
        ld a,3
        ld (r_fl),a
        ld ix,0
        exx
        ld hl,0
        ld bc,(r_sl)
        ld de,(r_sr)
        exx
        ld a,(r_y)
        jr .L66
.L44:   exx
        ld a,h
        exx
        ld h,a
        ld a,ixh
        ld d,a
        call span
        exx
        add hl,bc
        add ix,de
        exx
        ld hl,r_y
        inc (hl)
        ld a,(hl)
.L66:   cp iyl
        jr z,.L71
.L54:   cp iyh
        jr nz,.L44
.L59:   ld hl,r_cnt
        dec (hl)
        jp m,.L443
        ld hl,(r_rp)
        inc hl
        inc hl
        ld (r_rp),hl
        inc hl
        ld a,(hl)
        inc hl
        inc hl
        sub (hl)
        jr z,.L59
        jp p,.L443
        ld e,(hl)
        ld iyh,e
        dec a
        neg
        ld c,a
        dec hl
        ld e,(hl)
        dec hl
        dec hl
        ld a,(hl)
        ld d,a
        sub e
        call rslope
        ld (r_sr),hl
        ld b,h
        ld c,l
        ld a,(r_fl)
        bit 1,a
        jr nz,6F
        sra h
        rr l
6:      and 0xFD
        ld (r_fl),a
        ld a,d
        add a,h
        ld h,a
        push hl
        pop ix
        push bc
        exx
        pop de
        exx
        jp .L44
.L71:   ld hl,r_cnt
        dec (hl)
        jp m,.L443
        ld hl,(r_lp)
        dec hl
        dec hl
        ld (r_lp),hl
        inc hl
        ld a,(hl)
        dec hl
        dec hl
        sub (hl)
        jr z,.L71
        jp p,.L443
        ld e,(hl)
        ld iyl,e
        dec a
        neg
        ld c,a
        inc hl
        ld a,(hl)
        ld d,a
        dec hl
        dec hl
        sub (hl)
        call rslope
        ld (r_sl),hl
        ld b,h
        ld c,l
        ld a,(r_fl)
        bit 0,a
        jr nz,5F
        sra h
        rr l
5:      and 0xFE
        ld (r_fl),a
        ld a,d
        add a,h
        ld h,a
        push bc
        push hl
        exx
        pop hl
        pop bc
        exx
        ld a,(r_y)
        jp .L54
.L443:  ld a,(r_fl)                     ; chains done; still flagged -> the min / max x of all points
        or a
        jr z,9F
        ld hl,(r_rp)
        ld a,(hl)
        ld e,a
        ld d,a
        ld a,(r_n)
        sub 1
        jr c,8F
        jr z,8F
        ld b,a
        ld hl,r_pts
7:      inc hl
        inc hl
        ld a,(hl)
        cp e
        jr nc,71F
        ld e,a
        jr 72F
71:     cp d
        jr c,72F
        ld d,a
72:     djnz 7B
8:      ld a,e
        exx
        ld h,a
        exx
        ld ixh,d
9:      exx
        ld a,h
        exx
        ld h,a
        ld a,ixh
        ld d,a
        call span
        ld hl,(r_q)
        ret

; rline: the two points at r_pts (0x9484's line path)
rline:
        ld hl,(r_pts)                   ; L = x0, H = y0
        ld de,(r_pts+2)                 ; E = x1, D = y1
        ld a,d
        sub h
        jr nc,1F
        ex de,hl                        ; from the lower end
1:      ld a,h
        ld (r_y),a
        neg
        add a,112
        ld (r_row),a
        ld a,d
        sub h
        jr nz,2F
        ld h,l
        ld d,e
        call span
        ld hl,(r_q)
        ret
2:      inc a
        ld c,a
        ld (r_b),a                      ; dy + 1 spans
        push hl
        ld a,l
        sub e
        call rslope
        ld (r_sl),hl                    ; (as the game's 29654)
        ex de,hl
        pop hl
        ld a,d
        rlca
        ld a,255
        jr nc,3F
        ld a,1
3:      ld (r_step),a                   ; 1 when the slope is negative
        ld a,l
        ld (r_xr+1),a
        xor a
        ld (r_xr),a                     ; XR = x0 << 8
        ld hl,(r_xr)
        add hl,de
        ld (r_xl),hl                    ; XL = XR + slope
4:      ld a,(r_xl+1)
        ld hl,r_xr+1
        cp (hl)
        jr z,5F
        ld hl,r_step
        add a,(hl)
        ld (r_xl+1),a
5:      ld hl,r_b
        dec (hl)
        jr z,6F
        ld a,(r_xl+1)
        ld h,a
        ld a,(r_xr+1)
        ld d,a
        call span
        ld hl,r_y
        inc (hl)
        ld hl,(r_xr)
        ld de,(r_sl)
        add hl,de
        ld (r_xr),hl
        add hl,de
        ld (r_xl),hl
        jr 4B
6:      ld a,(r_xl+1)
        ld h,a
        ld a,(r_xr+1)
        ld d,a
        call span
        ld hl,(r_q)
        ret

; rclear: the view clear 0xA3F4 (in_sky = (27402); 0 = none, the stale picture stays)
rclear:
        xor a
        ld (c_mrows),a
        ld (c_moff),a
        ld (c_lrows),a
        ld (c_loff),a
        ld a,(in_sky)
        or a
        ret z
        ld c,a
        and 15
        ld (c_lo),a
        ld a,c
        swapnib
        and 15
        ld (c_hi),a
        jr nz,1F
        ld bc,113*256
        jp .paint
1:      ld a,(c_lo)
        or a
        jr nz,2F
        ld bc,113
        jp .paint
2:      ld a,(in_pitch)
        ld e,a
        sub 8
        jp m,.go                        ; go = pitch
        ld a,e
        sub 29
        jp m,.gnd
        ld a,e
        sub 61
        jp m,.sky
        ld a,e
        sub 72
        ld e,a                          ; go = pitch - 72
        jr .go
.gnd:   ld bc,113
        jp .paint
.sky:   ld bc,113*256
        jp .paint
.go:    ld l,e                          ; HL = s8(go) * 11 + 60
        ld a,e
        rla
        sbc a,a
        ld h,a
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,de
        add hl,hl
        add hl,de
        ld de,60
        add hl,de
        IFDEF M3
        ld de,(tw_hadj)                 ; an in-between view: the pitch's fraction in rows (0 otherwise)
        add hl,de
        ENDIF
        ld bc,113*256
        ld a,l
        bit 7,h
        jr nz,3F
        cp 113
        jr c,4F
        ld bc,113                       ; all ground
        jp .paint
4:      ld c,a
3:      ld (c_d),a
        ld a,(in_lflag)
        or a
        jr nz,5F
        push hl
        ld de,96
        add hl,de
        ld a,l
        bit 7,h
        pop hl
        jr nz,5F
        ld (c_lrows),a
        cp 87
        jr c,5F
        ld e,a
        ld a,86
        ld (c_lrows),a
        ld a,e
        cp 114
        jr c,5F
        ld a,b
        sub c
        sub 10
        ld (c_lrows),a
        ld e,a
        ld a,86
        sub e
        ld (c_loff),a
5:      ld a,(c_d)
        add a,18
        jp p,6F
        ld a,(c_mrows)
        ld e,a
        jr 7F
6:      ld (c_mrows),a
        ld e,a
        cp 19
        jr c,7F
        ld e,a
        ld a,18
        ld (c_mrows),a
        ld a,e
        ld e,18
        cp 114
        jr c,7F
        ld a,b
        sub c
        ld (c_mrows),a
        ld e,a
        ld a,18
        sub e
        ld (c_moff),a
        ld b,0
        jr .paint
7:      ld a,b                          ; B = B - C - mrows (E)
        sub c
        sub e
        ld b,a
.paint: xor a                           ; B sky rows from the top, band, bolt, C ground rows
        ld (c_r),a
        ld a,b
        or a
        jr z,8F
        push bc
        ld e,a
        ld a,(c_lo)
        call rfill
        pop bc
8:      ld a,(c_mrows)
        or a
        jr z,9F
        push bc
        call rmount
        pop bc
9:      ld a,(c_lrows)
        or a
        jr z,10F
        push bc
        call rlight
        pop bc
10:     ld a,c
        or a
        ret z
        ld e,a
        ld a,(c_hi)
        ; fall into rfill

; rfill: A = colour (pattern, never 0: period 4), E = rows from row (c_r) down; pattern row = rows left & 3.
; A whole row = 95 PUSHes (pixels 2-191) + pixels 0-1 last (interrupt margin, as span).
rfill:
        push de
        ld c,a
        add a,16
        ld b,c
        ld c,a
        ld a,b
        call rcol
        pop de
        ld b,e
1:      push bc
        ld a,(c_r)
        cp 113
        jr nc,2F
        call l2row
        ld a,b
        and 3
        add a,a
        add a,a
        add a,a
        add a,low rtile
        ld e,a
        ld d,high rtile
        ex de,hl
        ld c,(hl)
        inc l
        ld b,(hl)                       ; BC = pixels 0, 1 (and 4, 5 ..)
        inc l
        ld a,(hl)
        inc l
        ld h,(hl)
        ld l,a
        ex de,hl                        ; DE = pixels 2, 3; HL = pixel 0
        call .row
2:      ld hl,c_r
        inc (hl)
        pop bc
        djnz 1B
        ret
.row:   ld (r_sp),sp
        ld l,224
        ld sp,hl
        ld l,32
        xor a
        jp pbeg+1

; rmount: the mountain band, (c_mrows) rows from row (c_r): panorama row (c_moff) + j, bytes cyclic from yaw & 7 * 2
rmount:
        ld a,(in_mount)
        cp 1
        jr z,1F
        ld a,(c_mrows)
        ld e,a
        ld a,(c_lo)
        jr rfill
1:      ld a,(in_yaw)
        and 7
        add a,a
        IFDEF M3
        ld hl,tw_madj                   ; an in-between view: half a yaw unit = 1 byte (0 otherwise)
        add a,(hl)
        ENDIF
        ld (c_a),a
        ld a,(c_moff)
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,pano
        add hl,de
        ld (c_src),hl
        ld a,(c_mrows)
        ld b,a
2:      push bc
        ld a,(c_r)
        cp 113
        jr nc,5F
        call l2row
        ex de,hl                        ; DE = pixel 0
        ld a,(c_a)
        ld c,a
        ld b,24
3:      push bc
        ld a,c
        and 15
        ld hl,(c_src)
        add hl,a
        ld c,(hl)
        ex de,hl
        ld b,64
        ld d,0
        DUP 8                           ; 27 T a pixel: 64 + the bit
        ld a,b
        sla c
        adc a,d
        ld (hl),a
        inc l
        EDUP
        ex de,hl
        pop bc
        inc c
        djnz 3B
5:      ld hl,(c_src)
        ld de,16
        add hl,de
        ld (c_src),hl
        ld hl,c_r
        inc (hl)
        pop bc
        djnz 2B
        ret

; rlight: (c_lrows) rows of the 2-byte bolt (from row (c_loff) of its picture) OR'ed at byte column in_lcol,
; starting (max(mrows - 8, 0) + lrows) rows above row (c_r); rows outside the view are skipped
rlight:
        ld a,(c_mrows)
        sub 8
        jr nc,1F
        xor a
1:      ld hl,c_lrows
        add a,(hl)
        ld e,a
        rla
        sbc a,a
        ld d,a                          ; DE = s8(a)
        ld a,(c_r)
        ld l,a
        ld h,0
        or a
        sbc hl,de
        ld (c_lr),hl
        ld a,(c_loff)
        ld l,a
        ld h,0
        add hl,hl
        ld de,lgfx
        add hl,de
        ld (c_src),hl
        ld a,(c_lrows)
        ld b,a
2:      push bc
        ld hl,(c_lr)
        ld a,h
        or a
        jr nz,4F
        ld a,l
        cp 113
        jr nc,4F
        call l2row
        ld a,(in_lcol)
        add a,a
        add a,a
        add a,a
        add a,l
        ld e,a
        ld d,h                          ; DE = pixel 8 * column
        ld hl,(c_src)
        ld b,2
5:      ld c,(hl)
        inc hl
        push bc
        ld b,8
6:      sla c
        jr nc,7F
        ld a,67
        ld (de),a
7:      inc e
        djnz 6B
        pop bc
        djnz 5B
4:      ld hl,(c_src)
        inc hl
        inc hl
        ld (c_src),hl
        ld hl,(c_lr)
        inc hl
        ld (c_lr),hl
        pop bc
        djnz 2B
        ret

; raster: the sorted list (list / nrec / nfull from render_geom) drawn as 0x9EA3 does: a full-screen record ->
; from the last one, no clear; else the clear, then every record
raster:
        ld a,(in_l2page)
        inc a
        ld (l2pg),a
        ld a,255
        ld (l2cur),a
        ld a,(nrec)
        ld b,a
        ld hl,list
        ld a,(nfull)
        or a
        jr z,.clr
        ld c,a
        ld a,b
        or a
        ret z
1:      push hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        ex de,hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc de
        ld a,(de)
        pop hl
        and 0x80
        jr z,2F
        dec c
        jr z,.draw
2:      inc hl
        inc hl
        djnz 1B
        ret
.clr:   push bc
        push hl
        call rclear
        pop hl
        pop bc
.draw:  ld a,b
        or a
        ret z
3:      push bc
        push hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        ex de,hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        ex de,hl                        ; HL = record
        inc hl
        ld a,(hl)
        inc hl
        and 127
        jr z,5F
        ld b,a
4:      push bc
        ld a,(hl)
        inc hl
        call rface
        pop bc
        djnz 4B
5:      pop hl
        inc hl
        inc hl
        pop bc
        djnz 3B
        ret

render:                                 ; geometry + raster
        call render_geom
        jp raster

; ---- unit-test entries (m1_unit.py) ----
t_xform:                                ; tpoint -> tvert
        ld iy,tpoint
        ld ix,tvert
        jp xform
t_outc:
        ld ix,tvert
        call outc
        ld (tres),a
        ret
t_proj:
        ld ix,tvert
        call proj
        ld (tres),bc
        ret
t_bbox:                                 ; IX = record address (set by the harness)
        jp bbox
t_secull:
        call secull
        ld a,0
        rla
        ld (tres),a
        ret
t_faces:                                ; vtx / nv / f_* / cols set by the harness -> tres = 1 if a record
        ld hl,outbuf
        ld (outp),hl
        call allcodes
        call faces
        ld a,0
        rla
        ld (tres),a
        ret
t_clip:                                 ; clp / cc0 / cc1 set -> tres = 1 if rejected
        call clipedge
        ld a,0
        rla
        ld (tres),a
        ret
t_facing:                               ; vtx, ctmpl, f_refs set -> tres = facing, tres+1 = cover
        ld a,1
        ld (f_cover),a
        call facing
        ld (tres),a
        ld a,(f_cover)
        ld (tres+1),a
        ret

code_end:
        SAVEBIN "cm12_cmr.bin",0x0000,code_end
        DISPLAY "code bytes: ",/D,code_end

; ==== work RAM =================================================================================================
        ORG 0x4000
in_cam:   ds 6                          ; camera x, y, z (27309 / 27311 / 27313)
in_yaw:   ds 1                          ; 27319
in_pitch: ds 1                          ; 27318
in_cull:  ds 1                          ; (27325): 0 = sector limits on
in_alist: ds 2                          ; (29494)
in_acnt:  ds 1                          ; (29496)
in_glist: ds 2                          ; (27345)
in_gcnt:  ds 1                          ; (27344)
tmpl:     ds 334                        ; 27486-27819: edge templates and face lists (copied at init)
sincos:   ds 146                        ; 29337: sin, cos per 5-degree step (copied at init)
mat:      ds 9
ymat:     ds 9
pmat:     ds 9
ytmp:     ds 9
m3out:    ds 2
bounds:   ds 6
sm_x:     ds 2
sm_y:     ds 2
dv_sign:  ds 1
box:      ds 28                         ; 6 box words, then the pyramid's inset sums (vals 6-13)
side:     ds 1
tpoint:   ds 6
tvert:    ds 6
tres:     ds 2
tp:       ds 6
av:       ds 18
vtx:      ds 48
codes:    ds 8
cols:     ds 8
nv:       ds 1
b_type:   ds 1
b_start:  ds 2
py_src:   ds 2
r_u:      ds 2
r_v:      ds 2
pfl:      ds 9
f_tmpl:   ds 2
f_back:   ds 2
f_fl:     ds 2
f_mode:   ds 1
f_cb:     ds 1
f_id:     ds 1
f_clip:   ds 1
f_cnt:    ds 1
f_idx:    ds 1
f_left:   ds 1
f_ptr:    ds 2
f_n:      ds 1
f_nn:     ds 1
f_refs:   ds 2
f_col:    ds 1
f_cover:  ds 1
f_want:   ds 1
f_r:      ds 1
ctmpl:    ds 2
wp:       ds 2
fp:       ds 2
pp:       ds 2
np:       ds 1
cl_p1:    ds 2
estate:   ds 16
epts:     ds 64
eg_e:     ds 1
eg_a:     ds 1
eg_b:     ds 1
cc0:      ds 1
cc1:      ds 1
clp:      ds 12
cl_d:     ds 2
cl_t:     ds 2
cl_n1:    ds 2
cl_n2:    ds 2
cl_dv:    ds 2
fc_p1:    ds 1
fc_p2:    ds 1
fc_p3:    ds 1
fc_d1:    ds 6
fc_d3:    ds 6
fc_n:     ds 12
mac_v:    ds 2
wd_s:     ds 1
          ALIGN 8
acc48:    ds 8
s_passes: ds 1
s_swapped: ds 1
s_gen:    ds 1
nrec:     ds 1
nfull:    ds 1
outp:     ds 2
entp:     ds 2
listp:    ds 2
list:     ds 2*160
          ALIGN 256
entries:  ds 16*160
s_mat:    ds 1024                       ; (entries + 2560 = a page start)
outbuf:   ds 6144
; raster
in_l2page: ds 1                         ; 8K page of Layer 2 line 0 (the bank being drawn)
in_sky:   ds 1                          ; (27402): sky / ground pattern nibbles, 0 = no clear
in_mount: ds 1                          ; (27343): 1 = mountain panorama
in_lflag: ds 1                          ; (27391): 0 = lightning
in_lcol:  ds 1                          ; bolt byte column 0..19 (the game's (41970), from R)
pano:     ds 288                        ; 30660: panorama, 18 rows x 16 bytes (copied at init)
lgfx:     ds 688                        ; 31085: bolt, 2 bytes a row (copied at init)
l2pg:     ds 1                          ; page of view row 0 (= line 32)
l2cur:    ds 1                          ; page in slot 4 (must follow l2pg)
r_row:    ds 1
r_y:      ds 1
r_n:      ds 1
r_cnt:    ds 1
r_fl:     ds 1
r_b:      ds 1
r_step:   ds 1
r_xl:     ds 2
r_xr:     ds 2
r_sl:     ds 2
r_sr:     ds 2
r_q:      ds 2
r_lp:     ds 2
r_rp:     ds 2
r_sp:     ds 2
r_jp:     ds 3                          ; JP into the PUSH run (code is read-only)
r_p8:     ds 1
r_patp:   ds 2                          ; must precede r_pts: the min / max path can read (r_pts - 2), as 29664
r_pts:    ds 60
          ALIGN 64
rtile:    ds 32
c_mrows:  ds 1                          ; 41964
c_moff:   ds 1                          ; 41965
c_lrows:  ds 1                          ; 41966
c_loff:   ds 1                          ; 41967
c_hi:     ds 1                          ; 41968
c_lo:     ds 1                          ; 41969
c_d:      ds 1
c_a:      ds 1
c_r:      ds 1
c_src:    ds 2
c_lr:     ds 2
cur54:    ds 1                          ; page in MMU slot 4 while the renderer runs (written before the NEXTREG)
cur55:    ds 1                          ; the same for slot 5
ram_end:
          ASSERT ram_end <= 0x7F00
        IFDEF M3
        INCLUDE "cm12_glue.asm"
        ELSE
        IFDEF M2
        INCLUDE "cm2_glue.asm"
        ENDIF
        ENDIF
