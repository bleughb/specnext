"""Castle Master M3b: what the Next shows of the view (Layer 2 + overlay sprites, no ULA), as a PNG, for builds
side by side. Usage: python m3b_preview.py OUT.png STATE PREFIX [PREFIX ...] [--crop x0 y0 x1 y1] [--scale N]"""
import argparse, sys
from PIL import Image
from m0_lib import states
from m2_lib import Next, syms, PC, T
from m3_sim import view

END = 0x859F


def rgb(v):
    return ((v >> 5) * 255 // 7, ((v >> 2) & 7) * 255 // 7, (v & 3) * 255 // 3)


def shot(prefix, ram, regs):
    S = syms(prefix)
    nx = Next(ram, prefix, S)
    R = nx.R
    for i in range(24):
        R[i] = regs[i]
    R[PC], R[T], R[26] = 34142, 0, 0
    nx.run(END, max_ins=3_000_000)
    wk = nx.page(S['PG_W0']) + nx.page(S['PG_W1'])
    rows, _ = view(nx, wk[S['l2shown'] - 0x4000])
    spr = nx.sprite_pixels()
    img = Image.new('RGB', (192, 112))
    for r in range(112):
        for p in range(192):
            v = spr.get((32 + p, 32 + r))
            img.putpixel((p, r), rgb(v if v is not None else nx.pal.get(rows[r][p], 0)))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('state', type=int)
    ap.add_argument('prefixes', nargs='+')
    ap.add_argument('--crop', type=int, nargs=4, default=None)
    ap.add_argument('--scale', type=int, default=4)
    a = ap.parse_args()
    for k, (frame, regs, ram) in enumerate(states('m0_states.bin')):
        if k == a.state:
            break
    ims = [shot(p, ram, regs) for p in a.prefixes]
    if a.crop:
        ims = [im.crop(a.crop) for im in ims]
    w, h = ims[0].size
    out = Image.new('RGB', (len(ims) * (w * a.scale + 8), h * a.scale), (255, 255, 255))
    for i, im in enumerate(ims):
        out.paste(im.resize((w * a.scale, h * a.scale), Image.NEAREST), (i * (w * a.scale + 8), 0))
    out.save(a.out)
    print('wrote', a.out, out.size)


if __name__ == '__main__':
    sys.exit(main())
