# -*- coding: utf-8 -*-
"""Diag : schéma du parquet géoloc INSEE (oct 2026) + ressources du dataset SIRENE complet."""
import json, urllib.request
UA = {"User-Agent": "autour-de-moi/1.0 (contact@commercesautourdemoi.fr)"}
def hj(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

GEO = ("https://static.data.gouv.fr/resources/geolocalisation-des-etablissements-du-repertoire-sirene-"
       "pour-les-etudes-statistiques/20261021-064721/"
       "geoloc-geolocalisationetablissement-sirene-pour-etudes-statistiques-parquet.parquet")

print("### Schéma GÉOLOC (oct 2026)")
try:
    import duckdb
    con = duckdb.connect()
    try: con.execute("INSTALL httpfs; LOAD httpfs;")
    except Exception: pass
    cols = con.execute("DESCRIBE SELECT * FROM read_parquet('%s')" % GEO).fetchall()
    for c in cols:
        print("  ", c[0], c[1])
except Exception as e:
    print("  erreur duckdb:", str(e)[:200])

print("\n### Ressources dataset SIRENE complet (Stock Établissement / Unité légale)")
try:
    j = hj("https://www.data.gouv.fr/api/1/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/")
    print("titre:", j.get("title"))
    for r in j.get("resources", [])[:80]:
        t = (r.get("title") or "")
        if any(x in t for x in ("Stock", "stock", "Etablissement", "Unite", "parquet", ".csv")) or (r.get("format") or "").lower() in ("csv", "parquet", "zip"):
            print("  [%s] %-60s %s  %s" % (r.get("format"), t[:60], r.get("filesize"), r.get("url")))
except Exception as e:
    print("  erreur:", str(e)[:150])
