"""Etape 2 - rattachement de chaque colonne a une donnee pivot (concept partage entre trames).

Les regles sont dans RULES (premiere expression qui correspond) et OVR (exceptions colonne par colonne).

    python3 scripts/02_donnees_pivots.py        donnees/inventaire_brut.json -> donnees/pivots.json
"""
import json, re, sys, os, collections
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
inv = json.load(open(os.path.join(RACINE, 'donnees', 'inventaire_brut.json'), encoding='utf-8'))
OUT = os.path.join(RACINE, 'donnees', 'pivots.json')

# ---------------------------------------------------------------- families & pivots
FAMILIES = [
    ('ID', 'Identifiants & clés de jointure'),
    ('LOC', 'Localisation & zonages'),
    ('CAR', 'Caractéristiques du patrimoine'),
    ('ENE', 'Énergie & équipements'),
    ('OCC', 'Occupants, ménages & attributions'),
    ('LOY', 'Loyers, aides & quittancement'),
    ('CHG', 'Charges & comptabilité'),
    ('TRV', 'Travaux, maintenance & marchés'),
    ('DEV', 'Développement, ventes & finances d\'opération'),
]
P = {}  # id -> dict
def pv(pid, fam, label, desc):
    P[pid] = dict(id=pid, fam=fam, label=label, desc=desc)

pv('ORG', 'ID', 'Organisme (SIREN / raison sociale)', 'Identifiant de l\'organisme, présent en tête de presque toutes les trames.')
pv('AGENCE', 'ID', 'Agence / secteur de gestion', 'Rattachement organisationnel (agence, secteur, siège).')
pv('GRP', 'ID', 'Code groupe immobilier / programme', 'Clé de jointure patrimoniale n°1 : CODE_PATRIMOINE, CODE_GROUPE_IMMOBILIER, CODE_PATRIMOINE_FOYER, « code opération ».')
pv('GRP_NOM', 'ID', 'Nom du groupe immobilier', 'Libellé du programme ; doit être identique pour un même code dans toutes les trames.')
pv('BAT', 'ID', 'Code bâtiment / escalier', 'Maille bâtiment (Etat des lieux, cartographie énergétique, ascenseurs, DTA, charges).')
pv('LOT', 'ID', 'Identifiant lot / logement (interne)', 'Clé de jointure logement : IDENTIFIANT_LOT, CODE_IDENTIFIANT_LOT, IDENTIFIANT_LOGEMENT, « identifiant du logement ».')
pv('RPLS', 'ID', 'Identifiant RPLS', 'Identifiant national du logement, permet le rapprochement avec l\'enquête RPLS.')
pv('OPE', 'ID', 'Code / nom d\'opération', 'Opérations de construction, d\'accession ou de projet (hors code patrimoine).')
pv('CPT', 'ID', 'Compte locataire', 'NUM_COMPTE_LOCATAIRE, « identifiant du locataire » : clé de jointure ménage.')
pv('PERS', 'ID', 'Nom de la personne (locataire, candidat, acquéreur)', 'Donnée nominative : RGPD, transmission sécurisée.')
pv('MARCHE', 'ID', 'Référence de marché', 'CODE_MARCHE / NUM_MARCHE : relie équipements, interventions et marchés d\'entretien.')
pv('TITU', 'ID', 'Titulaire / fournisseur', 'Titulaire du marché, entreprise intervenante, promoteur, MOE.')

pv('COMMUNE', 'LOC', 'Commune (libellé)', 'Libellé de commune.')
pv('INSEE', 'LOC', 'Code INSEE commune', 'Code commune 5 caractères (format texte attendu, numérique dans 2 trames).')
pv('ADR', 'LOC', 'Adresse principale', 'Adresse du groupe immobilier.')
pv('EPCI', 'LOC', 'EPCI', 'Intercommunalité de rattachement (nom ou SIRET).')
pv('DEPT', 'LOC', 'Département', 'Code ou nom du département.')
pv('QPV', 'LOC', 'QPV / ANRU', 'Situation en quartier prioritaire ou en rénovation urbaine.')
pv('ZABC', 'LOC', 'Zonage A/B/C (tension)', 'ZONE_TENSION, ZONAGE_ABC : Abis, A, B1, B2, C.')
pv('Z123', 'LOC', 'Zonage 1/2/3 (loyers, plafonds, RLS)', 'ZONE_LOYERS, ZONAGE : 1, 1bis, 2, 3.')
pv('ZGEO', 'LOC', 'Zone géographique p/i/r/d', 'ZONE_GEOGRAPHIQUE : Paris, IdF, régions, DOM.')

pv('NBLGT', 'CAR', 'Nombre de logements / parc', 'Volumes de logements (individuels, collectifs, total, équivalents-logements, parc au 1/1 et au 31/12).')
pv('DCONS', 'CAR', 'Date de construction', 'Au bâtiment (BAT) ou au programme (PRG, date la plus ancienne).')
pv('DMES', 'CAR', 'Date / année de mise en service', 'Entrée dans le patrimoine, première mise en location.')
pv('FINI', 'CAR', 'Financement initial', 'Financement d\'origine (PLA, HLMO, ILN, PLUS…).')
pv('FCUS', 'CAR', 'Financement CUS (PLAI / PLUS / PLS / PLI)', 'Catégorie de financement au sens de la CUS ; ventilations par financement.')
pv('CONV', 'CAR', 'Conventionnement APL', 'Conventionné ou non, date de convention APL.')
pv('TYPO', 'CAR', 'Typologie (T1…T7)', 'Type de logement / de lot.')
pv('INDCOL', 'CAR', 'Individuel / collectif / étudiant', 'Nature du logement.')
pv('SHAB', 'CAR', 'Surface habitable', 'Au logement ou agrégée au groupe / à l\'opération.')
pv('SUTIL', 'CAR', 'Surface utile / corrigée / quittancée', 'Surfaces servant au calcul du loyer et du prix de revient.')
pv('NATLOT', 'CAR', 'Nature de lot / annexes', 'Logement, garage, commerce, cave…')
pv('COPRO', 'CAR', 'Copropriété', 'Bâtiment en copropriété, tantièmes, gouvernance de la copropriété.')
pv('PSP', 'CAR', 'Stratégie patrimoniale (PSP)', 'Classification et intervention issues du PSP.')
pv('REHA', 'CAR', 'Réhabilitation (date, nature, statut)', 'Dernière réhabilitation, réception des travaux (EXE6).')
pv('ACCESS', 'CAR', 'Accessibilité & adaptation', 'Logements accessibles (UFR, canne), adaptés, demandes et travaux d\'adaptation, dégrèvements TFPB.')
pv('VAC', 'CAR', 'Vacance', 'Taux de vacance, date de vacance, logements vacants.')

pv('DPE', 'ENE', 'DPE / GES', 'Étiquettes et valeurs DPE / GES, mode de calcul, n° ADEME.')
pv('CHAUF', 'ENE', 'Mode & vecteur de chauffage / ECS', 'Chauffage individuel/collectif, énergie, chaufferie, VMC gaz.')
pv('DIAG', 'ENE', 'Diagnostics réglementaires & installations', 'CREP, DTA, DAPP, électricité, gaz : dates et résultats.')
pv('EQUIP', 'ENE', 'Équipements & contrôles', 'Ascenseurs, aires de jeux, SSI, fermetures, 3D : dates, contrôles, pannes.')

pv('BAIL', 'OCC', 'Dates de bail & d\'entrée dans les lieux', 'Signature du bail, entrée dans les lieux.')
pv('SORTIE', 'OCC', 'Sortie du locataire', 'Préavis, date de sortie, décompte.')
pv('RESS', 'OCC', 'Ressources du ménage (RFR, revenus)', 'RFR N-1 / N-2, ressources mensuelles.')
pv('MENAGE', 'OCC', 'Composition du ménage', 'Catégorie de ménage, personnes à charge, occupants, UC, âge.')
pv('PLAF', 'OCC', 'Plafonds de ressources & quartiles', 'Plafonds PLUS/PLS, 1er quartile EPCI, dépassement.')
pv('PUBLIC', 'OCC', 'Publics & mutations', 'DALO, prioritaires, relogements, mutations internes.')
pv('CAL', 'OCC', 'Passage en CALEOL', 'Identifiant, date, décision, rang, retour candidat.')
pv('ACQ', 'OCC', 'Profil de l\'acquéreur', 'Qualité, type et origine de l\'acquéreur ou de l\'accédant.')

pv('LOYER', 'LOY', 'Loyer pratiqué / redevance', 'Loyer mensuel pratiqué, loyer à l\'attribution, loyer de relocation, redevance.')
pv('LMAX', 'LOY', 'Loyer maximum / taux de loyer', 'Loyer maximum conventionnel, taux de loyer avant/après travaux.')
pv('AIDES', 'LOY', 'APL / AL / RLS', 'Aides au logement et réduction de loyer de solidarité.')
pv('SLS', 'LOY', 'Supplément de loyer de solidarité', 'Calcul, montant retenu, quittancé, forfaitaire / calculé.')
pv('QUIT', 'LOY', 'Quittancement (rubriques & montants)', 'Rubriques, montants et périodes quittancés.')
pv('DG', 'LOY', 'Dépôt de garantie', 'Date, montant, restitution.')

pv('CHARGES', 'CHG', 'Charges récupérables', 'Natures de charges, montants récupérables, répartition, régularisation.')
pv('COMPTA', 'CHG', 'Comptes comptables / budgétaires', 'Comptes et exercices comptables.')

pv('REL', 'TRV', 'Remise en état des logements (EDL / REL)', 'États des lieux sortants, travaux de remise en état, part imputée au locataire.')
pv('INTERV', 'TRV', 'Interventions & réclamations', 'Interventions curatives, pannes, montants d\'intervention.')
pv('MARCHEI', 'TRV', 'Caractéristiques des marchés', 'Nature, forme, périmètre, dates, montants et avenants des marchés.')
pv('CONT', 'TRV', 'Contentieux & sinistres', 'Dommage-ouvrage, contentieux techniques, jugements.')

pv('PROD', 'DEV', 'Mode de production / produit', 'MOD, VEFA, acquisition-amélioration, PSLA, BRS…')
pv('PRIX', 'DEV', 'Prix de revient & dépenses d\'opération', 'Prix de revient prévisionnels et définitifs, charge foncière, dépenses engagées.')
pv('FINOP', 'DEV', 'Plan de financement d\'opération', 'Prêts, subventions, fonds propres.')
pv('VENTE', 'DEV', 'Ventes (dates, prix, volumes)', 'Ventes HLM et accession : actes, prix, nombre de logements vendus.')
pv('GOUV', 'DEV', 'Décisions de gouvernance & autorisations', 'CA, CUS / préfet, permis, agréments, OS, CAO.')
pv('MOUV', 'DEV', 'Mouvements de parc', 'Démolitions, transformations d\'usage, évolution du parc.')

# ---------------------------------------------------------------- rules (first match wins)
RULES = [
    (r'^OBE?RVATIONS$', None), (r'^COMMENTAIRE', None), (r'^DESCRIPTION_RECLAMATION$', 'INTERV'),
    (r'^SIREN$|^RAISON[_ ]SOCIALE', 'ORG'),
    (r'ACCESSIBLE|^NON_AUDITE$|ADAPT|^DOSSIER\+12MOIS$|^DELAI_DEMANDE$|DEGREVEMENTS_TFPB', 'ACCESS'),
    (r'^LIB_AGENCE$|^AGENCE$|^LIB_SECTEUR$', 'AGENCE'),
    (r'^CODE_PATRIMOINE|^CODE_GROUPE_IMMOBILIER$|^CODE OP[EÉ]RATION$', 'GRP'),
    (r'^NOM_PATRIMOINE|^NOM_GROUPE_IMMOBILIER$|^NOM OP[EÉ]RATION$', 'GRP_NOM'),
    (r'^CODE_BATIMENT|^CODE_ESCALIER', 'BAT'),
    (r'RPLS', 'RPLS'),
    (r'^IDENTIFIANT_LOT$|^CODE_IDENTIFIANT_LOT$|^IDENTIFIANT_LOGEMENT$|^IDENTIFIANT DU LOGEMENT$', 'LOT'),
    (r"^NOM[_-]OP$|^CODE_OPERATION$|^NOM_OPERATION$|^CODE DE L'OP|^NOM DE L'OP", 'OPE'),
    (r'^NUM_COMPTE_LOCATAIRE$|^IDENTIFIANT DU LOCATAIRE', 'CPT'),
    (r'^NOM_PRENOM|^NOM DU LOCATAIRE|^NOM_ACQUEREUR$|^NOM_ACCEDANT$|^NUMERO_UNIQUE$', 'PERS'),
    (r'^CODE_MARCHE$|^NUM_MARCHE$', 'MARCHE'),
    (r'TITULAIRE|^FOURNISSEUR_INTERVENTION$|^MOE$|^GESTIONNAIRE$|^MANDATAIRE$|ASSOCI|SYNDIC|^MOA$|^MA[IÎ]TRE D', 'TITU'),
    (r'^COMMUNE$|^LIBELL[EÉ] COMMUNE$', 'COMMUNE'),
    (r'^CODE_INSEE|^CODE COMMUNE$', 'INSEE'),
    (r'^ADRESSE', 'ADR'),
    (r'EPCI', 'EPCI'),
    (r'^DEPARTEMENT$|^CODE_DEPARTEMENT$', 'DEPT'),
    (r'QPV|ANRU$|^OP_ANRU$|^ANRU$', 'QPV'),
    (r'^ZONE_TENSION$|^ZONAGE_ABC$|^ZONAGE \(A', 'ZABC'),
    (r'^ZONE_LOYERS$|^ZONAGE$', 'Z123'),
    (r'^ZONE_GEOGRAPHIQUE$', 'ZGEO'),
    (r'^ZRR', 'QPV'),
    (r'^VALEUR_QUARTILE|^PLAFOND|DEPASSEMENT_PLAFONDS', 'PLAF'),
    (r'PUBLIC_PREMIER_QUARTILE', 'PLAF'),
    (r'^NOMBRE_TOTAL_LOGEMENTS_MARCHE$|^NOMBRE_TOTAL_EQUIPEMENTS_MARCHE$', 'MARCHEI'),
    (r'NOMBRE_TOTAL_EQUIPEMENTS|NOMBRE_NIVEAUX_ASC|^CODE_EQUIPEMENT', 'EQUIP'),
    (r'NOMBRE_LOGEMENTS_VEFA$|^MOA_DIRECTE$|^AA$|^AUTRES$|^TYPE_PRODUIT$|^PRODUIT$|^NATURE \(VEFA|^MODE$|^NATURE_PROJET$', 'PROD'),
    (r'^VENTES$|^DATE_VENTE$|^DATE_CONTRAT_VENTE$|^DATE_CONTRAT_RESERVATION$|PRIX_VENTE|^PRIX_DE_VENTE|GRILLE_PRIX|^VNC$|PLUS_VALUE|^EMPRUNT$|^MARGE_OPERATEUR$|^DATE_LEVEE_OPTION$|^DATE_CONTRAT_LOCATION_ACCESSION$|^DATE_ACQUISITION_DES_DROITS|^PUB_|^DATE_DE_L.INSERTION$|^DATE_CONVENTION$', 'VENTE'),
    (r'^DEMOLITION$|^TRANSFORMATION_USAGE|^EVOLUTION$|^PARC_', 'MOUV'),
    (r'NOMBRE_.*LOGEMENTS|^TOTAL_LOGEMENTS$|^EQUIVALENT_LOGEMENT$|^TOTAL_PLACES$|LOTS CONSTRUITS|LOTS LIBRES|^T[1-7]$', 'NBLGT'),
    (r'^NOMBRE_GARAGES$|^NOMBRE_AUTRES_LOTS$|^NATURE_LOT$|^SURF_ANNEXES$', 'NATLOT'),
    (r'^DATE_DE_CONSTRUCTION', 'DCONS'),
    (r'MISE_EN_SERVICE|^DATE_MISE_EN_LOC$|^DATE DE LIVRAISON|^DATE_LIVRAISON$', 'DMES'),
    (r'^FINANCEMENT_INITIAL$', 'FINI'),
    (r'^TYPE FINANCEMENT$', 'FINI'),
    (r'^FINANCEMENT_CUS$|^FINANCEMENT$|_FINANCEMENT$', 'FCUS'),
    (r'CONVENTIONNE|^LOGT_CONV|CONVENTIONNEMENT_APL|^DATE_CONVENTION_APL$|^DATE_VALEUR_CONV$', 'CONV'),
    (r'^TYPE_LOGEMENT$|^TYPE_LOT$|^TYPE LOGEMENT$', 'TYPO'),
    (r'^INDIVIDUEL_COLLECTIF', 'INDCOL'),
    (r'^SURF_HABITABLE|^SURFACE_HABITABLE$', 'SHAB'),
    (r'^SURF_UTILE$|^SURFACE_UTILE$|^SU_AVANT|^SU_APRES|^SURF_CORRIGEE$|^SURF_QUITTANCEE$', 'SUTIL'),
    (r'^COPROPRIETE$|^TANTIEME$|CARNET D|DIAGNOSTIC TECHNIQUE GLOBAL|PLAN PLURIANNUEL', 'COPRO'),
    (r'^PSP_', 'PSP'),
    (r'^DATE_REHABILITATION$|^TRAVAUX$|^REHA_ETAT$|^TRAVAUX_REHABILITATION', 'REHA'),
    (r'^VACANCE$|^DATE_VACANCE$|^NB_VACANTS', 'VAC'),
    (r'DPE|^ADEME$|ETIQUETTE_GES$|VALEUR_GES$|^CONSO_NRJ|^LABEL_NRJ$', 'DPE'),
    (r'CHAUFFAGE|_ECS$|CHAUFF$|VMC_GAZ', 'CHAUF'),
    (r'CREP|^DATE_DTA|AMIANTE|DAPP|INSTALLATION_|DIAGNOSTIC_ELEC|DIAGNOSTIC_GAZ|QUALIGAZ', 'DIAG'),
    (r'_ASC$|^OBJECTIFS_SECURITE$|^DATE_CTQ$|^TAUX_DISPO$|EQUIPEMENT_AIRE$|DIAGNOSTIC_AIRE$|^TYPE_SOL$|^DATE_VISITE|REGISTRE_SECURITE|SFA$|^TYPE_EQUIPEMENT$|^TYPE_ENTRETIEN$|^TAUX_VISITE$|^NB_VISITES|^NB_ABSENCES', 'EQUIP'),
    (r'^DATE_SIGNATURE_BAIL$|^DATE_BAIL$|^DATE_ENTREE_LIEUX$|^DATE ENTR[EÉ]E DANS LE LOGT$', 'BAIL'),
    (r'^DATE_SORTIE$|^DATE SORTIE|^DATE PR[EÉ]AVIS|^DATE D[EÉ]COMPTE', 'SORTIE'),
    (r'RFR|^REVENU|RESSOURCES', 'RESS'),
    (r'CATEGORIE_MENAGE|PERSONNES_A_CHARGE|^NB_OCCUPANTS$|UNITE_CONSOMMATION|SITUATION_|^TYPE_LOCATAIRE$|^DATE_NAISSANCE$|^LOCATAIRE\+', 'MENAGE'),
    (r'^DALO$|^PUBLIC_|MUTATION|^COTATION', 'PUBLIC'),
    (r'CALEOL|^DECISION_DE_LA_CAL$|^NUMERO_RANG$|^RETOUR_CANDIDAT$|^DATE_DEPOT_DEMANDE$|PASSAGE EN CAL|^RESERVATAIRE|^TX_EFFORT|^RESTE_A_VIVRE', 'CAL'),
    (r'ACQUEREUR', 'ACQ'),
    (r'LOYER_MAX|TAUX_LOYER', 'LMAX'),
    (r'SLS|^SLR|^FORFAITAIRE_CALCULE$', 'SLS'),
    (r'LOYER|REDEVANCE', 'LOYER'),
    (r'APL|RLS_', 'AIDES'),
    (r'_QUIT$|RUBRIQUE', 'QUIT'),
    (r'D[EÉ]P[OÔ]T DE GARANTIE|DEPOT_GARANTIE', 'DG'),
    (r'CHARGES|^MODE_DE_REPARTITION$|^REGUL|RECUPERABLE', 'CHARGES'),
    (r'COMPTE_|^EXERCICE_COMPTABLE$', 'COMPTA'),
    (r'^EDL$|^REL$|DEPENSES_REL|REMISE EN [EÉ]TAT|MONTANT IMPUT', 'REL'),
    (r'INTERVENTION|PANNE|RECLAMATION|^DATE_DEBUT_ETAPE|^DATE_FIN_ETAPE|^LIBELLE_DECISION_ETAPE', 'INTERV'),
    (r'_MARCHE$|^DATE_MARCHE_|^MONTANT_CONSO_BPU$|^NOMBRE_AVENANT$|^MARCHE_NATURE$', 'MARCHEI'),
    (r'^DO$|CONTENTIEUX|DESORDRES|JUGEMENT|^ETAT_PROCEDURES$', 'CONT'),
    (r'PRIX_|^CHARGE_FONCIERE$|^DEPENSES_|^PRIX_PREVI$|^MONTANT_TRAVAUX', 'PRIX'),
    (r'^PR[EÊ]T_|^SUBVENTIONS$|^FONDS_PROPRES$|^TOTAL_FINANCEMENT$|PCRC', 'FINOP'),
    (r'^DATE_CA$|^DATE_CUS|^DATE_DEPOT_PC$|^DATE_OBTENTION_PC$|^DATE_AGREMENT$|^DATE_OS$|^DATE_CAO|^DATE_NOTIF|^DATE_RECEPTION_TRAVAUX$|^DELAI$|^DATE_CLOTURE$|^STATUT_OP|^DATE_PROJET$|^DATE_ABANDON$|^ETAT_PROJET$|^DESCRIPTIF_ABANDON$', 'GOUV'),
]
# field-level overrides: (file, sheet startswith, name) -> pivot
OVR = {
    ('11_30_05', '3_R', 'DATE_RECEPTION_TRAVAUX'): 'REHA',
    ('11_30_05', '3_R', 'DATE_DE_CONSTRUCTION'): 'DCONS',
    ('11_30_04', '1_1', 'DATE'): None, ('11_30_04', '1_2', 'DATE'): None,
    ('11_30_04', '2_A', 'ANNEE'): None, ('11_30_05', '1_S', 'ANNEE'): None,
    ('11_30_05', '2_O', 'TAUX_OCCUPATION'): 'VAC',
    ('11_30_05', '2_O', 'CONTENTIEUX'): 'CONT',
    ('11_30_05', '5_O', 'DEPENSES_ENGAGEES'): 'PRIX',
    ('11_30_01', '1_F', 'NATURE'): None, ('11_30_01', '1_F', 'TYPE_GESTION'): 'TITU',
    ('11_30_01', '1_F', 'DATE_CONVENTION_GESTION'): 'TITU',
    ('11_30_01', '1_F', 'DATE_REHABILITATION'): 'REHA',
    ('11_30_01', '1_F', 'DEPENSES_TRAVAUX'): 'FINOP',
    ('11_30_02', '1_E', 'DEPENSES_INVEST'): 'PRIX',
    ('12_30_07', 'LOC', 'montant dépôt de garantie'): 'DG',
    ('12_30_07', 'LOC', 'si absence de dépôt de garantie préciser le motif'): 'DG',
    ('12_30_07', 'LOC', 'date de restitution du dépôt de garantie'): 'DG',
    ('11_30_07', 'carac op. accession synthese', 'EPCI'): 'EPCI',
    ('11_30_04', '2_A', 'LABEL'): 'ACCESS',
    ('11_30_07', 'carac op. accession au lgt', 'MNT_REDEVANCE_LOCATIVE_INITIALE'): 'VENTE',
    ('11_30_07', 'carac op. accession au lgt', 'MNT_REDEVANCE_ACQUISITIVE'): 'VENTE',
    ('11_30_06', '1_V', 'DATE_CA'): 'GOUV',
}
SPECIFIC = {  # pivot None but keep a family for display
}

def norm(n):
    return n.upper().replace('  ', ' ').strip()

fields = inv['fields']
unmapped = []
for f in fields:
    if f['file'] == '11_30_07' and f['sheet'].endswith('synthese'):
        f['def_status'] = 'nodef'; f['definition'] = ''; f['values'] = ''; f['fmt'] = ''
    key = None
    for (fi, sh, nm), p in OVR.items():
        if f['file'] == fi and f['sheet'].startswith(sh) and f['name'] == nm:
            key = ('ovr', p); break
    if key:
        f['pivot'] = key[1]
    else:
        f['pivot'] = None
        n = norm(f['name'])
        hit = False
        for rx, p in RULES:
            if re.search(rx, n, re.I):
                f['pivot'] = p; hit = True; break
        if not hit:
            unmapped.append((f['file'], f['sheet'], f['name']))
    f['fam'] = P[f['pivot']]['fam'] if f['pivot'] else ''

print('unmapped:', len(unmapped))
for u in unmapped: print('  ', u)
json.dump(dict(fields=fields, pivots=P, families=FAMILIES), open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
c = collections.Counter(f['pivot'] for f in fields)
for k, v in sorted(c.items(), key=lambda x: -x[1]): print(k, v, sorted({f['file'] for f in fields if f['pivot'] == k}))
