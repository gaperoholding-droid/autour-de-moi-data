# -*- coding: utf-8 -*-
import json, urllib.request
UA={"User-Agent":"placette/1.0 (contact@commercesautourdemoi.fr)"}
def hj(u):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))
TARIFS=[(2000,19),(5000,29),(10000,39),(20000,49),(50000,69),(float('inf'),89)]
def tier(pop):
    for mx,m in TARIFS:
        if pop<mx: return m
    return 89

communes=hj("https://geo.api.gouv.fr/epcis/200046977/communes?fields=nom,code,population")
# scénario A : Lyon = 1 commune
totA=sum(tier(c.get('population') or 0) for c in communes)

# scénario B : Lyon remplacée par ses 9 arrondissements
arr=[]
for i in range(1,10):
    code="6938%d"%i
    try:
        g=hj("https://geo.api.gouv.fr/communes/"+code+"?fields=nom,population")
        arr.append((g.get('nom'),g.get('population') or 0))
    except Exception as e:
        print("arr echec",code,str(e)[:60])
print("Arrondissements de Lyon :")
for nom,pop in arr:
    print("  %-26s %7d -> %d€/mois"%(nom,pop,tier(pop)))
sum_arr=sum(tier(p) for _,p in arr)
# retirer Lyon (69123) et ajouter les arrondissements
lyon=[c for c in communes if c.get('code')=="69123"]
lyon_m=tier(lyon[0].get('population') or 0) if lyon else 89
totB=totA - lyon_m + sum_arr
nbB=len(communes)-1+len(arr)

print("\n=== TOTAUX MENSUELS (prix catalogue) ===")
print("A) Lyon = 1 commune  (%d entités) : %d €/mois = %d €/an"%(len(communes),totA,totA*12))
print("B) Lyon = 9 arrond.  (%d entités) : %d €/mois = %d €/an"%(nbB,totB,totB*12))
print("   (les 9 arrondissements pèsent %d €/mois au lieu de %d €)"%(sum_arr,lyon_m))

print("\n=== TARIFS NÉGOCIÉS (sur le scénario B, %d €/mois catalogue) ==="%totB)
for remise in (10,15,20,25,30):
    m=totB*(1-remise/100)
    print("  -%2d%% : %6.0f €/mois  |  %7.0f €/an"%(remise,m,m*12))
