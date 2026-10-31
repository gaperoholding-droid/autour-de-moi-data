# -*- coding: utf-8 -*-
"""
TEST SIRENE — récupère les établissements d'une commune via l'API officielle
Recherche d'entreprises, les classe (via naf.py) en Commerces / Services /
Services libéraux, affiche le résultat dans les logs ET l'écrit dans
build/_resultat_<code>.txt. Ne publie rien sur le site.

Usage : CODE_COMMUNE=42222 python build/test_sirene.py
"""
import os, sys, time, json, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import naf

VERSION = "v4 (artisans ajoutés, libéral affiné)"
CODE = os.environ.get("CODE_COMMUNE", "42222")
API = "https://recherche-entreprises.api.gouv.fr/search"
PER = 25
TITRES = {"commerce": "COMMERCES", "service": "SERVICES", "liberal": "SERVICES LIBÉRAUX"}

def get(page):
    q = urllib.parse.urlencode({"code_commune": CODE, "page": page, "per_page": PER,
                                "etat_administratif": "A"})
    url = API + "?" + q
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url,
                  headers={"User-Agent": "autour-de-moi-test/1.0 (contact@commercesautourdemoi.fr)"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e
            time.sleep(3 * (attempt + 1))
    raise last

def nom_etab(res, e):
    nc = (e.get("nom_commercial") or "").strip()
    if nc:
        return nc.title()
    ens = e.get("liste_enseignes") or []
    if ens and ens[0]:
        return ens[0].title()
    return (res.get("nom_complet") or res.get("nom_raison_sociale") or "").title()

def main():
    print("== TEST SIRENE %s — commune %s ==" % (VERSION, CODE), flush=True)
    j = get(1)
    total = j.get("total_results"); pages = j.get("total_pages") or 1
    print("total_results = %s | total_pages = %s" % (total, pages), flush=True)

    vus = set(); groupes = {"commerce": [], "service": [], "liberal": []}; exclus = {}
    page = 1
    while page <= min(pages, 400):
        try:
            data = j if page == 1 else get(page)
        except Exception as e:
            print("  page %d ignorée (%s)" % (page, str(e)[:60]), flush=True)
            page += 1
            continue
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
                groupes[k[0]].append({"nom": nom_etab(res, e), "lib": k[1],
                                      "adr": (e.get("adresse") or "").strip(),
                                      "lat": e.get("latitude"), "lon": e.get("longitude")})
        page += 1
        time.sleep(0.25)

    tot = sum(len(v) for v in groupes.values())
    avec_geo = sum(1 for v in groupes.values() for f in v if f["lat"] and f["lon"])
    L = []
    def out(s=""):
        print(s, flush=True); L.append(s)
    out("== TEST SIRENE %s — commune %s ==" % (VERSION, CODE))
    out("total_results = %s | total_pages = %s" % (total, pages))
    out("\n===== RÉSULTAT =====")
    out("COMMERCES : %d   |   SERVICES : %d   |   SERVICES LIBÉRAUX : %d   |   total : %d"
        % (len(groupes["commerce"]), len(groupes["service"]), len(groupes["liberal"]), tot))
    out("avec coordonnées GPS : %d / %d" % (avec_geo, tot))
    for g in ("commerce", "service", "liberal"):
        lst = sorted(groupes[g], key=lambda x: x["nom"].lower())
        out("\n----- %s (%d) -----" % (TITRES[g], len(lst)))
        for f in lst:
            out("  %-34s | %-30s | %s" % (f["nom"][:34], f["lib"][:30], f["adr"][:40]))
    if exclus:
        top = sorted(exclus.items(), key=lambda kv: kv[1], reverse=True)[:30]
        out("\n----- Codes NAF écartés (les plus fréquents) -----")
        for code, n in top:
            out("  %s : %d" % (code, n))
    with open("build/_resultat_%s.txt" % CODE, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

if __name__ == "__main__":
    main()
