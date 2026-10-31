# -*- coding: utf-8 -*-
"""
Autour de moi — génération nocturne des annuaires de commerces (version rapide).

Nouveautés par rapport à la v1 :
- les communes sont traitées des PLUS GRANDES aux plus petites (les villes clientes d'abord),
  pour que les plus importantes soient toujours prêtes ;
- une commune qui bloque est abandonnée vite (pas de longs réessais) ;
- un budget de temps : le script s'arrête proprement avant la limite de GitHub (6 h)
  et publie ce qui est déjà prêt. Les communes non faites restent chargées en direct.

Aucune dépendance à installer : uniquement la bibliothèque standard de Python.
"""
import json, os, time, pathlib, urllib.request, urllib.parse, unicodedata, sys

SEUIL_POP   = int(os.environ.get("SEUIL_POP", "10000"))     # communes >= ce nb d'habitants
PAUSE       = float(os.environ.get("PAUSE", "0.5"))          # pause entre deux communes
BUDGET_MIN  = int(os.environ.get("BUDGET_MIN", "300"))       # minutes max (GitHub coupe à 360)
TIMEOUT_OVP = int(os.environ.get("TIMEOUT_OVERPASS", "90"))  # secondes max par requête
OUT         = pathlib.Path("public/communes"); OUT.mkdir(parents=True, exist_ok=True)
OUT_MAIRIES = pathlib.Path("public/mairies"); OUT_MAIRIES.mkdir(parents=True, exist_ok=True)
OVERPASS    = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

TYPES = {
 "shop": {"bakery":("Boulangerie","alim"),"pastry":("Pâtisserie","alim"),"butcher":("Boucherie","alim"),"greengrocer":("Primeur","alim"),
  "supermarket":("Supermarché","alim"),"convenience":("Épicerie","alim"),"cheese":("Fromagerie","alim"),"wine":("Caviste","alim"),
  "alcohol":("Caviste","alim"),"deli":("Épicerie fine","alim"),"confectionery":("Confiserie","alim"),"chocolate":("Chocolatier","alim"),
  "seafood":("Poissonnerie","alim"),"coffee":("Torréfacteur / café","alim"),"tea":("Thés","alim"),"organic":("Bio","alim"),
  "farm":("Produits fermiers","alim"),"frozen_food":("Surgelés","alim"),"beverages":("Boissons","alim"),"health_food":("Diététique","alim"),
  "food":("Alimentation","alim"),"spices":("Épices","alim"),"pasta":("Pâtes fraîches","alim"),
  "chemist":("Droguerie","sante"),"optician":("Opticien","sante"),"hearing_aids":("Audioprothésiste","sante"),"medical_supply":("Matériel médical","sante"),
  "hairdresser":("Coiffeur","beaute"),"beauty":("Institut de beauté","beaute"),"cosmetics":("Cosmétiques","beaute"),"perfumery":("Parfumerie","beaute"),
  "massage":("Massage","beaute"),"tattoo":("Tatouage","beaute"),"barber":("Barbier","beaute"),
  "clothes":("Vêtements","mode"),"shoes":("Chaussures","mode"),"jewelry":("Bijouterie","mode"),"bag":("Maroquinerie","mode"),
  "boutique":("Boutique","mode"),"watches":("Horlogerie","mode"),"fashion_accessories":("Accessoires","mode"),"leather":("Maroquinerie","mode"),
  "second_hand":("Dépôt-vente","mode"),"fabric":("Tissus","mode"),"tailor":("Retouches","mode"),"lingerie":("Lingerie","mode"),
  "furniture":("Ameublement","maison"),"interior_decoration":("Décoration","maison"),"florist":("Fleuriste","maison"),"garden_centre":("Jardinerie","maison"),
  "hardware":("Quincaillerie","maison"),"doityourself":("Bricolage","maison"),"houseware":("Arts de la table","maison"),"kitchen":("Cuisines","maison"),
  "antiques":("Antiquités","maison"),"frame":("Encadrement","maison"),"curtain":("Rideaux","maison"),"bed":("Literie","maison"),
  "lighting":("Luminaires","maison"),"bathroom_furnishing":("Salles de bain","maison"),"carpet":("Tapis","maison"),"appliance":("Électroménager","maison"),
  "books":("Librairie","loisir"),"stationery":("Papeterie","loisir"),"toys":("Jouets","loisir"),"music":("Disquaire","loisir"),
  "musical_instrument":("Instruments de musique","loisir"),"gift":("Cadeaux","loisir"),"sports":("Sport","loisir"),"bicycle":("Vélos","loisir"),
  "games":("Jeux","loisir"),"newsagent":("Presse","loisir"),"photo":("Photographie","loisir"),"art":("Galerie d'art","loisir"),
  "craft":("Loisirs créatifs","loisir"),"outdoor":("Plein air","loisir"),"video_games":("Jeux vidéo","loisir"),"comics":("Bandes dessinées","loisir"),
  "dry_cleaning":("Pressing","serv"),"laundry":("Laverie","serv"),"travel_agency":("Agence de voyages","serv"),"copyshop":("Reprographie","serv"),
  "mobile_phone":("Téléphonie","serv"),"computer":("Informatique","serv"),"electronics":("Électronique","serv"),"tobacco":("Tabac","serv"),
  "car_repair":("Garage","serv"),"shoe_repair":("Cordonnerie","serv"),"locksmith":("Serrurier","serv"),"pet":("Animalerie","serv"),
  "funeral_directors":("Pompes funèbres","serv"),"estate_agent":("Agence immobilière","serv"),"e_cigarette":("Cigarette électronique","serv"),
  "car":("Automobiles","serv"),"tyres":("Pneus","serv"),"pawnbroker":("Rachat d'or","serv"),"repair":("Réparation","serv"),
  "lottery":("Loterie","serv"),"ticket":("Billetterie","serv"),"key_cutter":("Clés","serv")},
 "amenity": {"restaurant":("Restaurant","resto"),"cafe":("Café","resto"),"bar":("Bar","resto"),"pub":("Bar","resto"),"fast_food":("Restauration rapide","resto"),
  "ice_cream":("Glacier","resto"),"pharmacy":("Pharmacie","sante"),"dentist":("Dentiste","sante"),"doctors":("Cabinet médical","sante"),
  "veterinary":("Vétérinaire","sante"),"bank":("Banque","serv"),"post_office":("Bureau de poste","serv"),"marketplace":("Marché","alim")},
 "craft": {"shoemaker":("Cordonnier","serv"),"key_cutter":("Clés","serv"),"tailor":("Retouches","mode"),"jeweller":("Bijoutier","mode"),
  "watchmaker":("Horloger","mode"),"confectionery":("Confiseur","alim"),"caterer":("Traiteur","alim"),"photographer":("Photographe","loisir"),
  "upholsterer":("Tapissier","maison"),"framer":("Encadreur","maison")},
 "office": {"estate_agent":("Agence immobilière","serv"),"insurance":("Assurance","serv"),"travel_agent":("Agence de voyages","serv")},
 "leisure": {"fitness_centre":("Salle de sport","loisir")},
}

def classer(t):
    for k in ("shop","amenity","craft","office","leisure"):
        v = t.get(k)
        if v and v in TYPES[k]:
            return TYPES[k][v]
    if t.get("shop") and t["shop"] not in ("vacant","no"):
        return ("Commerce","autre")
    return None

def norm(s):
    s = (s or "").lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s

def http(url, data=None, timeout=120):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "autour-de-moi-data/2.0 (contact@commercesautourdemoi.fr)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def requete(code):
    return ('[out:json][timeout:%d];'
     'rel["ref:INSEE"="%s"]["boundary"="administrative"]["admin_level"~"^(8|9)$"]->.r;'
     '.r out center tags;.r map_to_area->.a;('
     'nwr["shop"]["name"](area.a);'
     'nwr["amenity"~"^(restaurant|cafe|bar|pub|fast_food|ice_cream|pharmacy|bank|post_office|dentist|doctors|veterinary|marketplace)$"]["name"](area.a);'
     'nwr["craft"]["name"](area.a);'
     'nwr["office"~"^(estate_agent|insurance|travel_agent)$"]["name"](area.a);'
     'nwr["leisure"="fitness_centre"]["name"](area.a);'
     ');out center tags;') % (TIMEOUT_OVP, code)

def overpass(code):
    body = urllib.parse.urlencode({"data": requete(code)}).encode()
    last = None
    for ep in OVERPASS:                       # un seul essai par serveur, puis on abandonne
        try:
            return http(ep, data=body, timeout=TIMEOUT_OVP + 15)
        except Exception as e:
            last = e
    raise last

def transformer(j):
    info = None; vus = set(); out = []
    for e in j.get("elements", []):
        t = e.get("tags", {})
        if e["type"] == "relation" and t.get("boundary") == "administrative" and info is None:
            c = e.get("center", {})
            info = {"nom": t.get("name"), "lat": c.get("lat"), "lon": c.get("lon"),
                    "cp": t.get("addr:postcode") or t.get("postal_code") or ""}
            continue
        lat = e.get("lat", (e.get("center") or {}).get("lat"))
        lon = e.get("lon", (e.get("center") or {}).get("lon"))
        if lat is None or not t.get("name"):
            continue
        k = classer(t)
        if not k:
            continue
        cle = norm(t["name"]) + "|" + format(lat, ".4f") + "|" + format(lon, ".4f")
        if cle in vus:
            continue
        vus.add(cle)
        rue = ((t.get("addr:housenumber", "") + " ") if t.get("addr:housenumber") else "") + (t.get("addr:street") or t.get("addr:place") or "")
        out.append({"i": e["type"][0] + str(e["id"]), "n": t["name"], "l": k[0], "c": k[1],
                    "y": round(float(lat), 6), "x": round(float(lon), 6), "r": rue.strip(),
                    "p": t.get("addr:postcode", ""), "v": t.get("addr:city", ""),
                    "t": t.get("phone") or t.get("contact:phone") or "",
                    "w": t.get("website") or t.get("contact:website") or "",
                    "h": t.get("opening_hours") or ""})
    out.sort(key=lambda a: a["n"].lower())
    return {"info": info, "d": out}

def arrondissements():
    codes = []
    for base, n in ((75101, 20), (69381, 9), (13201, 16)):
        codes += [str(base + i) for i in range(n)]
    return codes

def dep_de(code):
    c = (code or "").upper()
    if c[:2] in ("2A", "2B"):
        return c[:2]
    if c[:2] in ("97", "98"):
        return c[:3]
    return c[:2]

def ecrire_mairies():
    """Découpe build/mairies_emails.json en public/mairies/<dep>.json (routage des signalements)."""
    src = pathlib.Path("build/mairies_emails.json")
    if not src.exists():
        print("mairies_emails.json absent : routage mairies ignoré.", flush=True)
        return 0
    m = json.loads(src.read_text(encoding="utf-8"))
    pardep = {}
    for code, email in m.items():
        pardep.setdefault(dep_de(code), {})[code] = email
    for d, sous in pardep.items():
        (OUT_MAIRIES / (d + ".json")).write_text(
            json.dumps(sous, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("E-mails mairies : %d communes, %d départements." % (len(m), len(pardep)), flush=True)
    return len(m)

def main():
    t0 = time.time()
    nb_mairies = ecrire_mairies()      # d'abord : toujours publié, même si la génération est partielle
    print("Liste des communes…", flush=True)
    communes = http("https://geo.api.gouv.fr/communes?fields=code,nom,population,codesPostaux,centre&format=json", timeout=120)
    par_code = {c["code"]: c for c in communes}
    forcees = set()
    f = pathlib.Path("communes_forcees.txt")
    if f.exists():
        for ligne in f.read_text(encoding="utf-8").splitlines():
            code = ligne.split("#")[0].strip()
            if code:
                forcees.add(code)

    # cibles avec une priorité : forcées d'abord, puis par population décroissante
    cibles = {}  # code -> (priorite, meta)
    for c in communes:
        if (c.get("population") or 0) >= SEUIL_POP:
            cibles[c["code"]] = (c.get("population") or 0, c)
    for code in arrondissements():
        if code not in cibles:
            cibles[code] = (150000, par_code.get(code))   # grands arrondissements : tôt
    for code in forcees:
        meta = par_code.get(code)
        cibles[code] = (10**9 + (meta.get("population") if meta and meta.get("population") else 0), meta)  # clients : en tout premier

    liste = sorted(cibles.keys(), key=lambda cc: cibles[cc][0], reverse=True)  # plus gros d'abord
    print("Communes à générer : %d (seuil %d hab.) — plus grandes d'abord, budget %d min." % (len(liste), SEUIL_POP, BUDGET_MIN), flush=True)

    ok = 0; vides = 0; echecs = []; arretes = 0
    for idx, code in enumerate(liste, 1):
        if (time.time() - t0) / 60.0 > BUDGET_MIN:
            arretes = len(liste) - idx + 1
            print("Budget de temps atteint : arrêt propre, %d communes non traitées (elles resteront en direct)." % arretes, flush=True)
            break
        meta = cibles[code][1]
        try:
            res = transformer(overpass(code))
            if meta:
                res["info"] = res.get("info") or {}
                res["info"]["nom"] = res["info"].get("nom") or meta.get("nom")
                if not res["info"].get("cp"):
                    res["info"]["cp"] = (meta.get("codesPostaux") or [""])[0]
                ctr = meta.get("centre") or {}
                if res["info"].get("lat") is None and ctr.get("coordinates"):
                    res["info"]["lat"] = ctr["coordinates"][1]; res["info"]["lon"] = ctr["coordinates"][0]
            res["t"] = int(time.time() * 1000)
            (OUT / (code + ".json")).write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            ok += 1
            if not res["d"]:
                vides += 1
            print("  [%d/%d] %s : %d commerces" % (idx, len(liste), code, len(res["d"])), flush=True)
        except Exception as e:
            echecs.append(code)
            print("  [%d/%d] %s : échec (%s)" % (idx, len(liste), code, str(e)[:80]), flush=True)
        time.sleep(PAUSE)

    build = {"genere_le": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "seuil_population": SEUIL_POP, "communes_ok": ok, "communes_vides": vides,
             "echecs": echecs, "non_traitees_budget": arretes, "total_cible": len(liste),
             "mairies_emails": nb_mairies,
             "minutes": round((time.time() - t0) / 60.0, 1)}
    pathlib.Path("public/build.json").write_text(json.dumps(build, ensure_ascii=False, indent=2), encoding="utf-8")
    pathlib.Path("public/index.html").write_text(
        "<!doctype html><meta charset=utf-8><title>Autour de moi — données</title>"
        "<h1>Autour de moi — annuaires pré-générés</h1>"
        "<p>%d communes générées le %s (%s min). Fichiers dans /communes/&lt;code INSEE&gt;.json</p>" % (ok, build["genere_le"], build["minutes"]),
        encoding="utf-8")
    print("Terminé : %d ok, %d échecs, %d non traitées, en %s min." % (ok, len(echecs), arretes, build["minutes"]), flush=True)
    if ok == 0:
        sys.exit("Aucune commune générée.")

if __name__ == "__main__":
    main()
