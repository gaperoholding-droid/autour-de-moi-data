# -*- coding: utf-8 -*-
"""
Générateur national — annuaires par commune à partir de la base SIRENE
géolocalisée de l'INSEE (fichier parquet national, data.gouv.fr), via DuckDB.

Pour chaque commune : écrit public/c/<code>.json = {info, c, s, l}
où c/s/l = commerces / services / services libéraux (classement via naf.py).

Variables d'environnement :
  DEP        : "42" pour un département de test, "ALL" pour toute la France (défaut 42)
  BUDGET_MIN : minutes max (défaut 320)
"""
import os, sys, io, json, time, pathlib, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import naf

DEP = os.environ.get("DEP", "42").strip()
BUDGET_MIN = int(os.environ.get("BUDGET_MIN", "320"))
OUT = pathlib.Path("public/c"); OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "autour-de-moi/1.0 (contact@commercesautourdemoi.fr)"}
DATASET = "61d5e2d372a52d9f9411ff88"   # INSEE : géolocalisation établissements SIRENE
PARQUET_LOCAL = "/tmp/sirene-geo.parquet"

# préfixes NAF (sans point) à pré-filtrer en SQL ; naf.classer tranche ensuite
PREFIXES = ["47", "56", "96", "95", "43", "86", "75", "1071", "1013",
            "4520", "4532", "4511", "4519", "4540", "8130", "6419", "6492",
            "6512", "6622", "6619", "6831", "7911", "8553", "5310", "5320",
            "9313", "9311", "6910", "6920", "7111", "7112", "7120"]

def http(url, timeout=120):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()

def url_parquet():
    j = json.loads(http("https://www.data.gouv.fr/api/1/datasets/%s/" % DATASET, 60).decode("utf-8"))
    cands = [r for r in j.get("resources", []) if (r.get("format") or "").lower() == "parquet" and r.get("url")]
    if not cands:
        sys.exit("Aucun parquet trouvé dans le dataset INSEE.")
    cands.sort(key=lambda r: r.get("url"), reverse=True)   # le plus récent (URL horodatée)
    return cands[0]["url"]

def telecharger(url, dest):
    print("Téléchargement du parquet : %s" % url, flush=True)
    t = time.time()
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    print("  téléchargé en %.0fs (%.0f Mo)" % (time.time() - t, os.path.getsize(dest) / 1e6), flush=True)

def nom_etab(ens, usuel, denom, nom):
    for v in (ens, usuel, denom, nom):
        if v and v.strip():
            return v.strip().title()
    return "Établissement"

def adresse(num, typ, lib, cp, ville):
    rue = " ".join(x for x in (num, typ, lib) if x)
    return (rue + (", " if rue else "") + ((cp + " ") if cp else "") + (ville or "")).strip(" ,").title()

def flush_commune(code, ville, fiches):
    groupes = {"commerce": [], "service": [], "liberal": []}
    vus = set()
    for f in fiches:
        if f["siret"] in vus:
            continue
        vus.add(f["siret"])
        k = naf.classer(f["naf"])
        if not k:
            continue
        groupes[k[0]].append({"nom": f["nom"], "lib": k[1], "adr": f["adr"], "cp": f["cp"],
                              "lat": f["lat"], "lon": f["lon"], "tel": "", "web": "", "horaires": ""})
    if not any(groupes.values()):
        return 0, 0, 0
    for g in groupes.values():
        g.sort(key=lambda x: x["nom"].lower())
    res = {"info": {"nom": (ville or code).title(), "code": code},
           "c": groupes["commerce"], "s": groupes["service"], "l": groupes["liberal"]}
    (OUT / (code + ".json")).write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(groupes["commerce"]), len(groupes["service"]), len(groupes["liberal"])

def main():
    t0 = time.time()
    import duckdb
    telecharger(url_parquet(), PARQUET_LOCAL)
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")

    like = " OR ".join("naf2 LIKE '%s%%'" % p for p in PREFIXES)
    where_dep = "" if DEP.upper() == "ALL" else "AND codeCommuneEtablissement LIKE '%s%%'" % DEP
    sql = """
      SELECT codeCommuneEtablissement AS code, libelleCommuneEtablissement AS ville, siret,
             enseigne1Etablissement, denominationUsuelleEtablissement, denominationUniteLegale, nomUniteLegale,
             activitePrincipaleEtablissement AS naf,
             numeroVoieEtablissement, typeVoieEtablissement, libelleVoieEtablissement,
             codePostalEtablissement,
             ST_Y(geometry) AS lat, ST_X(geometry) AS lon
      FROM (
        SELECT *, replace(activitePrincipaleEtablissement, '.', '') AS naf2
        FROM read_parquet('%s')
        WHERE etatAdministratifEtablissement = 'A' %s
      )
      WHERE (%s)
      ORDER BY codeCommuneEtablissement
    """ % (PARQUET_LOCAL, where_dep, like)

    print("Requête DuckDB…", flush=True)
    cur = con.execute(sql)
    cur_code = None; cur_ville = ""; buf = []
    nb_com = ok = tc = ts = tl = 0
    while True:
        rows = cur.fetchmany(20000)
        if not rows:
            break
        for r in rows:
            code = r[0]
            if code != cur_code:
                if cur_code is not None:
                    a, b, d = flush_commune(cur_code, cur_ville, buf)
                    if a + b + d:
                        ok += 1; tc += a; ts += b; tl += d
                    nb_com += 1
                cur_code = code; cur_ville = r[1] or ""; buf = []
            buf.append({"siret": r[2],
                        "nom": nom_etab(r[3], r[4], r[5], r[6]),
                        "naf": r[7],
                        "adr": adresse(r[8], r[9], r[10], r[11], r[1]),
                        "cp": r[11] or "",
                        "lat": (str(r[12]) if r[12] is not None else None),
                        "lon": (str(r[13]) if r[13] is not None else None)})
        if (time.time() - t0) / 60 > BUDGET_MIN:
            print("Budget atteint.", flush=True); break
    if cur_code is not None and buf:
        a, b, d = flush_commune(cur_code, cur_ville, buf)
        if a + b + d:
            ok += 1; tc += a; ts += b; tl += d

    build = {"genere_le": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "perimetre": DEP, "communes_fichiers": ok,
             "total_commerces": tc, "total_services": ts, "total_liberaux": tl,
             "minutes": round((time.time() - t0) / 60, 1)}
    pathlib.Path("public/build.json").write_text(json.dumps(build, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Terminé : %d communes (fichiers), C=%d S=%d L=%d, %s min." %
          (ok, tc, ts, tl, build["minutes"]), flush=True)
    if ok == 0:
        sys.exit("Aucune commune générée.")

if __name__ == "__main__":
    main()
