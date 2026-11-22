"""zxnDDMA probe: does this machine / emulator run the core 3.03 extended DMA commands? Builds ddma_probe.nex:
five transfers into a 64-byte buffer, each compared with the expected bytes; results to NR 0x7F (test << 4 | 1
pass / 2 fail), to RAM at `res`, and as attribute cells (green / red) on the top row. Usage: python ddma_probe.py"""
import subprocess
from m2_lib import W, SJ

SRC = [0 if i % 4 == 1 else 0x40 + i for i in range(64)]
HEAD = lambda n: '        db 0x83,0xC3,0x7D\n        dw src,%d\n        db 0x14,0x10,0xAD\n        dw dst\n        db 0x82\n' % n
SHAPE = '        db 0xE3,%d,0,0xE7,3,0,0xEB,%d,0,0xEF,16,0\n'
TESTS = [
    ('classic copy, 16 bytes', HEAD(16), lambda d: d.__setitem__(slice(0, 16), SRC[:16])),
    ('2D fill 5 x 3', HEAD(0) + '        db 0xDF,0x0A,0xF7,0xA5\n' + SHAPE % (5, 0),
     lambda d: [d.__setitem__(r * 16 + c, 0xA5) for r in range(3) for c in range(5)]),
    ('2D copy 4 x 3, strides 8 / 16', HEAD(0) + '        db 0xDF,0x02\n' + SHAPE % (4, 8),
     lambda d: [d.__setitem__(r * 16 + c, SRC[r * 8 + c]) for r in range(3) for c in range(4)]),
    ('2D transparent copy (0 skipped)', HEAD(0) + '        db 0xDF,0x06,0xF3,0\n' + SHAPE % (4, 8),
     lambda d: [d.__setitem__(r * 16 + c, SRC[r * 8 + c]) for r in range(3) for c in range(4) if SRC[r * 8 + c]]),
    ('physical 2D fill 5 x 3 (page 4 = 0x008000)', HEAD(0) + '        db 0xDB,0,0xDF,0x0B,0xF7,0x5A\n' + SHAPE % (5, 0),
     lambda d: [d.__setitem__(r * 16 + c, 0x5A) for r in range(3) for c in range(5)]),
    ('physical 2D fill 5 x 3 (page 4 = 0x048000)', HEAD(0) + '        db 0xDB,4,0xDF,0x0B,0xF7,0x5A\n' + SHAPE % (5, 0),
     lambda d: [d.__setitem__(r * 16 + c, 0x5A) for r in range(3) for c in range(5)]),
]


def db(v):
    return ''.join('        db %s\n' % ','.join(str(x) for x in v[i:i + 16]) for i in range(0, len(v), 16))


def main():
    a = ['        DEVICE ZXSPECTRUMNEXT\n        ORG 0x8000\nstart:  di\n        ld sp,0xBF00\n        nextreg 0x07,3\n']
    data = []
    for k, (name, prog, fn) in enumerate(TESTS):
        exp = [0x11] * 64
        fn(exp)
        a.append('        ld hl,p%d\n        ld b,p%de-p%d\n        ld de,e%d\n        ld a,%d\n        call run        ; %s\n' % (k, k, k, k, k + 1, name))
        data.append('p%d:\n%s        db 0xCF,0x87\np%de:\ne%d:\n%s' % (k, prog, k, k, db(exp)))
    a.append('        nextreg 0x7F,0xEE\n1:      jr 1B\n')
    a.append('''run:    ld (tn),a
        push de
        push hl
        push bc
        ld hl,dst
        ld de,dst+1
        ld bc,63
        ld (hl),0x11
        ldir
        pop bc
        pop hl
        ld c,0x6B
        otir
        DUP 8
        nop
        EDUP
        pop de
        ld hl,dst
        ld b,64
        ld c,1
2:      ld a,(de)
        cp (hl)
        jr z,3F
        ld c,2
3:      inc hl
        inc de
        djnz 2B
        ld a,(tn)
        ld e,a
        ld d,0
        ld hl,res-1
        add hl,de
        ld (hl),c
        ld hl,0x5800-1
        add hl,de
        ld a,c
        dec a
        ld a,0x20               ; green paper
        jr z,4F
        ld a,0x10               ; red paper
4:      ld (hl),a
        ld a,(tn)
        swapnib
        or c
        nextreg 0x7F,a
        ret
tn:     db 0
res:    db 0,0,0,0,0,0
src:
''' + db(SRC) + 'dst:    ds 64\n' + ''.join(data))
    a.append('        SAVENEX OPEN "ddma_probe.nex",start,0xBF00\n        SAVENEX CORE 3,0,0\n        SAVENEX AUTO\n        SAVENEX CLOSE\n')
    open(W + 'ddma_probe.asm', 'w').write(''.join(a))
    r = subprocess.run([SJ, '--nologo', '--zxnext', '--sym=ddma_probe.sym', 'ddma_probe.asm'], cwd=W, capture_output=True, text=True)
    print((r.stdout + r.stderr)[-400:])


if __name__ == '__main__':
    main()
