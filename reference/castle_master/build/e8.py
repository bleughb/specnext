s=open('m3_sim.py',encoding='utf-8').read()
a="        pshow = before[0x7349] >= 2 and 'ov_pstep' in S "
assert a in s
s=s.replace(a,"        dshow = before[0x7349] == 1 and 'h_dshow' in S         # the dissolve's view: in colour after it (h_off1)\n        pshow = dshow or before[0x7349] >= 2 and 'ov_pstep' in S ",1)
b="            res['portcullis shows in colour'] += 1"
assert b in s
s=s.replace(b,"            res['dissolve ends in colour' if dshow else 'portcullis shows in colour'] += 1",1)
open('m3_sim.py','w',encoding='utf-8').write(s)
