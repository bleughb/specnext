; R-Type prototype (2026-11-15): scenery on a hardware-scrolled Layer 2.
; The original game runs unchanged and visible on the ULA (figures, stars, HUD);
; only the scenery pixels move to Layer 2. No pace machinery: the main loop runs
; at 28MHz and the native three-interrupt wait paces it. The native ISR (all
; beeper effects) runs at 3.5MHz with ROM in slot 0. Not an engine or deliverable.
;
; Native scenery: 8842 shifts every background span of the ULA one pixel per call
; (7A8E = 0), fed from the staged column the controller copies to hidden ULA
; column 31 (89C3, every eighth call). Here the staged column is drawn on Layer 2
; instead and its staging pixels are zeroed, so the ULA keeps no scenery and the
; native shift moves blank cells. Owner/attribute/dirty maps are untouched.
        DEVICE ZXSPECTRUMNEXT
L2BANK  EQU 9                   ; 16K bank: 8K pages 18..23
L2PAGE  EQU L2BANK*2
TRANSP  EQU 0xE3
        IFDEF L2_SPR_BEHIND
LORDER  EQU 0x44                ; NR 0x15: Layer 2 over sprites over ULA, sprite 0 on top
        ELSE
LORDER  EQU 0x40                ; NR 0x15: sprites over Layer 2 over ULA, sprite 0 on top
        ENDIF
        ; Outside play (titles, high scores, name entry, continue) the game runs at
        ; its own 3.5MHz: those screens time themselves with busy loops.
        MACRO L2_OFF
        nextreg 0x69,0
        xor a
        ld (run_fast),a
        nextreg 7,0
        IFDEF L2_SPRITES
        nextreg 0x15,LORDER     ; sprites hidden
        xor a
        ld (spr_on),a
        ENDIF
        ENDM
        ORG 0x2000
hook_setup:
        ; The game reads Kempston only on port 1F. NextZXOS may leave either
        ; connector in another mode, so make both Kempston 1; keep 50/60Hz and
        ; the scandoubler bit. (l2_off_title clears the game's "no Kempston"
        ; flag 7A8B at every title.)
        push af
        push bc
        ld bc,0x243B
        ld a,5
        out (c),a
        inc b
        in a,(c)
        and 0x05
        or 0x50                 ; mode 001 (Kempston 1) on both connectors
        nextreg 5,a
        pop bc
        pop af
        IFDEF L2_NOTAPE
        call spec_hold
        ENDIF
        nextreg 0x12,L2BANK
        nextreg 0x14,TRANSP
        nextreg 0x70,0          ; 256x192, 8bpp
        nextreg 0x69,0          ; Layer 2 off until a level is drawn
        nextreg 0x16,0
        nextreg 0x17,0
        nextreg 0x1C,1          ; reset Layer 2 clip index
        nextreg 0x18,8          ; visible columns 1..30, rows 0..19
        nextreg 0x18,247
        nextreg 0x18,0
        nextreg 0x18,159
        IFDEF L2_SPRITES
        call spr_setup
        ENDIF
        ret

; ---- ISR wrapper: BE26 replaces PUSH IX / PUSH IY / PUSH HL -------------------
irq_in: push ix
        push iy
        push hl
        nextreg 0x50,0xFF       ; the noise effect reads ROM bytes
        nextreg 7,0
        jp 0xBE2B
; BE52 replaces POP AF / EX AF,AF' / POP HL.
irq_out:
        IFDEF L2_GLIDE
        call glide_irq
        ENDIF
        ld a,(cur_mmu0)
        nextreg 0x50,a
        ld a,(run_fast)
        nextreg 7,a
        pop af
        ex af,af'
        pop hl
        jp 0xBE55

; ---- 8F40 replaces DI / LD BC,7FFD: a level's data is unpacked with interrupts off (several
; seconds at 3.5MHz, hidden on tape by the loading screen's logo). Run it at 28MHz; the first
; interrupt after it (EI at 5C4C) puts the speed back (irq_out: run_fast).
unpack_fast:
        nextreg 7,3
        di
        ld bc,0x7FFD
        jp 0x8F44

; ---- 863D replaces CALL 73D8: life/level restart, Layer 2 off -----------------
l2_off: L2_OFF
        jp 0x73D8
; 8BE8 replaces LD HL,5800: continue screen. FE03 replaces CALL 73C2: title
; and between-level screens. Both clear the ULA; Layer 2 must not stay over them.
l2_off_continue:
        L2_OFF
        ld hl,0x5800
        jp 0x8BEB
l2_off_title:
        L2_OFF
        IFDEF L2_SPRITES
        call spr_start          ; title figures (logo, TM) as sprites too; Layer 2 stays off
        ENDIF
        xor a                   ; 7A8B: the game's start-up Kempston test (73EC),
        ld (0x7A8B),a           ; "absent" in the snapshot. Port 1F is real here.
        ; L2_NOTAPE builds patch the prompts out of FE03 itself (l2scroll.py
        ; NOTAPE): its level load pages 7FFD, which maps ROM over this hook page,
        ; so the load must return into the game's own code.
        call 0x73C2
        jp 0xFE06

; 92E8 replaces LD DE,71C9: game over, high-score check and name entry.
l2_off_scores:
        L2_OFF
        ld de,0x71C9
        jp 0x92EB

        IFDEF L2_NOTAPE
; Full build start: keep the R-TYPE technical specification (the snapshot's
; screen) up for five seconds or until a key or fire, then let it go.
spec_hold:
        push af
        push bc
        push de
        ld e,250
.f:     call .frame
        xor a
        in a,(0xFE)
        cpl
        and 0x1F
        jr nz,.key
        in a,(0x1F)
        inc a
        jr z,.n                 ; FF: no Kempston interface answering
        dec a
        and 0x1F
        jr nz,.key
.n:     dec e
        jr nz,.f
        jr .out
.key:   call .frame             ; wait for release so the game does not see it
        xor a
        in a,(0xFE)
        cpl
        and 0x1F
        jr nz,.key
        in a,(0x1F)
        inc a
        jr z,.out
        dec a
        and 0x1F
        jr nz,.key
.out:   pop de
        pop bc
        pop af
        ret
.frame: ld bc,0x243B            ; one frame: wait for line 192, then for line 0
.w1:    ld a,0x1F
        out (c),a
        inc b
        in a,(c)
        dec b
        cp 192
        jr nz,.w1
.w2:    ld a,0x1F
        out (c),a
        inc b
        in a,(c)
        dec b
        cp 1
        jr nz,.w2
        ret
        ENDIF

; ---- 8842 replaces LD IX,8080: one pixel per scrolling copier call ------------
l2_scroll:
        IFNDEF L2_NOLAZY
        ld a,(l2_ready)
        or a
        call z,l2_convert       ; test builds started from a mid-level snapshot
        ENDIF
        call l2_sync
        ld a,(0x7A8E)
        or a
        jr nz,.no
        ld a,(l2_s)
        inc a
        ld (l2_s),a
        nextreg 0x16,a
.no:
        IFDEF L2_SPRITES
        IFDEF L2_GLIDE
        call glide_publish
        ELSE
        call spr_publish
        ENDIF
        ENDIF
        ld ix,0x8080
        jp 0x8846

; Scroll and sprites change together while the raster is below the play area
; (video line 160 or later). A copier call normally starts just after the frame
; interrupt, so this only waits after an update that overran.
l2_sync:
        ld bc,0x243B
.w:     ld a,0x1E
        out (c),a
        inc b
        in a,(c)
        dec b
        and 1
        ret nz
        ld a,0x1F
        out (c),a
        inc b
        in a,(c)
        dec b
        cp 160
        jr c,.w
        ret

; ---- 89C3 replaces LD HL,5E00: the new column goes to Layer 2 -----------------
l2_stage:
        ld a,0x2C               ; INC L: staging bytes are consecutive
        ld (src_step),a
        ld a,(l2_s)
        add a,248               ; hidden screen column 31
        ld (.x+1),a
        ld hl,0x5E00
        ld b,0
.row:   push bc
        push hl
        ld a,l
        add a,8
        ld l,a
        ld a,(hl)               ; staged attribute; bit 7 = scenery
        pop hl
        push hl
        bit 7,a
        ld e,0
        jr nz,.bg
        ld hl,zero8             ; not scenery: clear the Layer 2 cell
        xor a
        ld e,TRANSP
.bg:    push af
        ld a,e
        ld (pc_blk),a
        pop af
.x:     ld c,0
        call put_cell
        pop hl
        pop bc
        ld de,9
        add hl,de
        inc b
        ld a,b
        cp 20
        jr nz,.row
        ld hl,0x5E00
        jp 0x89C6

; ---- 8734 replaces CALL FEEB: move the freshly drawn scenery to Layer 2 -------
l2_init:
        call 0xFEEB
l2_convert:
        push af
        push bc
        push de
        push hl
        nextreg 0x69,0
        ld a,L2PAGE
.fill:  ld (cur_mmu0),a
        nextreg 0x50,a
        ld hl,0
        ld de,1
        ld bc,0x1FFF
        ld (hl),TRANSP
        ldir
        inc a
        cp L2PAGE+6
        jr nz,.fill
        ld a,0xFF
        ld (cur_mmu0),a
        nextreg 0x50,0xFF
        xor a
        ld (l2_s),a
        nextreg 0x16,0
        ld a,0x24               ; INC H: down a ULA character cell
        ld (src_step),a
        xor a
        ld (pc_blk),a
        ld b,0
.row:   ld c,0
.col:   ld l,b
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,l
        or c
        ld l,a                  ; HL = row*32+col
        push hl
        ld de,0x7E00
        add hl,de
        ld a,(hl)
        pop hl
        inc a
        jr nz,.next             ; only owner FF is scenery
        push bc
        ld de,0x7800
        add hl,de
        ld a,(hl)
        push af
        ld a,b
        and 0x18
        or 0x40
        ld h,a
        ld a,b
        and 7
        rrca
        rrca
        rrca
        or c
        ld l,a                  ; HL = ULA cell
        ld a,c
        add a,a
        add a,a
        add a,a
        ld c,a
        pop af
        call put_cell
        pop bc
.next:  inc c
        ld a,c
        cp 32
        jr nz,.col
        inc b
        ld a,b
        cp 20
        jr nz,.row
        IFNDEF L2_HIDE
        nextreg 0x69,0x80
        ENDIF
        ld a,3                  ; play runs at 28MHz (the ISR stays 3.5MHz)
        ld (run_fast),a
        nextreg 7,3
        ld a,1
        ld (l2_ready),a
        IFDEF L2_SPRITES
        call spr_start
        ENDIF
        pop hl
        pop de
        pop bc
        pop af
        ret

; ---- one 8x8 cell: HL = source bytes (zeroed), A = attribute, B = row, C = x --
put_cell:
        push hl
        ld e,a
        and 7
        ld d,a
        ld a,e
        and 0x40
        rrca
        rrca
        rrca                    ; 8 when bright
        ld (.br+1),a
        or d
        ld hl,col_tab
        add hl,a
        ld a,(hl)
        ld (pc_ink+1),a
        ld a,e
        rrca
        rrca
        rrca
        and 7
        jr z,.clear             ; black paper: see pc_blk
.br:    or 0
        ld hl,col_tab
        add hl,a
        ld a,(hl)
        jr .pp
.clear: ld a,(pc_blk)
.pp:    ld (pc_pap+1),a
        ld a,b
        rrca
        rrca
        and 7
        add a,L2PAGE
        ld (cur_mmu0),a         ; variable first: the ISR restores from it
        nextreg 0x50,a
        ld a,b
        and 3
        add a,a
        add a,a
        add a,a
        ld d,a
        ld e,c
        pop hl
        ld b,8
pc_line:  ld a,(hl)
        IFNDEF L2_KEEP_ULA
        ld (hl),0
        ENDIF
        push bc
        ld c,a
        ld b,8
pc_px:    sla c
        jr c,pc_ink
pc_pap: ld a,0
        jr pc_put
pc_ink: ld a,0
pc_put:   ld (de),a
        inc e
        djnz pc_px
        pop bc
        ld a,e
        sub 8
        ld e,a
        inc d
src_step:
        inc h
        djnz pc_line
        ld a,0xFF
        ld (cur_mmu0),a
        nextreg 0x50,0xFF
        ret

; RRRGGGBB for the eight normal then the eight bright Spectrum colours.
col_tab: db 0x00,0x02,0xA0,0xA2,0x14,0x16,0xB4,0xB6
        db 0x00,0x03,0xE0,0xE7,0x1C,0x1F,0xFC,0xFF
l2_s:   db 0
run_fast: db 0
; Black paper of a scenery cell is opaque: in the original a figure never draws
; into a cell the scenery owns (8EC2), so scenery hides any figure behind it.
; Cleared cells stay transparent.
pc_blk: db 0
l2_ready: db 0
cur_mmu0: db 0xFF
        ALIGN 16
zero8:  ds 8
        IFDEF L2_SPRITES
        INCLUDE "l2sprites_body.asm"
        ENDIF
        ASSERT $ < 0x3E00
        IFNDEF L2_SPRITES
        SAVEBIN "l2scroll_code.bin",hook_setup,$-hook_setup
        ENDIF
