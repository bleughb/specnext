s=open('m2_build.py',encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,a
    s=s.replace(a,b)
rep("    ap.add_argument('--prefix', default='cm2')\n    a = ap.parse_args()\n",
"""    ap.add_argument('--prefix', default='cm2')
    ap.add_argument('--mono', action='store_true', help='col_on = 0: the original look (the .nxc colour set)')
    ap.add_argument('--screen', help='a 6,912-byte loading screen for the NEX header (game data: local only)')
    ap.add_argument('--delay', type=int, default=255, help='frames the loader waits before the start (with --screen)')
    a = ap.parse_args()
    global MONO
    MONO = a.mono
""")
rep("    print('Boot check:', 'OK' if not bad else bad)\n",
"""    print('Boot check:', 'OK' if not bad else bad)
    if a.screen and not bad:            # as nexclash's loading_nex: the ULA screen after the header, a start delay
        scr, nex = open(a.screen, 'rb').read(), open(a.o, 'rb').read()
        assert len(scr) == 6912 and nex[10] == 0
        h = bytearray(nex[:512])
        h[10], h[133] = 2, a.delay
        open(a.o, 'wb').write(bytes(h) + scr + nex[512:])
        print('Screen    : %s, start delay %d frames' % (a.screen, a.delay))
""")
rep("def main():","MONO = False\n\n\ndef main():")
open('m2_build.py','w',encoding='utf-8').write(s)
