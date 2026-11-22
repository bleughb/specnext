p='C:/1NEXT/nexclash/games/castle_master.md'
s=open(p,encoding='utf-8',newline='').read()
nl='\r\n' if '\r\n' in s else chr(10)
def rep(a,b):
    global s
    a=a.replace('\n',nl); b=b.replace('\n',nl)
    assert s.count(a)==1,a
    s=s.replace(a,b)
rep("helped: the consumer probe (cm_consumers) found gameplay reads of the projected\n  polygons, which ruled out replacing the game's own redraw with a tween.","helped: cm_consumers found gameplay reads of the projected polygons: the\n  game's own redraw stays.")
rep("the gain is colour (as Quazatron).","the gain is colour.")
open(p,'w',encoding='utf-8',newline='').write(s)
