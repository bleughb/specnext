p='C:/1NEXT/nxc/firmware/nexclash.asm'
s=open(p,encoding='utf-8',newline='').read()
cr=chr(13)+chr(10) in s
if cr: s=s.replace(chr(13)+chr(10),chr(10))
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:60])
    s=s.replace(a,b)
rep("vars            equ $3A25\n","vars            equ $3A21\n")
rep("        VAR     scr_show, 1                 ; INF1's build_screen: bank 5's screen while the .nex is built\n","        VAR     scr_show, 1                 ; INF1's build_screen: the game file's own screen from ENTER\n        VAR     scr_at, 4                   ; where it is in the game file\n")
rep("""        ld      de,key_build_screen
        call    text_find
        ret     c
        ld      a,1
        ld      (scr_show),a
        ret
""","""        ld      de,key_build_screen
        call    text_find
        ret     c
        ld      de,0                        ; its value: decimal, below 65536
.dig:   ld      a,b
        or      c
        jr      z,.got
        ld      a,(hl)
        sub     '0'
        cp      10
        jr      nc,.got
        push    hl
        ld      h,d
        ld      l,e
        add     hl,hl
        add     hl,hl
        add     hl,de
        add     hl,hl
        ld      e,a
        ld      d,0
        add     hl,de
        ex      de,hl
        pop     hl
        inc     hl
        dec     bc
        jr      .dig
.got:   ld      (scr_at),de
        ld      a,1
        ld      (scr_show),a
        ret
""")
rep("""nexclash_chosen:
""","""nexclash_chosen:
        call    scr_first
""")
i=s.index("; INF1's build_screen: the menu stays up"); j=s.index(".say:   ld      a,NR_MMU5")
s=s[:i]+"""; INF1's build_screen: a screen the player's own game file holds as it is, 6912 bytes at the
; offset given, such as a tape's SCREEN$ block. It is read straight to the display at ENTER,
; before the game is checked, with Patching on its last line; each bank made adds a dot.
; BASIC's CLS before .nexload then clears to black.
scr_first:
        ld      a,(scr_show)
        or      a
        ret     z
        xor     a
        out     ($fe),a
        ld      a,7                         ; ATTR_P and BORDCR: white on black
        ld      ($5c8d),a
        ld      ($5c48),a
        ld      a,(gh)
        ld      hl,scr_at
        call    seek_file
        ld      hl,$4000
        ld      bc,6912
        call    read_game
        jr      scr_bank.say
scr_bank:
        ld      a,(scr_show)
        or      a
        ret     z
        ld      hl,scr_dots
        ld      a,(hl)
        cp      24
        jr      nc,.say
        inc     (hl)
"""+s[j:]
rep("""        ld      a,(scr_dots)
        ld      b,a
.dot:   ld      a,'.'
        call    putc
        djnz    .dot
        ret
""","""        ld      a,(scr_dots)
        or      a
        ret     z
        ld      b,a
.dot:   ld      a,'.'
        call    putc
        djnz    .dot
        ret
""")
rep("; build_screen: Patching and a dot for each bank so far, on the last line of the build's screen.","; build_screen: Patching and a dot for each bank so far, on the last line of the game's screen.")
if cr: s=s.replace(chr(10),chr(13)+chr(10))
open(p,'w',encoding='utf-8',newline='').write(s)
p='C:/1NEXT/nxc/tools/nxc.py'
s=open(p,encoding='utf-8',newline='').read()
i=s.index("    elif key == 'build_screen'"); j=s.index(chr(10),i)
s=s[:i]+"    elif key == 'build_screen' and not (value.isdigit() and len(value) <= 5 and int(value) < 65536): raise Wrong('build_screen is the offset in the game file of a 6912-byte screen, 0 to 65535')"+s[j:]
open(p,'w',encoding='utf-8',newline='').write(s)
