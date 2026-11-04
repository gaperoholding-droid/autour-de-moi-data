# -*- coding: utf-8 -*-
import json, urllib.request
from shapely.geometry import shape, mapping
UA={"User-Agent":"placette/1.0 (contact@commercesautourdemoi.fr)"}
def hj(u):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

def rnd(o,n=4):
    if isinstance(o,float): return round(o,n)
    if isinstance(o,list): return [rnd(x,n) for x in o]
    return o

TARIFS=[(2000,19),(5000,29),(10000,39),(20000,49),(50000,69),(float('inf'),89)]
def tier(pop):
    for mx,m in TARIFS:
        if (pop or 0)<mx: return m
    return 89

fc=hj("https://geo.api.gouv.fr/epcis/200046977/communes?geometry=contour&format=geojson&fields=nom,code,population")
feats=[f for f in fc["features"] if f["properties"].get("code")!="69123"]
print("communes epci (hors Lyon):",len(feats))
for i in range(1,10):
    code="6938%d"%i
    d=hj("https://geo.api.gouv.fr/communes/"+code+"?geometry=contour&format=geojson&fields=nom,code,population")
    f=d if d.get("type")=="Feature" else d["features"][0]
    feats.append(f); print("  +",f["properties"].get("nom"))

out={"type":"FeatureCollection","features":[]}
for f in feats:
    try:
        g=shape(f["geometry"]).buffer(0).simplify(0.0006, preserve_topology=True)
        gm=mapping(g)
    except Exception as e:
        gm=f["geometry"]
    gm=json.loads(json.dumps(gm))
    gm["coordinates"]=rnd(gm["coordinates"])
    p=f["properties"]
    out["features"].append({"type":"Feature","properties":{
        "nom":p.get("nom"),"code":p.get("code"),"pop":p.get("population"),"prix":tier(p.get("population"))
    },"geometry":gm})

txt=json.dumps(out,ensure_ascii=False,separators=(",",":"))
open("build/_metropole.geojson","w",encoding="utf-8").write(txt)
print("FEATURES:",len(out["features"]),"| taille:",round(len(txt.encode())/1024),"Ko")
