"""Castle Master M0: shared geometry, ported from the original (games/castle_master.md, Build design M0).

Camera-space vertices V (x, y, z: 16-bit), outcodes (0x93DE), projection (0x9294), and an object's faces turned
into the output record (no-clip 0x8C74 / clip 0x8E88 with the edge clipper 0x8746, corner insertion 0x91C2,
facing test 0x8A69, winding test 0x9300). Faces come from an edge template: tmpl = [edge count, pairs...],
faces = [(colour nibble, n, [edge refs, bit 7 = walked backwards])]. Exactness notes: all 16-bit sums wrap,
'negative' = bit 15 of the wrapped result (JP P / JP M), divides round half up on magnitudes (45740).
"""

CORNERS = [(192, 112), (0, 112), (0, 0), (192, 0)]          # 36480


def sw(v):
    v &= 0xFFFF
    return v - 65536 if v & 0x8000 else v


def s32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


def mul16(a, b):                                           # 41555: signed 16 x 16 -> 32
    return s32(sw(a) * sw(b))


def div32(n, d):                                           # 45740: DEHL / BC -> HL (low 16 bits used)
    n, d = s32(n), sw(d)
    if n == 0:
        return 0
    if d == 0:
        raise ZeroDivisionError
    q, r = divmod(abs(n), abs(d))
    if r >= abs(d) // 2:
        q += 1
    return sw(q if (n < 0) == (d < 0) else -q)


def project(v):
    x, y, z = v
    if z == 0:
        return 96, 56

    def one(p, half, full):
        if p < 0:
            if sw(p + z - 1) < 0:
                return 0
        elif sw(p - z) >= 0:
            return full
        n = half * p
        q = abs(n) // abs(z)
        q = q if (n >= 0) == (z > 0) else -q
        return (half + q) & 0xFF
    return one(x, 96, 192), one(y, 56, 112)


def outcode(v):
    x, y, z = v
    a = 31
    if sw(x + z) < 0:
        a &= 15
    if sw(y + z) < 0:
        a &= 23
    if sw(y - z) >= 0:
        a &= 29
    if sw(x - z) >= 0:
        a &= 27
    if z < 0:
        a &= 30
    return a


def clip_edge(P, Q, c0, c1):
    """0x8746: P, Q camera-space endpoints (lists, modified copies), c0 / c1 their codes.
    -> (P', Q') clipped, or None if rejected."""
    x0, y0, z0 = P
    x1, y1, z1 = Q

    def rej(b):
        return not (c0 >> b & 1) and not (c1 >> b & 1)

    # plane 0: z >= 0
    if rej(0):
        return None
    if not (c0 & 1 and c1 & 1):
        bc = sw(z0 - z1)
        nx = sw(div32(mul16(sw(x1 - x0), z0), bc) + x0)
        ny = sw(div32(mul16(sw(y1 - y0), z0), bc) + y0)
        if not c0 & 1:
            x0, y0, z0 = nx, ny, 0
        else:
            x1, y1, z1 = nx, ny, 0
        c0 |= 2
        c1 |= 2
        if sw(z0 - y0) < 0:
            c0 &= ~2
        if sw(z1 - y1) < 0:
            c1 &= ~2
    # plane 1: y <= z
    if rej(1):
        return None
    if not (c0 & 2 and c1 & 2):
        bc = sw(sw(y1 - y0) - z1 + z0)
        t = sw(z0 - y0)
        nz = sw(div32(mul16(sw(z1 - z0), t), bc) + z0)
        nx = sw(div32(mul16(sw(x1 - x0), t), bc) + x0)
        if not c0 & 2:
            x0, y0, z0 = nx, nz, nz
        else:
            x1, y1, z1 = nx, nz, nz
    c0 |= 4
    c1 |= 4
    if sw(z0 - x0) < 0:
        c0 &= ~4
    if sw(z1 - x1) < 0:
        c1 &= ~4
    # plane 2: x <= z
    if rej(2):
        return None
    if not (c0 & 4 and c1 & 4):
        bc = sw(sw(x1 - x0) - z1 + z0)
        t = sw(z0 - x0)
        nz = sw(div32(mul16(sw(z1 - z0), t), bc) + z0)
        ny = sw(div32(mul16(sw(y1 - y0), t), bc) + y0)
        if not c0 & 4:
            x0, y0, z0 = nz, ny, nz
        else:
            x1, y1, z1 = nz, ny, nz
    c0 |= 8
    c1 |= 8
    if sw(z0 + y0) < 0:
        c0 &= ~8
    if sw(z1 + y1) < 0:
        c1 &= ~8
    # plane 3: y >= -z
    if rej(3):
        return None
    if not (c0 & 8 and c1 & 8):
        bc = sw(sw(y0 - y1) - z1 + z0)
        t = sw(z0 + y0)
        nz = sw(div32(mul16(sw(z1 - z0), t), bc) + z0)
        nx = sw(div32(mul16(sw(x1 - x0), t), bc) + x0)
        if not c0 & 8:
            x0, y0, z0 = nx, sw(-nz), nz
        else:
            x1, y1, z1 = nx, sw(-nz), nz
    c0 |= 16
    c1 |= 16
    if sw(z0 + x0) < 0:
        c0 &= ~16
    if sw(z1 + x1) < 0:
        c1 &= ~16
    # plane 4: x >= -z
    if rej(4):
        return None
    if not (c0 & 16 and c1 & 16):
        bc = sw(sw(x0 - x1) - z1 + z0)
        t = sw(z0 + x0)
        nz = sw(div32(mul16(sw(z1 - z0), t), bc) + z0)
        ny = sw(div32(mul16(sw(y1 - y0), t), bc) + y0)
        if not c0 & 16:
            x0, y0, z0 = sw(-nz), ny, nz
        else:
            x1, y1, z1 = sw(-nz), ny, nz
    return (x0, y0, z0), (x1, y1, z1)


def ends(tmpl, ref):
    """(start, end) vertex of an edge ref in walking order"""
    a, b = tmpl[1 + 2 * (ref & 127)], tmpl[2 + 2 * (ref & 127)]
    return (b, a) if ref & 128 else (a, b)


def facing(V, tmpl, refs, state):
    """0x8A69: -> 1 (carry: dot >= 0) or 0; clears state['cover'] when the signs of nz and the dot differ"""
    p1, p2 = ends(tmpl, refs[0])
    a = tmpl[1 + 2 * (refs[1] & 127)]
    b = tmpl[2 + 2 * (refs[1] & 127)]
    p3 = a if refs[1] & 128 else b
    (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = V[p1], V[p2], V[p3]
    nx = s32(mul16(sw(y1 - y2), sw(z3 - z2)) - mul16(sw(z1 - z2), sw(y3 - y2)))
    ny = s32(mul16(sw(z1 - z2), sw(x3 - x2)) - mul16(sw(x1 - x2), sw(z3 - z2)))
    nz = s32(mul16(sw(x1 - x2), sw(y3 - y2)) - mul16(sw(y1 - y2), sw(x3 - x2)))
    dot = (nx * sw(x2) + ny * sw(y2) + nz * sw(z2)) & ((1 << 48) - 1)
    top = dot >> 40
    hz = (nz >> 24) & 0xFF if nz >= 0 else ((nz & 0xFFFFFFFF) >> 24)
    if (top ^ hz) & 0x80:
        state['cover'] = 0
    return 0 if top & 0x80 else 1


def winding(V, tmpl, refs, want):
    """0x9300: every edge's 2D cross (end x start) sign = want -> True"""
    for r in refs:
        s, e = ends(tmpl, r)
        c = s32(mul16(V[e][0], V[s][1]) - mul16(V[e][1], V[s][0]))
        if (1 if c >= 0 else 0) != want:
            return False
    return True


def corners(pts, first, nx, ny):
    """0x91C2: screen corners between the last point and (nx, ny), appended to pts"""
    lx, ly = pts[-1]
    L = 1 if ly == 112 else 2 if lx == 0 else 3 if ly == 0 else 0
    H = 0 if nx == 192 else 1 if ny == 112 else 2 if nx == 0 else 3
    while L != H:
        c = CORNERS[L]
        if c != pts[-1] and c != first:
            pts.append(c)
        L = (L + 1) & 3


def faces_record(oid, V, tmpl, faces, mode=0, colbyte=0, tmpl_back=None):
    """-> output record bytes (id, count | 0x80 full screen, faces) like 0x9448's callers; None if nothing.
    faces: [(colour, n, refs)]; mode = (24160): 0 one colour per face; 1 the same, back faces skipped (facing
    test); 2 two-sided: front = colbyte low nibble, back = high nibble drawn with tmpl_back (reversed edges)."""
    codes = [outcode(v) for v in V]
    clip = any(c != 31 for c in codes)
    out = []
    count = 0
    cache = {}

    def edge(e):
        if e in cache:
            return cache[e]
        a, b = tmpl[1 + 2 * e], tmpl[2 + 2 * e]
        c0, c1 = codes[a], codes[b]
        p0 = project(V[a]) if c0 == 31 else None
        p1 = project(V[b]) if c1 == 31 else None
        if c0 & c1 != 31 and (c0 | c1) == 31:
            r = clip_edge(list(V[a]), list(V[b]), c0, c1)
            if r:
                if p0 is None:
                    p0 = project(r[0])
                if p1 is None:
                    p1 = project(r[1])
        cache[e] = (p0, p1)
        return cache[e]

    base = tmpl
    for colour, n, refs in faces:
        tmpl = base
        if not colour:
            continue
        state = {'cover': 1}
        if clip:                                 # 0x8E88 phase A runs before the facing test
            c = 30
            for k in range(0, (n + 1) >> 1):
                r = refs[2 * k]
                hit = False
                for v in (tmpl[1 + 2 * (r & 127)], tmpl[2 + 2 * (r & 127)]):
                    if codes[v] == 31:
                        hit = True
                        break
                    c &= codes[v]
                if hit:
                    c = None
                    break
            if c is None or c != 0:
                state['cover'] = 0
        want = None
        if mode == 1:
            want = facing(V, tmpl, refs, state)
            if want:
                continue
        elif mode == 2:
            want = facing(V, tmpl, refs, state)
            if want:
                colour = colbyte >> 4
                tmpl = tmpl_back
                want = 0
            else:
                colour = colbyte & 15
            if not colour:
                continue
        if not clip:
            pts = []
            for r in refs:
                s, _ = ends(tmpl, r)
                pts.append(project(V[s]))
            out.append(bytes([colour << 4 | n] + [c for p in pts for c in p]))
            count += 1
            continue
        nn = 1 if n == 2 else n
        for r in refs[:nn]:
            edge(r & 127)
        pts = []
        first = None
        for r in refs[:nn]:
            p0, p1 = edge(r & 127)
            if p0 is None:
                continue
            if r & 128:
                p0, p1 = p1, p0
            if pts:
                if pts[-1] != p0:
                    corners(pts, first, *p0)
                    pts.append(p0)
            else:
                pts.append(p0)
                first = p0
            if p1 != p0:
                pts.append(p1)
        if len(pts) >= 2:
            if not (len(pts) == 2 and nn == 1):
                if pts[0] == pts[-1]:
                    pts.pop()
                else:
                    corners(pts, first, *pts[0])
            out.append(bytes([colour << 4 | len(pts)] + [c for p in pts for c in p]))
            count += 1
            continue
        if nn == 1 or not state['cover']:
            continue
        if mode == 0:
            want = facing(V, tmpl, refs, state)
            if not state['cover']:
                continue
        if winding(V, tmpl, refs[:n], want):
            out.append(bytes([colour << 4 | 4] + [c for p in CORNERS for c in p]))
            count += 1
            return bytes([oid, count | 0x80]) + b''.join(out)
    if not count:
        return None
    return bytes([oid, count]) + b''.join(out)


def sector_bounds(yaw, pitch, cam):
    """0x8D4F: the 6 coarse cull limits at 29488 (when (27325) == 0); cam = 16-bit x, y, z"""
    b = [255] * 6
    for h in (4, 3, 2, 1):
        y = (yaw - 8) % 72 if h >= 3 else (yaw + 8) % 72
        p = (pitch + 8) % 72 if h & 1 else (pitch - 8) % 72
        d = 1 if y < 18 else 3 if y < 36 else 5 if y < 54 else 7
        if p < 18:
            d += 1
        elif p < 36:
            d = d + 5 - (8 if d + 5 >= 9 else 0)
        elif p < 54:
            d = d + 4 - (8 if d + 4 >= 9 else 0)
        for i in {1: (0, 2, 4), 2: (0, 3, 4), 3: (0, 2, 5), 4: (0, 3, 5),
                  5: (1, 2, 5), 6: (1, 3, 5), 7: (1, 2, 4), 8: (1, 3, 4)}[d]:
            b[i] = (127, 0, 63, 0, 127, 0)[i]
    for k in range(3):
        hi = ((cam[k] * 4) >> 8) & 0xFF
        if b[2 * k] == 255:
            b[2 * k] = (hi + 1) & 0xFF
        elif b[2 * k + 1] == 255:
            b[2 * k + 1] = hi
    return b


def sector_cull(rec, b):
    """0x85C9 34286-34311: True = the object is skipped"""
    for k in range(3):
        a = rec[1 + k]
        if a != b[2 * k] and not ((a - b[2 * k]) & 0x80):
            return True
        if ((a + rec[4 + k]) - b[2 * k + 1]) & 0x80:
            return True
    return False
