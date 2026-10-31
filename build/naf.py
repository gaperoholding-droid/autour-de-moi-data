# -*- coding: utf-8 -*-
"""
Classement des établissements par code NAF/APE en TROIS familles :
  - "commerce" : on y achète un produit (boulangerie, vêtements, pharmacie, resto…)
  - "service"  : prestation commerciale/artisanale (coiffeur, banque, garage, pressing…)
  - "liberal"  : profession libérale (santé et juridique : infirmier, médecin,
                 kiné, vétérinaire, avocat, notaire, expert-comptable, architecte…)

classer(code) -> (groupe, libellé)  ou  None si hors périmètre de proximité.
Table facile à ajuster.
"""

def _norm(code):
    if not code:
        return ""
    return "".join(c for c in str(code).upper() if c.isalnum())  # "47.24Z" -> "4724Z"

PRECIS = {
    # ================= COMMERCES : alimentaire =================
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
    # ================= COMMERCES : non alimentaire =================
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
    # ================= COMMERCES : restauration =================
    "5610A": ("commerce", "Restaurant"),
    "5610B": ("commerce", "Cafétéria"),
    "5610C": ("commerce", "Restauration rapide"),
    "5621Z": ("commerce", "Traiteur"),
    "5629A": ("commerce", "Restauration collective"),
    "5629B": ("commerce", "Traiteur"),
    "5630Z": ("commerce", "Bar / café"),

    # ================= SERVICES (prestation commerciale/artisanale) =================
    "9602A": ("service", "Coiffure"),
    "9602B": ("service", "Institut de beauté"),
    "9604Z": ("service", "Bien-être / spa"),
    "9609Z": ("service", "Services personnels divers"),
    "9601A": ("service", "Blanchisserie (industrielle)"),
    "9601B": ("service", "Pressing / laverie"),
    "9603Z": ("service", "Pompes funèbres"),
    "9511Z": ("service", "Réparation informatique"),
    "9512Z": ("service", "Réparation téléphonie"),
    "9521Z": ("service", "Réparation hi-fi / électronique"),
    "9522Z": ("service", "Réparation électroménager"),
    "9523Z": ("service", "Cordonnerie"),
    "9524Z": ("service", "Réparation de meubles"),
    "9525Z": ("service", "Horloger / réparation"),
    "9529Z": ("service", "Réparations diverses"),
    "4520A": ("service", "Garage (entretien auto)"),
    "4520B": ("service", "Carrosserie"),
    "7120B": ("service", "Contrôle technique automobile"),
    "6419Z": ("service", "Banque"),
    "6492Z": ("service", "Crédit / financement"),
    "6512Z": ("service", "Assurance"),
    "6622Z": ("service", "Assurance / courtage"),
    "6619A": ("service", "Change / services financiers"),
    "6619B": ("service", "Conseil financier"),
    "6831Z": ("service", "Agence immobilière"),
    "7911Z": ("service", "Agence de voyage"),
    "8553Z": ("service", "Auto-école"),
    "5310Z": ("service", "Bureau de poste"),
    "5320Z": ("service", "Services de courrier / colis"),
    "9313Z": ("service", "Salle de sport / fitness"),
    "9311Z": ("service", "Équipement sportif"),
    "8690C": ("service", "Ambulances / transport sanitaire"),
    # -- Artisans du bâtiment / travaux --
    "4321A": ("service", "Électricien"),
    "4321B": ("service", "Installation électrique (autres)"),
    "4322A": ("service", "Plombier-chauffagiste"),
    "4322B": ("service", "Installation eau / gaz / climatisation"),
    "4329A": ("service", "Isolation"),
    "4329B": ("service", "Autres travaux d'installation"),
    "4331Z": ("service", "Plâtrier"),
    "4332A": ("service", "Menuisier (bois / PVC)"),
    "4332B": ("service", "Menuiserie métallique / serrurerie"),
    "4332C": ("service", "Agencement de magasins"),
    "4333Z": ("service", "Carreleur / revêtements"),
    "4334Z": ("service", "Peintre / vitrier"),
    "4339Z": ("service", "Travaux de finition"),
    "4391A": ("service", "Charpentier"),
    "4391B": ("service", "Couvreur"),
    "4399A": ("service", "Étanchéité"),
    "4399C": ("service", "Maçon"),
    "4399D": ("service", "Travaux spécialisés (autres)"),
    "8130Z": ("service", "Paysagiste / entretien de jardins"),

    # ================= SERVICES LIBÉRAUX (santé + juridique) =================
    # -- Santé --
    "8621Z": ("liberal", "Médecin généraliste"),
    "8622A": ("liberal", "Cardiologue"),
    "8622B": ("liberal", "Radiologue"),
    "8622C": ("liberal", "Médecin spécialiste"),
    "8623Z": ("liberal", "Chirurgien-dentiste"),
    "8690A": ("liberal", "Laboratoire d'analyses médicales"),
    "8690B": ("liberal", "Centre de santé"),
    "8690D": ("liberal", "Kinésithérapeute / orthophoniste"),
    "8690E": ("liberal", "Infirmier(ère)"),
    "8690F": ("liberal", "Santé (autres praticiens)"),
    "7500Z": ("liberal", "Vétérinaire"),
    "8610Z": ("liberal", "Établissement de santé"),
    # -- Juridique / comptable / technique libérale --
    "6910Z": ("liberal", "Avocat / notaire / huissier"),
    "6920Z": ("liberal", "Expert-comptable"),
    "7111Z": ("liberal", "Architecte"),
    "7112A": ("liberal", "Géomètre"),
    # 71.12B (bureaux d'études / ingénierie B2B) volontairement exclu.
}

# --- Rattrapage par sous-classe (4) puis division (2) si le code précis manque ---
SOUS = {
    "4520": ("service", "Garage automobile"),
    "8621": ("liberal", "Cabinet médical"),
    "8622": ("liberal", "Médecin spécialiste"),
    "8623": ("liberal", "Chirurgien-dentiste"),
    "8690": ("liberal", "Santé de proximité"),
    "6419": ("service", "Banque"),
    "6831": ("service", "Agence immobilière"),
    "7911": ("service", "Agence de voyage"),
    "6910": ("liberal", "Activité juridique"),
    "6920": ("liberal", "Expert-comptable"),
    "7111": ("liberal", "Architecte"),
}
DIVISION = {
    "47": ("commerce", "Commerce de détail"),
    "56": ("commerce", "Restauration"),
    "96": ("service", "Services à la personne"),
    "95": ("service", "Réparation"),
    "43": ("service", "Artisan du bâtiment"),
    "75": ("liberal", "Vétérinaire"),
    "86": ("liberal", "Santé"),
}
# Codes à NE PAS retenir (vente à distance / hors magasin)
EXCLURE = {"4781Z", "4782Z", "4789Z", "4791A", "4791B", "4799A", "4799B"}

def classer(code):
    c = _norm(code)
    if not c or c in EXCLURE:
        return None
    if c in PRECIS:
        return PRECIS[c]
    if c[:4] in SOUS:
        return SOUS[c[:4]]
    if c[:2] in DIVISION:
        return DIVISION[c[:2]]
    return None
