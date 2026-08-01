import sys,struct,collections
def recs(d):
    i=0
    while i<len(d):
        ln=struct.unpack('>H',d[i:i+2])[0]
        if ln<4: break
        yield d[i+2],d[i+3],d[i+4:i+ln]; i+=ln
d=open(sys.argv[1],'rb').read()
cur=dt=None; elem=None; ext=collections.defaultdict(lambda:[9e9,9e9,-9e9,-9e9]); allb=[9e9,9e9,-9e9,-9e9]
for rt,dty,p in recs(d):
    if rt in (0x08,0x09,0x0a,0x0c,0x2d): elem=rt
    elif rt==0x0d: cur=struct.unpack('>h',p)[0]
    elif rt==0x0e: dt=struct.unpack('>h',p)[0]
    elif rt==0x10 and elem==0x08:
        pts=[struct.unpack('>ii',p[i:i+8]) for i in range(0,len(p),8)]
        e=ext[(cur,dt)]
        for x,y in pts:
            e[0]=min(e[0],x); e[1]=min(e[1],y); e[2]=max(e[2],x); e[3]=max(e[3],y)
            allb[0]=min(allb[0],x); allb[1]=min(allb[1],y); allb[2]=max(allb[2],x); allb[3]=max(allb[3],y)
print(f"{sys.argv[1]}")
print(f"  overall bbox: ({allb[0]},{allb[1]})..({allb[2]},{allb[3]}) db units = {(allb[2]-allb[0])/1000:.3f} x {(allb[3]-allb[1])/1000:.3f} um")
for k in sorted(ext):
    e=ext[k]; print(f"  {k[0]:>3}/{k[1]:<3}  x[{e[0]:>6},{e[2]:>6}] y[{e[1]:>6},{e[3]:>6}]  ({(e[2]-e[0])/1000:.3f} x {(e[3]-e[1])/1000:.3f} um)")
