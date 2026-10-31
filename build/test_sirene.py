# -*- coding: utf-8 -*-
"""
TEST (ne publie rien) : récupère les établissements d'une commune via l'API
officielle Recherche d'entreprises (annuaire-entreprises.data.gouv.fr),
les filtre/classe en commerces et services, et affiche le résultat dans les logs.
Sert à valider la source et le périmètre AVANT de changer le site.

Usage : CODE_COMMUNE=42222 python build/test_sirene.py
"""
import os, sys, time, json, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import naf

CODE = os.environ.get("CODE_COMMUNE", "42222")
API = "https://recherche-entreprises.api.gouv.fr/search"
PER = 25

def get(page):
    q = urllib.parse.urlencode({"code_commune": CODE, "page": page, "per_page": PER,
                                "etat_administratif": "A"})
    req = urllib.request.Request(API + "?" + q,
          headers={"User-Agent": "autour-de-moi-test/1.0 (contact@commercesautourdemoi.fr)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def nom_etab(res, e):
    ens = e.get("liste_enseignes") or []
    if ens and ens[0]:
        return ens[0].title()
    return (res.get("nom_complet") or res.get("nom_raison_sociale") or "").title()

def main():
    print("== TEST SIRENE commune %s ==" % CODE, flush=True)
    j = get(1)
    total = j.get("total_results"); pages = j.get("total_pages") or 1
    print("total_results =", total, "| total_pages =", pages, flush=True)
    # aperçu de structure (pour vérifier les champs réellement renvoyés)
    if j.get("results"):
        r0 = j["results"][0]
        print("clés résultat :", list(r0.keys()), flush=True)
        if r0.get("matching_etablissements"):
            print("clés établissement :", list(r0["matching_etablissements"][0].keys()), flush=True)

    vus = set(); commerces = []; services = []; exclus = {}
    page = 1
    while page <= min(pages, 400):
        data = j if page == 1 else get(page)
        for res in data.get("results", []):
            for e in res.get("matching_etablissements", []):
                siret = e.get("siret")
                if not siret or siret in vus:
                    continue
                if (e.get("etat_administratif") or "A") != "A":
                    continue
                code_naf = e.get("activite_principale")
                k = naf.classer(code_naf)
                if not k:
                    exclus[code_naf] = exclus.get(code_naf, 0) + 1
                    continue
                vus.add(siret)
                fiche = {"nom": nom_etab(res, e), "lib": k[1],
                         "naf": code_naf,
                         "adr": (e.get("adresse") or "").strip(),
                         "lat": e.get("latitude"), "lon": e.get("longitude")}
                (commerces if k[0] == "commerce" else services).append(fiche)
        page += 1
        time.sleep(0.25)

    commerces.sort(key=lambda x: x["nom"].lower())
    services.sort(key=lambda x: x["nom"].lower())
    avec_geo = sum(1 for f in commerces + services if f["lat"] and f["lon"])

    print("\n===== RÉSULTAT =====", flush=True)
    print("COMMERCES : %d   |   SERVICES : %d   |   total retenu : %d"
          % (len(commerces), len(services), len(commerces) + len(services)), flush=True)
    print("avec coordonnées GPS : %d / %d" % (avec_geo, len(commerces) + len(services)), flush=True)

    print("\n----- COMMERCES -----", flush=True)
    for f in commerces:
        print("  %-34s | %-28s | %s" % (f["nom"][:34], f["lib"][:28], f["adr"][:40]), flush=True)
    print("\n----- SERVICES -----", flush=True)
    for f in services:
        print("  %-34s | %-28s | %s" % (f["nom"][:34], f["lib"][:28], f["adr"][:40]), flush=True)

    if exclus:
        top = sorted(exclus.items(), key=lambda kv: kv[1], reverse=True)[:25]
        print("\n----- Codes NAF écartés (les plus fréquents) -----", flush=True)
        for code, n in top:
            print("  %s : %d" % (code, n), flush=True)
        print("(si un de ces codes devrait être gardé, on l'ajoute à naf.py)", flush=True)

if __name__ == "__main__":
    main()
