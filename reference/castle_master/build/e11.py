s=open('m2_build.py',encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,a
    s=s.replace(a,b)
i=s.index("    if a.screen and not bad:"); j=s.index("    return 1 if bad else 0")
s=s[:i]+"    if a.screen:\n        print('Screen    : %s as the image\'s screen, held by the start-up code (scr_on)' % a.screen)\n"+s[j:]
rep("    ap.add_argument('--screen', help='a 6,912-byte loading screen for the NEX header (game data: local only)')\n    ap.add_argument('--delay', type=int, default=255, help='frames the loader waits before the start (with --screen)')\n",
    "    ap.add_argument('--screen', help='a 6,912-byte loading screen: the image\'s own screen until the start-up code '\n                    'puts the game\'s back (cm11 on: scr_on; game data, local only)')\n")
rep("    global MONO\n    MONO = a.mono\n","    global MONO, SCREEN\n    MONO = a.mono\n    SCREEN = open(a.screen, 'rb').read() if a.screen else None\n    assert SCREEN is None or len(SCREEN) == 6912\n")
rep("    patch = CastlePatch(a.prefix)\n    snap,","    patch = CastlePatch(a.prefix)\n    patch.for_check = True              # the boot check's reference: the game's own screen at the entry\n    snap,")
rep("MONO = False\n","MONO = False\nSCREEN = None\n")
rep("        snap.banks[5], snap.banks[2], snap.banks[0] = bytes(ram[0:16384])",
"""        if SCREEN is not None and not getattr(self, 'for_check', False):
            o = self.S['scr_on'] - 0xD000
            assert self.stub_extra[o] == 0
            self.stub_extra = self.stub_extra[:o] + bytes([1]) + self.stub_extra[o + 1:]
            self.hook_page_data = bytes(ram[0:6912])
            ram[0:6912] = SCREEN
        snap.banks[5], snap.banks[2], snap.banks[0] = bytes(ram[0:16384])""")
open('m2_build.py','w',encoding='utf-8').write(s)
