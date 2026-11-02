# -*- coding: utf-8 -*-
"""Diag : couverture des données publiées sur GitHub Pages."""
import json, urllib.request
BASE = "https://gaperoholding-droid.github.io/autour-de-moi-data/"
UA = {"User-Agent": "autour-de-moi-diag/1.0"}

def get(path):
    with urllib.request.urlopen(urllib.request.Request(BASE + path, headers=UA), timeout=40) as r:
        return r.read()

print("### build.json")
try:
    print(get("build.json").decode("utf-8"))
except Exception as e:
    print("échec:", str(e)[:120])

echants = {
 "69382": "Lyon 2e (arr.)", "69381": "Lyon 1er (arr.)", "75102": "Paris 2e (arr.)", "13202": "Marseille 2e (arr.)",
 "75056": "Paris", "69123": "Lyon", "13055": "Marseille", "31555": "Toulouse",
 "06088": "Nice", "33063": "Bordeaux", "59350": "Lille", "44109": "Nantes",
 "67482": "Strasbourg", "42222": "Saint-Galmier", "2A004": "Ajaccio",
 "97411": "Saint-Denis (974)", "01004": "Ambérieu", "50129": "Carentan",
 "01001": "petit village (Abergement)",
}
print("\n### Échantillon de communes (C/S/L)")
for code, nom in echants.items():
    try:
        d = json.loads(get("c/" + code + ".json"))
        print("  OK   %-7s %-22s C=%d S=%d L=%d" % (code, nom, len(d["c"]), len(d["s"]), len(d["l"])))
    except Exception as e:
        print("  ---  %-7s %-22s absent (%s)" % (code, nom, str(e)[:40]))

print("\n### Saint-Galmier (42222) — noms de la grande distribution (vérif enseignes)")
try:
    d = json.loads(get("c/42222.json"))
    cibles = ("Supermarché", "Hypermarché", "Supérette / épicerie", "Magasin multi-commerces")
    for f in d["c"]:
        if f["lib"] in cibles:
            print("   %-32s | %s" % (f["nom"], f["lib"]))
except Exception as e:
    print("  échec:", str(e)[:80])
