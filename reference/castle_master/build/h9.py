p='cm9_glue.asm'
s=open(p,encoding='latin-1').read()
def rep(a,b,n=1):
    global s
    assert s.count(a)==n,(a,s.count(a))
    s=s.replace(a,b)
# work RAM
rep("ov_lumt:  ds 256", "dis_n:    ds 1                          ; the colour dissolve: passes left (4-1), this pass's table row x 4\ndis_t:    ds 1\nov_lumt:  ds 256")
# final: the dissolve's view is drawn but not shown yet
rep("        call waittgt\n3:      call ov_sightc", "        call waittgt\n        ld a,(m_pc)                     ; 2 = the dissolve brings this view on (m3_dshow): no flip yet\n        cp 2\n        jp z,m3_end\nm3_fl3: call ov_sightc")
# m3_pshow entry label
rep("1:      ld a,1\n        ld (m_pc),a\n        xor a\n        ld (tw_n),a", "1:      ld a,1\n        ld (m_pc),a\nm3_pgo: xor a\n        ld (tw_n),a")
new_r='''; m3_dshow (h_off1, (0x7349) = 1: the view goes on by the dissolve): the final view drawn in the hidden bank at the
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

'''
rep("; ov_pstep: a portcullis step over the view in colour", new_r+"; ov_pstep: a portcullis step over the view in colour")
i=s.index('h_off1: pop af'); j=s.index('h_flip:',i)
s=s[:i]+'''h_off1: pop af                          ; (0x7349) = 1: this view goes to the screen by the dissolve 0xB66E (0x9F35;
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
'''+s[j:]
rep("h_diss: nextreg 0x69,0\n        nextreg 0x15,0\n        push ix", '''h_diss: push af
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
        push ix''')
open(p,'w',encoding='latin-1').write(s)
