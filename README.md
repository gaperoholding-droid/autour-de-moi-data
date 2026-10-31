# Autour de moi — annuaires pré-générés

Ce dépôt prépare **chaque nuit**, automatiquement et gratuitement, les annuaires de commerces
des grandes communes, pour que les pages du site s'affichent **instantanément** au lieu
d'interroger OpenStreetMap en direct (ce qui est lent pour les grosses villes).

- Les petites communes restent chargées en direct (c'est déjà rapide).
- Les grandes communes (+ de 20 000 habitants), les arrondissements de Paris / Lyon / Marseille,
  et vos communes clientes sont pré-générées la nuit.
- Chaque commune devient un petit fichier `public/communes/<code INSEE>.json`.
- Tout est publié sur **GitHub Pages**, que le site lit en une fraction de seconde.

## Mise en route (à faire une seule fois)

1. **Créer un compte GitHub** (gratuit) sur https://github.com
2. **Créer un dépôt** : bouton « New repository ».
   - Nom : `autour-de-moi-data`
   - Cochez **Public** (indispensable pour que ce soit gratuit et illimité).
   - Créez le dépôt.
3. **Déposer ces fichiers** : sur la page du dépôt, « Add file » → « Upload files »,
   puis glissez **tout le contenu** de ce dossier (en gardant les sous-dossiers
   `.github/` et `build/`). Cliquez « Commit changes ».
4. **Activer GitHub Pages** : onglet **Settings** → **Pages** →
   « Build and deployment » → **Source : GitHub Actions**.
5. **Lancer la première génération** : onglet **Actions** →
   « Générer les annuaires (nuit) » → bouton **Run workflow**.
   La première fois prend un peu de temps (environ 1 h selon les villes). Ensuite c'est
   automatique chaque nuit.
6. **Récupérer l'adresse** : une fois le travail terminé, Settings → Pages affiche
   l'adresse de votre site de données, du type :
   `https://VOTRE-NOM.github.io/autour-de-moi-data/`

## Brancher le site dessus

Dans le code de votre page annuaire (variable en haut du script), renseignez :

    var DATA_BASE = "https://VOTRE-NOM.github.io/autour-de-moi-data/";

C'est tout : le site lira d'abord le fichier pré-généré (instantané), et basculera
automatiquement sur le direct si une commune n'a pas encore été générée.

## Réglages

- **Couvrir plus de communes** : dans `.github/workflows/build.yml`, baissez `SEUIL_POP`
  (par exemple `10000`). Plus bas = plus de communes, mais génération plus longue.
- **Ajouter une commune précise** (même petite, ex. un client) : ajoutez son code INSEE
  dans `communes_forcees.txt`.

## Coût

Zéro. Dépôt public = minutes GitHub Actions illimitées, et GitHub Pages est gratuit.

## Données

Commerces : © contributeurs OpenStreetMap (licence ODbL). Liste et population des communes :
API Découpage administratif (geo.api.gouv.fr).
