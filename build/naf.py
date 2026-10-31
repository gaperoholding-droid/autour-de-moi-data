# -*- coding: utf-8 -*-
"""
Classement des établissements par code NAF/APE en deux familles :
  - "commerce" : on y achète un produit (boulangerie, vêtements, pharmacie, resto…)
  - "service"  : on y reçoit une prestation (coiffeur, banque, garage, santé…)

classer(code) -> (groupe, libellé)  ou  None si l'activité n'est pas un
commerce/service de proximité (industrie, gros, administration, agriculture…).

Table volontairement centrée sur la proximité. Facile à ajuster après le test.
"""

def _norm(code):
    if not code:
        return ""
    return "".join(c for c in str(code).upper() if c.isalnum())  # "47.24Z" -> "4724Z"

# --- Codes précis (5 caractères, lettre comprise) : libellé soigné ---
PRECIS = {
    # ---------- COMMERCES : alimentaire ----------
    "1071C": ("commerce", "Boulangerie-pâtisserie"),
    "1071D": ("commerce", "Pâtisserie"),
    "1071B": ("commerce", "Boulangerie"),
    "1013A": ("commerce", "Charcuterie / traiteur"),
    "1013B": ("commerce", "Charcuterie"),
    "4711A": ("commerce", "Supérette / épicerie"),
    "4711B": ("commerce", "Supérette"),
    "4711C": ("commerce", "Supermarché"),
    "4711D": ("commerce", "Supermarché"),
    "4711E": ("commerce", "Magasin multi-commerces"),
    "4711F": ("commerce", "Hypermarché"),
    "4721Z": ("commerce", "Primeur (fruits et légumes)"),
    "4722Z": ("commerce", "Boucherie-charcuterie"),
    "4723Z": ("commerce", "Poissonnerie"),
    "4724Z": ("commerce", "Boulangerie / pâtisserie / confiserie"),
    "4725Z": ("commerce", "Caviste (boissons)"),
    "4726Z": ("commerce", "Tabac"),
    "4729Z": ("commerce", "Épicerie fine / alimentation"),
    # ---------- COMMERCES : non alimentaire ----------
    "4719A": ("commerce", "Grand magasin"),
    "4719B": ("commerce", "Bazar / commerce non spécialisé"),
    "4741Z": ("commerce", "Informatique"),
    "4742Z": ("commerce", "Téléphonie"),
    "4743Z": ("commerce", "Hi-fi / son / image"),
    "4751Z": ("commerce", "Tissus / mercerie"),
    "4752A": ("commerce", "Bricolage (petite surface)"),
    "4752B": ("commerce", "Bricolage (grande surface)"),
    "4753Z": ("commerce", "Revêtements sols et murs"),
    "4754Z": ("commerce", "Électroménager"),
    "4759A": ("commerce", "Ameublement"),
    "4759B": ("commerce", "Arts de la table / décoration"),
    "4761Z": ("commerce", "Librairie"),
    "4762Z": ("commerce", "Presse / papeterie"),
    "4763Z": ("commerce", "Musique / vidéo"),
    "4764Z": ("commerce", "Articles de sport"),
    "4765Z": ("commerce", "Jeux et jouets"),
    "4771Z": ("commerce", "Vêtements"),
    "4772A": ("commerce", "Chaussures"),
    "4772B": ("commerce", "Maroquinerie"),
    "4773Z": ("commerce", "Pharmacie"),
    "4774Z": ("commerce", "Matériel médical / orthopédie"),
    "4775Z": ("commerce", "Parfumerie / cosmétiques"),
    "4776Z": ("commerce", "Fleuriste / jardinerie / animalerie"),
    "4777Z": ("commerce", "Horlogerie-bijouterie"),
    "4778A": ("commerce", "Opticien"),
    "4778B": ("commerce", "Charbon / combustibles"),
    "4778C": ("commerce", "Cadeaux / déco / divers"),
    "4779Z": ("commerce", "Occasion / dépôt-vente / brocante"),
    "4532Z": ("commerce", "Pièces et accessoires auto"),
    "4511Z": ("commerce", "Automobiles"),
    "4519Z": ("commerce", "Véhicules (autres)"),
    "4540Z": ("commerce", "Motos / scooters"),
    # ---------- COMMERCES : restauration ----------
    "5610A": ("commerce", "Restaurant"),
    "5610B": ("commerce", "Cafétéria"),
    "5610C": ("commerce", "Restauration rapide"),
    "5621Z": ("commerce", "Traiteur"),
    "5629A": ("commerce", "Restauration collective"),
    "5629B": ("commerce", "Traiteur"),
    "5630Z": ("commerce", "Bar / café"),

    # ---------- SERVICES : beauté / soin / personnel ----------
    "9602A": ("service", "Coiffure"),
    "9602B": ("service", "Institut de beauté"),
    "9604Z": ("service", "Bien-être / spa"),
    "9609Z": ("service", "Services personnels divers"),
    "9601A": ("service", "Blanchisserie (industrielle)"),
    "9601B": ("service", "Pressing / laverie"),
    "9603Z": ("service", "Pompes funèbres"),
    # ---------- SERVICES : réparation ----------
    "9511Z": ("service", "Réparation informatique"),
    "9512Z": ("service", "Réparation téléphonie"),
    "9521Z": ("service", "Réparation hi-fi / électronique"),
    "9522Z": ("service", "Réparation électroménager"),
    "9523Z": ("service", "Cordonnerie"),
    "9524Z": ("service", "Réparation de meubles"),
    "9525Z": ("service", "Horloger / réparation"),
    "9529Z": ("service", "Réparations diverses"),
    # ---------- SERVICES : auto ----------
    "4520A": ("service", "Garage (entretien auto)"),
    "4520B": ("service", "Carrosserie"),
    # ---------- SERVICES : banque / assurance / immobilier ----------
    "6419Z": ("service", "Banque"),
    "6492Z": ("service", "Crédit / financement"),
    "6512Z": ("service", "Assurance"),
    "6622Z": ("service", "Assurance / courtage"),
    "6619A": ("service", "Change / services financiers"),
    "6619B": ("service", "Conseil financier"),
    "6831Z": ("service", "Agence immobilière"),
    # ---------- SERVICES : divers de proximité ----------
    "7911Z": ("service", "Agence de voyage"),
    "8553Z": ("service", "Auto-école"),
    "5310Z": ("service", "Bureau de poste"),
    "5320Z": ("service", "Services de courrier / colis"),
    "9313Z": ("service", "Salle de sport / fitness"),
    "9311Z": ("service", "Équipement sportif"),
    # ---------- SERVICES : santé ----------
    "8621Z": ("service", "Médecin généraliste"),
    "8622A": ("service", "Cardiologie"),
    "8622B": ("service", "Radiologie"),
    "8622C": ("service", "Médecin spécialiste"),
    "8623Z": ("service", "Dentiste"),
    "8690A": ("service", "Laboratoire d'analyses"),
    "8690B": ("service", "Centre de santé"),
    "8690C": ("service", "Ambulances"),
    "8690D": ("service", "Kinésithérapie / orthophonie"),
    "8690E": ("service", "Soins infirmiers"),
    "8690F": ("service", "Santé (autres)"),
    "7500Z": ("service", "Vétérinaire"),
}

# --- Rattrapage par division (2 chiffres) ou sous-classe (4) si code précis absent ---
# Évite de rater un établissement dont le code exact n'est pas listé ci-dessus.
DIVISION = {
    "47": ("commerce", "Commerce de détail"),
    "56": ("commerce", "Restauration"),
    "96": ("service", "Services à la personne"),
    "95": ("service", "Réparation"),
    "75": ("service", "Vétérinaire"),
}
SOUS = {
    "4520": ("service", "Garage automobile"),
    "8621": ("service", "Cabinet médical"),
    "8622": ("service", "Médecin spécialiste"),
    "8623": ("service", "Dentiste"),
    "8690": ("service", "Santé de proximité"),
    "6419": ("service", "Banque"),
    "6831": ("service", "Agence immobilière"),
    "7911": ("service", "Agence de voyage"),
}
# Codes de la division 47 à NE PAS retenir (vente à distance / hors magasin)
EXCLURE = {"4781Z", "4782Z", "4789Z", "4791A", "4791B", "4799A", "4799B"}

def classer(code):
    c = _norm(code)
    if not c:
        return None
    if c in EXCLURE:
        return None
    if c in PRECIS:
        return PRECIS[c]
    if c[:4] in SOUS:
        return SOUS[c[:4]]
    if c[:2] in DIVISION:
        return DIVISION[c[:2]]
    return None
