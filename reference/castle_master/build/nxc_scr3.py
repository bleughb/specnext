p='C:/1NEXT/nxc/firmware/nexclash.asm'
s=open(p,encoding='utf-8',newline='').read()
cr=chr(13)+chr(10) in s
if cr: s=s.replace(chr(13)+chr(10),chr(10))
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:60])
    s=s.replace(a,b)
rep("""nexclash_chosen:
        call    scr_first
""","""nexclash_chosen:
""")
i=s.index("; INF1's build_screen: from ENTER the screen is black"); j=s.index("; The Bth bank in .nex order into cur_bank, and A. Keeps BC.")
s=s[:i]+"""; INF1's build_screen: the menu stays up, saying Patching..., until bank 5, the first, is in
; WORK, sets and all: its first 6912 bytes are the build's own screen, shown from then on, with
; Patching and a dot for each bank made along its last line. BASIC's CLS before .nexload then
; clears to black.
scr_bank:
        ld      a,(scr_show)
        or      a
        ret     z
        ld      a,(cur_bank)
        cp      5
        jr      nz,.dot
        xor     a
        out     ($fe),a
        ld      a,7                         ; ATTR_P and BORDCR: white on black
        ld      ($5c8d),a
        ld      ($5c48),a
        ld      (scr_show),a                ; and the screen is up
        ld      hl,WORK
        ld      de,$4000
        ld      bc,6912
        ldir
.dot:   ld      a,(scr_show)
        cp      7
        ret     nz
        ld      hl,scr_dots
        ld      a,(hl)
        cp      24
        jr      nc,.say
        inc     (hl)
.say:   ld      ix,scr_say
        jp      big_call

"""+s[j:]
rep("""s_patching:     db "Patching...            ",0
""","""s_patching:     db "Patching...            ",0
; build_screen: Patching and a dot for each bank so far, on the last line of the build's screen.
scr_say:
        ld      a,23
        ld      c,0
        call    at
        ld      a,$47
        ld      (MV_ATTR),a
        ld      hl,s_patching
        ld      b,8
        call    puts_max
        ld      a,(scr_dots)
        ld      b,a
.dot:   ld      a,'.'
        call    putc
        djnz    .dot
        ret
""")
if cr: s=s.replace(chr(10),chr(13)+chr(10))
open(p,'w',encoding='utf-8',newline='').write(s)
