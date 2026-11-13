"""Analyse 6 — MCDM × IA : classification supervisée, XAI (Shapley) pour re-pondérer, LLM extracteur de scores."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine import ai
from engine.mcdm import rank, normalize_weights
from ui import kit, state, theme as T


def _tab_classif(p):
    kit.section('Scénario 1 — MCDM → étiquettes → apprentissage supervisé', 'Le MCDM produit des classes A/B/C/D ; un modèle apprend à les reproduire pour classer instantanément de nouvelles alternatives')
    kit.callout('La matrice de décision contient trop peu de lignes pour entraîner un modèle : l’application génère des alternatives **synthétiques** autour des valeurs observées (bruit gaussien), les étiquette avec le score MCDM puis entraîne le modèle. Les performances mesurent la capacité à **imiter le MCDM**, pas la réalité.', 'info')
    c1, c2, c3 = st.columns(3)
    name = c1.selectbox('Modèle', list(ai.CLASSIFIERS))
    n = c2.slider('Alternatives synthétiques', 100, 2000, 400, 100)
    seed = c3.number_input('Graine', 0, 999, 7, key='cl_seed')
    r = ai.train_classifier(p, name, n, seed=int(seed))
    kit.kpis([('Exactitude (test)', f'{100 * r["accuracy"]:.1f} %', f'{r["n_test"]} cas de test', T.TEAL), ('Entraînement', r['n_train'], 'alternatives synthétiques', T.BLUE),
              ('Seuils des classes', ' · '.join(f'{b:.2f}' for b in r['bounds']), 'A | B | C | D (quartiles du score)', T.AMBER)])
    a, b = st.columns(2, gap='large')
    with a:
        st.markdown('**Matrice de confusion (jeu de test)**')
        kit.heatmap(r['confusion'], [f'prédit {l}' for l in r['labels']], [f'réel {l}' for l in r['labels']], fmt='d', h=300)
    with b:
        st.markdown('**Alternatives du projet : classe MCDM**')
        st.dataframe(pd.DataFrame({'Alternative': p.alternatives, 'Score WSM': r['original_scores'], 'Classe': r['original_labels'],
                                   'Classe prédite': r['model'].predict(p.matrix)}).round(4), hide_index=True, width='stretch')
    kit.section('Prédire une nouvelle alternative')
    lo, hi = p.matrix.min(axis=0), p.matrix.max(axis=0)
    cols = st.columns(min(4, len(p.criteria)))
    x = np.array([cols[j % len(cols)].number_input(f'{c} ({"↑" if k == "max" else "↓"})', value=float((lo[j] + hi[j]) / 2), key=f'cl_x{j}') for j, (c, k) in enumerate(zip(p.criteria, p.kinds))])
    pred = r['model'].predict([x])[0]
    proba = dict(zip(r['model'].classes_, r['model'].predict_proba([x])[0])) if hasattr(r['model'], 'predict_proba') else {}
    true_s = float(ai.mcdm_score(x[None, :], p)[0])
    kit.callout(f'Classe prédite : **{pred}** · score MCDM direct : {true_s:.3f}' + (' · probabilités : ' + ', '.join(f'{k} {100 * v:.0f} %' for k, v in proba.items()) if proba else ''), 'ok')
    kit.course_note('Scénario 1', '**Avantages** : décision instantanée, apprentissage de règles non linéaires, automatisation. **Limites** : dépend du MCDM utilisé pour étiqueter (biais hérité), nécessite beaucoup d’exemples, explicabilité limitée sans XAI.')


def _tab_xai(p):
    kit.section('Scénario 2 — XAI pour mettre à jour les poids', 'Un modèle apprend le score MCDM ; les valeurs de Shapley mesurent l’influence réelle de chaque critère ; les poids sont recalibrés')
    c1, c2, c3 = st.columns(3)
    model = c1.selectbox('Modèle de régression', ['Random Forest', 'Gradient Boosting', 'Ridge (linéaire)'])
    alpha = c2.slider('α · confiance dans les poids initiaux', 0.0, 1.0, .6, .05, help='w_new = α·w_initial + (1−α)·part SHAP')
    n = c3.slider('Alternatives synthétiques', 100, 1000, 300, 100, key='xai_n')
    if len(p.criteria) > 10:
        st.error('Shapley exact limité à 10 critères.')
        return
    with st.spinner('Calcul des valeurs de Shapley exactes…'):
        r = ai.xai_reweight(p, p.weights, model, alpha, n)
    kit.kpis([('R² du modèle (test)', f'{r["r2"]:.3f}', 'fidélité au score MCDM', T.TEAL if r['r2'] > .8 else T.AMBER), ('Valeur de base', f'{r["base"]:.3f}', 'prédiction moyenne', T.BLUE),
              ('Critère le plus influent', p.criteria[int(np.argmax(r['global']))], f'{100 * r["share"].max():.0f} % de l’importance SHAP', T.ORANGE)])
    if r['r2'] < .6:
        kit.callout('Le modèle reproduit mal le score MCDM (R² faible) : les valeurs de Shapley sont peu fiables.', 'warn')
    a, b = st.columns(2, gap='large')
    with a:
        st.markdown('**Importance globale mean |φⱼ|**')
        kit.weights_chart(p.criteria, r['share'], 280)
    with b:
        st.markdown('**Poids initiaux vs recalibrés**')
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Initiaux', x=p.criteria, y=100 * p.weights, marker=dict(color=T.SLATE, cornerradius=4)))
        fig.add_trace(go.Bar(name='SHAP', x=p.criteria, y=100 * r['share'], marker=dict(color=T.AMBER, cornerradius=4)))
        fig.add_trace(go.Bar(name='Recalibrés', x=p.criteria, y=100 * r['w_new'], marker=dict(color=T.TEAL, cornerradius=4)))
        fig.update_layout(barmode='group'); fig.update_yaxes(title='%')
        kit.show(fig, 280)
    st.markdown('**Explication locale : contribution φⱼ de chaque critère à la prédiction de chaque alternative**')
    kit.heatmap(r['local'], p.criteria, p.alternatives, scale=T.DIV, fmt='.3f', h=max(280, 46 * len(p.alternatives) + 70), zmin=-np.abs(r['local']).max(), zmax=np.abs(r['local']).max())
    st.caption('Les valeurs de Shapley sont calculées exactement (toutes les coalitions de critères, 2ⁿ), sans bibliothèque externe.')
    kit.formula(r'w_j^{new}=\alpha\,w_j^{init}+(1-\alpha)\frac{\overline{|\varphi_j|}}{\sum_k\overline{|\varphi_k|}}')
    if st.button('✓ Utiliser les poids recalibrés', type='primary'):
        state.set_weights(r['w_new'], 'XAI-SHAP')
        st.success('Poids XAI-SHAP activés pour toutes les méthodes.')
        st.rerun()


def _tab_llm(p):
    kit.section('LLM comme extracteur de scores', 'Texte non structuré (CV, avis, rapport) → scores [0, 10] par critère → matrice de décision → MCDM')
    kit.callout('Chaîne : **texte T → LLM → scores s ∈ [0,10]ⁿ → normalisation → MCDM**. Ici aucun LLM n’est appelé : l’application génère le **prompt** à coller dans ton LLM favori et accepte sa réponse JSON. Un **simulateur à règles** permet de tester la chaîne hors-ligne.', 'info')
    rub = ai.DEFAULT_RUBRIC
    with st.expander('Rubrique des critères (modifiable)'):
        rb = st.data_editor(pd.DataFrame({'Critère': list(rub), 'Sens': [v['kind'] for v in rub.values()], 'Rubrique': [v['rubric'] for v in rub.values()]}), hide_index=True, disabled=['Critère'], key='llm_rub', width='stretch')
    crit = {r['Critère']: {**rub[r['Critère']], 'kind': r['Sens'], 'rubric': r['Rubrique']} for _, r in rb.iterrows()}
    nb = st.number_input('Nombre de candidats / documents', 1, 5, 2)
    cands = []
    for i in range(nb):
        txt = st.text_area(f'Texte {i + 1}', ai.SAMPLE_CV if i == 0 else 'Développeuse junior, 2 ans d’expérience en Python, stage en équipe. Prétentions : 38 000 €/an.', height=100, key=f'llm_t{i}')
        cands.append(txt)
    st.markdown('**Prompt à envoyer au LLM**')
    st.code(ai.build_prompt(cands[0], crit), language='text')
    mode = st.radio('Source des scores', ['Simulateur hors-ligne (règles)', 'Coller la réponse JSON du LLM (candidat 1)'], horizontal=True)
    results = []
    if mode.startswith('Simulateur'):
        results = [ai.simulate_extract(t, crit) for t in cands]
    else:
        raw = st.text_area('Réponse JSON du LLM', '{"scores": {"Expérience technique": 8, "Communication / leadership": 7, "Adéquation salariale": 3}, "justifications": {}}', height=110)
        try:
            results = [ai.parse_llm_json(raw, crit)] + [ai.simulate_extract(t, crit) for t in cands[1:]]
        except Exception as e:
            st.error('JSON invalide : ' + str(e))
            return
    df = pd.DataFrame([r['scores'] for r in results], index=[f'Candidat {i + 1}' for i in range(len(results))])
    st.markdown('**Scores extraits**')
    st.dataframe(df, width='stretch')
    for i, r in enumerate(results):
        if r['justifications']:
            with st.expander(f'Justifications — candidat {i + 1}'):
                for c, j in r['justifications'].items():
                    st.markdown(f'- **{c}** : {j}')
    if len(df) >= 2:
        from engine.mcdm import Problem
        kinds = ['max' if crit[c]['kind'] == 'max' else 'max' for c in df.columns]  # scores déjà orientés « plus grand = mieux »
        w = normalize_weights(np.ones(len(df.columns)))
        sub = Problem(list(df.index), list(df.columns), kinds, w, df.to_numpy(float))
        r = rank(sub, 'TOPSIS')
        st.markdown('**Classement TOPSIS des candidats** (scores inversés pour les critères de coût, poids égaux)')
        kit.bar_ranking(sub.alternatives, r['scores'], r['ranks'])
    kit.course_note('LLM', 'Le LLM sert de **module d’extraction**, pas de décideur. Points de vigilance de référence : biais du modèle, variabilité des réponses, nécessité d’une rubrique explicite et d’une validation humaine.')


def render():
    p = state.problem()
    kit.header('J · MCDM × INTELLIGENCE ARTIFICIELLE', 'Quand le MCDM rencontre l’IA',
               'Trois ponts entre aide à la décision et apprentissage automatique : automatiser le classement, expliquer les critères pour recalibrer les poids, et transformer du texte en scores.',
               ['Classification supervisée', 'XAI · Shapley', 'LLM extracteur'])
    kit.callout('**Lecture prudente.** Les classes A/B/C/D sont produites par le MCDM, pas observées dans la réalité : un modèle qui les reproduit n’apprend pas à prédire la réussite financière d’un projet. Les données d’entraînement sont **synthétiques** (générées autour de ta matrice).','warn')
    tabs = st.tabs(['Scénario 1 · Classification', 'Scénario 2 · XAI → poids', 'LLM · texte → scores'])
    with tabs[0]:
        _tab_classif(p)
    with tabs[1]:
        _tab_xai(p)
    with tabs[2]:
        _tab_llm(p)
    state.mark('ai')
