"""Choisir la bonne méthode : taxonomie de référence + assistant de sélection."""
import pandas as pd
import streamlit as st
from ui import kit, nav, theme as T

CATALOG = [
    # (méthode, étape, famille, données, principe, page)
    ('AHP', 'Pondération', 'Subjective', 'Crisp', 'Comparaisons par paires (Saaty 1–9), vecteur propre, ratio de cohérence CR < 0,1', 'weights'),
    ('BWM', 'Pondération', 'Subjective', 'Crisp', 'Compare au Best et au Worst seulement (2n−3 comparaisons), programme linéaire min ξ', 'weights'),
    ('Entropie', 'Pondération', 'Objective', 'Crisp', 'Plus un critère disperse les alternatives, plus son poids est élevé', 'weights'),
    ('CRITIC', 'Pondération', 'Objective', 'Crisp', 'Écart-type × (1 − corrélation) : dispersion et indépendance du critère', 'weights'),
    ('WSM / WPM / WASPAS', 'Classement', 'Additive (compensatoire)', 'Crisp', 'Somme / produit pondérés et leur combinaison λ', 'additive'),
    ('TOPSIS', 'Classement', 'Additive (compensatoire)', 'Crisp', 'Proximité à l’idéal positif, éloignement de l’idéal négatif', 'additive'),
    ('VIKOR', 'Classement', 'Additive (compensatoire)', 'Crisp', 'Compromis entre utilité de groupe S et regret individuel R', 'additive'),
    ('PROMETHEE I/II', 'Classement', 'Surclassement', 'Crisp', 'Préférences par paires, flux Φ⁺, Φ⁻, Φ net', 'outrank'),
    ('ELECTRE III', 'Classement', 'Surclassement', 'Crisp', 'Concordance, discordance, veto, crédibilité σ, distillations', 'outrank'),
    ('MAUT / ROC', 'Alternative unique', 'Absolue', 'Crisp', 'Score d’utilité S(A) comparé à un seuil τ (expert ou ROC)', 'single'),
    ('Fuzzy TOPSIS', 'Classement flou', 'Additive', 'Flou · groupe', 'Variables linguistiques en nombres triangulaires, agrégation des décideurs', 'fuzzy_mcdm'),
    ('IF-TOPSIS', 'Classement flou', 'Additive', 'Flou intuitionniste', 'Degrés (μ, ν) et hésitation π, opérateur IFWA', 'fuzzy_mcdm'),
]


OBJECTIVES = {
    'Maximiser la création de valeur (VAN)': ('Les critères VAN / indice de profitabilité dominent : privilégier des méthodes qui conservent l’échelle des valeurs (WSM, TOPSIS) et vérifier la colinéarité VAN–IP.', 'financial'),
    'Maîtriser le risque et la liquidité': ('Le risque et le payback comptent plus que le rendement : pondérer fortement ces critères et tester la robustesse aux poids.', 'robust'),
    'Respecter une contrainte de budget': ('Le classement individuel ne suffit pas : un portefeuille sous budget se calcule par optimisation 0/1.', 'portfolio'),
    'Équilibrer rentabilité et stratégie': ('Objectifs multiples : pondération AHP ou BWM pour expliciter les arbitrages, puis comparaison de plusieurs méthodes.', 'weights'),
}


def render():
    kit.header('D · ASSISTANT MÉTHODOLOGIQUE', 'Choisir la bonne méthode',
               'Aucune méthode n’est meilleure dans l’absolu : le choix dépend de la décision à prendre. '
               'Réponds à cinq questions pour obtenir des recommandations justifiées.',
               ['Données crisp / floues', 'Décideurs', 'Compensation', 'Effort de pondération', 'Objectif financier'])

    kit.section('Assistant de sélection', 'Cinq questions, des recommandations argumentées')
    c1, c2 = st.columns(2, gap='large')
    with c1:
        data = st.radio('① Nature des données', ['Valeurs exactes', 'Jugements imprécis / linguistiques'], horizontal=True)
        dm = st.radio('② Nombre de décideurs', ['Un seul expert', 'Plusieurs décideurs'], horizontal=True)
        nalt = st.radio('③ Nombre d’alternatives à évaluer', ['Plusieurs projets à classer', 'Un seul projet à accepter ou refuser'], horizontal=True)
    with c2:
        comp = st.radio('④ Compensation entre critères', ['Acceptée (un bon score compense un mauvais)', 'Refusée (sécurité, conformité…)'])
        effort = st.radio('⑤ Effort demandé pour les poids', ['Élevé (comparaisons par paires)', 'Faible', 'Nul (poids calculés)'])
    obj = st.selectbox('⑥ Objectif financier principal', list(OBJECTIVES))

    reco, why = [], []
    if effort.startswith('Élevé'):
        reco.append(('Pondération', 'AHP + ratio de cohérence', 'weights')); why.append('AHP exige n(n−1)/2 comparaisons mais fournit un test de cohérence (CR < 0,1).')
    elif effort.startswith('Faible'):
        reco.append(('Pondération', 'BWM', 'weights')); why.append('BWM ne demande que 2n−3 comparaisons (Best / Worst) et un programme linéaire.')
    else:
        reco.append(('Pondération', 'CRITIC ou Entropie', 'weights')); why.append('Aucune comparaison : les poids viennent des données (reproductible, mais ignore l’importance stratégique).')
    if nalt.startswith('Un seul'):
        reco.append(('Évaluation absolue', 'MAUT + seuil (expert ou ROC)', 'single')); why.append('Un projet isolé se compare à un seuil d’acceptation ; la courbe ROC n’est possible que si un historique étiqueté existe.')
    elif data.startswith('Jugements'):
        reco.append(('Classement', 'Fuzzy TOPSIS (agrégation des décideurs)' if dm.startswith('Plusieurs') else 'TOPSIS flou (nombres triangulaires)', 'fuzzy_mcdm'))
        reco.append(('Classement', 'IF-TOPSIS si les décideurs hésitent', 'fuzzy_mcdm'))
        why.append('Les évaluations linguistiques se modélisent par des nombres flous ; l’hésitation par des ensembles intuitionnistes.')
    elif comp.startswith('Acceptée'):
        reco += [('Classement', 'TOPSIS', 'additive'), ('Classement', 'WASPAS', 'additive'), ('Classement', 'VIKOR (solution de compromis)', 'additive')]
        why.append('Méthodes additives : un score global agrège les critères et un bon rendement peut compenser un risque élevé.')
    else:
        reco += [('Classement', 'ELECTRE III', 'outrank'), ('Classement', 'PROMETHEE II', 'outrank')]
        why.append('Sans compensation, les méthodes de surclassement (seuils, veto) interdisent qu’un excellent critère masque un défaut rédhibitoire.')
    if dm.startswith('Plusieurs') and not data.startswith('Jugements'):
        why.append('Plusieurs décideurs : agréger les matrices de poids (moyenne géométrique des jugements AHP) avant de classer.')
    why.append(OBJECTIVES[obj][0]); reco.append(('Objectif financier', obj, OBJECTIVES[obj][1]))
    reco.append(('Vérification', 'Comparer plusieurs méthodes (Spearman) puis analyser la sensibilité', 'compare'))
    why.append('Bonnes pratiques : appliquer plusieurs méthodes, tester la robustesse, justifier le choix.')

    kit.section('Recommandation')
    for stage, name, key in reco:
        a, b = st.columns([4, 1], vertical_alignment='center')
        with a:
            st.markdown(f'<div class="card teal" style="margin-bottom:8px"><div class="tag">{stage}</div><h4>{name}</h4></div>', unsafe_allow_html=True)
        with b:
            nav.link(key, 'Ouvrir →')
    kit.section('Pourquoi ces choix ?')
    for w in why:
        kit.callout(w, 'tip')
    st.session_state['method_profile'] = {'données': data, 'décideurs': dm, 'alternatives': nalt, 'compensation': comp,
                                          'pondération': effort, 'objectif': obj, 'recommandations': [n for _, n, _ in reco], 'justifications': why}

    kit.section('Catalogue des méthodes de l’application')
    df = pd.DataFrame(CATALOG, columns=['Méthode', 'Étape', 'Famille', 'Données', 'Principe', 'page'])
    st.dataframe(df.drop(columns='page'), hide_index=True, width='stretch')

    kit.section('Taxonomie MADM de référence')
    a, b, c, d = st.columns(4, gap='medium')
    with a:
        kit.card('Précision', 'Crisp / Fuzzy', 'Valeurs exactes ou préférences subjectives difficiles à chiffrer.', 'teal')
    with b:
        kit.card('Décideurs', 'Single / Group', 'Un expert, ou plusieurs avec stratégie d’agrégation.', 'accent')
    with c:
        kit.card('Alternatives', 'Une / plusieurs', 'Évaluation absolue (seuils) ou classement relatif.', 'blue')
    with d:
        kit.card('Étape', 'Poids / classement', 'Subjectif (AHP, BWM) ou objectif (CRITIC, entropie) ; additif ou surclassement.', 'amber')
