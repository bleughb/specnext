s=open('cm8_glue.asm',encoding='latin-1').read()
i=s.index('h_off1: pop af'); j=s.index('h_flip:',i)
new='''h_off1: pop af                          ; (0x7349) = 1: this view goes to the screen by the dissolve 0xB66E (0x9F35;
        call ov_capw                    ; the drawbridge, a new area). As the portcullis at BEGIN: the view on
        call r_enter                    ; Layer 2 at the original's time, Layer 2 and the sprites off while the
        call m3_pshow                   ; dissolve runs (the original's look, 3.5 MHz), then on again in the
        call r_leave                    ; area's colours as 0xB347 left them (hardware 2026-11-22: the castle
        nextreg 0x69,0                  ; stayed in the original's look until the next move)
        nextreg 0x15,0
        call 0x9F19
h_dshow:
        push af
        ld a,(m_pc)
        cp 1
        jr nz,1F
        xor a
        ld (m_pc),a
        call r_enter
        call ov_pstep
        call r_leave
        nextreg 0x69,0x80
        nextreg 0x15,1
1:      pop af
        ret
'''
s=s[:i]+new+s[j:]
open('cm8_glue.asm','w',encoding='latin-1').write(s)
