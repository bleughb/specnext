"""Assembled text classifier/trampoline ABI + R checks, all four real plot entries.

Crosses all R high-bit/rollover seeds with text, reused-owner normal graphics,
wrong dimensions/signature and a text-to-enemy role change on the same owner.
"""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash'
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from asm2profile import assemble,sjasm
from nexclash import simpool,z80tonex as Z
from nexclash.dizzy6 import _rw_simulator
from register_bridge import until


def run():
    blocks,s=assemble(str(HERE/'publication_integrated.asm'),sjasm.find())
    snap=Z.Z80Snapshot(str(HERE/'review/credits.z80'))
    base=bytearray((snap.read(a) or 0)for a in range(65536))
    signature=bytes.fromhex('05007e18181818181805004141417f41414105001f3161417f414105006171795d4f')
    assert base[0xCAFF:0xCAFF+len(signature)]==signature
    cases=[]
    for pc,size in [(0x8CFD,3),(0x8D65,4),(0x8DD3,3),(0x8E29,4)]:
        for r0 in (0,127,128,255):
            for kind in ('text','graphic','dimensions','signature','reuse'):
                mem=base[:];mem[0x7A9C]=0x88
                regs=[0]*30;regs[0]=0xBE;regs[1]=0xD5;regs[2:8]=[3,5,21,24,0xCA,0xFF]
                regs[8:12]=[0x80,0x84,0x85,0x40];regs[12]=0x3C00;regs[14]=0x84;regs[15]=r0;regs[16:24]=[1,2,3,4,5,6,7,8];regs[24]=pc;regs[26]=1;regs[27]=2
                if kind in ('graphic','reuse'):regs[6]=0xC0
                if kind=='dimensions':regs[4]=20
                if kind=='signature':mem[0xCAFF]^=1
                original=simpool.machine(_rw_simulator(),mem,regs,slot='text-o',copy=True);until(original,pc+size)
                patched=simpool.machine(_rw_simulator(),mem,regs,slot='text-p',copy=True)
                patched.memory[0x2000:0x2000+len(blocks['code'])]=blocks['code']
                patched.memory[pc:pc+3]=b'\xc3'+s['text_%04x'%pc].to_bytes(2,'little')
                patched.memory[s['text_owners']+0x88]=1 if kind=='reuse' else 0
                until(patched,pc+size)
                diffs=[i for i in list(range(25))+[26,27,28]if original.registers[i]!=patched.registers[i]]
                assert not diffs,(hex(pc),r0,kind,[(i,original.registers[i],patched.registers[i])for i in diffs])
                tag=patched.memory[s['text_owners']+0x88]
                assert tag==(kind=='text'),(hex(pc),kind,tag)
                cases.append(dict(site=hex(pc),R=r0,kind=kind,tag=tag))
    Path('/workspace/work/r_type_integrated/text-check.json').write_text(json.dumps(cases,indent=2)+'\n')
    print(len(cases),'text classifier cases PASS, registers/R exact')

if __name__=='__main__':run()
