# -*- coding: utf-8 -*-
"""
Générateur national — annuaires par commune à partir des fichiers SIRENE
officiels à jour (data.gouv.fr, format parquet), assemblés avec DuckDB :
  - StockEtablissement  : activité (NAF), enseigne, adresse, commune, état
  - StockUniteLegale    : dénomination / nom du gérant
  - Géolocalisation INSEE: coordonnées GPS (y_latitude / x_longitude)

Écrit public/c/<code>.json = {info, c, s, l} (commerces / services / libéraux).

Variables d'environnement :
  DEP        : "42" (test département) ou "ALL" (France entière). Défaut 42.
  BUDGET_MIN : minutes max (défaut 320)
"""
import os, sys, json, time, pathlib, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import naf

DEP = os.environ.get("DEP", "42").strip()
BUDGET_MIN = int(os.environ.get("BUDGET_MIN", "320"))
OUT = pathlib.Path("public/c"); OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "autour-de-moi/1.0 (contact@commercesautourdemoi.fr)"}
DS_GEO = "61d5e2d372a52d9f9411ff88"
DS_SIRENE = "base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret"

PREFIXES = ["47", "56", "96", "95", "43", "86", "75", "1071", "1013",
            "4520", "4532", "4511", "4519", "4540", "8130", "6419", "6492",
            "6512", "6622", "6619", "6831", "7911", "8553", "5310", "5320",
            "9313", "9311", "6910", "6920", "7111", "7112", "7120"]

def hj(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def resource(dataset, fmt, inc=(), exc=()):
    j = hj("https://www.data.gouv.fr/api/1/datasets/%s/" % dataset)
    best = None
    for r in j.get("resources", []):
        if (r.get("format") or "").lower() != fmt: continue
        t = r.get("title") or ""
        if any(x.lower() not in t.lower() for x in inc): continue
        if any(x.lower() in t.lower() for x in exc): continue
        if r.get("url"):
            if best is None or (r.get("url") > best):  # URL horodatée -> plus récent
                best = r.get("url")
    return best

def telecharger(url, dest):
    print("  télécharge %s" % url.split("/")[-1], flush=True)
    t = time.time()
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=1200) as r, open(dest, "wb") as f:
        while True:
            c = r.read(1 << 20)
            if not c: break
            f.write(c)
    print("    -> %.0f Mo en %.0fs" % (os.path.getsize(dest) / 1e6, time.time() - t), flush=True)

def cv(v):
    """Nettoie une valeur SIRENE : '[ND]' (non-diffusible) -> vide."""
    if not v: return ""
    v = v.strip()
    return "" if v.upper() in ("[ND]", "[N.D.]", "ND") else v

def nom_etab(ens, usuel, denom, nom, prenom):
    for v in (ens, usuel, denom):
        v = cv(v)
        if v: return v.title()
    np = (cv(prenom) + " " + cv(nom)).strip()
    return np.title() if np else "Établissement"

def adresse(num, typ, lib, cp, ville):
    rue = " ".join(x for x in (cv(num), cv(typ), cv(lib)) if x)
    cp = cv(cp); ville = cv(ville)
    return (rue + (", " if rue else "") + ((cp + " ") if cp else "") + ville).strip(" ,").title()

def flush_commune(code, ville, rows):
    groupes = {"commerce": [], "service": [], "liberal": []}; vus = set()
    for r in rows:
        siret = r[2]
        if siret in vus: continue
        vus.add(siret)
        k = naf.classer(r[8])
        if not k: continue
        groupes[k[0]].append({"nom": nom_etab(r[3], r[4], r[5], r[6], r[7]), "lib": k[1],
                              "adr": adresse(r[9], r[10], r[11], r[12], r[1]), "cp": r[12] or "",
                              "lat": (str(r[13]) if r[13] is not None else None),
                              "lon": (str(r[14]) if r[14] is not None else None),
                              "tel": "", "web": "", "horaires": ""})
    if not any(groupes.values()): return 0, 0, 0
    for g in groupes.values(): g.sort(key=lambda x: x["nom"].lower())
    res = {"info": {"nom": (ville or code).title(), "code": code},
           "c": groupes["commerce"], "s": groupes["service"], "l": groupes["liberal"]}
    (OUT / (code + ".json")).write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(groupes["commerce"]), len(groupes["service"]), len(groupes["liberal"])

def dep_de(code):
    c = (code or "").upper()
    if c[:2] in ("2A", "2B"): return c[:2]
    if c[:2] in ("97", "98"): return c[:3]
    return c[:2]

def ecrire_mairies():
    src = pathlib.Path("build/mairies_emails.json")
    if not src.exists():
        print("mairies_emails.json absent : routage mairies ignoré.", flush=True); return
    m = json.loads(src.read_text(encoding="utf-8"))
    OUTM = pathlib.Path("public/mairies"); OUTM.mkdir(parents=True, exist_ok=True)
    pardep = {}
    for code, email in m.items():
        pardep.setdefault(dep_de(code), {})[code] = email
    for d, sous in pardep.items():
        (OUTM / (d + ".json")).write_text(json.dumps(sous, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("E-mails mairies : %d communes, %d départements." % (len(m), len(pardep)), flush=True)

def main():
    t0 = time.time()
    import duckdb
    ecrire_mairies()
    print("Découverte des fichiers…", flush=True)
    u_geo = resource(DS_GEO, "parquet")
    u_etab = resource(DS_SIRENE, "parquet", inc=["StockEtablissement"], exc=["Historique", "LiensSuccession"])
    u_ul = resource(DS_SIRENE, "parquet", inc=["StockUniteLegale"], exc=["Historique"])
    for nom, u in (("geoloc", u_geo), ("etab", u_etab), ("ul", u_ul)):
        if not u: sys.exit("Fichier %s introuvable." % nom)
    telecharger(u_geo, "/tmp/geo.parquet")
    telecharger(u_etab, "/tmp/etab.parquet")
    telecharger(u_ul, "/tmp/ul.parquet")

    con = duckdb.connect()
    like = " OR ".join("replace(e.activitePrincipaleEtablissement,'.','') LIKE '%s%%'" % p for p in PREFIXES)
    where_dep = "" if DEP.upper() == "ALL" else "AND e.codeCommuneEtablissement LIKE '%s%%'" % DEP
    sql = """
      SELECT e.codeCommuneEtablissement AS code, e.libelleCommuneEtablissement AS ville, e.siret,
             e.enseigne1Etablissement, e.denominationUsuelleEtablissement,
             u.denominationUniteLegale, u.nomUniteLegale, u.prenom1UniteLegale,
             e.activitePrincipaleEtablissement AS naf,
             e.numeroVoieEtablissement, e.typeVoieEtablissement, e.libelleVoieEtablissement,
             e.codePostalEtablissement,
             g.y_latitude AS lat, g.x_longitude AS lon
      FROM read_parquet('/tmp/etab.parquet') e
      LEFT JOIN read_parquet('/tmp/ul.parquet') u ON e.siren = u.siren
      LEFT JOIN read_parquet('/tmp/geo.parquet') g ON e.siret = g.siret
      WHERE e.etatAdministratifEtablissement = 'A'
        AND e.statutDiffusionEtablissement = 'O'
        %s AND (%s)
      ORDER BY e.codeCommuneEtablissement
    """ % (where_dep, like)
    print("Requête DuckDB (jointure 3 fichiers)…", flush=True)
    cur = con.execute(sql)
    cur_code = None; cur_ville = ""; buf = []; ok = tc = ts = tl = 0
    while True:
        rows = cur.fetchmany(20000)
        if not rows: break
        for r in rows:
            if r[0] != cur_code:
                if cur_code is not None:
                    a, b, d = flush_commune(cur_code, cur_ville, buf)
                    if a + b + d: ok += 1; tc += a; ts += b; tl += d
                cur_code = r[0]; cur_ville = r[1] or ""; buf = []
            buf.append(r)
        if (time.time() - t0) / 60 > BUDGET_MIN:
            print("Budget atteint.", flush=True); break
    if cur_code is not None and buf:
        a, b, d = flush_commune(cur_code, cur_ville, buf)
        if a + b + d: ok += 1; tc += a; ts += b; tl += d

    build = {"genere_le": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "perimetre": DEP,
             "communes_fichiers": ok, "total_commerces": tc, "total_services": ts, "total_liberaux": tl,
             "minutes": round((time.time() - t0) / 60, 1)}
    pathlib.Path("public/build.json").write_text(json.dumps(build, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Terminé : %d communes, C=%d S=%d L=%d, %s min." % (ok, tc, ts, tl, build["minutes"]), flush=True)
    if ok == 0: sys.exit("Aucune commune générée.")

if __name__ == "__main__":
    main()
