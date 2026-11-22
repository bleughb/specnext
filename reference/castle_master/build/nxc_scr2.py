p='C:/1NEXT/nxc/tools/nxc.py'
s=open(p,encoding='utf-8',newline='').read()
cr=chr(13)+chr(10) in s
if cr: s=s.replace(chr(13)+chr(10),chr(10))
def rep(a,b,n=1):
    global s
    assert s.count(a)==n,(s.count(a),a)
    s=s.replace(a,b)
rep("MENU_KEYS = ('publisher', 'patch_by', 'colours_by', 'fix_label', 'colours_label', 'version', 'game_language_name')","MENU_KEYS = ('publisher', 'patch_by', 'colours_by', 'fix_label', 'colours_label', 'version', 'game_language_name', 'build_screen')")
rep("INFO_KEYS = ('publisher', 'patch_by', 'colours_by', 'fix_label', 'colours_label', 'version', 'game_language_name', 'build',","INFO_KEYS = ('publisher', 'patch_by', 'colours_by', 'fix_label', 'colours_label', 'version', 'game_language_name', 'build_screen', 'build',")
rep("l.startswith((b'fix_label=', b'colours_label=', b'version=', b'game_language_name='))]","l.startswith((b'fix_label=', b'colours_label=', b'version=', b'game_language_name=', b'build_screen='))]")
rep("    elif key == 'version': check_version(value)\n","    elif key == 'version': check_version(value)\n    elif key == 'build_screen' and value != '1': raise Wrong('build_screen is 1, or empty to remove it: the loader shows bank 5\'s screen while it builds')\n")
if cr: s=s.replace(chr(10),chr(13)+chr(10))
open(p,'w',encoding='utf-8',newline='').write(s)
