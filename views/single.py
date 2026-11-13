"""Analyse 3 — Évaluer UNE alternative : MAUT, seuil de décision, ROC, distance à l'idéal."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine import single as S
from engine.mcdm import utility
from ui import kit, state, theme as T


def _gauge(score, thr):
    fig = go.Figure(go.Indicator(mode='gauge+number', value=score, number=dict(valueformat='.3f', font=dict(color=T.INK)),
                                 gauge=dict(axis=dict(range=[0, 1]), bar=dict(color=T.TEAL), bgcolor='#E8EEF5',
                                            steps=[dict(range=[0, thr], color='#FFE3D3'), dict(range=[thr, 1], color='#D6F2EF')],
                                            threshold=dict(line=dict(color=T.ORANGE, width=4), value=thr))))
    kit.show(fig, 250, legend=False)


def render():
    p = state.problem()
    kit.header('H · PROJET INDIVIDUEL', 'Évaluer une option isolée',
               'Pas de classement ici : on décide « accepter / refuser » en comparant un score à un seuil τ. '
               'Applications : crédit, recrutement, validation d’un modèle.',
               ['MAUT', 'Seuil expert', 'Seuil par ROC (Youden, distance)', 'Distance à l’idéal'])
    kit.section('Alternative évaluée', 'Bornes [x_min, x_max] de chaque critère et valeur observée')
    pick = st.selectbox('Partir d’une alternative du projet', ['(saisie libre)'] + p.alternatives)
    lo0, hi0 = p.matrix.min(axis=0), p.matrix.max(axis=0)
    span = hi0 - lo0
    vals0 = p.matrix[p.alternatives.index(pick)] if pick != '(saisie libre)' else (lo0 + hi0) / 2
    df = pd.DataFrame({'Critère': p.criteria, 'Sens': p.kinds, 'x_min': lo0 - .1 * span, 'x_max': hi0 + .1 * span, 'Valeur x': vals0, 'Poids': p.weights})
    ed = st.data_editor(df, hide_index=True, disabled=['Critère', 'Sens'], width='stretch', key='sg_' + pick + str(hash(tuple(p.criteria))))
    lo, hi, v, w = (ed[c].to_numpy(float) for c in ('x_min', 'x_max', 'Valeur x', 'Poids'))
    if np.any(hi <= lo) or w.sum() <= 0:
        st.error('Chaque x_max doit dépasser x_min, et la somme des poids doit être positive.')
        return
    w = w / w.sum()
    t1, t2, t3 = st.tabs(['MAUT & décision', 'Seuil appris : courbe ROC', 'Distance à l’idéal'])
    with t1:
        c1, c2 = st.columns(2)
        thr = c1.slider('Seuil d’acceptation τ (fixé par l’expert)', 0.0, 1.0, .65, .01)
        with c2:
            ca, cb, cc = st.columns(3)
            ga = ca.number_input('Classe A ≥', 0.0, 1.0, .8, .05)
            gb = cb.number_input('Classe B ≥', 0.0, 1.0, .6, .05)
            gc = cc.number_input('Classe C ≥', 0.0, 1.0, .4, .05)
        r = S.maut(v, lo, hi, p.kinds, w, thr, (ga, gb, gc))
        kit.formula(r'u_j=\frac{x_j-x_j^{min}}{x_j^{max}-x_j^{min}}\;(\text{bénéfice})\;;\; u_j=\frac{x_j-x_j^{max}}{x_j^{min}-x_j^{max}}\;(\text{coût})\;;\; S(A)=\sum_j w_j u_j')
        kit.kpis([('Score S(A)', f'{r["score"]:.3f}', f'seuil τ = {thr:.2f}', T.TEAL), ('Décision', 'ACCEPTER' if r['accepted'] else 'REFUSER', 'S ≥ τ ?', T.GREEN if r['accepted'] else T.RED),
                  ('Classe', r['class'], 'A > B > C > D', T.BLUE), ('Niveau de risque', r['risk'], 'déduit de la classe', T.ORANGE)])
        a, b = st.columns([1, 1.3], gap='large')
        with a:
            _gauge(r['score'], thr)
        with b:
            fig = go.Figure(go.Bar(x=p.criteria, y=r['contrib'], marker=dict(color=T.CAT[:len(p.criteria)], cornerradius=6), text=[f'{x:.3f}' for x in r['contrib']], textposition='outside'))
            fig.update_yaxes(title='wⱼ·uⱼ (contribution au score)')
            kit.show(fig, 250, legend=False)
        st.dataframe(pd.DataFrame({'Critère': p.criteria, 'Valeur': v, 'Utilité uⱼ': r['utility'], 'Poids': w, 'Contribution': r['contrib']}).round(4), hide_index=True, width='stretch')
    with t2:
        kit.section('Apprendre le seuil à partir de décisions passées', 'Pour chaque τ possible : TPR, FPR, distance au point idéal (0,1) et indice de Youden J = TPR − FPR')
        src = st.radio('Historique', ['Exemple de référence (6 dossiers)', 'Alternatives du projet (score MAUT)'], horizontal=True)
        if src.startswith('Exemple'):
            hist = pd.DataFrame({'Dossier': [f'A{i}' for i in range(1, 7)], 'Score': [.85, .78, .71, .69, .62, .54], 'Accepté (réel)': [1, 1, 1, 0, 0, 0]})
        else:
            u = utility(p)
            sc = u @ p.weights
            lab = (sc >= np.median(sc)).astype(int)
            hist = pd.DataFrame({'Dossier': p.alternatives, 'Score': sc.round(4), 'Accepté (réel)': lab})
        hist = st.data_editor(hist, hide_index=True, num_rows='dynamic', width='stretch', key='roc_hist' + src[:5],
                              column_config={'Accepté (réel)': st.column_config.SelectboxColumn(options=[0, 1], required=True)})
        hist = hist.dropna()
        if hist['Accepté (réel)'].nunique() < 2 or len(hist) < 3:
            st.warning('Il faut au moins 3 dossiers, dont des acceptés ET des refusés.')
        else:
            mode = st.radio('Seuils testés', ['Automatiques (milieux entre scores)', 'Liste personnalisée'], horizontal=True)
            ths = None
            if mode.startswith('Liste'):
                txt = st.text_input('Seuils séparés par des virgules', '0.75, 0.65, 0.60')
                try:
                    ths = [float(x) for x in txt.split(',') if x.strip()]
                except ValueError:
                    st.error('Seuils invalides.')
                    ths = None
            rows = S.roc_table(hist['Score'], hist['Accepté (réel)'], ths)
            crit = st.radio('Critère de choix', ['youden', 'distance', 'exactitude', 'coût'], horizontal=True,
                            format_func={'youden': 'Youden (max J)', 'distance': 'Distance min au point (0,1)', 'exactitude': 'Exactitude', 'coût': 'Coût asymétrique'}.get)
            cfp = cfn = 1.0
            if crit == 'coût':
                a, b = st.columns(2)
                cfp = a.number_input('Coût d’un faux positif (accepter un mauvais dossier)', 0.0, 100.0, 5.0)
                cfn = b.number_input('Coût d’un faux négatif (refuser un bon dossier)', 0.0, 100.0, 1.0)
            best = S.best_threshold(rows, crit, cfp, cfn)
            kit.kpis([('Seuil optimal τ*', f'{best["seuil"]:.3f}', 'selon le critère choisi', T.ORANGE), ('TPR / FPR', f'{best["TPR"]:.2f} / {best["FPR"]:.2f}', 'sensibilité / fausses alarmes', T.TEAL),
                      ('AUC', f'{S.auc(S.roc_table(hist["Score"], hist["Accepté (réel)"])):.3f}', 'pouvoir discriminant du score', T.BLUE)])
            a, b = st.columns([1, 1.1], gap='large')
            with a:
                full = S.roc_table(hist['Score'], hist['Accepté (réel)'])
                pts = sorted({(r['FPR'], r['TPR']) for r in full} | {(0, 0), (1, 1)})
                fig = go.Figure(go.Scatter(x=[q[0] for q in pts], y=[q[1] for q in pts], mode='lines', line=dict(color=T.TEAL, width=3), fill='tozeroy', fillcolor='rgba(10,143,139,.10)', name='ROC'))
                fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines', line=dict(color=T.SLATE, dash='dot'), name='hasard'))
                fig.add_trace(go.Scatter(x=[r['FPR'] for r in rows], y=[r['TPR'] for r in rows], mode='markers+text', text=[f'{r["seuil"]:.2f}' for r in rows], textposition='bottom right',
                                         marker=dict(size=10, color=T.AMBER, line=dict(color='#fff', width=2)), name='seuils testés'))
                fig.add_trace(go.Scatter(x=[best['FPR']], y=[best['TPR']], mode='markers', marker=dict(size=18, color=T.ORANGE, symbol='star', line=dict(color='#fff', width=2)), name='τ*'))
                fig.update_xaxes(title='FPR (faux positifs)', range=[-.02, 1.02]); fig.update_yaxes(title='TPR (vrais positifs)', range=[-.02, 1.05])
                kit.show(fig, 380)
            with b:
                tab = pd.DataFrame(rows).round(3)
                st.dataframe(tab, hide_index=True, width='stretch')
            kit.callout('Dans l’exemple de référence : τ = 0,75 → TPR 0,67, FPR 0, d = 0,33, J = 0,67 ; τ = 0,65 → TPR 1, FPR 0,33, d = 0,33, J = 0,67 ; τ = 0,60 → FPR 0,67, d = 0,67, J = 0,33. '
                        'Deux seuils sont ex æquo : le choix dépend du coût relatif des erreurs.', 'tip')
    with t3:
        kit.section('Distance à l’idéal (type TOPSIS)', 'C = D⁻ / (D⁺ + D⁻) ∈ [0, 1] : plus C est proche de 1, plus l’alternative ressemble à l’idéal')
        use_w = st.checkbox('Pondérer les distances par les poids', True)
        d = S.distance_to_ideal(v, lo, hi, p.kinds, w if use_w else None)
        kit.kpis([('D⁺ (à l’idéal)', f'{d["D_plus"]:.3f}', 'plus petit = mieux', T.TEAL), ('D⁻ (à l’anti-idéal)', f'{d["D_minus"]:.3f}', 'plus grand = mieux', T.BLUE), ('Indice C', f'{d["C"]:.3f}', 'proximité relative', T.ORANGE)])
        kit.radar(['Alternative évaluée', 'Idéal'], p.criteria, [list(d['u']), [1] * len(p.criteria)], [0, 1], 360)
    kit.course_note('Alternative unique', 'Un score S(A) = Σ wⱼuⱼ est comparé à un seuil τ. **Seuil expert** : fixé par règle métier. **Seuil appris** : on teste plusieurs τ sur un historique et on retient celui qui maximise J = TPR − FPR ou minimise d = √(FPR² + (1 − TPR)²).')
    state.mark('single')
