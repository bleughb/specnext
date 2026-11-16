"""R-Type test environment: paths and the emulator to use (README.md in this folder).

Every path can be set by an environment variable; the defaults are the original setup
(/workspace/work, the private card in /workspace/scratch) and, on Windows, the same paths through
C:\\workspace junctions. Nothing here downloads or installs anything.

Emulator order (RTYPE_EMULATOR = auto | cspect | jnext; default auto):
  1. CSpect, when its control server answers at CSPECT_MCP_URL, or CSPECT_EXE exists and opens one
     when started with -mcp. The control server (MCP) needs CSpect's paid Builder tier: most users'
     CSpect will not answer, and auto then falls back to JNext. Set RTYPE_CSPECT_START=0 to never
     start CSpect (only use one already running);
  2. JNext, when NEXCLASH_JNEXT (or jnext on PATH) and an SD card image exist;
  3. otherwise a clear error naming what is missing.
A test that needs something CSpect cannot do (keys at exact game updates) asks for JNext itself and
says so; it never silently changes what it measures.
"""
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTAKE = HERE.parent
REF = INTAKE.parent
NEXCLASH = REF.parents[2] / 'nexclash'
for p in (str(NEXCLASH), str(INTAKE), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

WIN = os.name == 'nt'


def _first(*cands):
    for c in cands:
        if c and Path(c).exists():
            return str(c)
    return None


WORK = Path(os.environ.get('RTYPE_WORK') or ('C:/workspace/work' if WIN else '/workspace/work'))
CARD = os.environ.get('NEXCLASH_JNEXT_CARD') or os.environ.get('RTYPE_CARD') or _first(
    'C:/workspace/scratch/cspect-next-2gb.img' if WIN else '/workspace/scratch/cspect-next-2gb.img',
    'C:/1NEXT/cspect-next-2gb.img')
JNEXT = os.environ.get('NEXCLASH_JNEXT') or shutil.which('jnext') or _first(
    'C:/1NEXT/jnext-1.2.0-windows-x64/jnext.exe', '/workspace/work/jnext-bin/root/usr/bin/jnext')
JNEXT_HOME = os.environ.get('NEXCLASH_JNEXT_HOME') or str(WORK / 'r_type_jnext_home')
CSPECT_EXE = os.environ.get('CSPECT_EXE') or _first('C:/CSpect/CSpect.exe')
CSPECT_URL = os.environ.get('CSPECT_MCP_URL') or 'http://127.0.0.1:8765/mcp'
OUT = WORK / 'r_type_l2scroll'


def describe():
    return {'work': str(WORK), 'card': CARD, 'jnext': JNEXT, 'cspect': CSPECT_EXE, 'cspect_url': CSPECT_URL}


def cspect_up(timeout=2):
    try:
        req = urllib.request.Request(CSPECT_URL, b'{"jsonrpc":"2.0","id":0,"method":"tools/list"}',
                                     {'Content-Type': 'application/json', 'Accept': 'application/json'})
        urllib.request.urlopen(req, timeout=timeout).read()
        return True
    except Exception:            # noqa: BLE001 - any failure means "not answering"
        return False


_NO_SERVER = WORK / '.cspect_no_mcp'      # remembers a CSpect that never opened its server


def start_cspect(nex=None, wait=60):
    """Start CSpect with its control server (no SD card needed: it loads .nex files directly).
    A CSpect without the Builder tier never opens the server: it is closed again, and the result is
    remembered (delete RTYPE_WORK/.cspect_no_mcp after an upgrade)."""
    if cspect_up():
        return True
    if not CSPECT_EXE or os.environ.get('RTYPE_CSPECT_START') == '0' or _NO_SERVER.exists():
        return False
    args = [CSPECT_EXE, '-mcp', '-w2', '-zxnext', '-mmc=%s/' % str(Path(nex).parent if nex else WORK)]
    if nex:
        args.append(str(nex))
    proc = subprocess.Popen(args, cwd=str(Path(CSPECT_EXE).parent), stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t = time.time()
    while time.time() - t < wait:
        if cspect_up():
            return True
        time.sleep(2)
    proc.terminate()
    try:
        WORK.mkdir(parents=True, exist_ok=True)
        _NO_SERVER.write_text('CSpect at %s did not open its control server (Builder tier needed)' % CSPECT_EXE + chr(10))
    except OSError:
        pass
    return False


def emulator(need=(), say=print):
    """'cspect' or 'jnext' by the order above. need: capabilities the test requires; 'update_keys'
    (keys pressed at exact game updates) and 'card' (NextZXOS boot) are JNext only."""
    want = (os.environ.get('RTYPE_EMULATOR') or 'auto').lower()
    jnext_ok = bool(JNEXT and CARD)
    cs_only_missing = [n for n in need if n in ('update_keys', 'card')]
    if want in ('auto', 'cspect') and not cs_only_missing:
        if cspect_up() or start_cspect():
            return 'cspect'
        if want == 'cspect':
            raise SystemExit('CSpect requested but its control server is not answering at %s '
                             '(CSPECT_EXE=%s)' % (CSPECT_URL, CSPECT_EXE))
        say('emulator: CSpect not available, using JNext')
    elif cs_only_missing and want != 'jnext':
        say('emulator: this test needs %s, which only JNext provides' % ', '.join(cs_only_missing))
    if not jnext_ok:
        raise SystemExit('no emulator: CSpect not answering and JNext needs NEXCLASH_JNEXT (%s) and an '
                         'SD card image (%s); see README.md' % (JNEXT, CARD))
    os.environ.setdefault('NEXCLASH_JNEXT', JNEXT)
    os.environ.setdefault('NEXCLASH_JNEXT_HOME', JNEXT_HOME)
    return 'jnext'
