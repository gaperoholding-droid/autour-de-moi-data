# -*- coding: utf-8 -*-
"""
TEST SIRENE v3 — fichier unique et autonome (n'importe plus naf.py).
Récupère les établissements d'une commune via l'API officielle Recherche
d'entreprises, les classe en Commerces / Services / Services libéraux, et
affiche le résultat dans les logs. Ne publie rien.

Usage : CODE_COMMUNE=42222 python build/test_sirene.py
"""
import os, sys, time, json, urllib.request, urllib.parse

VERSION = "v3 (3 familles)"
CODE = os.environ.get("CODE_COMMUNE", "42222")
API = "https://recherche-entreprises.api.gouv.fr/search"
PER = 25
TITRES = {"commerce": "COMMERCES", "service": "SERVICES", "liberal": "SERVICES LIBÉRAUX"}

# ======================= Classement NAF (3 familles) =======================
PRECIS = {
    "1071C": ("commerce", "Boulangerie-pâtisserie"), "1071D": ("commerce", "Pâtisserie"),
    "1071B": ("commerce", "Boulangerie"), "1013A": ("commerce", "Charcuterie / traiteur"),
    "1013B": ("commerce", "Charcuterie"), "4711A": ("commerce", "Supérette / épicerie"),
    "4711B": ("commerce", "Supérette"), "4711C": ("commerce", "Supermarché"),
    "4711D": ("commerce", "Supermarché"), "4711E": ("commerce", "Magasin multi-commerces"),
    "4711F": ("commerce", "Hypermarché"), "4721Z": ("commerce", "Primeur (fruits et légumes)"),
    "4722Z": ("commerce", "Boucherie-charcuterie"), "4723Z": ("commerce", "Poissonnerie"),
    "4724Z": ("commerce", "Boulangerie / pâtisserie / confiserie"), "4725Z": ("commerce", "Caviste (boissons)"),
    "4726Z": ("commerce", "Tabac"), "4729Z": ("commerce", "Épicerie fine / alimentation"),
    "4719A": ("commerce", "Grand magasin"), "4719B": ("commerce", "Bazar / commerce non spécialisé"),
    "4741Z": ("commerce", "Informatique"), "4742Z": ("commerce", "Téléphonie"),
    "4743Z": ("commerce", "Hi-fi / son / image"), "4751Z": ("commerce", "Tissus / mercerie"),
    "4752A": ("commerce", "Bricolage (petite surface)"), "4752B": ("commerce", "Bricolage (grande surface)"),
    "4753Z": ("commerce", "Revêtements sols et murs"), "4754Z": ("commerce", "Électroménager"),
    "4759A": ("commerce", "Ameublement"), "4759B": ("commerce", "Arts de la table / décoration"),
    "4761Z": ("commerce", "Librairie"), "4762Z": ("commerce", "Presse / papeterie"),
    "4763Z": ("commerce", "Musique / vidéo"), "4764Z": ("commerce", "Articles de sport"),
    "4765Z": ("commerce", "Jeux et jouets"), "4771Z": ("commerce", "Vêtements"),
    "4772A": ("commerce", "Chaussures"), "4772B": ("commerce", "Maroquinerie"),
    "4773Z": ("commerce", "Pharmacie"), "4774Z": ("commerce", "Matériel médical / orthopédie"),
    "4775Z": ("commerce", "Parfumerie / cosmétiques"), "4776Z": ("commerce", "Fleuriste / jardinerie / animalerie"),
    "4777Z": ("commerce", "Horlogerie-bijouterie"), "4778A": ("commerce", "Opticien"),
    "4778B": ("commerce", "Charbon / combustibles"), "4778C": ("commerce", "Cadeaux / déco / divers"),
    "4779Z": ("commerce", "Occasion / dépôt-vente / brocante"), "4532Z": ("commerce", "Pièces et accessoires auto"),
    "4511Z": ("commerce", "Automobiles"), "4519Z": ("commerce", "Véhicules (autres)"),
    "4540Z": ("commerce", "Motos / scooters"), "5610A": ("commerce", "Restaurant"),
    "5610B": ("commerce", "Cafétéria"), "5610C": ("commerce", "Restauration rapide"),
    "5621Z": ("commerce", "Traiteur"), "5629A": ("commerce", "Restauration collective"),
    "5629B": ("commerce", "Traiteur"), "5630Z": ("commerce", "Bar / café"),
    # ---- Services ----
    "9602A": ("service", "Coiffure"), "9602B": ("service", "Institut de beauté"),
    "9604Z": ("service", "Bien-être / spa"), "9609Z": ("service", "Services personnels divers"),
    "9601A": ("service", "Blanchisserie (industrielle)"), "9601B": ("service", "Pressing / laverie"),
    "9603Z": ("service", "Pompes funèbres"), "9511Z": ("service", "Réparation informatique"),
    "9512Z": ("service", "Réparation téléphonie"), "9521Z": ("service", "Réparation hi-fi / électronique"),
    "9522Z": ("service", "Réparation électroménager"), "9523Z": ("service", "Cordonnerie"),
    "9524Z": ("service", "Réparation de meubles"), "9525Z": ("service", "Horloger / réparation"),
    "9529Z": ("service", "Réparations diverses"), "4520A": ("service", "Garage (entretien auto)"),
    "4520B": ("service", "Carrosserie"), "7120B": ("service", "Contrôle technique automobile"),
    "6419Z": ("service", "Banque"), "6492Z": ("service", "Crédit / financement"),
    "6512Z": ("service", "Assurance"), "6622Z": ("service", "Assurance / courtage"),
    "6619A": ("service", "Change / services financiers"), "6619B": ("service", "Conseil financier"),
    "6831Z": ("service", "Agence immobilière"), "7911Z": ("service", "Agence de voyage"),
    "8553Z": ("service", "Auto-école"), "5310Z": ("service", "Bureau de poste"),
    "5320Z": ("service", "Services de courrier / colis"), "9313Z": ("service", "Salle de sport / fitness"),
    "9311Z": ("service", "Équipement sportif"), "8690C": ("service", "Ambulances / transport sanitaire"),
    # ---- Services libéraux (santé + juridique) ----
    "8621Z": ("liberal", "Médecin généraliste"), "8622A": ("liberal", "Cardiologue"),
    "8622B": ("liberal", "Radiologue"), "8622C": ("liberal", "Médecin spécialiste"),
    "8623Z": ("liberal", "Chirurgien-dentiste"), "8690A": ("liberal", "Laboratoire d'analyses médicales"),
    "8690B": ("liberal", "Centre de santé"), "8690D": ("liberal", "Kinésithérapeute / orthophoniste"),
    "8690E": ("liberal", "Infirmier(ère)"), "8690F": ("liberal", "Santé (autres praticiens)"),
    "7500Z": ("liberal", "Vétérinaire"), "8610Z": ("liberal", "Établissement de santé"),
    "6910Z": ("liberal", "Avocat / notaire / huissier"), "6920Z": ("liberal", "Expert-comptable"),
    "7111Z": ("liberal", "Architecte"), "7112A": ("liberal", "Géomètre"),
    "7112B": ("liberal", "Ingénierie / études techniques"),
}
SOUS = {
    "4520": ("service", "Garage automobile"), "8621": ("liberal", "Cabinet médical"),
    "8622": ("liberal", "Médecin spécialiste"), "8623": ("liberal", "Chirurgien-dentiste"),
    "8690": ("liberal", "Santé de proximité"), "6419": ("service", "Banque"),
    "6831": ("service", "Agence immobilière"), "7911": ("service", "Agence de voyage"),
    "6910": ("liberal", "Activité juridique"), "6920": ("liberal", "Expert-comptable"),
    "7111": ("liberal", "Architecte"),
}
DIVISION = {
    "47": ("commerce", "Commerce de détail"), "56": ("commerce", "Restauration"),
    "96": ("service", "Services à la personne"), "95": ("service", "Réparation"),
    "75": ("liberal", "Vétérinaire"), "86": ("liberal", "Santé"),
}
EXCLURE = {"4781Z", "4782Z", "4789Z", "4791A", "4791B", "4799A", "4799B"}

def classer(code):
    c = "".join(ch for ch in str(code or "").upper() if ch.isalnum())
    if not c or c in EXCLURE:
        return None
    if c in PRECIS:
        return PRECIS[c]
    if c[:4] in SOUS:
        return SOUS[c[:4]]
    if c[:2] in DIVISION:
        return DIVISION[c[:2]]
    return None

# ======================= Récupération API =======================
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
    print("total_results =", total, "| total_pages =", pages, flush=True)

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
                k = classer(code_naf)
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

