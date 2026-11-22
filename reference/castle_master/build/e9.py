s=open('m3_sim.py',encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,a
    s=s.replace(a,b)
rep("        nx.nr[1], nx.int_line = int(a.core, 16), a.intline\n",
    "        nx.nr[1], nx.int_line = int(a.core, 16), a.intline\n        cdis = ram[0x7349] == 1 and 'h_dpass' in S           # a view by the dissolve, the last view on Layer 2:\n        if cdis:                                              # the dissolve runs in colour (m3_dshow)\n            nx.nr[0x69], nx.nr[0x15] = 0x80, 1\n")
rep("        if (nonview or pshow) and got.get('at9f19', (0, 0)) != (0, 0):",
    "        if (nonview or pshow) and got.get('at9f19', (0, 0)) != ((0x80, 1) if cdis else (0, 0)):")
rep("            res['dissolve ends in colour' if dshow else 'portcullis shows in colour'] += 1",
    "            res['dissolve in colour' if cdis else 'dissolve ends in colour' if dshow else 'portcullis shows in colour'] += 1")
rep("            if outside_a or any(rows_a[r][p] != STALE + bit(before, r, p) for r in range(112) for p in range(192)):\n                errs.append('the bank shown before has changed')",
    "            if cdis:\n                if outside_a or rows_a != want:\n                    errs.append('colour dissolve: the bank it ran on is not the new view')\n            elif outside_a or any(rows_a[r][p] != STALE + bit(before, r, p) for r in range(112) for p in range(192)):\n                errs.append('the bank shown before has changed')")
open('m3_sim.py','w',encoding='utf-8').write(s)
