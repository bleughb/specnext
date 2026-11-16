"""One interface over CSpect (control server) and JNext (scripts) for the R-Type tests.

run(nex, updates, shots=(), keys=None, emulator=None, out=DIR) -> Run
  Plays a .nex from its start until game update max(updates) + 1 (probe 8649, the main loop),
  recording the frames each update took and a screenshot after the drawing of each update in
  `shots` is complete (868C, the native wait). keys: [(update, [keys], held_updates)] pressed at
  exact game updates (JNext only).
Frames per update come from the game itself on CSpect (7A8A counts interrupts and is read at 8649
before the game clears it) and from JNext's frame counter; both are checked against each other by
selfcheck(). A run that does not reach every requested update raises.
"""
import base64
import collections
import glob
import json
import os
import re
import urllib.request
from pathlib import Path

import rtenv

PROBE, WAIT, FRAMES, IRQ = 0x8649, 0x868C, 0x7A8A, 0x8383


class Run:
    def __init__(self, emulator, frames, shots, info=None):
        self.emulator, self.frames, self.shots, self.info = emulator, frames, shots, info or {}

    def histogram(self):
        return dict(sorted(collections.Counter(self.frames[1:]).items()))


class CSpect:
    def __init__(self, url=None):
        self.url, self.n = url or rtenv.CSPECT_URL, 0

    def call(self, name, **args):
        self.n += 1
        body = json.dumps({'jsonrpc': '2.0', 'id': self.n, 'method': 'tools/call',
                           'params': {'name': name, 'arguments': args}}).encode()
        req = urllib.request.Request(self.url, body, {'Content-Type': 'application/json',
                                                      'Accept': 'application/json'})
        res = json.load(urllib.request.urlopen(req, timeout=150))
        if 'error' in res:
            raise RuntimeError('CSpect %s: %s' % (name, res['error']))
        return res['result']

    def text(self, name, **args):
        return '\n'.join(c.get('text', '') for c in self.call(name, **args)['content'] if c['type'] == 'text')

    def byte(self, addr):
        t = self.text('read_memory', address='$%04X' % addr, length=1)
        m = re.search(r'\$%04X\s+([0-9A-F]{2})' % addr, t)
        if not m:
            raise RuntimeError('CSpect read_memory: unexpected reply %r' % t[:80])
        return int(m.group(1), 16)

    def pc(self):
        m = re.search(r'PC \$([0-9A-F]{4})', self.text('get_status'))
        return int(m.group(1), 16) if m else None

    def run_to(self, addr, timeout_ms=60000):
        self.text('run_to', address='$%04X' % addr, timeout_ms=timeout_ms)
        pc = self.pc()
        if pc != addr:
            raise RuntimeError('CSpect: did not reach %04X within %d ms (PC %s)' % (
                addr, timeout_ms, None if pc is None else '%04X' % pc))

    def screenshot(self, path):
        for c in self.call('screenshot', scale=2)['content']:
            if c['type'] == 'image':
                Path(path).write_bytes(base64.b64decode(c['data']))
                return path
        raise RuntimeError('CSpect: no screenshot image')


def run_cspect(nex, updates, shots, out):
    cs = CSpect()
    cs.text('clear_breakpoint', all=True)
    cs.text('load_nex', path=str(Path(nex).resolve()))
    last = max(updates)
    frames, files = [], {}
    for u in range(1, last + 2):
        cs.run_to(PROBE)
        frames.append(cs.byte(FRAMES) if u > 1 else 0)    # interrupts during the previous update
        if u in shots:
            cs.run_to(WAIT)          # the update's drawing is complete ...
            cs.run_to(IRQ)           # ... and displayed: CSpect shows a screen write made after the
            cs.run_to(IRQ)           # beam passed one frame later (the control's copier), so wait two
            files[u] = cs.screenshot(Path(out) / ('u%05d.png' % u))
    cs.text('run')
    return Run('cspect', frames, files)


def run_jnext(nex, updates, shots, out, keys=None):
    from nexclash import jnext as J
    d = Path(out)
    s = J.Script(J.start_frame(str(nex)))
    s.var('u')
    s.var('shot')
    s.rule('on execute %d do\n  set u = u + 1\n  set shot = 0\n  log "U u=${u} F=${FRAME}"\nend\n' % PROBE)
    s.rule('on execute %d do\n  set shot = 1\nend\n' % WAIT)
    for n in shots:
        s.rule('on frame when u == %d and shot == 1 do\n  screenshot "%s/u%05d.png"\n  set shot = 2\nend\n'
               % (n, d.as_posix(), n))
    for at, k, held in keys or ():
        s.rule('on execute %d when u == %d do\n%s  log "KEY D u=${u} %s"\nend\n' % (PROBE, at, J.down(k), '+'.join(k)))
        s.rule('on execute %d when u == %d do\n%s  log "KEY U u=${u}"\nend\n' % (PROBE, at + held, J.up(k)))
    last = max(updates)
    s.rule('on execute %d when u == %d do\n  exit 0\nend\n' % (PROBE, last + 2))
    s.exit_at(60 * (last + 2) + 3000)
    code = J.run_all([(str(nex), s.text(), str(d), 60 * (last + 2) + 3100, rtenv.CARD, rtenv.JNEXT_HOME)],
                     timeout=7200)
    if code != [0]:
        raise RuntimeError('JNext exit %s (%s)' % (code, d / 'run.log'))
    F = [int(m[1]) for line in open(d / 'run.log') for m in [re.search(r'U u=\d+ F=(\d+)', line)] if m]
    pressed = sum(1 for line in open(d / 'run.log') if ' KEY D ' in line)
    if keys and pressed != len(keys):
        raise RuntimeError('only %d of %d scheduled key presses happened' % (pressed, len(keys)))
    frames = [0] + [b - a for a, b in zip(F, F[1:])]
    files = {n: d / ('u%05d.png' % n) for n in shots if (d / ('u%05d.png' % n)).exists()}
    return Run('jnext', frames, files, {'keys pressed': pressed})


def run(nex, updates, shots=(), keys=None, emulator=None, out=None, say=print):
    need = ('update_keys',) if keys else ()
    emu = emulator or rtenv.emulator(need, say)
    out = Path(out or rtenv.OUT / 'tests' / Path(nex).stem)
    out.mkdir(parents=True, exist_ok=True)
    for f in glob.glob(str(out / 'u*.png')):
        os.remove(f)
    shots = sorted(set(shots))
    if emu == 'cspect':
        if keys:
            raise RuntimeError('keys at exact game updates need JNext')
        r = run_cspect(nex, updates, shots, out)
    else:
        r = run_jnext(nex, updates, shots, out, keys)
    if len(r.frames) < max(updates) + 1:
        raise RuntimeError('%s reached only %d of %d updates' % (emu, len(r.frames) - 1, max(updates)))
    missing = [n for n in shots if n not in r.shots]
    if missing:
        raise RuntimeError('%s: no screenshot at updates %s' % (emu, missing))
    return r


def paper(path):
    """The 256x192 paper of a screenshot from either emulator (both include the border)."""
    from PIL import Image
    im = Image.open(path).convert('RGB')
    s = im.width // 320
    return im.crop((32 * s, 32 * s, 288 * s, 224 * s)).resize((256, 192), Image.NEAREST)
