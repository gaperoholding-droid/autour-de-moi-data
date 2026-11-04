# -*- coding: utf-8 -*-
import json, urllib.request
BASE="https://gaperoholding-droid.github.io/autour-de-moi-data/"
UA={"User-Agent":"placette/1.0"}
CODES=['69003', '69029', '69033', '69034', '69040', '69044', '69046', '69063', '69068', '69069', '69071', '69072', '69081', '69085', '69087', '69088', '69089', '69091', '69096', '69100', '69116', '69117', '69127', '69142', '69143', '69149', '69153', '69163', '69168', '69191', '69194', '69199', '69202', '69204', '69205', '69207', '69233', '69244', '69250', '69256', '69259', '69260', '69266', '69271', '69273', '69275', '69276', '69278', '69279', '69282', '69283', '69284', '69286', '69290', '69292', '69293', '69296', '69381', '69382', '69383', '69384', '69385', '69386', '69387', '69388', '69389']
def get(p):
    with urllib.request.urlopen(urllib.request.Request(BASE+p,headers=UA),timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))
tc=ts=tl=0; manquants=[]
for code in CODES:
    try:
        d=get("c/"+code+".json")
        tc+=len(d.get("c",[])); ts+=len(d.get("s",[])); tl+=len(d.get("l",[]))
    except Exception as e:
        manquants.append(code)
print("Communes comptées :", len(CODES)-len(manquants), "/", len(CODES))
if manquants: print("Manquants :", manquants)
print("COMMERCES  :", tc)
print("ENTREPRISES/SERVICES :", ts)
print("LIBERAUX   :", tl)
print("TOTAL      :", tc+ts+tl)
