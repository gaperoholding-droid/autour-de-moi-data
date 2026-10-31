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

# ===================== Enrichissement OpenStreetMap (téléphone / site / horaires) =====================
import unicodedata
OVERPASS = ["https://overpass.kumi.systems/api/interpreter",
            "https://overpass-api.de/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]

def osm_requete(code):
    return ('[out:json][timeout:70];'
            'rel["ref:INSEE"="%s"]["boundary"="administrative"]["admin_level"~"^(8|9)$"]->.r;'
            '.r map_to_area->.a;('
            'nwr["shop"]["name"](area.a);'
            'nwr["amenity"]["name"](area.a);'
            'nwr["craft"]["name"](area.a);'
            'nwr["office"]["name"](area.a);'
            'nwr["healthcare"]["name"](area.a);'
            'nwr["leisure"="fitness_centre"]["name"](area.a);'
            ');out center tags;') % code

def osm_pois(code):
    body = urllib.parse.urlencode({"data": osm_requete(code)}).encode()
    for ep in OVERPASS:
        try:
            req = urllib.request.Request(ep, data=body,
                  headers={"User-Agent": "autour-de-moi-test/1.0 (contact@commercesautourdemoi.fr)"})
            with urllib.request.urlopen(req, timeout=80) as r:
                j = json.loads(r.read().decode("utf-8"))
            pois = []
            for e in j.get("elements", []):
                t = e.get("tags", {})
                if not t.get("name"):
                    continue
                lat = e.get("lat", (e.get("center") or {}).get("lat"))
                lon = e.get("lon", (e.get("center") or {}).get("lon"))
                if lat is None:
                    continue
                pois.append({"nom": t["name"], "lat": float(lat), "lon": float(lon),
                             "tel": t.get("phone") or t.get("contact:phone") or "",
                             "web": t.get("website") or t.get("contact:website") or "",
                             "horaires": t.get("opening_hours") or ""})
            print("  OSM : %d points récupérés" % len(pois), flush=True)
            return pois
        except Exception as ex:
            print("  OSM endpoint échec (%s)" % str(ex)[:50], flush=True)
    return []

def _nk(s):
    s = "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if unicodedata.category(c) != "Mn")
    s = "".join(c if c.isalnum() else " " for c in s)
    return " ".join(s.split())

_STOP = set("sarl sas sasu eurl sa snc sci scm selarl selas sel dr docteur cabinet pharmacie boulangerie "
            "patisserie restaurant garage coiffure institut le la les du de des et au aux chez".split())
def _toks(s):
    return set(w for w in _nk(s).split() if len(w) >= 4 and w not in _STOP)

def _dist(a, b, c, d):
    import math
    R = 6371000.0; p = math.pi / 180
    x = math.sin((c - a) * p / 2); y = math.sin((d - b) * p / 2)
    h = x * x + math.cos(a * p) * math.cos(c * p) * y * y
    return 2 * R * math.asin(math.sqrt(h))

def enrichir(groupes, pois):
    if not pois:
        return 0
    n = 0
    for g in groupes.values():
        for f in g:
            if not f.get("lat"):
                continue
            fla, flo = float(f["lat"]), float(f["lon"])
            nkf = _nk(f["nom"]); tkf = _toks(f["nom"])
            best = None; bestd = 250.0
            for p in pois:
                d = _dist(fla, flo, p["lat"], p["lon"])
                if d > 250:
                    continue
                nkp = _nk(p["nom"])
                ok = (nkp == nkf) or (len(nkp) >= 5 and (nkp in nkf or nkf in nkp)) or len(tkf & _toks(p["nom"])) >= 1
                if ok and d < bestd:
                    best = p; bestd = d
            if best and (best["tel"] or best["web"] or best["horaires"]):
                f["tel"] = best["tel"]; f["web"] = best["web"]; f["horaires"] = best["horaires"]
                n += 1
    return n

def main():
    print("== TEST SIRENE %s — commune %s ==" % (VERSION, CODE), flush=True)
    j = get(1)
    total = j.get("total_results"); pages = j.get("total_pages") or 1
    print("total_results = %s | total_pages = %s" % (total, pages), flush=True)

    vus = set(); groupes = {"commerce": [], "service": [], "liberal": []}; exclus = {}
    nom_commune = ""
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
                nom_commune = nom_commune or (e.get("libelle_commune") or "")
                groupes[k[0]].append({"nom": nom_etab(res, e), "lib": k[1],
                                      "adr": (e.get("adresse") or "").strip(),
                                      "cp": e.get("code_postal") or "",
                                      "lat": e.get("latitude"), "lon": e.get("longitude"),
                                      "tel": "", "web": "", "horaires": ""})
        page += 1
        time.sleep(0.25)

    print("Enrichissement OpenStreetMap (téléphone / site / horaires)…", flush=True)
    nb_enr = enrichir(groupes, osm_pois(CODE))
    tot = sum(len(v) for v in groupes.values())
    avec_geo = sum(1 for v in groupes.values() for f in v if f["lat"] and f["lon"])
    avec_tel = sum(1 for v in groupes.values() for f in v if f.get("tel"))
    avec_web = sum(1 for v in groupes.values() for f in v if f.get("web"))
    L = []
    def out(s=""):
        print(s, flush=True); L.append(s)
    out("== TEST SIRENE %s — commune %s ==" % (VERSION, CODE))
    out("total_results = %s | total_pages = %s" % (total, pages))
    out("\n===== RÉSULTAT =====")
    out("COMMERCES : %d   |   SERVICES : %d   |   SERVICES LIBÉRAUX : %d   |   total : %d"
        % (len(groupes["commerce"]), len(groupes["service"]), len(groupes["liberal"]), tot))
    out("avec coordonnées GPS : %d / %d" % (avec_geo, tot))
    out("enrichis via OpenStreetMap : %d (téléphone : %d, site web : %d)" % (nb_enr, avec_tel, avec_web))
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
    data = {"info": {"nom": (nom_commune or CODE).title(), "code": CODE},
            "c": groupes["commerce"], "s": groupes["service"], "l": groupes["liberal"]}
    with open("build/_data_%s.json" % CODE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))

if __name__ == "__main__":
    main()
