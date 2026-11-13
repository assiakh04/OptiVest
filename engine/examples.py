"""Jeux de données d'exemple (fictifs, sauf mention « cas type »)."""


def _c(name, kind, unit, weight):
    return {'name': name, 'kind': kind, 'unit': unit, 'weight': weight}


EXAMPLES = {
    'Fournisseurs responsables': {
        'name': 'Choisir un fournisseur', 'domain': 'Industrie',
        'description': 'Quel fournisseur retenir parmi 5 offres en combinant qualité, prix, délai et RSE ?',
        'alternatives': ['Atlas Supply', 'Cèdre Partners', 'Noria Industrie', 'Sahara Solutions', 'Rif Logistics'],
        'criteria': [_c('Qualité', 'max', '/100', .35), _c('Prix', 'min', 'kMAD', .25), _c('Délai', 'min', 'jours', .20), _c('RSE', 'max', '/100', .20)],
        'matrix': [[91, 76, 12, 84], [85, 66, 9, 75], [94, 89, 16, 91], [83, 60, 14, 89], [88, 71, 11, 80]]},
    'Modèle de machine learning': {
        'name': 'Sélectionner un modèle ML', 'domain': 'Machine Learning',
        'description': 'Quel modèle offre le meilleur compromis performance / latence / explicabilité ?',
        'alternatives': ['Random Forest', 'XGBoost', 'SVM', 'KNN', 'Régression logistique'],
        'criteria': [_c('Accuracy', 'max', '%', .25), _c('Recall', 'max', '%', .25), _c('F1-score', 'max', '%', .25), _c('Latence', 'min', 'ms', .15), _c('Explicabilité', 'max', '/10', .10)],
        'matrix': [[92, 89, 90, 33, 7], [94, 91, 93, 40, 5], [90, 87, 89, 23, 6], [86, 88, 87, 8, 6], [84, 82, 83, 4, 10]]},
    'Système énergétique': {
        'name': 'Électrifier un village isolé', 'domain': 'Énergie',
        'description': 'Solaire, éolien, hybride… : arbitrer entre efficacité, coût, fiabilité et émissions.',
        'alternatives': ['Solaire', 'Éolien', 'Hybride', 'Mini-hydro', 'Biomasse'],
        'criteria': [_c('Efficacité', 'max', '%', .30), _c('Investissement', 'min', 'M MAD', .25), _c('Fiabilité', 'max', '/100', .25), _c('Émissions', 'min', 'gCO₂/kWh', .20)],
        'matrix': [[21, 11, 86, 42], [32, 14, 78, 18], [29, 18, 95, 21], [41, 24, 89, 15], [27, 10, 83, 78]]},
    'Actions boursières': {
        'name': 'Choisir une action à acheter', 'domain': 'Finance',
        'description': 'Sélection d’actifs : rendement, risque, liquidité et ratios fondamentaux (données fictives).',
        'alternatives': ['Tech Horizon', 'Banque Atlas', 'Énergie Rif', 'Telecom Maghreb', 'Immo Casablanca', 'Mines Anti-Atlas'],
        'criteria': [_c('Rendement moyen', 'max', '%', .22), _c('Écart-type', 'min', '%', .18), _c('Volume échangé', 'max', 'M', .10), _c('Bêta', 'min', '', .12), _c('ROE', 'max', '%', .20), _c('P/B', 'min', '', .08), _c('ROA', 'max', '%', .10)],
        'matrix': [[14.2, 21.0, 8.5, 1.35, 18.2, 3.9, 8.1], [9.8, 12.5, 14.2, 0.92, 12.4, 1.8, 1.4], [11.1, 18.4, 6.3, 1.10, 14.9, 2.2, 6.2],
                   [8.3, 9.8, 10.7, 0.71, 22.1, 4.5, 9.8], [10.4, 15.2, 4.1, 1.05, 9.6, 1.4, 3.3], [12.9, 24.6, 5.8, 1.48, 16.3, 2.6, 7.4]]},
    'Cas type · Voitures (TOPSIS)': {
        'name': 'Cas type — choisir une voiture', 'domain': 'Cas type',
        'description': 'Cas TOPSIS : 4 marques, critères style (+), fiabilité (+), économie de carburant (+), coût (−). Poids (0,2 ; 0,1 ; 0,4 ; 0,3).',
        'alternatives': ['M1', 'M2', 'M3', 'M4'],
        'criteria': [_c('Style', 'max', '', .2), _c('Fiabilité', 'max', '', .1), _c('Économie carburant', 'max', '', .4), _c('Coût', 'min', '', .3)],
        'matrix': [[7, 9, 9, 8], [8, 7, 8, 7], [9, 6, 8, 9], [6, 7, 8, 6]]},
    'Cas type · Fournisseur (BWM)': {
        'name': 'Cas type — choisir un fournisseur', 'domain': 'Cas type',
        'description': 'Les 4 critères de l’exemple BWM : Qualité (Best), Prix, Délai, RSE (Worst). Les valeurs des offres sont fictives.',
        'alternatives': ['Fournisseur 1', 'Fournisseur 2', 'Fournisseur 3', 'Fournisseur 4'],
        'criteria': [_c('Qualité', 'max', '/10', .552), _c('Prix', 'min', 'kMAD', .207), _c('Délai', 'min', 'jours', .155), _c('RSE', 'max', '/10', .086)],
        'matrix': [[9, 120, 10, 5], [7, 95, 7, 8], [8, 105, 14, 9], [6, 80, 6, 4]]},
}

# Exemple AHP « achat d'une voiture » du cours
AHP_CAR = {
    'criteria': ['Coût', 'Confort', 'Sécurité'],
    'alternatives': ['Voiture 1', 'Voiture 2'],
    'criteria_matrix': [[1, 7, 3], [1 / 7, 1, 1 / 3], [1 / 3, 3, 1]],
    'alt_matrices': [[[1, 7], [1 / 7, 1]], [[1, .2], [5, 1]], [[1, 1 / 9], [9, 1]]],
}

# Exemple de classement Spearman du cours (A1…A6)
SPEARMAN_COURSE = {'Alternative': ['A1', 'A2', 'A3', 'A4', 'A5', 'A6'], 'TOPSIS': [2, 1, 3, 5, 4, 6],
                   'VIKOR': [1, 2, 4, 3, 5, 6], 'PROMETHEE II': [2, 1, 3, 6, 4, 5]}
