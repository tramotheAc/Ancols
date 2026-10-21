"""Etape 3 - jeu d'analyse complet : fiches des trames, liens des questionnaires, controles, alertes, themes.

Le contenu redactionnel (enjeux, controles, alertes) est saisi ici : c'est le fichier a modifier
pour enrichir le diagnostic.

    python3 scripts/03_analyse.py               donnees/pivots.json -> donnees/analyse.json + donnees/inventaire_champs.csv
"""
import json, sys, os, csv, collections, itertools
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = json.load(open(os.path.join(RACINE, 'donnees', 'pivots.json'), encoding='utf-8'))
OUT = os.path.join(RACINE, 'donnees', 'analyse.json')
fields, P, FAM = M['fields'], M['pivots'], M['families']
# Les charges rejoignent les loyers : huit familles, huit couleurs de serie distinctes.
FAM = [[k, ('Loyers, charges & quittancement' if k == 'LOY' else v)] for k, v in FAM if k != 'CHG']
for _p in P.values():
    if _p['fam'] == 'CHG': _p['fam'] = 'LOY'
for _f in fields:
    if _f.get('fam') == 'CHG': _f['fam'] = 'LOY'

# ------------------------------------------------------------ files
# kind: R = recueil (extraction), Q = questionnaire, A = tableau agrégé
F = [
 dict(code='11_30_01', dom='GP', kind='R', short='Foyers', title='Foyers et résidences',
      maille='1 ligne par foyer / résidence', period='Photo à la date d\'extraction ; PCRC sur 2021-2025, stock au 31/12/2025',
      fmt='.xlsx', vol='Faible (nb de foyers)', effort='M', wave=2,
      sources='Patrimoine, conventions de gestion, comptabilité (PCRC)',
      enjeux='Connaissance du parc foyer, gestion déléguée (conventions, gestionnaires), suivi de la provision pour grosses réparations (PCRC) et des réhabilitations.',
      manual='PCRC (disponible, dotations, dépenses) souvent hors ERP ; dates de convention de gestion.'),
 dict(code='11_30_02', dom='GP', kind='R', short='Etat des lieux patrimoine', title='Etat des lieux et connaissance du patrimoine',
      maille='Bâtiment / groupe (onglet 1), bâtiment (onglet 2), logement (onglet 3)', period='Photo à la date d\'extraction ; vacance au 1er janvier ; cumuls sur 5 ans (EDL, REL, dépenses)',
      fmt='.xlsx', vol='Élevée (1 ligne par logement en onglet 3)', effort='XL', wave=0,
      sources='Référentiel patrimoine, base DPE, PSP, GMAO / comptabilité (dépenses REL et investissement)',
      enjeux='Trame socle : référentiel groupe / bâtiment / logement, zonages, QPV, financement, PSP, cartographie énergétique. Toutes les autres trames s\'y rapprochent.',
      manual='Classification PSP, nb de dossiers DO, ventilation REL récupérable / non récupérable, tantièmes.'),
 dict(code='11_30_03', dom='GP', kind='R', short='Exploitation & sécurité', title='Exploitation et sécurité',
      maille='Marché (onglet 1), équipement ou groupe équipé (onglets 2.x), logement ou bâtiment par diagnostic (onglets 3.x)', period='Photo à la date d\'extraction ; indicateurs N-1 et N-2',
      fmt='.xlsx (13 onglets)', vol='Élevée (diagnostics au logement)', effort='XL', wave=2,
      sources='Marchés / achats, GMAO, prestataires (ascensoristes, chauffagistes), base diagnostics (DDT)',
      enjeux='Sécurité des personnes et obligations réglementaires : ascenseurs, aires de jeux, gaz, SSI, plomb, amiante, électricité ; pilotage des marchés d\'entretien.',
      manual='Visites, absences et refus d\'entretien, pannes et taux de disponibilité souvent détenus par les prestataires ; avenants et variations des marchés.'),
 dict(code='11_30_04', dom='GP', kind='A', short='Accessibilité & adaptation', title='Accessibilité et adaptation',
      maille='Agrégats parc (1 ligne) et 1 ligne par année 2021-2025', period='Au 31/12/2025 (accessibilité) ; annuel 2021-2025 (adaptation)',
      fmt='.xlsx', vol='Très faible', effort='M', wave=3,
      sources='Base accessibilité (si existante), demandes d\'adaptation, fiscalité (dégrèvements TFPB), occupation (âges)',
      enjeux='Connaissance du niveau d\'accessibilité, réponse aux demandes d\'adaptation, vieillissement des locataires, dégrèvements TFPB.',
      manual='Comptages accessibilité UFR / canne, délais et dossiers en attente, dégrèvements demandés / obtenus.'),
 dict(code='11_30_05', dom='GP', kind='R', short='Politique patrimoniale', title='Politique patrimoniale',
      maille='Année (synthèse), opération (onglets 2, 4, 5), groupe réhabilité (onglet 3)', period='Période de contrôle 2021-2025 ; situation à fin N-1',
      fmt='.xlsx (5 onglets)', vol='Moyenne', effort='XL', wave=2,
      sources='Maîtrise d\'ouvrage / développement, contrôle de gestion, comptabilité (prix de revient, financements), juridique (contentieux)',
      enjeux='Évolution du parc (production, ventes, démolitions), coûts et financements des opérations neuves et des réhabilitations, contentieux, opérations abandonnées.',
      manual='Opérations abandonnées et dépenses engagées, contentieux et incidences financières, taux d\'occupation à la mise en location.'),
 dict(code='11_30_06', dom='GP', kind='R', short='Vente HLM', title='Vente à l\'unité',
      maille='1 ligne par logement vendu', period='Ventes signées sur la période de contrôle',
      fmt='.xlsx', vol='Faible à moyenne', effort='L', wave=2,
      sources='Service ventes, notaires, comptabilité (VNC, plus-values, emprunts), gestion locative (bail, loyer)',
      enjeux='Régularité des ventes : autorisation (CA, CUS / préfet), publicité, prix vs grille, qualité et ressources des acquéreurs, VNC et plus-values.',
      manual='Publicité (journaux, sites), ressources des acquéreurs, grilles de prix.'),
 dict(code='11_30_07', dom='GP', kind='R', short='Accession sociale', title='Accession sociale',
      maille='Opération (synthèse) et logement vendu (onglet au logement)', period='Opérations livrées et ventes sur 2021-2025',
      fmt='.xlsx', vol='Faible à moyenne', effort='M', wave=2,
      sources='Service accession / ventes, SCCV, notaires',
      enjeux='Respect des plafonds (prix, ressources) PSLA / BRS / VEFA ANRU, TVA réduite en QPV, profil des accédants.',
      manual='Associés SCCV et parts, catégorie de ménage avant 2024 (nombre de personnes).'),
 dict(code='11_30_08', dom='GP', kind='R', short='Patrimoine en copropriété', title='Patrimoine en copropriété',
      maille='1 ligne par copropriété / groupe', period='Au 1er janvier 2025',
      fmt='.xlsx (sans onglet Définitions)', vol='Faible', effort='M', wave=2,
      sources='Gestion des copropriétés, syndics externes',
      enjeux='Poids du patrimoine en copropriété, gouvernance (syndic), carnet d\'entretien, DTG et plan pluriannuel de travaux.',
      manual='Existence / dates de DTG et de PPT, carnet d\'entretien, nombre total de lots de la copropriété.'),
 dict(code='11_30_09', dom='GP', kind='Q', short='Q. Accessibilité', title='Questionnaire accessibilité et adaptation (5.2.3)',
      maille='Questionnaire rédactionnel + pièces', period='3 dernières années et années à venir',
      fmt='.docx', vol='—', effort='M', wave=4,
      sources='Direction patrimoine, gestion locative, partenaires (CCAS, caisses de retraite)',
      enjeux='Politique d\'accessibilité et d\'adaptation, Ad\'AP des ERP, procédure de demande, base de données accessibilité au logement.',
      manual='Rédactionnel ; la base « niveau d\'accessibilité au logement » demandée doit reprendre RPLS, code interne, commune, adresse et programme.'),
 dict(code='11_30_10', dom='GP', kind='Q', short='Q. Offre nouvelle', title='Questionnaire offre nouvelle',
      maille='Questionnaire rédactionnel + pièces', period='N-1 et N-2 pour la ventilation par financement',
      fmt='.docx', vol='—', effort='M', wave=4,
      sources='Direction du développement, gouvernance, commercialisation',
      enjeux='Organisation et pilotage du développement, stratégie foncière, arbitrage des financements, conformité des agréments au PMT, gestion des risques (GPA, DO).',
      manual='Rédactionnel ; ventilation PLAI / PLUS / PLS / LLI à rapprocher de l\'onglet 2_Opérations nouvelles.'),
 dict(code='12_30_01', dom='GL', kind='R', short='CALEOL / attributions', title='CALEOL et attributions',
      maille='1 ligne par candidat présenté × CALEOL (un demandeur peut apparaître plusieurs fois)', period='CALEOL de N-3 à N-1 (2023-2025)',
      fmt='.xlsx', vol='Élevée', effort='XL', wave=1,
      sources='ERP locatif (module attribution), SNE, réservataires',
      enjeux='Conformité des décisions (valeurs CCH), atteinte des objectifs (1er quartile hors QPV, DALO, prioritaires), réservataires, taux d\'effort et reste à vivre.',
      manual='Retour candidat, rang, réservataire désignataire en gestion en flux, valeur du 1er quartile par EPCI.'),
 dict(code='12_30_02', dom='GL', kind='R', short='Loyers logements', title='Loyers des logements',
      maille='1 ligne par lot (toutes natures, occupé ou non)', period='Photo au 1er janvier de la dernière année contrôlée (01/01/2025)',
      fmt='.xlsx', vol='Élevée (1 ligne par lot)', effort='L', wave=0,
      sources='ERP locatif (lots, conventions APL, quittancement de janvier)',
      enjeux='Trame socle locative : loyers pratiqués vs loyers maximum conventionnels, surfaces, financements CUS, zonages ; référentiel lot ↔ RPLS.',
      manual='Loyers maximum initiaux en francs pour les conventions anciennes, date de valeur des conventions.'),
 dict(code='12_30_03', dom='GL', kind='R', short='Charges locatives', title='Charges locatives',
      maille='Groupe × nature de charge × exercice', period='Charges de N-5 à N-1 (2021-2025), comptes de classe 6',
      fmt='.csv (1 fichier ou 1 par année)', vol='Élevée', effort='L', wave=1,
      sources='Comptabilité, module charges de l\'ERP',
      enjeux='Récupérabilité des charges, poids par nature et par groupe, modes de répartition, régularisations.',
      manual='Rattachement compte comptable ↔ nature de charge récupérable.'),
 dict(code='12_30_04', dom='GL', kind='R', short='SLS', title='Supplément de loyer de solidarité',
      maille='1 ligne par locataire enquêté × année de calcul', period='Enquêtes SLS N-2 et N-1 (2024-2025)',
      fmt='.xlsx', vol='Moyenne', effort='M', wave=1,
      sources='ERP locatif (enquête SLS), prestataire éventuel',
      enjeux='Exactitude du calcul du SLS, application du forfaitaire, exemptions (QPV, ZRR, PLAI…), perte du droit au maintien dans les lieux.',
      manual='SLS de référence par zone, cas forfaitaires.'),
 dict(code='12_30_05', dom='GL', kind='R', short='Quittancement', title='Quittancement des logements',
      maille='Locataire × lot × rubrique × mois', period='Tous les mois de 2025 ; soldes avant quittancement non échu au 31/12/2025',
      fmt='.csv (1 fichier par année ou par mois)', vol='Très élevée (lots × rubriques × 12 mois)', effort='L', wave=1,
      sources='ERP locatif (quittancement), comptabilité auxiliaire',
      enjeux='Rapprochement loyers / SLS / charges / dépôts de garantie quittancés ; soldes débiteurs et créditeurs.',
      manual='Rubriques à rattacher aux comptes comptables ; limite de 1 048 576 lignes d\'Excel.'),
 dict(code='12_30_06', dom='GL', kind='R', short='Réclamations / interventions', title='Réclamations et interventions',
      maille='Réclamation × intervention', period='Réclamations saisies de N-5 à N-1 (2021-2025)',
      fmt='.xlsx', vol='Élevée', effort='L', wave=1,
      sources='CRM / GRC, GMAO, comptabilité (montants, comptes)',
      enjeux='Qualité de service : volumes, délais de traitement, natures, coût des interventions, lien avec les marchés.',
      manual='Rapprochement réclamation ↔ intervention ↔ marché ↔ facture.'),
 dict(code='12_30_07', dom='GL', kind='R', short='Sortants / entrants', title='Locataires sortants et entrants',
      maille='1 ligne par sortie de locataire (et entrant dans le logement libéré)', period='Sorties du 01/01/2025 au 31/12/2025, hors foyers et résidences étudiantes',
      fmt='.xlsx (sans onglet Définitions)', vol='Moyenne', effort='L', wave=3,
      sources='ERP locatif (sorties, EDL, décomptes), CALEOL, comptabilité (dépôts de garantie)',
      enjeux='Délais de relocation, remise en état et imputations au locataire, restitution du dépôt de garantie, loyer de relocation.',
      manual='Consolidation multi-sources (EDL, décompte, DG, CAL, nouveau bail).'),
 dict(code='12_30_08', dom='GL', kind='Q', short='Q. Qualité de service', title='Questionnaire qualité de service',
      maille='Questionnaire rédactionnel + pièces', period='3 dernières années',
      fmt='.docx', vol='—', effort='M', wave=4,
      sources='Direction clientèle, proximité, maintenance, DSU',
      enjeux='Stratégie qualité, satisfaction, accueil, traitement des réclamations, maintenance, TFPB en QPV, assurances locatives.',
      manual='Rédactionnel et indicateurs (centre de relation client, délais de traitement).'),
 dict(code='12_30_09', dom='GL', kind='Q', short='Q. Loyers', title='Questionnaire loyers',
      maille='Questionnaire rédactionnel', period='Période de contrôle',
      fmt='.docx', vol='—', effort='S', wave=4,
      sources='Gestion locative, gouvernance (politique de loyers)',
      enjeux='Organisation et contrôle interne du quittancement, politique de loyers (relocation, réhabilitation, neuf, hors QPV / 1er quartile).',
      manual='Rédactionnel.'),
 dict(code='12_30_10', dom='GL', kind='Q', short='Q. Charges', title='Questionnaire charges récupérables',
      maille='Questionnaire rédactionnel + pièces', period='Période de contrôle',
      fmt='.docx', vol='—', effort='M', wave=4,
      sources='Service charges, comptabilité, gestion des copropriétés',
      enjeux='Organisation, provisionnement, temporalité des régularisations, charges de personnel, régularisations des partis.',
      manual='% de programmes régularisés par année et liste des non régularisés.'),
 dict(code='12_30_11', dom='GL', kind='Q', short='Q. SLS', title='Questionnaire SLS',
      maille='Questionnaire rédactionnel + tableau chiffré', period='N-1 à N-3',
      fmt='.docx', vol='—', effort='S', wave=4,
      sources='Gestion locative (enquêtes SLS)',
      enjeux='Procédure SLS, exclusions, volumes calculés / forfaitaires, perte du droit au maintien dans les lieux.',
      manual='Tableau NB / montants SLS calculés et forfaitaires sur 3 années.'),
 dict(code='12_30_12', dom='GL', kind='A', short='Recouvrement', title='Suivi des procédures de recouvrement',
      maille='Indicateurs agrégés × année', period='2021-2025 + année N à date',
      fmt='.xls (benchmark USH intégré)', vol='Très faible', effort='M', wave=3,
      sources='Recouvrement / contentieux, huissiers, FSL',
      enjeux='Volume d\'impayés, efficacité des procédures amiables et contentieuses, comparaison au benchmark USH.',
      manual='Comptages de procédures souvent issus de tableaux de suivi internes.'),
]
FD = {f['code']: f for f in F}

# ------------------------------------------------------------ questionnaire / aggregate links (code -> list of (section, pivots, files))
QL = {
 '11_30_09': [
   ('Organisation et politique générale (accessibilité, adaptation, objectifs chiffrés)', ['ACCESS', 'PRIX'], ['11_30_04']),
   ('Ad\'AP des ERP', ['NATLOT'], ['11_30_02']),
   ('Locataires : repérage, procédure de demande, aides', ['MENAGE', 'PUBLIC', 'ACCESS'], ['11_30_04', '12_30_01']),
   ('Patrimoine existant : classification des parties communes, budgets', ['ACCESS', 'PRIX', 'GRP'], ['11_30_04', '11_30_02']),
   ('Base de données accessibilité au logement (RPLS, code, commune, adresse, programme)', ['RPLS', 'LOT', 'GRP', 'GRP_NOM', 'COMMUNE', 'ADR', 'ACCESS'], ['11_30_02', '11_30_04']),
   ('Financements spécifiques au-delà des dégrèvements TFPB', ['ACCESS', 'FINOP'], ['11_30_04']),
   ('Offre neuve dédiée aux personnes âgées / intergénérationnelle', ['OPE', 'NBLGT', 'PRIX', 'DMES'], ['11_30_05']),
 ],
 '11_30_10': [
   ('Organisation, gouvernance et outils de pilotage', ['GOUV'], ['11_30_05']),
   ('Territoires ciblés (départements, communes)', ['DEPT', 'COMMUNE', 'EPCI'], ['11_30_05']),
   ('Pilotage : part MOD / VEFA, délais par mode de production', ['PROD', 'GOUV', 'DMES'], ['11_30_05']),
   ('Arbitrage du financement : coût plafond, fonds propres', ['PRIX', 'FINOP'], ['11_30_05']),
   ('Ventilation PLAI / PLUS / PLS / LLI des agréments N-1 et N-2', ['FCUS', 'GOUV'], ['11_30_05']),
   ('Livraison et mise en location (commercialisation)', ['DMES', 'VAC'], ['11_30_05', '12_30_01']),
   ('Gestion des risques : levée des réserves, GPA, dommage-ouvrage', ['CONT'], ['11_30_05', '11_30_02']),
 ],
 '12_30_08': [
   ('Pilotage, indicateurs, certification', ['INTERV'], ['12_30_06']),
   ('Satisfaction et accueil (agences, proximité, canaux)', ['AGENCE', 'INTERV'], ['12_30_06']),
   ('Traitement des demandes et réclamations, troubles de voisinage', ['INTERV'], ['12_30_06']),
   ('Remise en état à la relocation, vétusté', ['REL'], ['11_30_02', '12_30_07']),
   ('Contrats de service, régie, pilotage des prestataires, entretien ménager', ['MARCHE', 'MARCHEI', 'TITU', 'CHARGES'], ['11_30_03', '12_30_06', '12_30_03']),
   ('Abattement TFPB en QPV, DSU, assurances locatives', ['QPV'], ['11_30_02']),
 ],
 '12_30_09': [
   ('Organisation et contrôle interne du quittancement', ['QUIT', 'LOYER'], ['12_30_05', '12_30_02']),
   ('Hausses de loyer à la relocation', ['LOYER', 'LMAX'], ['12_30_02', '12_30_07', '12_30_01']),
   ('Hausses de loyer après réhabilitation', ['LMAX', 'REHA'], ['11_30_05', '12_30_02']),
   ('Loyers des programmes neufs vs loyer maximum', ['LMAX', 'DMES'], ['11_30_05', '12_30_02']),
   ('Politique de loyers hors QPV / 1er quartile', ['QPV', 'PLAF', 'LOYER'], ['12_30_01', '12_30_02']),
 ],
 '12_30_10': [
   ('Organisation de la facturation et état des régularisations par programme', ['CHARGES', 'GRP'], ['12_30_03']),
   ('Copropriétés, ASL, AFUL', ['COPRO', 'CHARGES'], ['11_30_08', '11_30_02']),
   ('Provisionnement : acomptes et contrôle des sous / sur-provisions', ['QUIT', 'CHARGES'], ['12_30_05', '12_30_03']),
   ('Temporalité des régularisations, information du locataire', ['CHARGES'], ['12_30_03', '12_30_05']),
   ('Charges de personnel récupérées', ['CHARGES', 'COMPTA'], ['12_30_03']),
   ('Régularisations et impayés, locataires partis', ['CHARGES', 'SORTIE', 'CPT'], ['12_30_07', '12_30_05', '12_30_12']),
 ],
 '12_30_11': [
   ('Procédure, acteurs et rétroplanning de l\'enquête SLS', ['SLS'], ['12_30_04']),
   ('Logements exclus du champ du SLS', ['QPV', 'FCUS', 'SLS'], ['12_30_04', '12_30_02']),
   ('Nombre et montants de SLS calculés / forfaitaires (N-1 à N-3)', ['SLS', 'QUIT'], ['12_30_04', '12_30_05']),
   ('SLS forfaitaire', ['SLS'], ['12_30_04']),
   ('Perte du droit au maintien dans les lieux', ['PLAF', 'RESS', 'CPT'], ['12_30_04']),
 ],
 '12_30_12': [
   ('Locataires présents au 31/12 et locataires en impayé', ['CPT', 'QUIT', 'NBLGT'], ['12_30_05', '12_30_02']),
   ('Procédures amiables : FSL, plans d\'apurement, aides sur quittance', ['CPT', 'QUIT'], ['12_30_05']),
   ('Procédures contentieuses : commandements, assignations, expulsions', ['CPT', 'SORTIE'], ['12_30_05', '12_30_07']),
 ],
}

# ------------------------------------------------------------ controls
# crit: 1 bloquant / 2 majeur / 3 utile ; type
C = []
def ctl(cid, typ, crit, title, files, pivots, rule, test, theme):
    C.append(dict(id=cid, typ=typ, crit=crit, title=title, files=files, pivots=pivots, rule=rule, test=test, theme=theme))

ctl('C01', 'Référentiel', 1, 'Tout code groupe existe dans l\'Etat des lieux',
    ['11_30_02', '11_30_01', '11_30_03', '11_30_05', '11_30_06', '11_30_08', '12_30_01', '12_30_02', '12_30_03', '12_30_04', '12_30_05', '12_30_06', '12_30_07'], ['GRP'],
    'Chaque CODE_PATRIMOINE / CODE_GROUPE_IMMOBILIER / « code opération » utilisé dans une trame doit exister dans 11_30_02 onglet 1 (ou être justifié : vendu, démoli, foyer, nouveau programme après extraction).',
    'Jointure gauche de chaque trame sur la liste des codes de 11_30_02 ; lister les orphelins par trame.', 'REF')
ctl('C02', 'Référentiel', 1, 'Libellé, commune et INSEE identiques pour un même groupe',
    ['11_30_02', '11_30_03', '11_30_05', '11_30_06', '11_30_08', '12_30_01', '12_30_02', '12_30_03', '12_30_04', '12_30_05', '12_30_06'], ['GRP', 'GRP_NOM', 'COMMUNE', 'INSEE'],
    'Pour un code groupe donné, NOM_PATRIMOINE, COMMUNE et code INSEE doivent être strictement identiques dans toutes les trames.',
    'Table de référence groupe produite une seule fois et réutilisée (RECHERCHEV) plutôt que ressaisie.', 'REF')
ctl('C03', 'Référentiel', 1, 'Correspondance lot ↔ RPLS ↔ groupe stable',
    ['11_30_02', '11_30_06', '12_30_01', '12_30_02', '12_30_05'], ['LOT', 'RPLS', 'GRP'],
    'Un identifiant de lot = un seul identifiant RPLS et un seul groupe dans toutes les trames (bijection lot ↔ RPLS).',
    'Construire la table lot / RPLS / groupe / bâtiment depuis 12_30_02 et 11_30_02 onglet 3, puis contrôler les doublons et divergences.', 'REF')
ctl('C04', 'Référentiel', 1, 'Tout lot cité dans les trames locatives existe dans le référentiel des lots',
    ['12_30_02', '12_30_01', '12_30_04', '12_30_05', '12_30_06', '12_30_07', '11_30_03', '11_30_06'], ['LOT'],
    'IDENTIFIANT_LOT des trames CALEOL, SLS, quittancement, réclamations, sortants et diagnostics présent dans 12_30_02 (photo au 01/01/2025) ou expliqué par un mouvement (vente, mise en service, démolition).',
    'Jointure sur l\'identifiant de lot ; justifier les écarts par la liste des mouvements de 11_30_05 et 11_30_06.', 'REF')
ctl('C05', 'Référentiel', 2, 'Codes bâtiment homogènes (format et valeurs)',
    ['11_30_02', '11_30_03', '11_30_05', '12_30_03'], ['BAT'],
    'CODE_BATIMENT est « Numérique » dans 11_30_02 mais « Alphanumérique » dans 11_30_03 : risque de perte des zéros non significatifs et de jointures ratées.',
    'Forcer le format texte partout ; comparer les couples groupe / bâtiment entre trames.', 'REF')
ctl('C06', 'Référentiel', 1, 'Compte locataire ↔ lot ↔ nom cohérents',
    ['12_30_01', '12_30_04', '12_30_05', '12_30_06', '12_30_07'], ['CPT', 'LOT', 'PERS'],
    'Un compte locataire est rattaché au même lot et au même titulaire dans CALEOL (attributaires), SLS, quittancement, réclamations et sortants.',
    'Jointure sur NUM_COMPTE_LOCATAIRE ; contrôler lot et nom (attention aux homonymes et aux co-titulaires).', 'REF')
ctl('C07', 'Référentiel', 2, 'Références de marché connues',
    ['11_30_03', '12_30_06', '11_30_05'], ['MARCHE', 'TITU'],
    'Chaque CODE_MARCHE des onglets équipements (2.x) et chaque NUM_MARCHE des interventions existent dans 1_Marchés d\'entretien avec le même titulaire.',
    'Jointure sur la référence de marché ; comparer TITULAIRE_MARCHE / FOURNISSEUR_INTERVENTION.', 'TRV')
ctl('C08', 'Référentiel', 2, 'Zonages cohérents pour une même commune',
    ['11_30_02', '11_30_05', '11_30_07', '12_30_01', '12_30_02', '12_30_04'], ['ZABC', 'Z123', 'ZGEO', 'INSEE'],
    'Trois zonages coexistent (A/B/C, 1/2/3, p/i/r/d) : pour un même code INSEE, chaque zonage doit avoir une valeur unique dans toutes les trames.',
    'Table commune × 3 zonages issue des arrêtés en vigueur ; contrôle de cohérence par jointure INSEE.', 'REF')
ctl('C09', 'Référentiel', 2, 'QPV identique entre patrimoine et gestion locative',
    ['11_30_02', '11_30_08', '12_30_01', '12_30_02', '12_30_04', '11_30_06'], ['QPV'],
    'QPV_HORS_QPV au groupe (11_30_02) = valeur au lot (12_30_02, 12_30_01, 12_30_04) ; ANRU_QPV des ventes cohérent.',
    'Jointure groupe → lot ; écarts à expliquer (groupe à cheval sur un périmètre QPV).', 'ATT')

ctl('C10', 'Volumétrie', 1, 'Un seul nombre de logements familiaux au 31/12/2025',
    ['11_30_05', '11_30_04', '11_30_02', '12_30_02'], ['NBLGT', 'MOUV'],
    'PARC_31_DECEMBRE 2025 (synthèse) = NOMBRE_TOTAL_LOGEMENTS de 1_1_Accessibilité = valeur 2025 de 2_Adaptation ; rapproché de la somme 11_30_02 (date d\'extraction 2026) et du nombre de lots « logement » de 12_30_02 (01/01/2025) en expliquant les mouvements entre les dates.',
    'Tableau de passage unique : parc 01/01/2025 → mouvements 2025 → parc 31/12/2025 → mouvements 2026 → parc à la date d\'extraction.', 'REF')
ctl('C11', 'Volumétrie', 2, 'Logements par groupe identiques entre patrimoine et exploitation',
    ['11_30_02', '11_30_03', '11_30_05', '11_30_08'], ['NBLGT', 'GRP'],
    'NOMBRE_TOTAL_LOGEMENTS / INDIVIDUELS / COLLECTIFS par groupe dans les onglets 2.3 à 2.7 de 11_30_03, 3_Réhabilitation et la copropriété (détenus par le bailleur) = valeurs de 11_30_02.',
    'Jointure groupe ; tolérance nulle hors mouvements datés.', 'REF')
ctl('C12', 'Volumétrie', 2, 'Cartographie LGT exhaustive',
    ['11_30_02'], ['NBLGT', 'LOT', 'DPE'],
    'Le nombre de lignes de 3_Cartographie énergétique LGT = somme NOMBRE_TOTAL_LOGEMENTS de l\'onglet 1 (et par groupe / bâtiment).',
    'Comptage par groupe dans l\'onglet 3 vs onglet 1.', 'ENE')
ctl('C13', 'Volumétrie', 1, 'Ventes : synthèse = détail',
    ['11_30_05', '11_30_06', '11_30_07'], ['VENTE', 'MOUV'],
    'VENTES par année (1_Synthèse) = nombre de lignes de 11_30_06 par année de DATE_VENTE (hors accession neuve de 11_30_07, à ne pas compter).',
    'Tableau croisé dynamique par année sur 11_30_06.', 'VTE')
ctl('C14', 'Volumétrie', 1, 'Mises en service : synthèse = opérations nouvelles',
    ['11_30_05', '11_30_02'], ['PROD', 'NBLGT', 'DMES'],
    'MOA_DIRECTE, NOMBRE_LOGEMENTS_VEFA, AA par année = somme NOMBRE_TOTAL_LOGEMENTS des opérations « Réalisée » de 2_Opérations nouvelles par TYPE_PRODUIT et année de mise en service ; les dates sont cohérentes avec DATE_MISE_EN_SERVICE de 11_30_02.',
    'Tableau croisé TYPE_PRODUIT × année sur l\'onglet 2.', 'DEV')
ctl('C15', 'Volumétrie', 2, 'Parc foyer : foyers = accessibilité foyer',
    ['11_30_01', '11_30_04'], ['NBLGT'],
    'Somme EQUIVALENT_LOGEMENT de 11_30_01 = NOMBRE_TOTAL_LOGEMENTS_FOYER de 1_2_Accessibilité_FOYER (même règle 1 pour 1 / 1 pour 3).',
    'Somme simple ; documenter la règle d\'équivalence retenue.', 'FOY')
ctl('C16', 'Volumétrie', 2, 'Copropriétés : liste exhaustive',
    ['11_30_02', '11_30_08'], ['COPRO', 'GRP', 'NBLGT'],
    'Tout groupe / bâtiment COPROPRIETE = OUI dans 11_30_02 figure dans 11_30_08 avec le même nombre de logements détenus (attention : photo au 01/01/2025 vs date d\'extraction).',
    'Jointure groupe ; contrôle des TANTIEME renseignés.', 'REF')
ctl('C17', 'Volumétrie', 2, 'Locataires présents et en impayé au 31/12/2025',
    ['12_30_12', '12_30_05', '12_30_02'], ['CPT', 'QUIT', 'NBLGT'],
    'Locataires présents au 31/12/2025 (recouvrement) = comptes distincts actifs du quittancement de décembre 2025 ; locataires en impayé = comptes à solde débiteur dans 12_30_05.',
    'Comptage des comptes distincts et des soldes débiteurs dans le fichier de quittancement.', 'REC')
ctl('C18', 'Volumétrie', 2, 'Sorties 2025 cohérentes',
    ['12_30_07', '12_30_05', '11_30_02', '12_30_06'], ['SORTIE', 'CPT', 'REL'],
    'Nombre de lignes de 12_30_07 = comptes ayant une DATE_SORTIE en 2025 dans 12_30_05 (hors foyers / étudiants) ; la part 2025 des EDL (11_30_02, cumul 5 ans) est cohérente.',
    'Comptage des DATE_SORTIE 2025 ; expliquer les écarts de périmètre (foyers, étudiants, non-logements).', 'ATT')

ctl('C20', 'Valeurs croisées', 1, 'Loyer pratiqué = loyer quittancé de janvier 2025',
    ['12_30_02', '12_30_05'], ['LOYER', 'QUIT', 'LOT'],
    'MNT_LOYER_PRATIQUE_MENSUEL (12_30_02) = montant de la rubrique loyer principal quittancé pour 202501 sur le même lot (hors annexes et charges).',
    'Jointure lot × rubriques « loyer » du mois 202501 ; tolérance au centime.', 'LOY')
ctl('C21', 'Valeurs croisées', 1, 'Loyer pratiqué ≤ loyer maximum conventionnel',
    ['12_30_02', '12_30_09'], ['LOYER', 'LMAX', 'SUTIL', 'CONV'],
    'Pour les lots conventionnés : loyer pratiqué ≤ loyer maximum actualisé × surface quittancée. Les dépassements doivent être explicables dans le questionnaire loyers.',
    'Actualiser LOYER_MAX (IRL) depuis DATE_VALEUR_CONV ; convertir les FRF ; calcul ligne à ligne.', 'LOY')
ctl('C22', 'Valeurs croisées', 2, 'Loyer à l\'attribution et loyer de relocation',
    ['12_30_01', '12_30_07', '12_30_02', '12_30_05'], ['LOYER', 'LOT', 'BAIL'],
    'MNT_LOYER_MENSUEL_APPLIQUE_A_L_ATTRIBUTION (CALEOL) = « Montant loyer mensuel logt reloué » (sortants) = loyer quittancé au premier mois du nouveau bail.',
    'Jointure lot + date de bail.', 'ATT')
ctl('C23', 'Valeurs croisées', 1, 'SLS calculé, retenu et quittancé',
    ['12_30_04', '12_30_05', '12_30_11'], ['SLS', 'QUIT', 'CPT'],
    'SLS_CALCULE = coefficient × SLR × surface habitable ; SLS_QUITTANCE_EN_DECEMBRE = rubrique SLS quittancée en 202512 ; les totaux par année et par mode (calculé / forfaitaire) alimentent le tableau 2.1 du questionnaire SLS.',
    'Recalcul ligne à ligne + agrégat par ANNEE_CALCUL_SLS × FORFAITAIRE_CALCULE.', 'LOY')
ctl('C24', 'Valeurs croisées', 2, 'Surface habitable identique d\'une trame à l\'autre',
    ['12_30_02', '12_30_04', '11_30_02', '11_30_06', '12_30_03'], ['SHAB', 'LOT'],
    'SURF_HABITABLE au lot identique dans 12_30_02, 12_30_04 et 11_30_02 onglet 3 ; somme par groupe = SURF_HABITABLE_AU_GROUPE_IMMOBILIER (charges).',
    'Jointure lot ; agrégat par groupe pour les charges.', 'LOY')
ctl('C25', 'Valeurs croisées', 2, 'Exemptions de SLS respectées',
    ['12_30_04', '12_30_02', '11_30_02'], ['SLS', 'QPV', 'FCUS'],
    'Aucun SLS facturé sur un logement en QPV, en ZRR ou exclu par son financement ; QPV / financement du SLS = valeurs de 12_30_02.',
    'Filtre des lignes SLS > 0 croisé avec QPV / ZRR / financement.', 'LOY')
ctl('C26', 'Valeurs croisées', 1, 'Caractéristiques du logement attribué = référentiel',
    ['12_30_01', '12_30_02', '11_30_02'], ['CONV', 'FCUS', 'FINI', 'DPE', 'QPV', 'TYPO'],
    'LOGT_CONV_OU_NON, FINANCEMENT_CUS, FINANCEMENT_INITIAL, TYPE_LOGEMENT, QPV et CLASSE_DPE de la CALEOL = valeurs du lot dans 12_30_02 et 11_30_02 onglet 3.',
    'Jointure lot ; comparaison champ à champ.', 'ATT')
ctl('C27', 'Valeurs croisées', 1, 'DPE au logement identique partout',
    ['11_30_02', '12_30_01', '11_30_06', '11_30_05'], ['DPE', 'LOT'],
    'ETIQUETTE_DPE (11_30_02 onglet 3) = CLASSE_DPE (CALEOL) = ETIQUETTE_DPE (ventes) ; DPE_APRES_TX des réhabilitations réalisées cohérent avec la cartographie actuelle.',
    'Jointure lot ; pour les réhabilitations, jointure groupe.', 'ENE')
ctl('C28', 'Valeurs croisées', 1, 'Pas d\'attribution ni de relocation de logement classé G',
    ['12_30_01', '11_30_02', '12_30_07'], ['DPE', 'BAIL'],
    'Depuis le 01/01/2025, un logement classé G n\'est plus décent pour un nouveau bail : contrôler les baux signés en 2025 sur des logements G (puis F en 2028).',
    'Filtre CLASSE_DPE = G et DATE_SIGNATURE_BAIL ≥ 01/01/2025.', 'ENE')
ctl('C29', 'Valeurs croisées', 2, 'Dates de réhabilitation identiques',
    ['11_30_02', '11_30_01', '11_30_05'], ['REHA', 'GRP'],
    'DATE_REHABILITATION (11_30_02 onglets 1 et 2, 11_30_01) = DATE_RECEPTION_TRAVAUX des réhabilitations « Réalisée » de 11_30_05 ; PSP_REHA = OUI cohérent avec PSP_INTERVENTION.',
    'Jointure groupe ; date la plus récente.', 'DEV')
ctl('C30', 'Valeurs croisées', 2, 'Dates de construction cohérentes',
    ['11_30_02', '11_30_03', '11_30_06', '11_30_05', '11_30_08'], ['DCONS', 'GRP', 'BAT'],
    'DATE_DE_CONSTRUCTION_PRG (11_30_03, ventes) = la plus ancienne DATE_DE_CONSTRUCTION_BAT du groupe (11_30_02).',
    'MIN par groupe dans 11_30_02 vs valeur déclarée.', 'REF')
ctl('C31', 'Valeurs croisées', 2, 'Mode de chauffage ↔ équipements déclarés',
    ['11_30_02', '11_30_03'], ['CHAUF', 'GRP'],
    'Chauffage INDIVIDUEL au gaz (cartographie) ⇔ ligne dans 2.3_Chaudières ; chauffage COLLECTIF ⇔ ligne dans 2.4_Chaufferie_coll.',
    'Jointure groupe ; lister les groupes équipés sans suivi d\'entretien.', 'SEC')
ctl('C32', 'Valeurs croisées', 2, 'Date du dernier bail des diagnostics = bail réel',
    ['11_30_03', '12_30_05', '12_30_01', '12_30_02'], ['BAIL', 'LOT', 'DIAG'],
    'DATE_BAIL des onglets plomb, électricité, gaz = date de signature du dernier bail du lot (12_30_02, 12_30_05, CALEOL).',
    'Jointure lot ; contrôler la présence d\'un diagnostic valide à la date du bail.', 'SEC')
ctl('C33', 'Valeurs croisées', 2, 'Charges : quittancé vs réel',
    ['12_30_03', '12_30_05', '12_30_10'], ['CHARGES', 'QUIT', 'GRP'],
    'Provisions de charges quittancées en 2025 par groupe (12_30_05) vs charges récupérables 2025 (12_30_03) : écarts = sous / sur-provisionnement à commenter dans le questionnaire charges.',
    'Agrégat par groupe et par année ; ratio provisions / charges réelles.', 'CHG')
ctl('C34', 'Valeurs croisées', 2, 'Marchés récupérables ↔ natures de charges',
    ['11_30_03', '12_30_03', '12_30_06'], ['CHARGES', 'MARCHEI', 'COMPTA'],
    'Les montants récupérables des marchés (P2) se retrouvent dans les natures de charges 12_30_03 ; les interventions imputées sur des comptes récupérables sont cohérentes avec le décret n° 82-955.',
    'Rapprochement nature de marché ↔ nature de charge ↔ compte comptable.', 'CHG')
ctl('C35', 'Valeurs croisées', 2, 'Dépôt de garantie quittancé et restitué',
    ['12_30_07', '12_30_05'], ['DG', 'CPT'],
    'Montant et date du dépôt de garantie (sortants) = rubrique DEPOT GARANTIE du quittancement ; date de restitution dans le délai légal.',
    'Jointure compte locataire.', 'REC')
ctl('C36', 'Valeurs croisées', 2, 'Entrants : CALEOL ↔ sortants',
    ['12_30_07', '12_30_01'], ['CAL', 'BAIL', 'LOT'],
    '« date de passage en CAL » et « date entrée dans le logt » des sortants = DATE_CALEOL et DATE_ENTREE_LIEUX de l\'attributaire retenu dans 12_30_01.',
    'Jointure lot + date.', 'ATT')
ctl('C37', 'Valeurs croisées', 2, 'Remise en état : sortants vs cumul patrimoine',
    ['12_30_07', '11_30_02'], ['REL', 'GRP'],
    'Montants de remise en état et part imputée (sortants 2025) cohérents avec DEPENSES_REL_NON_RECUP / RECUP cumulées sur 5 ans (11_30_02) par groupe.',
    'Agrégat 2025 par groupe ; vérifier l\'ordre de grandeur.', 'TRV')
ctl('C38', 'Valeurs croisées', 2, 'Ventes : logement sorti du parc locatif',
    ['11_30_06', '12_30_02', '12_30_05'], ['VENTE', 'LOT', 'LOYER'],
    'Un logement vendu avant le 01/01/2025 n\'apparaît plus dans 12_30_02 ni dans le quittancement après la date de vente ; LOYER_PRATIQUE et DATE_BAIL de la vente cohérents avec la gestion locative.',
    'Jointure lot × date de vente.', 'VTE')
ctl('C39', 'Valeurs croisées', 3, 'Interventions ↔ équipements',
    ['12_30_06', '11_30_03'], ['INTERV', 'EQUIP', 'GRP'],
    'Les réclamations « ascenseur » / « chauffage » par groupe sont cohérentes avec les pannes et interventions curatives déclarées dans 11_30_03 (ordre de grandeur).',
    'Agrégat par groupe et nature.', 'TRV')
ctl('C40', 'Valeurs croisées', 3, 'Accession : synthèse = détail au logement',
    ['11_30_07'], ['OPE', 'NBLGT', 'VENTE'],
    'Nombre de lots construits par opération (synthèse) = nombre de logements vendus ou en stock de l\'onglet au logement ; produit (PSLA, BRS…) identique.',
    'Comptage par CODE_OPERATION.', 'VTE')
ctl('C41', 'Valeurs croisées', 3, 'Mutations pour adaptation ↔ attributions',
    ['11_30_04', '12_30_01'], ['PUBLIC', 'MENAGE'],
    'MUTATION (adaptation, +65 ans) par année ≤ attributions en MUTATION_INTERNE de la CALEOL la même année.',
    'Comptage par année.', 'ACC')

ctl('C50', 'Temporel', 1, 'Dates de référence explicites par trame',
    ['11_30_01', '11_30_02', '11_30_03', '11_30_04', '11_30_05', '11_30_08', '12_30_02', '12_30_05'], ['NBLGT'],
    'Photo à la date d\'extraction (2026), au 01/01/2025, au 31/12/2025 ou à fin N-1 : chaque fichier doit indiquer sa date d\'extraction réelle (cartouche « Date d\'extraction des données »).',
    'Renseigner systématiquement le cartouche ; tableau de passage des volumes entre dates.', 'REF')
ctl('C51', 'Temporel', 2, 'Chronologie des opérations',
    ['11_30_05'], ['GOUV', 'DMES', 'REHA'],
    'Dépôt PC ≤ obtention PC ≤ OS ≤ réception ≤ mise en location ; CAO ≤ notification ≤ OS pour les réhabilitations ; délai réel vs DELAI contractuel.',
    'Contrôles de dates ligne à ligne.', 'DEV')
ctl('C52', 'Temporel', 2, 'Chronologie des ventes',
    ['11_30_06'], ['GOUV', 'VENTE'],
    'Décision CA ≤ décision CUS / préfet ≤ publicité ≤ date de vente ; grille de prix en vigueur à la date de vente.',
    'Contrôles de dates ligne à ligne.', 'VTE')
ctl('C53', 'Temporel', 2, 'Chronologie CALEOL',
    ['12_30_01'], ['CAL', 'BAIL'],
    'Dépôt de la demande ≤ CALEOL ≤ signature du bail ≤ entrée dans les lieux ; rang renseigné pour toute attribution.',
    'Contrôles de dates et de complétude.', 'ATT')

ctl('C60', 'Réglementaire', 2, 'Diagnostics plomb présents pour le parc d\'avant 1949',
    ['11_30_03', '11_30_02'], ['DIAG', 'DCONS'],
    'Tout logement d\'un bâtiment construit avant le 01/01/1949 doit avoir un CREP (onglet 3.1.1).',
    'Filtre DATE_DE_CONSTRUCTION < 1949 dans 11_30_02 puis jointure lot.', 'SEC')
ctl('C61', 'Réglementaire', 2, 'DTA présents pour les permis d\'avant juillet 1997',
    ['11_30_03', '11_30_02'], ['DIAG', 'DCONS', 'BAT'],
    'Tout immeuble collectif dont le permis est antérieur au 01/07/1997 doit avoir un DTA (onglet 3.1.2).',
    'Filtre date de construction / permis puis jointure bâtiment.', 'SEC')
ctl('C62', 'Réglementaire', 2, 'Diagnostics gaz / électricité à la relocation',
    ['11_30_03', '12_30_01', '12_30_05'], ['DIAG', 'BAIL'],
    'Pour les installations de plus de 15 ans, un diagnostic de moins de 6 ans doit exister à la date de chaque bail signé sur la période.',
    'Jointure lot × date de bail.', 'SEC')
ctl('C63', 'Réglementaire', 2, 'Contrôles techniques ascenseurs à jour',
    ['11_30_03'], ['EQUIP'],
    'DATE_CTQ de moins de 5 ans ; travaux de sécurité réalisés pour les appareils installés avant le 24/08/2000.',
    'Contrôle de dates ligne à ligne.', 'SEC')
ctl('C64', 'Réglementaire', 1, 'Objectifs d\'attribution (1er quartile, prioritaires)',
    ['12_30_01', '11_30_02'], ['PLAF', 'QPV', 'PUBLIC', 'CAL'],
    'Part des attributions hors QPV à des demandeurs du 1er quartile (objectif légal de 25 %) ; part des publics DALO / prioritaires ; décisions conformes aux valeurs du CCH.',
    'Calcul par année de CALEOL et par EPCI.', 'ATT')

ctl('C70', 'Recueil ↔ questionnaire', 2, 'Tableau SLS du questionnaire = recueil SLS',
    ['12_30_11', '12_30_04', '12_30_05'], ['SLS'],
    'Le tableau 2.1 (N-1 à N-3) doit être cohérent avec 12_30_04 (N-2 et N-1 seulement) : prévoir l\'extraction complémentaire de N-3.',
    'Agrégats du recueil + extraction complémentaire.', 'LOY')
ctl('C71', 'Recueil ↔ questionnaire', 2, '% de programmes régularisés = recueil charges',
    ['12_30_10', '12_30_03'], ['CHARGES', 'GRP'],
    'L\'état des régularisations par année déclaré au questionnaire charges correspond aux groupes et exercices présents dans 12_30_03.',
    'Liste des groupes par année dans 12_30_03.', 'CHG')
ctl('C72', 'Recueil ↔ questionnaire', 2, 'Base accessibilité au logement = comptages agrégés',
    ['11_30_09', '11_30_04', '11_30_02'], ['ACCESS', 'RPLS', 'LOT'],
    'L\'extraction au logement demandée par le questionnaire (RPLS, code, niveau d\'accessibilité) reconstitue exactement les comptages UFR / canne / inaccessible / non audité de 1_1_Accessibilité.',
    'Agrégat de l\'extraction au logement.', 'ACC')
ctl('C73', 'Recueil ↔ questionnaire', 2, 'Ventilation des agréments = opérations nouvelles',
    ['11_30_10', '11_30_05'], ['FCUS', 'GOUV'],
    'La ventilation PLAI / PLUS / PLS / LLI des agréments N-1 et N-2 = sommes par DATE_AGREMENT de l\'onglet 2_Opérations nouvelles.',
    'Tableau croisé par année d\'agrément.', 'DEV')
ctl('C74', 'Recueil ↔ questionnaire', 3, 'Politique de loyers ↔ loyers constatés',
    ['12_30_09', '12_30_02', '11_30_05', '12_30_07'], ['LOYER', 'LMAX'],
    'Les pratiques décrites (hausse à la relocation, après réhabilitation, loyers des neufs) sont observables dans les loyers de relocation, TAUX_LOYER_APRES_TX et le ratio loyer pratiqué / loyer maximum.',
    'Statistiques descriptives par catégorie.', 'LOY')
ctl('C75', 'Recueil ↔ questionnaire', 3, 'Remise en état et réclamations ↔ qualité de service',
    ['12_30_08', '12_30_06', '12_30_07'], ['INTERV', 'REL'],
    'Les indicateurs cités dans le questionnaire qualité de service (délais, taux de clôture) sont recalculables à partir de 12_30_06 et 12_30_07.',
    'Recalcul des indicateurs.', 'QDS')

# ------------------------------------------------------------ themes
T = [
 dict(id='REF', label='Référentiel & connaissance du patrimoine', files=['11_30_02', '12_30_02', '11_30_08', '11_30_01', '11_30_05'],
      enjeu='Disposer d\'un référentiel unique groupe / bâtiment / lot / RPLS et d\'un nombre de logements réconcilié : c\'est la condition de toutes les jointures des contrôleurs.'),
 dict(id='ENE', label='Performance énergétique & décence', files=['11_30_02', '11_30_05', '12_30_01', '11_30_06'],
      enjeu='Cartographie DPE au bâtiment et au logement, trajectoire de sortie des passoires (G interdits à la location depuis 2025, F en 2028, E en 2034), DPE avant / après réhabilitation.'),
 dict(id='SEC', label='Sécurité des personnes & diagnostics', files=['11_30_03', '11_30_02'],
      enjeu='Couverture et actualité des diagnostics (plomb, amiante, gaz, électricité) et des contrôles d\'équipements (ascenseurs, aires de jeux, SSI, chaudières).'),
 dict(id='TRV', label='Maintenance, marchés & remise en état', files=['11_30_03', '12_30_06', '11_30_02', '12_30_07'],
      enjeu='Couverture du parc par les marchés, coûts d\'intervention, remise en état à la relocation et imputations aux locataires.'),
 dict(id='DEV', label='Développement & réhabilitation', files=['11_30_05', '11_30_10', '11_30_02'],
      enjeu='Production (MOD, VEFA, AA), coûts et plans de financement, délais, contentieux, réhabilitations et loyers après travaux.'),
 dict(id='VTE', label='Ventes HLM & accession sociale', files=['11_30_06', '11_30_07', '11_30_05'],
      enjeu='Régularité des procédures de vente, prix, profils et ressources des acquéreurs, respect des plafonds PSLA / BRS.'),
 dict(id='ATT', label='Attributions & occupation sociale', files=['12_30_01', '12_30_07', '11_30_02', '11_30_04'],
      enjeu='Conformité des décisions de CALEOL, objectifs légaux (1er quartile hors QPV, DALO, prioritaires), réservataires, taux d\'effort, délais de relocation.'),
 dict(id='LOY', label='Loyers & SLS', files=['12_30_02', '12_30_05', '12_30_04', '12_30_09', '12_30_11'],
      enjeu='Loyers pratiqués ≤ loyers maximum, exactitude du SLS et des exemptions, cohérence avec le quittancement.'),
 dict(id='CHG', label='Charges récupérables', files=['12_30_03', '12_30_05', '12_30_10', '11_30_03', '11_30_08'],
      enjeu='Récupérabilité, régularisations annuelles par programme, provisions vs réel, copropriétés.'),
 dict(id='REC', label='Impayés & recouvrement', files=['12_30_12', '12_30_05', '12_30_07'],
      enjeu='Volumes d\'impayés et de procédures, comparés au benchmark USH ; dépôts de garantie et soldes des partis.'),
 dict(id='QDS', label='Qualité de service', files=['12_30_06', '12_30_08'],
      enjeu='Traitement des réclamations (délais, clôture), organisation de la proximité, pilotage des prestataires.'),
 dict(id='ACC', label='Accessibilité & vieillissement', files=['11_30_04', '11_30_09', '12_30_01'],
      enjeu='Niveau d\'accessibilité du parc, réponse aux demandes d\'adaptation, mutations des seniors, dégrèvements TFPB.'),
 dict(id='FOY', label='Foyers & gestion déléguée', files=['11_30_01', '11_30_04'],
      enjeu='Connaissance du parc foyer, conventions de gestion, PCRC et travaux.'),
]

# ------------------------------------------------------------ alerts (vigilance)
A = []
def al(aid, cat, lvl, title, detail, files, action):
    A.append(dict(id=aid, cat=cat, lvl=lvl, title=title, detail=detail, files=files, action=action))

al('A01', 'Anomalies des trames', 2, 'Colonnes B et C inversées dans 3_Cartographie énergétique LGT',
   'L\'onglet Définitions annonce B = NOM_PATRIMOINE, C = CODE_BATIMENT ; l\'onglet de recueil porte B = CODE_BATIMENT, C = NOM_PATRIMOINE.', ['11_30_02'],
   'Respecter l\'ordre de l\'onglet de recueil (c\'est lui qui sera traité) et le signaler au contrôleur.')
al('A02', 'Anomalies des trames', 2, 'Ordre des colonnes K à N différent dans Réclamations / interventions',
   'Définitions : K = ANNEE_MISE_EN_SERVICE_PATRIMOINE, L = CODE_INSEE, M = COMMUNE, N = NATURE_LOT. Recueil : K = CODE_INSEE, L = COMMUNE, M = NATURE_LOT, N = ANNEE_MISE_EN_SERVICE_PATRIMOINE.', ['12_30_06'],
   'Mapper l\'extraction sur les en-têtes du recueil, pas sur la lettre de colonne des définitions.')
al('A03', 'Anomalies des trames', 3, 'Noms de colonnes différents entre définition et recueil',
   'IDENTIFIANT_RPLS → IDENTIFIANT_LOGEMENT_RPLS (Loyers) ; FINANCEMENT → FINANCEMENT_CUS (SLS) ; NOM_OP → NOM-OP (Opérations nouvelles) ; NB_INTERVENTION_VMC_GAZ → NB_INTERVENTION_CURATIVE_VMC_GAZ ; NOMBRE_INTERVENTION_CHAUFF → NB_INTERVENTION_CHAUFF ; OBERVATIONS → OBSERVATIONS ; OBSERVATIONS en colonne L (définition) mais K (recueil) dans 3.1.2_DTA.',
   ['12_30_02', '12_30_04', '11_30_05', '11_30_03', '11_30_01', '11_30_04'],
   'Conserver les en-têtes du recueil à l\'identique ; ne pas renommer.')
al('A04', 'Anomalies des trames', 3, 'Noms d\'onglets différents entre Définitions et recueil',
   '« 2.2_Aires-de-jeux » / « 2.2_Aires_de_jeux », « 2.3_Chaudières-ind & vmc gaz » / « 2.3_Chaudières_ind_et_vmc gaz », « 2.4_Chaufferie-coll » / « 2.4_Chaufferie_coll », « 1_1_Accessibilité LGT » / « 1_1_Accessibilité_LGT ».', ['11_30_03', '11_30_04'],
   'Ne pas renommer les onglets de recueil.')
al('A05', 'Anomalies des trames', 2, 'Trois trames sans définitions',
   'Patrimoine en copropriété, Locataires sortants / entrants et la synthèse Accession n\'ont pas de dictionnaire : le sens de chaque colonne est à interpréter (ex. « Regul charges », « date décompte de solde »).', ['11_30_08', '12_30_07', '11_30_07'],
   'Rédiger nos propres définitions et les faire valider par le contrôleur en réunion technique.')
al('A06', 'Codifications hétérogènes', 1, 'Quatre noms pour la clé groupe, quatre pour la clé logement',
   'Groupe : CODE_PATRIMOINE, CODE_GROUPE_IMMOBILIER, CODE_PATRIMOINE_FOYER, « code opération ». Logement : IDENTIFIANT_LOT, CODE_IDENTIFIANT_LOT, IDENTIFIANT_LOGEMENT, « identifiant du logement ». RPLS : IDENTIFIANT_LOGEMENT_RPLS, CODE_IDENTIFIANT_RPLS.',
   ['11_30_01', '11_30_02', '11_30_03', '11_30_06', '11_30_07', '12_30_01', '12_30_02', '12_30_03', '12_30_05', '12_30_06', '12_30_07'],
   'Une seule source de vérité par clé (table de correspondance), injectée dans chaque trame.')
al('A07', 'Codifications hétérogènes', 1, 'Trois zonages distincts à ne pas confondre',
   'A/B/C (ZONE_TENSION, ZONAGE_ABC), 1/2/3 (ZONE_LOYERS, ZONAGE pour la RLS) et p/i/r/d (ZONE_GEOGRAPHIQUE, avec « idf » dans Accession et « i » ailleurs).', ['11_30_02', '11_30_05', '11_30_07', '12_30_01', '12_30_02', '12_30_04'],
   'Table commune × zonages ; respecter la liste de valeurs propre à chaque trame.')
al('A08', 'Codifications hétérogènes', 1, 'Financement initial et financement CUS',
   'FINANCEMENT_INITIAL (PLA, HLMO, ILN…) et FINANCEMENT_CUS (PLAI, PLUS, PLS, PLI) coexistent ; « Type financement » (sortants) et FINANCEMENT (foyers) ne précisent pas le référentiel.', ['11_30_01', '11_30_02', '11_30_06', '12_30_01', '12_30_02', '12_30_04', '12_30_07'],
   'Table de passage financement initial → catégorie CUS, validée une fois.')
al('A09', 'Codifications hétérogènes', 2, 'Booléens et conventionnement codés de trois façons',
   'CONVENTIONNE / NON CONVENTIONNE, 1 / 0 (LOGT_CONV_OU_NON), OUI / NON (CONVENTIONNEMENT_APL) ; de même OUI / NON, Oui / Non et 1 / 0 pour les autres indicateurs ; QPV / HORS QPV vs OUI / NON (ANRU_QPV).', ['11_30_01', '11_30_02', '11_30_06', '12_30_01', '12_30_02'],
   'Respecter la liste de valeurs de chaque trame à partir d\'une donnée source unique.')
al('A10', 'Codifications hétérogènes', 2, 'Formats d\'identifiants incohérents',
   'CODE_BATIMENT « Numérique » (11_30_02) vs « Alphanumérique » (11_30_03) ; CODE_INSEE « Numérique » (Opérations nouvelles, Réclamations) vs texte ailleurs ; CODE_PATRIMOINE_FOYER « Numérique ».', ['11_30_02', '11_30_03', '11_30_05', '12_30_06', '11_30_01'],
   'Exporter tous les identifiants au format texte (zéros non significatifs conservés).')
al('A11', 'Codifications hétérogènes', 3, 'Typologie T1…T7 vs libellés libres',
   'TYPE_LOGEMENT en T1…T7 dans la plupart des trames, mais TYPE_LOT du quittancement en libellés ERP (« Apt. 2 pièces », « Studio »…).', ['12_30_05', '12_30_02', '11_30_02'],
   'Table de passage libellé ERP → T1…T7.')
al('A12', 'Dates & périmètres', 1, 'Huit dates de référence différentes',
   'Date d\'extraction (2026), 01/01/2025 (loyers, copropriété), 31/12/2025 (accessibilité, quittancement), fin N-1 (politique patrimoniale), CALEOL 2023-2025, SLS 2024-2025, charges et réclamations 2021-2025, sorties 2025. Les volumes ne se comparent qu\'avec un tableau de passage.', [f['code'] for f in F if f['kind'] != 'Q'],
   'Fixer et documenter une date d\'extraction par trame ; produire le tableau de passage des volumes.')
al('A13', 'Dates & périmètres', 2, '« N » n\'a pas le même sens partout',
   'CALEOL : « n étant l\'année en cours » (2026, donc 2023-2025) ; charges : N-5 à N-1 ; stock PCRC au 31/12/2025 ; questionnaire SLS : N-1 à N-3 alors que le recueil SLS couvre N-2 et N-1.', ['12_30_01', '12_30_03', '12_30_04', '12_30_11', '11_30_01'],
   'Faire confirmer les années exactes par le contrôleur et les écrire dans chaque cartouche.')
al('A14', 'Dates & périmètres', 2, 'Populations de logements différentes',
   'Logements familiaux seulement (accessibilité, CALEOL y compris étudiants gérés), toutes natures de lots (loyers), logements seulement (quittancement), hors foyers et résidences étudiantes (sortants), foyers en équivalents-logements.', ['11_30_04', '12_30_01', '12_30_02', '12_30_05', '12_30_07', '11_30_01'],
   'Documenter le filtre de population appliqué dans chaque extraction.')
al('A15', 'Données personnelles', 1, 'Sept trames contiennent des données nominatives et de revenus',
   'Noms de candidats, locataires, acquéreurs et accédants, dates de naissance, RFR, ressources, n° unique SNE.', ['12_30_01', '12_30_04', '12_30_05', '12_30_06', '12_30_07', '11_30_06', '11_30_07'],
   'Transmission par le canal sécurisé prévu par l\'ANCOLS ; associer le DPO ; pas de copies de travail non maîtrisées.')
al('A16', 'Volumétrie & formats', 2, 'Quittancement et charges au format CSV',
   'Le quittancement (locataire × rubrique × 12 mois) et les charges (groupe × nature × 5 ans) peuvent dépasser la limite d\'Excel (1 048 576 lignes) : fichiers CSV par année ou par mois.', ['12_30_05', '12_30_03'],
   'Fixer encodage (UTF-8), séparateur, format des dates et des décimales avant extraction.')
al('A17', 'Formules à préserver', 2, 'Colonnes calculées « Ne pas toucher »',
   'Totaux de logements (11_30_02 P, 11_30_03 2.3 G, 11_30_05 R et H, copropriété L), STOCK_PCRC (11_30_01 Y), parc au 31/12 et évolution (synthèse K, L), prix de revient au logement / m² et total financement (11_30_05), date reportée (1_2_Accessibilité_FOYER).', ['11_30_01', '11_30_02', '11_30_03', '11_30_04', '11_30_05', '11_30_08'],
   'Coller les extractions en valeurs, colonne par colonne, sans écraser les formules.')
al('A18', 'Données hors SI', 2, 'Nombreuses données à constituer manuellement',
   'PCRC, accessibilité et adaptation, DTG / PPT des copropriétés, avenants de marchés, visites et pannes d\'équipements, retours candidats, dépôts de garantie et régularisations des sortants, procédures de recouvrement.', ['11_30_01', '11_30_03', '11_30_04', '11_30_08', '12_30_01', '12_30_07', '12_30_12'],
   'Identifier tôt les détenteurs (services, prestataires) et tracer la source de chaque donnée.')
al('A19', 'Cohérence recueil ↔ questionnaire', 2, 'Les réponses rédigées doivent concorder avec les chiffres',
   'Questionnaires SLS, charges, offre nouvelle, accessibilité et loyers demandent des chiffres ou des affirmations vérifiables dans les recueils.', ['11_30_09', '11_30_10', '12_30_09', '12_30_10', '12_30_11'],
   'Rédiger les questionnaires après la production et le contrôle des recueils.')

# ------------------------------------------------------------ derived: matrix & proximity
pivot_files = collections.defaultdict(lambda: collections.Counter())  # pivot -> file -> n fields
for f in fields:
    if f['pivot']: pivot_files[f['pivot']][f['file']] += 1
qlinks = collections.defaultdict(set)  # pivot -> set(qfile)
for q, secs in QL.items():
    for (_, pvs, _fs) in secs:
        for p in pvs: qlinks[p].add(q)
GENERIC = {'ORG'}
filecodes = [f['code'] for f in F]
fp = {c: set() for c in filecodes}
for p, cnt in pivot_files.items():
    for c in cnt: fp[c].add(p)
for p, qs in qlinks.items():
    for q in qs: fp[q].add(p)
prox = {}
for a, b in itertools.combinations(filecodes, 2):
    s = sorted((fp[a] & fp[b]) - GENERIC)
    if s: prox[f'{a}|{b}'] = s

for f in F:
    c = f['code']
    fl = [x for x in fields if x['file'] == c]
    f['nfields'] = len(fl)
    f['nsheets'] = len({x['sheet'] for x in fl})
    f['nmand'] = sum(1 for x in fl if x['mandatory'])
    f['pivots'] = sorted(fp[c])
    f['controls'] = [k['id'] for k in C if c in k['files']]
    f['alerts'] = [a['id'] for a in A if c in a['files']]
    f['personal'] = c in A[14]['files']
    f['partners'] = sorted({x for k, v in prox.items() for x in k.split('|') if c in k.split('|') and len(v) >= 3} - {c})
    if f['kind'] == 'Q' or c == '12_30_12':
        f['qsections'] = [dict(s=s, p=p, f=fs) for (s, p, fs) in QL.get(c, [])]

piv = []
for pid, p in P.items():
    files_ = dict(pivot_files.get(pid, {}))
    q = sorted(qlinks.get(pid, []))
    nfiles = len(files_) + len(q)
    if nfiles == 0: continue
    p2 = dict(p, files=files_, qfiles=q, nfiles=nfiles,
              names=sorted({x['name'] for x in fields if x['pivot'] == pid}))
    piv.append(p2)

out = dict(files=F, pivots=piv, families=FAM, fields=[{k: x[k] for k in ('file', 'sheet', 'col', 'name', 'mandatory', 'definition', 'values', 'fmt', 'def_status', 'def_name_at_col', 'pivot')} for x in fields],
           controls=C, alerts=A, themes=T, prox=prox)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
FAMD = dict(FAM)
with open(os.path.join(RACINE, 'donnees', 'inventaire_champs.csv'), 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.writer(fh, delimiter=';')
    w.writerow(['Trame', 'Onglet', 'Colonne', 'Champ', 'Obligatoire', 'Donnee_pivot_id', 'Donnee_pivot', 'Famille', 'Definition', 'Valeurs_attendues', 'Format', 'Statut_definition'])
    for x in fields:
        pv = P.get(x['pivot']) if x['pivot'] else None
        w.writerow([x['file'], x['sheet'], x['col'], x['name'], 'oui' if x['mandatory'] else '', x['pivot'] or '', pv['label'] if pv else '', FAMD.get(pv['fam'], '') if pv else '', x['definition'], x['values'], x['fmt'], x['def_status']])
print('files', len(F), 'pivots', len(piv), 'controls', len(C), 'alerts', len(A), 'themes', len(T), 'prox pairs', len(prox))
shared = [p for p in piv if p['nfiles'] >= 2]
print('pivots shared by >=2 files:', len(shared), '; >=5 files:', len([p for p in piv if p['nfiles'] >= 5]))
for p in sorted(piv, key=lambda x: -x['nfiles'])[:15]: print(p['id'], p['nfiles'])
top = sorted(prox.items(), key=lambda kv: -len(kv[1]))[:12]
for k, v in top: print(k, len(v))
assert all(c in FD for k in C for c in k['files']), 'unknown file in controls'
assert all(c in FD for a in A for c in a['files'])
assert all(p in P for k in C for p in k['pivots'])
print('bytes', len(json.dumps(out, ensure_ascii=False)))
