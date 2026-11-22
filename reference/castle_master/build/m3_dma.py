"""Castle Master: the view copy by DMA. Builds prefix cm4 from the cm3 sources + the changes below (cm3 itself
is not touched: tests may be running on it). Usage: python m3_dma.py"""
from m2_lib import W, assemble

T = '        '
NL = chr(10)


def L(*lines):
    return ''.join((x if x.endswith(':') or x[:1] in '.123;' or ':' in x.split(' ')[0] else T + x) + NL for x in lines)


OLD_LOOP = L('2:      ld hl,0xA020', 'ld de,0x8020', '3:      ld bc,192', 'ldir', 'add hl,64', 'add de,64', 'dec a',
             'jr nz,3B', 'pop bc')
NEW_LOOP = L('2:      ld hl,0xA020', 'ld de,0x8020', 'rrca', 'rrca', 'rrca                            ; chunks of 8 rows',
             '3:      push af', 'call l2chunk', 'add hl,0x0800', 'add de,0x0800', 'pop af', 'dec a', 'jr nz,3B', 'pop bc')
ROUTINES = L(
    '; l2chunk: 8 view rows (7 x 256 + 192 bytes: the columns between the rows are the same in every bank, never',
    '; drawn) from HL to DE, both kept. By DMA (0.18 us a byte at 28 MHz against LDIR\'s 0.86: TECHNIQUES 1.0) unless',
    '; the core is older than 3.00, hardware IM 2 is on, or the frame interrupt may fall inside the transfer: the',
    '; CPU cannot see its pulse while the DMA holds the bus. The line\'s low byte 238-255 or 0-3 = the interrupt\'s',
    '; lines (248 VGA, 256 HDMI at 50 Hz) and the chunk\'s 6 lines before them: those chunks go by LDIR.',
    'l2chunk:',
    'push hl', 'push de', 'ld a,(dma_st)', 'or a', 'call z,dma_det', 'dec a',
    'jr z,.cpu                       ; 1 = CPU only',
    'ld (dma_pk+3),hl', 'ld (dma_pk+10),de',
    'HLIB_IFF_DI                     ; the handler\'s clock selects registers on the same port',
    'push af', 'ld bc,0x243B', 'ld a,0x1F', 'out (c),a', 'inc b', 'in a,(c)', 'ld c,a', 'pop af', 'HLIB_IFF_EI',
    'ld a,c', 'add a,18', 'cp 22', 'jr c,.cpu',
    'ld hl,dma_pk', 'ld bc,15*256+0x6B', 'otir', 'pop de', 'pop hl', 'ret',
    '.cpu:   ld a,8', '1:      ld bc,192', 'ldir', 'add hl,64', 'add de,64', 'dec a', 'jr nz,1B', 'pop de', 'pop hl', 'ret',
    '; dma_det: the first use. A = dma_st = 2 (DMA) or 1 (CPU); the program\'s fixed bytes to work RAM',
    'dma_det:',
    'push hl', 'push de', 'ld hl,dma_pk0', 'ld de,dma_pk', 'ld bc,15', 'ldir',
    'HLIB_IFF_DI', 'push af', 'ld bc,0x243B', 'ld a,0x01', 'out (c),a', 'inc b', 'in a,(c)',
    'ld d,a                          ; core version, major << 4 | minor', 'dec b', 'ld a,0xC0', 'out (c),a', 'inc b',
    'in a,(c)', 'ld e,a', 'pop af', 'HLIB_IFF_EI',
    'ld a,d', 'inc a', 'jr z,.no', 'dec a', 'cp 0x30', 'jr c,.no', 'bit 0,e', 'jr nz,.no', 'ld a,2', 'jr .set',
    '.no:    ld a,1', '.set:   ld (dma_st),a', 'pop de', 'pop hl', 'ret',
    'dma_pk0:',
    'db 0x83,0xC3,0x7D               ; disable, reset, WR0: A -> B, address + length follow',
    'dw 0,7*256+192',
    'db 0x14,0x10,0xAD               ; both memory, incrementing; continuous, B\'s address follows',
    'dw 0',
    'db 0x82,0xCF,0x87               ; stop at the end, load, enable',
    '')
SETPAL = NL + '; setpal: Layer 2 palette.'
RAM_OLD = 'ov_lc:    ds 1' + NL
RAM_NEW = RAM_OLD + 'dma_st:   ds 1                          ; 0 not looked at yet, 1 CPU copies, 2 DMA' + NL \
    + 'dma_pk:   ds 15                         ; the DMA program (source at +3, destination at +10)' + NL


def patched(src):
    for a, b in ((OLD_LOOP, NEW_LOOP), (SETPAL, NL + ROUTINES.rstrip(NL) + NL + SETPAL), (RAM_OLD, RAM_NEW)):
        assert src.count(a) == 1, (src.count(a), a)
        src = src.replace(a, b)
    return src


def main(nm='cm4'):
    glue = patched(open(W + 'cm3_glue.asm').read())
    open(W + nm + '_glue.asm', 'w').write(glue.replace('SAVEBIN "cm3_', 'SAVEBIN "%s_' % nm))
    open(W + nm + '_cmr.asm', 'w').write(open(W + 'cmr.asm').read().replace('INCLUDE "cm3_glue.asm"', 'INCLUDE "%s_glue.asm"' % nm)
                                         .replace('SAVEBIN "cmr.bin"', 'SAVEBIN "%s_cmr.bin"' % nm))
    open(W + nm + '.asm', 'w').write('        DEFINE M2\n        DEFINE M3\n        INCLUDE "%s_cmr.asm"\n' % nm)
    print(assemble(nm)[-300:])


if __name__ == '__main__':
    main()
