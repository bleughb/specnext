NL = chr(10)
N = chr(92) + 'n'
s = open('m3_mutants.py').read()
old = "        if src['glue'].count(a) != 1:" + NL + "            print('%s: pattern found %d times' % (name, src['glue'].count(a)))" + NL
assert s.count(old) == 1
new = ("        gl, cm = src['glue'], src['cmr']" + NL
       + "        if gl.count(a) == 1:" + NL + "            gl = gl.replace(a, b)" + NL
       + "        elif gl.count(a) == 0 and cm.count(a) == 1:" + NL + "            cm = cm.replace(a, b)" + NL
       + "        else:" + NL
       + "            print('%s: pattern found %d + %d times' % (name, gl.count(a), cm.count(a)))" + NL)
s = s.replace(old, new)
s = s.replace("write(src['glue'].replace(a, b).replace('SAVEBIN", "write(gl.replace('SAVEBIN")
s = s.replace("write(src['cmr'].replace('INCLUDE", "write(cm.replace('INCLUDE")
def q(*lines):
    return ' + '.join(("'" + x + N + "'") if x[:1] in '123456789.' or x.endswith(':') else ("T + '" + x + N + "'") for x in lines)
add = ("    # the speed pass (CMSRC=cm7): renderer maths, the PUSH run, the DMA copy" + NL
       + "    'k div32 without its rounding': (" + q('ex de,hl', 'jr c,5F', 'inc hl') + ", " + q('ex de,hl', 'jr c,5F') + ")," + NL
       + "    'l span: the third pixel below the PUSH run never written': (" + q('sbc a,a                         ; bit 0 = 3 pixels below m') + ", " + q('xor a') + ")," + NL
       + "    'm DMA chunks across the frame interrupt (no line gate)': (" + q('add a,18', 'cp 22', 'jr c,.cpu') + ", " + q('add a,18', 'cp 22') + ")," + NL
       + "    'n proj1: a failed step still counts': (" + q('sbc hl,de', 'dec a', '1:      inc a', 'ENDR') + ", " + q('sbc hl,de', '1:      inc a', 'ENDR') + ")," + NL)
old = "}" + NL + "CURSOR = "
assert s.count(old) == 1
s = s.replace(old, add + old)
open('m3_mutants.py', 'w').write(s)
