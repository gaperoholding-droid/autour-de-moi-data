# -*- coding: utf-8 -*-
"""Calcul du chiffre d'affaires potentiel - Saint-Etienne Metropole.
Recupere les communes de l'EPCI via geo.api.gouv.fr + applique la grille tarifaire Placette."""
import json, urllib.request

EPCI = "244200770"  # Saint-Etienne Metropole
URL = "https://geo.api.gouv.fr/epcis/%s/communes?fields=nom,population,code" % EPCI

# Grille tarifaire (mensuel, annuel) - meme logique que le site : pop < max -> ce palier
TARIFS = [
    (2000,    "Moins de 2 000",   19, 205),
    (5000,    "2 000 a 5 000",    29, 313),
    (10000,   "5 000 a 10 000",   39, 421),
    (20000,   "10 000 a 20 000",  49, 529),
    (50000,   "20 000 a 50 000",  69, 745),
    (10**12,  "Plus de 50 000",   89, 961),
]
def palier(pop):
    for i,(mx,lib,m,a) in enumerate(TARIFS):
        if pop < mx: return i
    return len(TARIFS)-1

req = urllib.request.Request(URL, headers={"User-Agent":"placette-calc"})
data = json.load(urllib.request.urlopen(req, timeout=60))
data.sort(key=lambda c: -(c.get("population") or 0))

tot_m = tot_a = 0
par_palier = {}
print("%-28s %10s %8s %8s" % ("Commune","Habitants","€/mois","€/an"))
print("-"*58)
for c in data:
    pop = c.get("population") or 0
    i = palier(pop)
    mx,lib,m,a = TARIFS[i]
    tot_m += m; tot_a += a
    par_palier[lib] = par_palier.get(lib,0)+1
    print("%-28s %10d %8d %8d" % (c["nom"][:28], pop, m, a))

print("-"*58)
print("NB COMMUNES :", len(data))
print()
print("Repartition par palier :")
for mx,lib,m,a in TARIFS:
    n = par_palier.get(lib,0)
    if n: print("  %-18s : %2d communes x %3d€/mois = %5d €/mois" % (lib,n,m,n*m))
print()
print("TOTAL MENSUEL  : %6d €/mois" % tot_m)
print("TOTAL ANNUEL   : %6d €/an (si paiement mensuel : %d €/an)" % (tot_a, tot_m*12))
