# Ancols — préparation du contrôle ANCOLS

Préparation du contrôle de l'ANCOLS chez Aiguillon Construction (période contrôlée 2021-2025).
Première brique : un **diagnostic des 22 trames** à remplir (recueils de données et questionnaires),
qui repère les données qu'elles mobilisent en commun afin de fixer les points de contrôle,
de vigilance et de cohérence **avant** de produire les réponses.

> Les trames versionnées ici sont les **modèles vierges** transmis par l'ANCOLS. Les trames
> remplies, qui contiennent des données nominatives et financières, ne sont **jamais** versionnées
> (voir `.gitignore`).

## Ouvrir le diagnostic

`app-statique/index.html` est une page autonome : double-clic, ou dans VS Code avec **Live Server**
(bouton « Go Live », réglage fourni dans `.vscode/settings.json`).

| Vue | Ce qu'elle montre |
|---|---|
| Synthèse | chiffres clés, cinq constats, étendue des chantiers, référentiels communs à constituer |
| Cartographie | réseau trames ↔ données pivots, et carte de proximité entre trames |
| Matrice | données pivots × trames, avec le détail des colonnes exactes |
| Thèmes & enjeux | 13 thèmes de contrôle, trames et données à aligner |
| Contrôles | 55 contrôles de cohérence inter-trames, par criticité, type, thème, trame |
| Alertes | frise des dates de référence et 19 points de vigilance |
| Fiches trames | maille, période, sources, données hors SI, voisins, contrôles, alertes |
| Organisation & charge | cinq vagues de production, plan de charge copiable en CSV (porteurs à affecter) |
| Inventaire des champs | les 751 colonnes, définition ANCOLS, donnée pivot, écarts de définition |
| Étape 2 | ordre de rapprochement avec le dictionnaire de données |

## Chiffres clés

- 22 trames : 14 recueils, 2 tableaux agrégés, 6 questionnaires
- 751 colonnes, rattachées à 67 données pivots, dont 64 partagées par au moins deux trames
- 40 données passerelles entre patrimoine et gestion locative
- 17 en-têtes qui diffèrent de leur définition ANCOLS, 3 trames sans définitions

## Régénérer

Python 3.10+ avec `openpyxl`.

```bash
python3 scripts/01_inventaire.py       # trames/vierges        -> donnees/inventaire_brut.json
python3 scripts/02_donnees_pivots.py   # rattachement aux données pivots -> donnees/pivots.json
python3 scripts/03_analyse.py          # fiches, contrôles, alertes -> donnees/analyse.json + inventaire_champs.csv
python3 scripts/04_assembler.py        # charte + page + données -> app-statique/index.html
```

Le contenu rédactionnel (enjeux, contrôles, alertes, vagues) se modifie dans `scripts/03_analyse.py` ;
les règles de rattachement des colonnes dans `scripts/02_donnees_pivots.py`.

## Charte visuelle

La mise en forme est celle de [`charte-visuelle`](https://github.com/tramotheAc/charte-visuelle),
copiée dans `src/theme/` avec sa version en tête de chaque fichier — comme dans le projet SIG.
Pour la mettre à jour depuis un clone local :

```bash
cp .env.exemple .env                   # puis renseigner CHARTE=<chemin du clone>
python3 scripts/synchroniser_charte.py
python3 scripts/04_assembler.py
python3 <CHARTE>/outils/couverture.py app-statique/index.html
python3 <CHARTE>/outils/contraste.py  app-statique/index.html
```

Les deux contrôles passent sur la version actuelle : 59 jetons employés, tous déclarés ;
aucun écart de contraste en clair ni en sombre.

## Structure

```
app-statique/index.html   page assemblée, prête à ouvrir
src/
  page.html               balisage (ossature de la charte : rail, scène, vues)
  page.css                styles propres au diagnostic (alias de la charte uniquement)
  page.js                 logique des vues
  theme/                  copie de la charte visuelle (ne pas modifier ici)
scripts/                  01 à 04 : chaîne de régénération ; synchroniser_charte.py
donnees/                  inventaire brut, données pivots, analyse, inventaire_champs.csv
trames/vierges/           modèles ANCOLS vierges (référence)
docs/METHODE.md           méthode d'analyse et conventions
```

## Suite

Étape 2 : rapprocher `donnees/inventaire_champs.csv` du dictionnaire de données de l'entrepôt
(`dictionnaire_donnees_entrepot`) pour rattacher chaque donnée pivot à son champ source.
