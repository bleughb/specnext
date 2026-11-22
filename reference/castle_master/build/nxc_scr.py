p='C:/1NEXT/nxc/firmware/nexclash.asm'
s=open(p,encoding='utf-8',newline='').read()
crlf='\r\n' in s
if crlf: s=s.replace('\r\n','\n')
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a)
    s=s.replace(a,b)
rep("vars            equ $3A27\n","vars            equ $3A25\n")
rep("        VAR     scr_now, 1\n","        VAR     scr_now, 1\n        VAR     scr_show, 1                 ; INF1's build_screen: bank 5's screen while the .nex is built\n        VAR     scr_dots, 1                 ; and a dot for each bank so far\n")
rep("""        ld      a,COLOURS_LABEL_MAX
        ret     c
        jp      copy_text
""","""        ld      a,COLOURS_LABEL_MAX
        call    nc,copy_text
        ld      de,key_build_screen
        call    text_find
        ret     c
        ld      a,1
        ld      (scr_show),a
        ret
""")
rep('key_colours_label: db "colours_label=",0\n','key_colours_label: db "colours_label=",0\nkey_build_screen: db "build_screen=",0\n')
rep("""nexclash_chosen:
        call    work_begin
""","""nexclash_chosen:
        call    scr_first
        call    work_begin
""")
rep(""".emit:  ld      a,1
        call    bank_sets
""",""".emit:  ld      a,1
        call    bank_sets
        call    scr_bank
""")
rep("""; The Bth bank in .nex order into cur_bank, and A. Keeps BC.
order_bank:""","""; INF1's build_screen: from ENTER the screen is black, with a row of dots along its last
; line, one more for each bank made; bank 5, the first, is the build's own screen, shown as
; soon as it is in WORK, sets and all. BASIC's CLS before .nexload then clears to black.
scr_first:
        ld      a,(scr_show)
        or      a
        ret     z
        xor     a
        out     ($fe),a
        ld      a,7                         ; ATTR_P and BORDCR: white on black
        ld      ($5c8d),a
        ld      ($5c48),a
        ld      hl,$4000
        ld      de,$4001
        ld      bc,6911
        ld      (hl),l
        ldir
        jr      scr_dot
scr_bank:
        ld      a,(scr_show)
        or      a
        ret     z
        ld      a,(cur_bank)
        cp      5
        jr      nz,scr_dot
        ld      hl,WORK
        ld      de,$4000
        ld      bc,6912
        ldir
scr_dot:
        ld      hl,scr_dots
        ld      a,(hl)
        cp      30
        jr      nc,.all
        inc     (hl)
.all:   ld      b,(hl)
        ld      hl,$5ae1                    ; the last line's cells, from the second
.next:  ld      (hl),$47
        push    hl
        ld      h,$50
.cell:  ld      (hl),0
        inc     h
        bit     3,h
        jr      z,.cell
        ld      h,$53
        ld      (hl),$18
        inc     h
        ld      (hl),$18
        pop     hl
        inc     l
        djnz    .next
        ret

; The Bth bank in .nex order into cur_bank, and A. Keeps BC.
order_bank:""")
if crlf: s=s.replace('\n','\r\n')
open(p,'w',encoding='utf-8',newline='').write(s)
