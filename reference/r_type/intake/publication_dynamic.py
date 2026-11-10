"""Live ZX-to-4bpp + shadow copier + native IRQ + DMA publication gate.

Game-specific feasibility, not an installed sprite engine. Independent bitmap
oracle, active attributes, source holes/tail/HUD and row deadlines. Generated
NEX/JNS and captured game state stay under work; the private card stays outside Git.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3] / 'nexclash'
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
from asm2profile import assemble, sjasm
from nexclash import jnext as J, z80tonex as Z
from irq_capture import load

OUT = Path('/workspace/work/r_type_publication_dynamic')
OUT.mkdir(exist_ok=True)


def source(x, y):
    return 0x6000 + ((y & 192) << 5) + ((y & 7) << 8) + ((y & 56) << 2) + x


def oracle(memory, text=()):
    """Direct individual-bit renderer; deliberately no nibble table or asm layout loop."""
    pixels = [[0] * 256 for _ in range(160)]
    for y in range(160):
        for x in range(256):
            cell = (y // 8) * 32 + x // 8
            owner = memory[0x7E00 + cell]
            if not 0 < owner < 0xDC or owner in text:
                continue
            if memory[source(x // 8, y)] & (128 >> (x & 7)):
                a = memory[0x7800 + cell]
                pixels[y][x] = ((a & 7) + (8 if a & 64 else 0)) or 8
    patterns, attrs = bytearray(), bytearray()
    for y in range(0, 160, 16):
        for x in range(0, 256, 16):
            p = [pixels[yy][xx] for yy in range(y, y + 16) for xx in range(x, x + 16)]
            if not any(p):
                continue
            i = len(patterns) // 128
            patterns.extend((p[k] << 4) | p[k+1] for k in range(0, 256, 2))
            attrs.extend(((x+32)&255, y+32, (x+32)//256, 0xC0+i//2, 0x80+(i%2)*64))
    return bytes(patterns), bytes(attrs)


def run():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument('--state', type=Path, help='captured banks/registers JSON; generated in work')
    ap.add_argument('--out', type=Path, default=OUT)
    args=ap.parse_args()
    out=args.out
    out.mkdir(exist_ok=True)
    state=json.loads(args.state.read_text()) if args.state else load()
    blocks, syms = assemble(str(HERE / 'publication_dynamic.asm'), sjasm.find())
    snap = Z.Z80Snapshot(str(HERE.parent / 'Rtype.z80'))
    os.environ.setdefault('NEXCLASH_JNEXT', '/workspace/work/jnext-bin/root/usr/bin/jnext')
    variants = [('dma', 1), ('default', 2), ('missing-tail', 1), ('bad-lut', 1), ('wide-restore', 1), ('missing-clear', 1)]
    jobs, inputs = [], {}
    for name, mode in variants:
        folder = out / name
        folder.mkdir(exist_ok=True)
        banks = {i: bytearray(b) for i, b in enumerate(state['banks'])}
        memory = bytes(0x4000) + bytes(banks[5]) + bytes(banks[2]) + bytes(banks[0])
        expected, attrs = oracle(memory)
        inputs[name] = (expected, attrs, memory)
        for off, old, label in [(0x3e26, 'dde5fde5e5', 'irq_in'), (0x3e52, 'f108e1', 'irq_out')]:
            assert banks[2][off:off+len(bytes.fromhex(old))] == bytes.fromhex(old)
            banks[2][off:off+3] = b'\xc3' + Z.w16(syms[label])
        code = bytearray(blocks['code'])
        code[syms['initial_mode']+1-0x2000] = mode
        if name == 'missing-tail':
            code[syms['tail_copy']-0x2000:syms['tail_copy']-0x2000+3] = bytes(3)
        if name == 'missing-clear':
            code[syms['clear_call']-0x2000:syms['clear_call']-0x2000+3]=bytes(3)
        if name == 'wide-restore':
            code[syms['restore_pixels']+1-0x2000:syms['restore_pixels']+3-0x2000]=Z.w16(6144)
        if name == 'bad-lut':
            # Corrupt the runtime table in this very binary, not a separate oracle.
            code[syms['expand_lut']-0x2000:syms['expand_lut']-0x2000+512] = bytes(512)
        banks.update({10: bytes.fromhex('ed915118c30020'), 12: code,
                      20: bytes([0xA5])*16384, 21: bytes([0x5A])*16384, 22: bytes(16384)})
        nex = folder / 'publication.nex'
        Z.write_nex(str(nex), snap, banks)
        s = J.Script(500)
        labels = [('PREP','prepare'), ('READY','shadow_ready'), ('GEN','dynamic_patterns'),
                  ('COPY','clear_call'), ('PREPEND','prep_end'), ('TAIL','tail_begin'),
                  ('BEGIN','pstart'), ('ROW','rend'), ('END','pend'), ('IRQIN','irq_in'), ('IRQOUT','irq_out')]
        for tag, label in labels:
            s.rule('on execute %d do\n  log "%s R=${mem[14337]} C=${CYCLE}"\nend\n' % (syms[label], tag))
        s.rule('on execute %d once do\n  save_snapshot "publication.jns"\nend\n' % syms['pend'])
        s.exit_at(12)
        jobs.append((str(nex), s.text(), str(folder), 50, '/workspace/scratch/cspect-next-2gb.img',
                     '/workspace/work/r_type_jnext_home'))
    codes = J.run_all(jobs)
    assert codes == [0]*len(jobs), codes
    results = []
    offsets = {source(x,y)-0x6000 for y in range(160) for x in range(32)}
    for name, mode in variants:
        folder = out / name
        rows = J.unwrap([dict(tag=tag, **r) for tag,r in J.records(str(folder/'run.log'))])
        unique = {(r['tag'], r.get('R',0)): r for r in rows if r['tag'] not in ('IRQIN','IRQOUT')}
        events = list(unique.values()) + [r for r in rows if r['tag'] in ('IRQIN','IRQOUT')]
        t = {r['tag']:r['C'] for r in unique.values()}
        assert 'END' in t, (name, 'no completed publication')
        frame = J.Frame(str(folder/'publication.jns'))
        expected, attrs, original_memory = inputs[name]
        pattern_bad = sum(a!=b for a,b in zip(frame.patterns, expected))
        with zipfile.ZipFile(frame.path) as z:
            ram = z.read('mem/ram.bin')
            live = z.read('mem/bank5-vram.bin')
        shadow = ram[0x40000+42*8192:0x40000+43*8192]
        backup = ram[0x40000+43*8192:0x40000+44*8192]
        code_ram = ram[0x40000+24*8192:0x40000+25*8192]
        at = syms['attrs']-0x2000
        attr_bad = sum(a!=b for a,b in zip(code_ram[at:at+525], attrs+bytes(525-len(attrs))))
        tail_bad = sum(a!=b for a,b in zip(live[0x1B00:0x2000], shadow[0x1B00:0x2000]))
        assert all(live[a]==shadow[a] for a in offsets|set(range(0x1800,0x1A80))), 'ULA commit'
        fg_offsets={source(x,y)-0x6000 for y in range(160) for x in range(32)
                    if 0<original_memory[0x7E00+(y//8)*32+x]<0xDC}
        foreground_bad=sum(live[a]!=0 for a in fg_offsets)
        if name=='missing-clear':
            assert foreground_bad, 'omitted live foreground clear escaped ULA oracle'
        else:
            assert not foreground_bad, (name, 'foreground remained on ULA', foreground_bad)
        assert live[0x1A80:0x1B00] == bytes(state['banks'][5][0x1A80:0x1B00]), 'HUD'
        assert all(live[0x2000+a]==backup[a] for a in offsets), 'source pixels'
        gap_expected=bytearray(backup)
        irq_count=sum(t['READY']<r['C']<t['TAIL'] for r in events if r['tag']=='IRQOUT')
        gap_expected[0x11D0]=(gap_expected[0x11D0]+irq_count)&255
        gap_bad=sum(live[0x2000+a]!=gap_expected[a] for a in set(range(0x1800))-offsets)
        if name=='wide-restore':
            assert gap_bad, 'broad source restore escaped post-IRQ oracle'
        else:
            assert not gap_bad, (name, 'source gaps', gap_bad)
        late = [r['R'] for r in events if r['tag']=='ROW' and r['C']-t['BEGIN'] >= (151+16*r['R'])*228*8]
        assert not late, (name, late)
        assert any(t['READY']<r['C']<t['PREPEND'] for r in events if r['tag']=='IRQIN'), 'prep IRQ not covered'
        assert not any(t['PREP']<r['C']<t['READY'] or t['TAIL']<r['C']<t['END'] for r in events if r['tag']=='IRQIN'), 'critical IRQ'
        if name == 'missing-tail':
            assert tail_bad, 'omitted runtime copy escaped'
        else:
            assert not tail_bad, (name, tail_bad)
        if name == 'bad-lut':
            assert pattern_bad, 'broken runtime LUT escaped'
        else:
            assert not pattern_bad and not attr_bad, (name, pattern_bad, attr_bad)
        result = dict(variant=name, mode=mode, sprites=len(expected)//128,
                      patterns_md5=hashlib.md5(expected).hexdigest(), pattern_mismatches=pattern_bad,
                      attribute_mismatches=attr_bad, tail_mismatches=tail_bad, gap_mismatches=gap_bad, foreground_ula_mismatches=foreground_bad, late_rows=late,
                      generation_ms=(t['COPY']-t['GEN'])/28000,
                      preparation_ms=(t['PREPEND']-t['PREP'])/28000,
                      publication_ms=(t['END']-t['BEGIN'])/28000, events=events)
        results.append(result)
        print(name, {k:v for k,v in result.items() if k!='events'}, flush=True)
    (out/'timing.json').write_text(json.dumps(dict(scope='captured game state with native IRQs; live patterns, not an installed engine',
          state_frame=state['frame'], captured_irq_T=state.get('T'), results=results), indent=2)+'\n')


if __name__ == '__main__':
    run()
