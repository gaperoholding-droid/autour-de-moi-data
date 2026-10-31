# -*- coding: utf-8 -*-
"""Diagnostic : ressources du jeu INSEE géocodé + schéma du parquet SIRENE géolocalisé."""
import json, urllib.request
UA = {"User-Agent": "autour-de-moi/1.0 (contact@commercesautourdemoi.fr)"}

def hj(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

print("### Ressources dataset INSEE 61d5e2d372a52d9f9411ff88")
try:
    j = hj("https://www.data.gouv.fr/api/1/datasets/61d5e2d372a52d9f9411ff88/")
    print("titre:", j.get("title"))
    for r in j.get("resources", [])[:40]:
        print("  [%s] %-55s %s  %s" % (r.get("format"), (r.get("title") or "")[:55],
              r.get("filesize"), r.get("url")))
except Exception as e:
    print("  erreur:", str(e)[:120])

URL = "https://static.data.gouv.fr/resources/sirene-geolocalise-parquet/20240107-143656/sirene2024-geo.parquet"
print("\n### Schéma du parquet", URL)
try:
    import duckdb
    con = duckdb.connect()
    try:
        con.execute("INSTALL httpfs; LOAD httpfs;")
    except Exception:
        pass
    cols = con.execute("DESCRIBE SELECT * FROM read_parquet('%s')" % URL).fetchall()
    for c in cols:
        print("  col:", c[0], c[1])
    print("\n### 1 ligne exemple")
    row = con.execute("SELECT * FROM read_parquet('%s') LIMIT 1" % URL).fetchall()
    names = [c[0] for c in cols]
    if row:
        for n, v in zip(names, row[0]):
            print("   %-35s = %s" % (n, str(v)[:60]))
except Exception as e:
    print("  erreur duckdb:", str(e)[:200])
