"""Assembled register/R bridge around the real copier, interrupts excluded.

Skips dynamic preparation/publication; not a whole-hook memory/IRQ proof. Tests
all caller registers incl R (both high-bit values), original SP/IFF and two game
copier paths. Negative changes only the assembled return-R immediate.
"""
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]/'nexclash'
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from asm2profile import assemble,sjasm
from nexclash import simpool,z80n
from nexclash.dizzy6 import _rw_simulator
from skoolkit.simulator import Simulator
from irq_capture import load


def until(sim, pc, limit=300000):
    for _ in range(limit):
        if sim.registers[24]==pc:return
        sim.opcodes[sim.memory[sim.registers[24]]]()
    raise RuntimeError(('bridge timeout',hex(sim.registers[24])))


def run():
    blocks,s=assemble(str(HERE/'publication_integrated.asm'),sjasm.find())
    states=[load(),json.loads(Path('/workspace/work/r_type_peak_state.json').read_text())]
    results=[]
    for state in states:
        for r0 in (0,1,63,127,128,255):
            mem=bytearray(0x4000)+bytearray(state['banks'][5])+bytearray(state['banks'][2])+bytearray(state['banks'][0])
            regs=state['registers'][:];regs[24]=0x8842;regs[15]=r0;regs[26]=1
            # Controlled caller return on the genuine game stack.
            regs[12]=0xFFF0;mem[0xFFF0:0xFFF2]=bytes.fromhex('0010')
            original=simpool.machine(Simulator,mem,regs,slot='bridge-original',copy=True)
            until(original,0x1000)
            for broken in (False,True):
                patched=simpool.machine(_rw_simulator(),mem,regs,slot='bridge-patched',copy=True)
                patched.memory[0x2000:0x2000+len(blocks['code'])]=blocks['code']
                patched.memory[0x8842:0x8845]=b'\xc3'+s['hook_entry'].to_bytes(2,'little')
                z80n.install(patched,lambda n,v:None)
                # Entry captures R and all original registers before private-stack work.
                until(patched,s['hook_save'])
                # Execute the save routine and stop at its caller return.
                sp=patched.registers[12];ret=patched.memory[sp]|patched.memory[sp+1]<<8
                until(patched,ret)
                patched.memory[s['hook_sp']:s['hook_sp']+2]=(0xFFF0).to_bytes(2,'little')
                patched.registers[12]=0x3D00
                # Load original inputs, preserving entry's captured R separately.
                patched.registers[24]=s['hook_load']
                patched.registers[12]=0x3CFE
                patched.memory[0x3CFE:0x3D00]=s['hook_copy_start'].to_bytes(2,'little')
                until(patched,s['hook_copy_start'])
                until(patched,s['copier_saved'])
                if broken:patched.memory[s['hook_r_add']+1]=(patched.memory[s['hook_r_add']+1]+1)&127
                patched.registers[24]=s['hook_finish']
                until(patched,0x1000)
                cmp=list(range(25))+[26,27,28]
                diffs=[i for i in cmp if original.registers[i]!=patched.registers[i]]
                if broken:assert 15 in diffs,('R negative escaped',state['frame'],r0)
                else:assert not diffs,(state['frame'],r0,[(i,original.registers[i],patched.registers[i])for i in diffs])
                results.append(dict(frame=state['frame'],R=r0,broken=broken,differences=diffs))
    Path('/workspace/work/r_type_integrated/register-bridge.json').write_text(json.dumps(dict(scope=__doc__,cases=results),indent=2)+'\n')
    print(len(results),'cases; good bridge exact incl R, wrong-R controls caught')


if __name__=='__main__':run()
