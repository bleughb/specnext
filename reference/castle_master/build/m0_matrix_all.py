"""All 72 x 72 (yaw, pitch) pairs: the original 0x9776 run in a sandbox vs m0_matrix.view_matrix."""
from m0_lib import states, CSimulator, s8
from m0_matrix import view_matrix
frame, regs, ram = next(states())
bad = 0
for yaw in range(72):
    for pitch in range(72):
        m = bytearray(ram); m[27319] = yaw; m[27318] = pitch
        c = CSimulator(m); R = c.registers
        R[12] = 0xFF00; R[26] = 0
        c.run(38774, 38904)
        got = [s8(c.memory[a]) for a in range(24149, 24158)]
        if got != view_matrix(yaw, pitch, bytes(m[29337:29337 + 146])):
            bad += 1
print('all angles: %d of %d differ' % (bad, 72 * 72))
