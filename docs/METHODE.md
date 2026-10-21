# Méthode d'analyse des trames

## 1. Inventaire (`scripts/01_inventaire.py`)

Pour chaque classeur de `trames/vierges/` :

- les en-têtes réels de chaque onglet de recueil sont lus (ligne 1, ou la ligne d'en-tête propre
  aux trames sans définitions : copropriété ligne 12, sortants ligne 7, accession lignes 10 et 4) ;
- l'onglet « Définitions » est lu dans ses trois formats (onglet + colonne, colonne + type, colonne seule) ;
- chaque en-tête est rapproché de sa définition, par nom puis par lettre de colonne. Un statut est posé :
  `ok`, `name_or_col_mismatch` (le nom à cette lettre de colonne diffère), `nodef` (pas de définitions).

Les questionnaires (.docx, .xls) ne sont pas lus par script : leurs sections sont décrites à la main
dans `scripts/03_analyse.py` (`QL`), avec les données et les trames qu'elles mobilisent.

## 2. Données pivots (`scripts/02_donnees_pivots.py`)

Une **donnée pivot** est un concept que plusieurs trames demandent sous des noms différents
(ex. `CODE_PATRIMOINE`, `CODE_GROUPE_IMMOBILIER`, `CODE_PATRIMOINE_FOYER`, « code opération »
→ *Code groupe immobilier*). 67 pivots sont définis, en 8 familles.

Le rattachement se fait par expressions régulières ordonnées (`RULES`, la première qui correspond
l'emporte), corrigées colonne par colonne quand le sens dépend de l'onglet (`OVR`). Les colonnes
libres (observations, année de ligne) restent sans pivot.

## 3. Analyse (`scripts/03_analyse.py`)

Saisie à la main, à partir de la lecture des définitions et des points d'attention ANCOLS :

- **fiches trames** : maille, période, format, volumétrie, charge estimée, vague, sources probables,
  données hors SI ;
- **contrôles** (`C..`) : règle, test, criticité (1 bloquant, 2 majeur, 3 utile), type
  (référentiel, volumétrie, valeurs croisées, temporel, réglementaire, recueil ↔ questionnaire) ;
- **alertes** (`A..`) : anomalies des modèles, codifications hétérogènes, dates et périmètres,
  données personnelles, formats, formules à préserver, données hors SI ;
- **thèmes** de contrôle.

Calculé : la proximité entre trames (pivots partagés hors SIREN / raison sociale), les passerelles
patrimoine ↔ gestion locative, les dépendances entre vagues.

## Charge estimée

S, M, L, XL selon le nombre de colonnes, la maille (agrégat → logement × mois), la profondeur
d'historique et la part de données hors SI. C'est une estimation de départ, à réviser une fois
le dictionnaire de données rapproché.

## Conventions

- Les en-têtes des onglets de recueil font foi, pas la lettre de colonne des définitions.
- Les identifiants s'exportent en texte (zéros non significatifs conservés).
- Une seule table de correspondance par clé (groupe, lot / RPLS / bâtiment, compte locataire).
