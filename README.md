# OptiVest — Investment Decision Intelligence

OptiVest est une **application Python + Streamlit** pour évaluer, comparer et sélectionner des **projets d’investissement**. Elle dérive directement de l'architecture et des moteurs scientifiques de **DecisionLab Studio v2**, mais sa navigation, son tableau de bord, ses exemples et ses nouvelles fonctionnalités sont centrés sur la finance d'entreprise.

![Capture de l'aperçu interactif](Apercu_Ecran.png)

## Démonstration et lancement

- **Sans installer Python :** ouvrir `Apercu_OptiVest_Interactif.html` dans le navigateur. C'est un **aperçu autonome limité** du dashboard, avec deux études, cash-flows, graphiques et curseurs de budget/taux. Les méthodes MCDM complètes sont dans Streamlit.
- **Sur Mac :** décompresser le dossier `OptiVest`, puis utiliser le Terminal :

```bash
cd ~/Downloads/OptiVest
zsh lancer_mac.sh
```

- Alternative manuelle :

```bash
cd ~/Downloads/OptiVest
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Le navigateur ouvre généralement `http://localhost:8501`.

## GitHub et Streamlit Community Cloud

1. Créer un dépôt GitHub et y publier **les fichiers et dossiers du projet**, pas uniquement le ZIP.
2. Ne **pas** publier `.venv/`, `__pycache__/`, `.env` ou `.streamlit/secrets.toml` (voir `.gitignore`).
3. Dans Streamlit Community Cloud : choisir le dépôt, la branche `main`, le fichier d'entrée `app.py`, Python 3.11 ou 3.12, puis déployer.
4. La plateforme installe les paquets répertoriés dans `requirements.txt`.

## Parcours utilisateur

| Ordre | Page | Action | Résultat |
|---|---|---|---|
| 1 | Vue d'ensemble | Choisir une étude ou partir du scénario fictif | Dashboard financier, KPI, VAN et flux |
| 2 | Étude & projets | Saisir montant investi, flux nets, risque et alignement | Données financières éditables + import/export JSON |
| 3 | Analyse financière | Fixer taux d'actualisation et calculer les indicateurs | VAN, TRI, payback, indice de profitabilité |
| 4 | Choisir la méthode | Répondre au questionnaire de sélection | Recommandation argumentée de méthodes |
| 5 | Pondération | Comparer l'importance des critères | AHP, BWM, Entropie, CRITIC, hybride |
| 6 | Classement MCDM | Tester les algorithmes sur la matrice financière | WSM, WPM, WASPAS, TOPSIS, VIKOR, AHP hiérarchique |
| 7 | Surclassement | Limiter la compensation entre critères | PROMETHEE I/II, ELECTRE III |
| 8 | Comparaison des rangs | Confronter les classements | Spearman, désaccord, concordance |
| 9 | Scénarios financiers | Modifier les flux et taux des trois scénarios | VAN conditionnelles et courbes de sensibilité |
| 10 | Robustesse MCDM | Perturber les poids | Fréquences simulées et stabilité des classements |
| 11 | Allocation du budget | Sélectionner un ensemble de projets finançables | Optimisation 0/1 maximisant la VAN (ou des scores TOPSIS à titre exploratoire) |
| 12 | Analyses spécialisées | Explorer MAUT, méthodes floues, IA et dynamique | Tests supplémentaires |
| 13 | Rapport d'investissement | Justifier et exporter | Rapport HTML, classeur Excel, CSV, JSON |

## Architecture

```text
OptiVest/
├── app.py                 # navigation Streamlit et sidebar
├── ui/                    # état, composants visuels, CSS pastel animé
├── views/                 # vues financières + modules MCDM hérités
├── engine/
│   ├── finance.py         # VAN, TRI, payback, IP, scénarios, allocation 0/1
│   ├── finance_examples.py# exemples d'études fictifs
│   ├── mcdm.py            # moteur multicritère d'origine
│   ├── fuzzy.py, ai.py, dynamic.py, single.py
├── tests/                 # tests des formules financières et MCDM
├── .streamlit/config.toml
├── Apercu_OptiVest_Interactif.html
└── requirements.txt
```

## Formules utilisées et transparence

- **VAN :** `-I0 + Σ(CF_t / (1+r)^t)`. Flux nets supposés reçus en fin d'année ; taux fixe et constant.
- **TRI :** racine du calcul de VAN seulement lorsqu'il y a **un changement de signe** dans les cash-flows (pas de TRI affiché lorsque l'interprétation est ambiguë).
- **Payback simple :** cumul des flux non actualisés avec interpolation à l'année de récupération. Si non atteint : valeur absente dans le module financier, pénalité `horizon+1` dans la matrice MCDM.
- **Indice de profitabilité :** valeur actuelle des flux futurs / investissement initial.
- **Risque expert et alignement :** notes subjectives sur dix, pas des mesures de volatilité de marché.
- **Matrice MCDM dérivée :** VAN (max), indice de profitabilité (max), risque expert (min), payback (min), alignement (max).
- **Risque de double comptage :** VAN et IP sont liés. L’utilisateur doit justifier leurs poids et tester la robustesse. Le montant investi est traité comme une **contrainte** dans l'allocation.
- **Optimisation de portefeuille :** maximiser la somme des VAN des projets sélectionnés sous un budget, variables de décision binaires, projets supposés indépendants et indivisibles. La maximisation des scores TOPSIS est explicitement un mode exploratoire non financier.

## Limitations

**Toutes les données d'exemple sont fictives.** Les paramètres et la sensibilité ne constituent pas une estimation probabiliste, une prévision validée ou un conseil d'investissement. Les modules avancés hérités de DecisionLab peuvent présenter des exemples génériques plutôt que des projets financiers. L'évaluation MCDM n'est pas une garantie de rentabilité.

Les études sont conservées en **session Streamlit**, sans base de données persistante. Télécharger le JSON avant de fermer la session. Les modèles IA restent des démonstrations, non une validation métier. La sauvegarde multi-utilisateur et l'authentification ne sont pas incluses.

## Tests

```bash
python -m pip install pytest
python -m pytest -q tests/test_engine.py tests/test_finance.py
```

Les **tests mathématiques** s'exécutent indépendamment de Streamlit. Pour les tests de rendu `tests/test_app.py`, l'installation de Streamlit est requise.


## Modifications de la refonte (v3)

- **Accueil** : bannière animée alimentée par les vrais chiffres de l'étude (VAN cumulée, nombre de projets, budget) ; plus aucune valeur décorative.
- **Sidebar** : contraste renforcé, page active très visible, groupes raccourcis, carte « Parcours » avec barre de progression calculée.
- **Animations** : entrée des KPI, survols, orbites ; `prefers-reduced-motion` désactive toutes les animations et transitions.
- **Vocabulaire** : suppression de « Analyse N », « cours », « exercice du cours » dans les titres, kickers et jeux d'exemple (les définitions, formules et limites sont conservées).
- **D · Assistant de méthode** : 6 questions dont l'objectif financier et le nombre d'alternatives ; recommandations justifiées, profil mémorisé et repris dans le rapport.
- **B · Import** : CSV et Excel (modèle téléchargeable, validation), en plus du JSON.
- **L · Allocation** : graphique d'utilisation du capital et tableau classement TOPSIS / rang VAN / portefeuille retenu.
- **M · Rapport** : export **PDF** (reportlab) en plus de HTML, Excel, CSV, JSON.
- **J / K** : avertissements explicites (données synthétiques, classes MCDM ≠ succès financier ; modèles dynamiques réellement implémentés : tendance, Holt, AR, MA, EWMA ; ARIMA/LSTM/GARCH non implémentés).
- **Tests** : `tests/test_optivest_pages.py` (pages financières, PDF) ; 27 tests rapides + smoke tests de toutes les pages.
- **Point à signaler** : VIKOR — la condition C2 exige que le meilleur classé par Q le soit aussi par S **et** R ; l'application suit cette règle.
