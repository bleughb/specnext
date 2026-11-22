s=open('m2_build.py','rb').read()
assert s.count(b"+ b'\x00' +")==1
s=s.replace(b"+ b'\x00' +",b"+ bytes(1) +")
open('m2_build.py','wb').write(s)
