import sys, struct, collections
RT={0x00:'HEADER',0x01:'BGNLIB',0x02:'LIBNAME',0x03:'UNITS',0x04:'ENDLIB',0x05:'BGNSTR',
0x06:'STRNAME',0x07:'ENDSTR',0x08:'BOUNDARY',0x09:'PATH',0x0a:'SREF',0x0b:'AREF',0x0c:'TEXT',
0x0d:'LAYER',0x0e:'DATATYPE',0x0f:'WIDTH',0x10:'XY',0x11:'ENDEL',0x12:'SNAME',0x13:'COLROW',
0x16:'TEXTTYPE',0x17:'PRESENTATION',0x19:'STRING',0x1a:'STRANS',0x1b:'MAG',0x1c:'ANGLE',
0x21:'PATHTYPE',0x22:'GENERATIONS',0x2d:'BOX',0x2e:'BOXTYPE'}
def real8(b):
    e=b[0]&0x7f; s=-1 if b[0]&0x80 else 1
    m=int.from_bytes(b[1:8],'big')/(1<<56)
    return s*m*(16.0**(e-64))
def recs(d):
    i=0
    while i<len(d):
        ln=struct.unpack('>H',d[i:i+2])[0]
        if ln<4: break
        rt,dt=d[i+2],d[i+3]; yield rt,dt,d[i+4:i+ln]; i+=ln
f=sys.argv[1]; d=open(f,'rb').read()
counts=collections.Counter(); layers=collections.Counter(); cur=None; elem=None
verts=0; structs=[]; units=None; srefs=collections.Counter()
for rt,dt,pay in recs(d):
    n=RT.get(rt,hex(rt)); counts[n]+=1
    if n=='UNITS': units=(real8(pay[0:8]),real8(pay[8:16]))
    elif n=='STRNAME': structs.append(pay.rstrip(b'\0').decode())
    elif n in ('BOUNDARY','PATH','SREF','TEXT','BOX'): elem=n
    elif n=='LAYER': cur=struct.unpack('>h',pay)[0]
    elif n=='DATATYPE' and elem: layers[(cur,struct.unpack('>h',pay)[0],elem)]+=1
    elif n=='SNAME': srefs[pay.rstrip(b'\0').decode()]+=1
    elif n=='XY': verts+=len(pay)//8
print(f"== {f}  ({len(d)} bytes)")
print(f"UNITS: user_unit={units[0]:.6g}  db_unit_in_metres={units[1]:.6g}  -> 1 db unit = {units[1]*1e9:.3f} nm")
print(f"structures: {structs}")
print(f"total XY vertices: {verts}")
print("records:", dict(counts.most_common()))
print("(layer,datatype,element) -> count:")
for k,v in sorted(layers.items()): print(f"   {k[0]:>3}/{k[1]:<3} {k[2]:<9} {v}")
if srefs: print("SREFs:", dict(srefs))
