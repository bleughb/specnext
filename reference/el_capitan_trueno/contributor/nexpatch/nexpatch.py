# nexpatch - a Spectrum Next .nex built from the user's own .z80 snapshot plus a patch, so that no game
# data is ever distributed. The patch describes the .nex relative to the snapshot (the file's bytes and
# its unpacked memory banks): "copy from the source", "fill with one byte", "our own bytes". Our own
# bytes are encrypted with ChaCha20, key = SHA-256 of the whole .z80 file: without the original file
# the patch is noise. The file is recognised by its CRC32 (stored); the key is never stored.
# The user-side tool is one HTML page per game (template.html, the patch inside, base64).
# Usage:
#   python nexpatch.py make GAME.z80 GAME.nex -o PAGE.html --title T [--subtitle S] [--about A]
#          [--notice N] [--credits C]      (about / notice / credits: HTML allowed)
#   several versions (one is chosen on the page) and options (check boxes, off by default):
#   python nexpatch.py make GAME.z80 -o PAGE.html --choice Language --variant Espanol "" es.nex
#          --variant English " EN" en.nex --option "Immortality" " immortal" es.nex es_immortal.nex ...
#          (an option = the bytes where the second .nex differs from the first; it must fit every version)
#   python nexpatch.py apply GAME.z80 PAGE.html [--variant N] [--option K ...] [-o OUT.nex]   (tests)
import base64
import hashlib
import os
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
MAGIC = b'NXP1'
MIN_COPY, MIN_FILL, KEYLEN = 16, 32, 8          # shortest copy / fill worth an op; index key length
NOTICE = ('This page stores no game resources: only the changes, which can be read only together with '
          'the original snapshot. Anyone who owns the original game can make a .z80 snapshot of it.')


# ---- .z80 snapshot: memory banks (16K) ----
def unrle(data, out_len):
    """.z80 compression: ED ED n b = b repeated n times."""
    out, i = bytearray(), 0
    while len(out) < out_len and i < len(data):
        if data[i] == 0xED and i + 1 < len(data) and data[i + 1] == 0xED:
            out += bytes([data[i + 3]]) * data[i + 2]
            i += 4
        else:
            out.append(data[i])
            i += 1
    if len(out) != out_len:
        raise ValueError('bad .z80 block: %d bytes, expected %d' % (len(out), out_len))
    return bytes(out)


def z80_banks(data):
    """{bank: 16384 bytes}: 48K = banks 5, 2, 0; 128K = banks 0-7 (pages 3-10)."""
    if data[6] | data[7]:                           # version 1: 48K, one block
        flags = data[12] if data[12] != 255 else 1
        body = data[30:]
        mem = unrle(body, 49152) if flags & 0x20 else body[:49152]
        return {5: mem[:16384], 2: mem[16384:32768], 0: mem[32768:]}
    pos = 32 + (data[30] | data[31] << 8)
    pages = {}
    while pos + 3 <= len(data):
        ln, page = data[pos] | data[pos + 1] << 8, data[pos + 2]
        pos += 3
        if ln == 0xFFFF:
            pages[page], pos = data[pos:pos + 16384], pos + 16384
        else:
            pages[page], pos = unrle(data[pos:pos + ln], 16384), pos + ln
    if 3 in pages:                                  # 128K: page p = bank p - 3
        return {p - 3: m for p, m in pages.items() if 3 <= p <= 10}
    return {{8: 5, 4: 2, 5: 0}[p]: m for p, m in pages.items() if p in (4, 5, 8)}


def source_of(data):
    """The copy source: the file's own bytes, then its banks in bank order."""
    banks = z80_banks(data)
    return data + b''.join(banks[k] for k in sorted(banks))


# ---- ChaCha20 (RFC 8439), the keystream for our own bytes ----
def _rotl(v, n):
    return (v << n | v >> (32 - n)) & 0xFFFFFFFF


def chacha_stream(key):
    const = struct.unpack('<4I', b'expand 32-byte k')
    k = struct.unpack('<8I', key)
    counter = 0
    while True:
        st = list(const) + list(k) + [counter, 0, 0, 0]
        x = st[:]
        for _ in range(10):
            for a, b, c, d in ((0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15),
                               (0, 5, 10, 15), (1, 6, 11, 12), (2, 7, 8, 13), (3, 4, 9, 14)):
                x[a] = (x[a] + x[b]) & 0xFFFFFFFF; x[d] = _rotl(x[d] ^ x[a], 16)
                x[c] = (x[c] + x[d]) & 0xFFFFFFFF; x[b] = _rotl(x[b] ^ x[c], 12)
                x[a] = (x[a] + x[b]) & 0xFFFFFFFF; x[d] = _rotl(x[d] ^ x[a], 8)
                x[c] = (x[c] + x[d]) & 0xFFFFFFFF; x[b] = _rotl(x[b] ^ x[c], 7)
        yield from struct.pack('<16I', *((x[i] + st[i]) & 0xFFFFFFFF for i in range(16)))
        counter += 1


# ---- the patch ----
def varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def make_patch(z80, target):
    """Patch bytes: MAGIC, CRC32 of the .z80, its size, target size, SHA-256 of the target, then ops:
    varint((length - 1) * 4 + type); type 0 = our bytes (length encrypted bytes follow), 1 = copy
    (varint source offset follows), 2 = fill (one byte follows)."""
    src = source_of(z80)
    index = {}
    for i in range(len(src) - KEYLEN + 1):
        index.setdefault(src[i:i + KEYLEN], []).append(i)
    ks = chacha_stream(hashlib.sha256(z80).digest())
    ops, lit, stats = bytearray(), bytearray(), {'copy': 0, 'fill': 0, 'own': 0}

    def flush():
        if lit:
            ops.extend(varint((len(lit) - 1) * 4) + bytes(b ^ next(ks) for b in lit))
            stats['own'] += len(lit)
            lit.clear()
    i, n = 0, len(target)
    while i < n:
        run = 1
        while i + run < n and target[i + run] == target[i]:
            run += 1
        best, at = 0, 0
        for p in index.get(target[i:i + KEYLEN], [])[:64]:
            ln = 0
            while i + ln < n and p + ln < len(src) and src[p + ln] == target[i + ln]:
                ln += 1
            if ln > best:
                best, at = ln, p
        if best >= MIN_COPY and best >= run:
            flush()
            ops.extend(varint((best - 1) * 4 + 1) + varint(at))
            stats['copy'] += best
            i += best
        elif run >= MIN_FILL:
            flush()
            ops.extend(varint((run - 1) * 4 + 2) + bytes([target[i]]))
            stats['fill'] += run
            i += run
        else:
            lit.append(target[i])
            i += 1
    flush()
    head = MAGIC + struct.pack('<III', zlib.crc32(z80), len(z80), len(target)) + hashlib.sha256(target).digest()
    return head + bytes(ops), stats


def apply_patch(z80, patch):
    if patch[:4] != MAGIC:
        raise ValueError('not a nexpatch patch')
    crc, size, tlen = struct.unpack('<III', patch[4:16])
    if zlib.crc32(z80) != crc or len(z80) != size:
        raise ValueError('this is not the expected .z80 (CRC32 %08X expected)' % crc)
    sha, pos = patch[16:48], 48
    src = source_of(z80)
    ks = chacha_stream(hashlib.sha256(z80).digest())
    out = bytearray()

    def rd():
        nonlocal pos
        v, sh = 0, 0
        while True:
            b = patch[pos]
            pos += 1
            v |= (b & 0x7F) << sh
            sh += 7
            if not b & 0x80:
                return v
    while pos < len(patch):
        op = rd()
        ln, kind = op // 4 + 1, op % 4
        if kind == 0:
            out += bytes(b ^ next(ks) for b in patch[pos:pos + ln])
            pos += ln
        elif kind == 1:
            at = rd()
            out += src[at:at + ln]
        else:
            out += bytes([patch[pos]]) * ln
            pos += 1
    if len(out) != tlen or hashlib.sha256(out).digest() != sha:
        raise ValueError('the result does not match the expected .nex')
    return bytes(out)


def nex_name(z80_path):
    """The .z80 name without the parts in brackets: 'Capitan Trueno, El (1990)(Dinamic)(ES).z80' ->
    'Capitan Trueno, El.nex'."""
    base = os.path.splitext(os.path.basename(z80_path))[0]
    return re.sub(r'\s+', ' ', re.sub(r'\([^)]*\)|\[[^\]]*\]', '', base)).strip() + '.nex'


# ---- the page ----
def html_escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def option_edits(base, other):
    """An option = the bytes where `other` differs from `base` (same size): [[offset, [new bytes]]].
    Only the new bytes are stored (no game bytes); the variant is checked by its SHA-256 first."""
    if len(base) != len(other):
        raise SystemExit('an option .nex must have the size of its base')
    edits, i = [], 0
    while i < len(base):
        if base[i] != other[i]:
            j = i
            while j < len(base) and base[j] != other[j]:
                j += 1
            edits.append([i, list(other[i:j])])
            i = j
        else:
            i += 1
    return edits


def apply_options(nex, options):
    out = bytearray(nex)
    for o in options:
        for off, new in o['edits']:
            out[off:off + len(new)] = bytes(new)
    return bytes(out)


def make_page(z80_path, variants, options, out, texts):
    """variants: [(label, suffix, .nex path)]; options: [(label, suffix, base .nex, .nex with it)]."""
    import json
    z80 = open(z80_path, 'rb').read()
    data = {'choice': texts['choice'], 'variants': [], 'options': []}
    for label, suffix, path in variants:
        target = open(path, 'rb').read()
        patch, stats = make_patch(z80, target)
        if apply_patch(z80, patch) != target:
            raise SystemExit('round trip failed: ' + path)
        data['variants'].append({'label': label, 'suffix': suffix, 'patch': base64.b64encode(patch).decode()})
        print('%s: %d bytes = copied from the snapshot %d, fills %d, own bytes %d; patch %d bytes'
              % (label, len(target), stats['copy'], stats['fill'], stats['own'], len(patch)))
    for label, suffix, base, other in options:
        b, o = open(base, 'rb').read(), open(other, 'rb').read()
        edits = option_edits(b, o)
        if apply_options(b, [{'edits': edits}]) != o:
            raise SystemExit('option round trip failed: ' + label)
        data['options'].append({'label': label, 'suffix': suffix, 'edits': edits})
        print('option %s: %d bytes in %d places' % (label, sum(len(n) for _, n in edits), len(edits)))
    page = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
    for k, v in (('TITLE', html_escape(texts['title'])), ('SUBTITLE', html_escape(texts['subtitle'])),
                 ('ABOUT', texts['about']), ('NOTICE', texts['notice']), ('CREDITS', texts['credits']),
                 ('Z80NAME', html_escape(os.path.basename(z80_path))), ('CRC', '%08X' % zlib.crc32(z80)),
                 ('DATA', json.dumps(data, separators=(',', ':')))):
        page = page.replace('{{%s}}' % k, v)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, 'w', encoding='utf-8', newline='\n').write(page)
    print('wrote', out)


def page_data(path):
    import json
    return json.loads(re.search(r'const DATA = (\{.*?\});$', open(path, encoding='utf-8').read(), re.S | re.M).group(1))


def main():
    sys.stdout.reconfigure(errors='replace')     # labels like 'Espanol' with n-tilde on a cp1251 console
    a = sys.argv[1:]
    opt = lambda name, default=None: a[a.index(name) + 1] if name in a else default
    multi = lambda name, n: [tuple(a[i + 1:i + 1 + n]) for i, x in enumerate(a) if x == name]
    if a[:1] == ['make']:
        variants = multi('--variant', 3) or [('Original', '', a[2])]
        texts = {'title': opt('--title', 'A game'), 'subtitle': opt('--subtitle', 'patcher for the ZX Spectrum Next'),
                 'about': opt('--about', ''), 'notice': opt('--notice', NOTICE), 'credits': opt('--credits', ''),
                 'choice': opt('--choice', 'Version')}
        make_page(a[1], variants, multi('--option', 4), opt('-o'), texts)
    elif a[:1] == ['apply']:
        z80 = open(a[1], 'rb').read()
        data = page_data(a[2])
        v = data['variants'][int(opt('--variant', '0'))]
        picked = {int(k) for (k,) in multi('--option', 1)}
        chosen = [o for i, o in enumerate(data['options']) if i in picked]
        nex = apply_options(apply_patch(z80, base64.b64decode(v['patch'])), chosen)
        name = nex_name(a[1])[:-4] + v['suffix'] + ''.join(o['suffix'] for o in chosen) + '.nex'
        out = opt('-o', os.path.join(os.path.dirname(a[1]), name))
        open(out, 'wb').write(nex)
        print('wrote', out)
    else:
        print(open(__file__).read().split('import')[0])


if __name__ == '__main__':
    main()
