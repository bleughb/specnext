"""Castle Master M1 raster model: the game's raster 0x9EA3 (clear 0xA3F4, polygon filler 0x9484, span 0x9696)
transliterated onto a copy of RAM, plus a per-pixel source map for Layer 2 (which face colour / clear part wrote
each pixel last). Checked against the game: the view buffer (0x5CBC-0x6753, incl. the y = 0 overrun row 112)
after the drawing (PC 40715, before the XOR marker 53061) must be equal, from the RAM at the raster call (34201).
Source codes in the map: 1 + face colour nibble (1-16); 32 + c sky / ground fill of pattern c; 64 mountains; 65 lightning;
0 not drawn this view (stale).
Usage: python m1_raster.py [states file] [every N-th] [--light]
"""
import collections, sys
from m0_lib import states, Sandbox

BUF, ROWS = 23740, 113
PAT, MASK1, MASKL = 53825, 38543, 38536


def s8(v):
    v &= 255
    return v - 256 if v & 128 else v


def s16(v):
    v &= 0xFFFF
    return v - 65536 if v & 0x8000 else v


def div45740(n, d):
    """DEHL / BC as 45740: magnitudes, + 1 when remainder >= |d| >> 1, sign applied; full signed quotient"""
    if n == 0:
        return 0
    q, r = divmod(abs(n), abs(d))
    if r - (abs(d) >> 1) >= 0:
        q += 1
    return q if (n < 0) == (d < 0) else -q


class Raster:
    def __init__(self, mem, lightning_col=0, clip_bolt=False):
        self.m = mem                       # bytearray(65536), modified like the game's RAM
        self.src = [[0] * 192 for _ in range(ROWS)]
        self.lcol = lightning_col
        self.clip = clip_bolt              # the Next renderer's spec: bolt rows outside the buffer not written (the
                                           # original's 255-row bolt at pitch 4 overwrites its RAM up to 30056)

    # ---- 38492 / 0x9696 ----
    def rowsetup(self, y):
        m = self.m
        a = (112 - y) & 255
        hl = (a * 24 + BUF) & 0xFFFF
        m[29662], m[29663] = hl & 255, hl >> 8
        p = (PAT + (((m[29501] - 1) & 255) << 2 & 255)) & 0xFFFF
        m[29664], m[29665] = p & 255, p >> 8

    def w16(self, a):
        return self.m[a] | self.m[a + 1] << 8

    def span(self, h, d):
        m = self.m
        if h >= 193 or d >= 193:
            return
        pat = m[(self.w16(29664) + (m[29658] & 3)) & 0xFFFF]
        row = self.w16(29662)
        lo, hi = min(h, d), max(h, d)
        p0 = max(lo, 1) - 1
        r = (row - BUF) // 24 if (row - BUF) % 24 == 0 else None
        for p in range(p0, hi):
            a = row + (p >> 3)
            bit = 0x80 >> (p & 7)
            m[a] = (m[a] & ~bit & 255) | (pat & bit)
            if r is not None and 0 <= r < ROWS:
                self.src[r][p] = 1 + m[29501]
        row = (row - 24) & 0xFFFF
        m[29662], m[29663] = row & 255, row >> 8

    # ---- 0x9484 ----
    def face(self, pts):
        m = self.m
        n = m[29544]
        if n == 2:
            return self.line(pts)
        m[29661] = n
        flat = [c for p in pts for c in p]
        for i, c in enumerate(flat + flat):
            m[29666 + i] = c
        a = m[29667]
        de = 29667
        hl = 29667
        for _ in range(n - 1):
            hl += 2
            if not a < m[hl]:
                de = hl
                a = m[hl]
        de -= 1
        m[29658] = a
        self.rowsetup(a)
        ix = de - 2
        iy = de + 2 * (n + 1)
        m[29660] = 3
        HL = DE = 0
        state = 'L38266'
        a = m[29658]
        while True:
            if state == 'L38244':
                self.span(HL >> 8, DE >> 8)
                HL = (HL + self.w16(29654)) & 0xFFFF
                DE = (DE + self.w16(29656)) & 0xFFFF
                m[29658] = (m[29658] + 1) & 255
                a = m[29658]
                state = 'L38266'
            elif state == 'L38266':
                state = 'L38271' if a == m[iy - 1] else 'L38354'
            elif state == 'L38271':
                m[29661] = (m[29661] - 1) & 255
                if m[29661] & 128:
                    state = 'L38443'
                    continue
                iy -= 2
                d = m[iy + 1] - m[iy - 1]
                if d == 0:
                    continue
                if d > 0:
                    state = 'L38443'
                    continue
                bc = 0xFF00 | ((d - 1) & 255)
                dx = m[iy] - m[iy - 2]
                q = div45740(dx * 256, s16(bc)) if dx else 0
                sl = q & 0xFFFF
                m[29654], m[29655] = sl & 255, sl >> 8
                b = sl if m[29660] & 1 else ((s16(sl) >> 1) & 0xFFFF)
                m[29660] &= 254
                HL = ((m[iy] << 8) + b) & 0xFFFF
                a = m[29658]
                state = 'L38354'
            elif state == 'L38354':
                state = 'L38359' if a == m[ix + 3] else 'L38244'
            elif state == 'L38359':
                m[29661] = (m[29661] - 1) & 255
                if m[29661] & 128:
                    state = 'L38443'
                    continue
                ix += 2
                d = m[ix + 1] - m[ix + 3]
                if d == 0:
                    continue
                if d > 0:
                    state = 'L38443'
                    continue
                bc = 0xFF00 | ((d - 1) & 255)
                dx = m[ix] - m[ix + 2]
                q = div45740(dx * 256, s16(bc)) if dx else 0
                sl = q & 0xFFFF
                m[29656], m[29657] = sl & 255, sl >> 8
                b = sl if m[29660] & 2 else ((s16(sl) >> 1) & 0xFFFF)
                m[29660] &= 253
                DE = ((m[ix] << 8) + b) & 0xFFFF
                state = 'L38244'
            elif state == 'L38443':
                if m[29660]:
                    e = d_ = m[ix]
                    p = 29666
                    for _ in range(n - 1):
                        p += 2
                        v = m[p]
                        if v < e:
                            e = v
                        elif v >= d_:
                            d_ = v
                    HL = e << 8 | (HL & 255)
                    DE = d_ << 8 | (DE & 255)
                self.span(HL >> 8, DE >> 8)
                return

    def line(self, pts):
        m = self.m
        (l, h), (e, d) = pts
        if d - h < 0:
            l, h, e, d = e, d, l, h
        dy = d - h
        m[29658] = h
        self.rowsetup(h)
        if dy == 0:
            self.span(l, e)
            return
        bc = s16((0xFF00 | ((h - d) & 255)) - 1)
        # numerator: A = L - E (8-bit), DE = -1 on borrow -> (L - E) as a signed 9-bit value * 256
        num = (l - e) * 256
        q = div45740(num, bc)
        sl = q & 0xFFFF
        m[29654], m[29655] = sl & 255, sl >> 8
        step = 1 if q < 0 else 255
        b = dy + 1
        HL = (l << 8) + sl & 0xFFFF
        DE = l << 8
        while True:
            hh = HL >> 8
            if hh != DE >> 8:
                HL = ((hh + step) & 255) << 8 | (HL & 255)
            b -= 1
            if b == 0:
                self.span(HL >> 8, DE >> 8)
                return
            self.span(HL >> 8, DE >> 8)
            m[29658] = (m[29658] + 1) & 255
            HL = (DE + sl) & 0xFFFF
            DE = HL
            HL = (HL + sl) & 0xFFFF

    # ---- 0xA3F4 ----
    def fill(self, hl, rows, colour, srcv):
        m = self.m
        pp = PAT + (((colour - 1) & 255) * 4 & 255)
        for b in range(rows, 0, -1):
            v = m[pp + (b & 3)]
            r = (hl - BUF) // 24
            for k in range(24):
                m[hl + k] = v
            for p in range(192):
                if 0 <= r < ROWS:
                    self.src[r][p] = srcv
            hl += 24
        return hl

    def clear(self):
        m = self.m
        for a in (41964, 41965, 41966, 41967):
            m[a] = 0
        v = m[27402]
        if v == 0:
            return
        m[41969] = v & 15
        m[41968] = v >> 4
        if m[41968] == 0:
            B, C = 113, 0
            m[41964] = 0
        elif m[41969] == 0:
            m[41964] = 0
            B, C = 0, 113
        else:
            a = m[27318]
            go = None
            if s8(a - 8) < 0:
                go = a
            elif s8(a - 29) < 0:
                m[41964] = 0
                B, C = 0, 113
            elif s8(a - 61) < 0:
                B, C = 113, 0
                m[41964] = 0
            else:
                go = (a - 72) & 255
            if go is not None:
                B, C = 113, 0
                hl = (s8(go) * 11 + 60) & 0xFFFF
                A = hl & 255
                if not (hl & 0x8000) and A >= 113:
                    C, B = B, 0
                else:
                    if not (hl & 0x8000):
                        C = A
                    D = A
                    if m[27391] == 0:
                        hl2 = (hl + 96) & 0xFFFF
                        if not (hl2 & 0x8000):
                            A = hl2 & 255
                            m[41966] = A
                            if A >= 87:
                                m[41966] = 86
                                if A >= 114:
                                    m[41966] = (B - C - 10) & 255
                                    m[41967] = (86 - m[41966]) & 255
                    A = (D + 18) & 255
                    if A & 128:
                        B = (B - C - m[41964]) & 255
                    else:
                        m[41964] = A
                        if A < 19:
                            B = (B - C - m[41964]) & 255
                        else:
                            m[41964] = 18
                            if A < 114:
                                B = (B - C - m[41964]) & 255
                            else:
                                m[41964] = (B - C) & 255
                                m[41965] = (18 - m[41964]) & 255
                                B = 0
        hl = BUF
        if B:
            hl = self.fill(hl, B, m[41969], 32 + m[41969])
        if m[41964]:
            hl = self.mountains(hl)
        if m[41966]:
            self.lightning(hl)
        if C:
            self.fill(hl, C, m[41968], 32 + m[41968])

    def mountains(self, hl):
        m = self.m
        if m[27343] != 1:
            return self.fill(hl, m[41964], m[41969], 32 + m[41969])
        a = (m[27319] & 7) * 2
        src = 30660 + a
        c = 16 - a
        if m[41965]:
            src += 16 * m[41965]
        de = hl
        for _ in range(m[41964]):
            r = (de - BUF) // 24
            row = [m[src + k] for k in range(c)]
            left = 24 - c
            while left >= 17:
                row += [m[src - a + k] for k in range(16)]
                left -= 16
            row += [m[src - a + k] for k in range(left)]
            for k in range(24):
                m[de + k] = row[k]
            if 0 <= r < ROWS:
                for p in range(192):
                    self.src[r][p] = 64
            de += 24
            src += 16
        return de

    def lightning(self, hl):
        m = self.m
        m[41970] = self.lcol
        a = m[41964] - 8
        if a < 0:
            a = 0
        a = (a + m[41966]) & 255
        de = (hl - 24 * s8(a)) & 0xFFFF
        gfx = 31085 + 2 * m[41967]
        col = m[41970] | m[41971] << 8
        for _ in range(m[41966]):
            d = (de + col) & 0xFFFF
            r = (d - BUF) // 24
            for k in range(2 if not self.clip or 0 <= r < ROWS else 0):
                old = m[d + k]
                new = old | m[gfx + k]
                m[d + k] = new
                if 0 <= r < ROWS:
                    px = (d + k - BUF) % 24 * 8
                    for b in range(8):
                        if m[gfx + k] & (0x80 >> b):
                            self.src[r][px + b] = 65
            gfx += 2
            de += 24

    # ---- 0x9EA3 ----
    def run(self):
        m = self.m
        d = m[29502]
        full = m[29523]
        lst = 26452
        recs = [(m[lst + 4 * i] | m[lst + 4 * i + 1] << 8) for i in range(d)]
        start = 0
        if full:
            k = full
            for i, p in enumerate(recs):
                if m[p + 1] & 0x80:
                    k -= 1
                    if k == 0:
                        start = i
                        break
        else:
            self.clear()
        for p in recs[start:]:
            cnt = m[p + 1]
            if not cnt:
                continue
            q = p + 2
            for _ in range(cnt & 127):
                hdr = m[q]
                m[29501] = hdr >> 4
                m[29544] = hdr & 15
                n = hdr & 15
                pts = [(m[q + 1 + 2 * j], m[q + 2 + 2 * j]) for j in range(n)]
                self.face(pts)
                q += 1 + 2 * n


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    light = '--light' in sys.argv            # force (27391) = 0 where the sky is cleared: lightning drawn
    name = args[0] if args else 'm0_states_3k.bin'
    every = int(args[1]) if len(args) > 1 else 1
    res = collections.Counter()
    ex = []
    for k, (frame, regs, ram) in enumerate(states(name)):
        if k % every:
            continue
        sb = Sandbox(ram, regs)
        if not sb.to(34198):                # CALL 48643 (panel; may wait for an interrupt): skipped
            res['no raster call'] += 1
            continue
        sb.R[24] = 34201
        if light and sb.m[27402] and not sb.m[29523]:
            sb.m[27391] = 0
        before = bytearray(sb.m)
        if not sb.to(40715):
            res['raster end not reached'] += 1
            continue
        game = bytes(sb.m[BUF:BUF + 24 * ROWS + 24])
        rz = Raster(before, lightning_col=sb.m[41970])
        rz.run()
        mine = bytes(rz.m[BUF:BUF + 24 * ROWS + 24])
        ok = mine == game
        res['views %s' % ('EQUAL' if ok else 'DIFFER')] += 1
        if before[27402] == 0 and not before[29523]:
            res['  no clear (27402 = 0)'] += 1
            stale = sum(1 for r in range(112) for p in range(192) if rz.src[r][p] == 0)
            if stale:
                res['  ... with stale pixels'] += 1
                res['  ... stale pixels total'] += stale
        if before[27391] == 0 and before[27402] and not before[29523]:
            res['  lightning (27391 = 0)'] += 1
            res['  ... rows %d' % rz.m[41966]] += 1
        if not ok and len(ex) < 4:
            diff = [i for i in range(len(game)) if game[i] != mine[i]]
            ex.append((k, frame, len(diff), [(divmod(i, 24), game[i], mine[i]) for i in diff[:6]]))
    for kk, v in sorted(res.items()):
        print('  %-28s %d' % (kk, v))
    for e in ex:
        print('  state %d frame %d: %d bytes differ %s' % e)
    return 0 if not ex else 1


if __name__ == '__main__':
    sys.exit(main())
