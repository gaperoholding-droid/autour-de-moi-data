# -*- coding: utf-8 -*-
"""
Générateur national — annuaires par commune à partir de la base officielle
geo-sirene (SIRENE géolocalisée, découpée par commune) de data.gouv.fr.

Pour chaque commune : télécharge son CSV geo-sirene, filtre les établissements
actifs qui sont des commerces/services/libéraux (via naf.py), et écrit
public/c/<code>.json = {info, c:[...], s:[...], l:[...]}.

Paramètres (variables d'environnement) :
  DEP   : "42" pour un département de test, ou "ALL" pour toute la France (défaut 42)
  MOIS  : "2025-07" pour forcer un millésime, sinon détection automatique
  BUDGET_MIN : minutes max (défaut 300)
"""
import os, sys, io, csv, json, time, datetime, pathlib, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import naf

DEP = os.environ.get("DEP", "42").strip()
MOIS = os.environ.get("MOIS", "").strip()
BUDGET_MIN = int(os.environ.get("BUDGET_MIN", "300"))
OUT = pathlib.Path("public/c"); OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://files.data.gouv.fr/geo-sirene"
UA = {"User-Agent": "autour-de-moi/1.0 (contact@commercesautourdemoi.fr)"}

def http(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def http_json(url, timeout=60):
    return json.loads(http(url, timeout).decode("utf-8"))

def mois_candidats():
    d = datetime.date.today(); y, m = d.year, d.month
    out = []
    for _ in range(24):
        out.append("%04d-%02d" % (y, m))
        m -= 1
        if m == 0: y -= 1; m = 12
    return out

def trouver_mois():
    if MOIS:
        return MOIS
    sentinelles = ["18233", "75056", "42218", "42222"]
    log = 0
    for mo in mois_candidats():
        for s in sentinelles:
            url = BASE + "/%s/communes/%s.csv" % (mo, s)
            try:
                req = urllib.request.Request(url, headers=UA)
                with urllib.request.urlopen(req, timeout=25) as r:
                    head = r.read(300)
                    if getattr(r, "status", 200) == 200 and head:
                        print("Millésime trouvé : %s (témoin %s)" % (mo, s), flush=True)
                        return mo
            except Exception as e:
                if log < 12:
                    print("  probe %s/%s -> %s" % (mo, s, str(e)[:70]), flush=True); log += 1
    sys.exit("Impossible de trouver un millésime geo-sirene disponible.")

# --- colonnes possibles (on prend la 1re présente) ---
def pick(row, *names):
    for n in names:
        if n in row and (row[n] or "").strip():
            return row[n].strip()
    return ""

def nom_etab(row):
    n = pick(row, "enseigne1Etablissement", "enseigne1UniteLegale",
             "denominationUsuelleEtablissement", "denominationUsuelle1UniteLegale",
             "denominationUniteLegale")
    if not n:
        nom = pick(row, "nomUniteLegale"); pre = pick(row, "prenom1UniteLegale", "prenomUsuelleUniteLegale")
        n = (pre + " " + nom).strip() if (nom or pre) else ""
    return n.title() if n else "Établissement"

def adresse(row):
    num = pick(row, "numeroVoieEtablissement")
    typ = pick(row, "typeVoieEtablissement")
    lib = pick(row, "libelleVoieEtablissement")
    cp = pick(row, "codePostalEtablissement")
    ville = pick(row, "libelleCommuneEtablissement")
    rue = " ".join(x for x in [num, typ, lib] if x)
    return (rue + (", " if rue else "") + (cp + " " if cp else "") + ville).strip(" ,").title()

def charger_commune_csv(code, mois):
    data = http(BASE + "/%s/communes/%s.csv" % (mois, code), timeout=60)
    txt = data.decode("utf-8", "replace")
    return list(csv.DictReader(io.StringIO(txt)))

def traiter(code, mois, meta):
    rows = charger_commune_csv(code, mois)
    vus = set(); groupes = {"commerce": [], "service": [], "liberal": []}
    for r in rows:
        if pick(r, "etatAdministratifEtablissement").upper() not in ("A", ""):
            continue
        naf_code = pick(r, "activitePrincipaleEtablissement")
        k = naf.classer(naf_code)
        if not k:
            continue
        siret = pick(r, "siret")
        if siret and siret in vus:
            continue
        vus.add(siret)
        lat = pick(r, "latitude", "geo_latitude", "geometry_y")
        lon = pick(r, "longitude", "geo_longitude", "geometry_x")
        groupes[k[0]].append({"nom": nom_etab(r), "lib": k[1], "adr": adresse(r),
                              "cp": pick(r, "codePostalEtablissement"),
                              "lat": lat or None, "lon": lon or None,
                              "tel": "", "web": "", "horaires": ""})
    for g in groupes.values():
        g.sort(key=lambda x: x["nom"].lower())
    info = {"nom": (meta.get("nom") or code), "code": code,
            "cp": (meta.get("codesPostaux") or [""])[0],
            "pop": meta.get("population"),
            "dep": (meta.get("departement") or {}).get("nom", "")}
    res = {"info": info, "c": groupes["commerce"], "s": groupes["service"], "l": groupes["liberal"]}
    (OUT / (code + ".json")).write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(groupes["commerce"]), len(groupes["service"]), len(groupes["liberal"])

def liste_communes():
    champs = "fields=code,nom,population,codesPostaux,departement"
    if DEP.upper() == "ALL":
        return http_json("https://geo.api.gouv.fr/communes?%s&format=json" % champs)
    return http_json("https://geo.api.gouv.fr/departements/%s/communes?%s&format=json" % (DEP, champs))

def main():
    t0 = time.time()
    mois = trouver_mois()
    print("Millésime geo-sirene : %s | périmètre : %s" % (mois, DEP), flush=True)
    communes = liste_communes()
    communes.sort(key=lambda c: c.get("population") or 0, reverse=True)
    print("Communes à traiter : %d" % len(communes), flush=True)
    ok = tc = ts = tl = 0; echecs = []
    for i, c in enumerate(communes, 1):
        if (time.time() - t0) / 60 > BUDGET_MIN:
            print("Budget atteint, arrêt à %d/%d." % (i, len(communes)), flush=True); break
        code = c["code"]
        try:
            a, b, d = traiter(code, mois, c)
            ok += 1; tc += a; ts += b; tl += d
            if i <= 12 or i % 200 == 0:
                print("  [%d/%d] %s %s : C=%d S=%d L=%d" % (i, len(communes), code, c.get("nom", "")[:22], a, b, d), flush=True)
        except Exception as e:
            echecs.append(code)
            if len(echecs) <= 10:
                print("  [%d/%d] %s : échec (%s)" % (i, len(communes), code, str(e)[:70]), flush=True)
        time.sleep(0.05)
    build = {"genere_le": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "millesime": mois,
             "perimetre": DEP, "communes_ok": ok, "echecs": len(echecs),
             "total_commerces": tc, "total_services": ts, "total_liberaux": tl,
             "minutes": round((time.time() - t0) / 60, 1)}
    pathlib.Path("public/build.json").write_text(json.dumps(build, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Terminé : %d communes, C=%d S=%d L=%d, %s échecs, %s min." %
          (ok, tc, ts, tl, len(echecs), build["minutes"]), flush=True)
    if ok == 0:
        sys.exit("Aucune commune générée.")

if __name__ == "__main__":
    main()
