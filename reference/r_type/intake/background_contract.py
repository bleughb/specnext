"""Source-only background initialization oracle; no renderer or intake scan.

Compare native FEEB with an independent block-map decoder on reconstructed levels.
Generated source images stay outside Git. IRQs are excluded; this does not prove
scroll progression, timing, RGB composition or a replacement writer.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'nexclash'))
from skoolkit.simulator import Simulator
from register_bridge import until
from live_assets import group


def word(data, address):
    return data[address] | data[address + 1] << 8


def pixel_address(x, y):
    return 0x4000 + (y & 7) * 256 + ((y >> 3) & 7) * 32 + (y >> 6) * 2048 + x


def expected(data, start, ideal_flip=False):
    pixels = bytearray(5120)
    attrs = bytearray(640)
    owners = bytearray(640)
    base = word(data, 0xC4BC)
    for column in range(8):
        for blockrow in range(5):
            tile = data[base + (start + column) * 5 + blockrow]
            # Native 882D wraps the two ADD A,A operations before widening.
            source = (base - (((tile + 1) * 4) & 255) * 36) & 65535
            for sy in range(4):
                for sx in range(4):
                    cell = source + (sy * 4 + sx) * 9
                    attr = data[cell]
                    x = column * 4 + (3 - sx if tile & 64 else sx)
                    row = blockrow * 4 + (3 - sy if tile & 128 else sy)
                    if x == 0 or attr == 0x36:
                        continue
                    attrs[row * 32 + x] = attr & 127
                    owners[row * 32 + x] = 255 if attr & 128 else 0
                    for py in range(8):
                        y = row * 8 + (7 - py if tile & 128 else py)
                        b = data[cell + 1 + py]
                        if tile & 64:
                            b = int(f'{b:08b}'[::-1], 2) if ideal_flip else data[0x5D00 + b]
                        pixels[y * 32 + x] = b
    return pixels, attrs, owners


def execute(data, start):
    mem = bytearray(data)
    for address, size in ((0x4000, 0x1800), (0x7800, 640), (0x7E00, 640), (0x8100, 640)):
        mem[address:address + size] = bytes(size)
    mem[0x7A84] = start
    mem[0x8EB1] = 0
    mem[0x8EDA] = 0xC9
    mem[0x8F0B:0x8F0D] = bytes.fromhex('1c1a')
    mem[0x5EFE:0x5F00] = bytes.fromhex('0010')
    sim = Simulator(mem, {'PC': 0xFEEB, 'SP': 0x5EFE})
    until(sim, 0x1000, limit=500000)
    m = sim.memory
    pixels = bytes(m[pixel_address(x, y)] for y in range(160) for x in range(32))
    return sim, (pixels, bytes(m[0x7800:0x7A80]), bytes(m[0x7E00:0x8080]))


def foreground_flip_check(data):
    """Synthetic legal cell through unchanged native plotters and current compiler."""
    texture = group(bytes([1] * 8), 7, 49, 0x5E00, {})
    results = []
    for normalized in (False, True):
        for flip, pc in enumerate((0x8CFD, 0x8D65, 0x8DD3, 0x8E29)):
            mem = bytearray(data)
            mem[0x7E00:0x8080] = bytes(640)
            mem[0x5E00:0x5E09] = bytes([7] + [1] * 8)
            mem[0x5EFE:0x5F00] = bytes.fromhex('0010')
            mem[0x7A82] = mem[0x8EB1] = 0
            mem[0x8EBF], mem[0x8F10], mem[0x8EDA] = 0x60, 0xD0, 0xC9
            mem[0x8F0B:0x8F0D] = bytes.fromhex('1c1a')
            if normalized:
                mem[0x5D01] = 0x80
            sim = Simulator(mem, {'PC': pc, 'SP': 0x5EFE, 'BC': 0x0A0A,
                                  'DE': 0x0101, 'HL': 0x5E00})
            until(sim, 0x1000)
            native = [sim.memory[pixel_address(10, 80 + y) + 0x2000] for y in range(8)]
            compiled = []
            for y in range(8):
                packed = texture[flip * 32 + y * 4:flip * 32 + y * 4 + 4]
                colours = [c for b in packed for c in (b >> 4, b & 15)]
                compiled.append(sum((128 >> x) for x, c in enumerate(colours) if c))
            matches = native == compiled
            assert matches == (normalized or not (flip & 1)), (normalized, flip, native, compiled)
            results.append(dict(normalized_table_control=normalized, flip=flip,
                                native_row=native[0], compiled_row=compiled[0], matches=matches))
    return results


def run():
    raw = Path('/workspace/work/r_type_review/decoded.bin').read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    identity = json.loads((HERE / 'continuation/identity-budget.json').read_text())
    assert digest == identity['source']['decoded_sha256']
    cases = []
    for level in range(1, 9):
        data = raw[level * 65536:(level + 1) * 65536]
        base, end = word(data, 0xC4BC), word(data, 0xC4B4)
        assert end > base and (end - base) % 5 == 0
        columns = (end - base) // 5
        for start in sorted({0, columns // 2, columns - 8}):
            sim, actual = execute(data, start)
            wanted = expected(data, start)
            for label, got, want in zip(('pixels', 'attributes', 'owners'), actual, wanted):
                diffs = [i for i, (a, b) in enumerate(zip(got, want)) if a != b]
                assert not diffs, (level, start, label, [(i, got[i], want[i]) for i in diffs[:8]])
            m = sim.memory
            assert not any(m[0x8100:0x8380]), 'initialization changed dirty map'
            assert not any(m[0x5800:0x5A80]), 'initialization published attributes early'
            assert [m[a] for a in (0x8D19, 0x8D83, 0x8DEF, 0x8E49)] == [31] * 4
            assert m[0x8EBF] == 0x60 and m[0x8F10] == 0xD0
            assert m[0x7A84] == start + 8
            assert word(m, 0x7A87) == word(m, 0x7A85) == base + (start + 8) * 5
            ideal = expected(data, start, ideal_flip=True)[0]
            cases.append(dict(level=level, start=start, columns=columns,
                              ideal_flip_pixel_byte_differences=sum(a != b for a, b in zip(actual[0], ideal))))
    flips = foreground_flip_check(raw[65536:2 * 65536])
    result = dict(scope=__doc__, decoded_sha256=digest, cases=cases,
                  foreground_flip_cases=flips,
                  passed=len(cases), ideal_flip_negative_detected=sum(c['ideal_flip_pixel_byte_differences'] > 0 for c in cases))
    assert result['ideal_flip_negative_detected'], 'ideal-flip negative failed to expose native difference'
    output = HERE / 'continuation/background-contract.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ('scope', 'cases', 'foreground_flip_cases')}))
    print('8 foreground flip cases: original table exposes two compiler mismatches; normalized-table controls isolate cause')


if __name__ == '__main__':
    run()
