# -*- coding: utf-8 -*-
import json, urllib.request
UA={"User-Agent":"placette/1.0 (contact@commercesautourdemoi.fr)"}
def hj(u):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))
communes=None
for url in ("https://geo.api.gouv.fr/departements/69M/communes?fields=nom,code,population",
            "https://geo.api.gouv.fr/epcis/200046977/communes?fields=nom,code,population"):
    try:
        d=hj(url)
        if isinstance(d,list) and d: communes=d; print("source:",url); break
    except Exception as e:
        print("echec",url,str(e)[:80])
if not communes:
    raise SystemExit("pas de communes")
TARIFS=[(2000,19,205),(5000,29,313),(10000,39,421),(20000,49,529),(50000,69,745),(float('inf'),89,961)]
def tier(pop):
    for mx,m,a in TARIFS:
        if pop<mx: return m,a
    return 89,961
communes.sort(key=lambda c:-(c.get('population') or 0))
tot_m=tot_a=0; cnt={}
print("%-30s %9s  %-8s %-8s"%("Commune","Habitants","Mensuel","Annuel"))
for c in communes:
    pop=c.get('population') or 0
    m,a=tier(pop); tot_m+=m; tot_a+=a; cnt[m]=cnt.get(m,0)+1
    print("%-30s %9d  %4d€/mois %5d€/an"%(c['nom'],pop,m,a))
print("---")
print("Nombre de communes :", len(communes))
print("Répartition par tranche (prix mensuel -> nb communes):", dict(sorted(cnt.items())))
print("TOTAL MENSUEL : %d €/mois  (soit %d €/an en payant au mois)"%(tot_m,tot_m*12))
print("TOTAL ANNUEL (formule annuelle -10%%) : %d €/an"%tot_a)
