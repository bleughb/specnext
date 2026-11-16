"""R-Type intake: plain conversion with the snapshot's printer buffer restored.

Build/start-up proof only. The chosen tail also needs the full memory-access scan
before hardware delivery. No figure instructions are patched by this script.
"""
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'nexclash'))
from nexclash import midres, nextboot, z80tonex as zt

class Plain:
    name = 'R-Type plain printer restoration'
    uses_printer_buffer = False
    hook_page_data = b''
    extra_banks = {}
    sites = []
    slot1 = None
    setup_call = zt.STUB_ORG + 0x1000
    stub_extra = b''

    def apply(self, snap):
        printer = bytes(snap.read(a) for a in range(0x5B00, 0x5C00))
        # Original data first, then the converter copies its own temporary tail.
        self.stub_extra = (b'\x21' + zt.w16(self.setup_call + 12) + b'\x11\x00\x5B'
                           + b'\x01\x00\x01\xED\xB0\xC9' + printer)
        assert len(self.stub_extra) == 268


def build(src, dst):
    return zt.convert(str(src), str(dst), tail_req=0x5B00, force50=True,
                      quiet=True, patch=Plain())


def check(src, dst):
    snap, tail, code, _ = build(src, dst)
    bad = midres.boot_check(str(dst), str(src))
    for loaded in (False, True):
        bad += nextboot.check(str(dst), str(src), tail=(tail, tail + len(code)), nexload=loaded)
        state = nextboot.boot(str(dst), snap.pc, nexload=loaded)
        if state['R'][15] != snap.r:
            bad.append(('R differs', loaded, state['R'][15], snap.r))
    # Remove only restoration code in the built stub; both paths use the same tail.
    from nexclash.recolour import nex_offsets
    broken = bytearray(dst.read_bytes())
    broken[nex_offsets(broken)[10] + 0x1000] = 0xC9
    negative = dst.with_name(dst.stem + '-negative.nex')
    negative.write_bytes(broken)
    caught = nextboot.check(str(negative), str(src), tail=(tail, tail + len(code)), nexload=True)
    negative.unlink()
    if not any(p[0] == 'RAM differs' for p in caught):
        bad.append(('negative control escaped', caught))
    return dict(md5=hashlib.md5(dst.read_bytes()).hexdigest(), tail=[tail, tail + len(code)],
                boot_problems=bad, negative_control=caught,
                scope='All 8 NEX game banks, boot registers including R, mapped RAM and ROM; with/without NEXLOAD')


if __name__ == '__main__':
    src = HERE.parent / 'Rtype.z80'
    assert hashlib.md5(src.read_bytes()).hexdigest() == '5a2179b4006d7888a1f7f821a4316bf5'
    result = check(src, HERE.parent / 'Rtype.nex')
    (HERE / 'plain-boot.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if result['boot_problems']:
        raise SystemExit(1)
