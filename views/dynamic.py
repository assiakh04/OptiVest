"""Analyse 6 — MCDM dynamique : prévision des critères à t+1 puis classement."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine import dynamic as D
from engine.mcdm import Problem, normalize_weights, rank, METHODS
from ui import kit, state, theme as T


def render():
    kit.header('K · MCDM DYNAMIQUE', 'Décider sur le futur, pas sur le passé',
               'Les critères évoluent dans le temps : on prévoit chaque critère à t+1 (série temporelle), on reconstruit la matrice de décision prévue, puis on applique un MCDM. '
               'Application type : sélection d’actions en finance.',
               ['Prévision à t+1', 'Rendement · volatilité · liquidité', 'Propagation des erreurs', 'Volatilité EWMA'])
    kit.callout('**Modèles réellement implémentés** : tendance linéaire, lissage de Holt, autorégressif AR(p), moyenne mobile, volatilité EWMA et propagation d’erreur de prévision. ARIMA, LSTM et GARCH sont cités comme pistes de la littérature mais ne sont **pas** implémentés. Les séries sont **simulées** (graine reproductible), pas des cours de marché réels.','info')
    c1, c2, c3 = st.columns(3)
    T_ = c1.slider('Historique (mois)', 24, 96, 48, 6)
    seed = c2.number_input('Graine de simulation', 0, 999, 11)
    h = c3.slider('Horizon de prévision (mois)', 1, 6, 1)
    series = D.simulate_assets(T_, int(seed))
    alts = list(series)
    crits = list(next(iter(series.values())))
    kit.section('Séries temporelles simulées', 'Trois actions fictives — les niveaux de départ reprennent l’exemple de référence (rendement 8/6/7, volatilité 0,25/0,15/0,20, liquidité 100/80/120)')
    crit_sel = st.selectbox('Critère affiché', crits)
    fig = go.Figure()
    for i, a in enumerate(alts):
        fig.add_trace(go.Scatter(y=series[a][crit_sel], name=a, line=dict(width=3, color=T.CAT[i])))
    fig.update_xaxes(title='mois'); fig.update_yaxes(title=crit_sel)
    kit.show(fig, 300)

    kit.section('Méthode de prévision par critère')
    cols = st.columns(len(crits))
    methods = {c: cols[k].selectbox(c, D.FORECASTERS, index=1 if k == 0 else 2 if k == 1 else 0, key=f'dyn_m{k}') for k, c in enumerate(crits)}
    a_, c_, X = D.decision_matrix_forecast(series, methods, h)
    last = np.array([[series[a][c][-1] for c in crits] for a in alts])
    kit.section('Matrice de décision prévue (t+h)')
    st.dataframe(pd.DataFrame({'Alternative': alts, **{f'{c} (t)': last[:, j] for j, c in enumerate(crits)}, **{f'{c} (t+{h})': X[:, j] for j, c in enumerate(crits)}}).round(3), hide_index=True, width='stretch')

    kinds = ['max', 'min', 'max']
    st.markdown('**Sens et poids**')
    cw = st.columns(len(crits))
    ws = [cw[j].slider(f'Poids · {c} ({"↑" if kinds[j] == "max" else "↓"})', 0, 100, [50, 30, 20][j], key=f'dyn_w{j}') for j, c in enumerate(crits)]
    method = st.selectbox('Méthode MCDM', METHODS, index=3, key='dyn_method')
    if sum(ws) == 0:
        st.warning('Au moins un poids > 0.')
        return
    w = normalize_weights(ws)
    pf = Problem(alts, crits, kinds, w, X)
    pn = Problem(alts, crits, kinds, w, last)
    rf, rn = rank(pf, method), rank(pn, method)
    kit.kpis([('Meilleur choix aujourd’hui', alts[int(np.argmin(rn['ranks']))], 'matrice observée à t', T.SLATE), (f'Meilleur choix à t+{h}', alts[int(np.argmin(rf['ranks']))], 'matrice prévue', T.ORANGE),
              ('Changement de leader', 'Oui' if np.argmin(rn['ranks']) != np.argmin(rf['ranks']) else 'Non', 'décision statique vs dynamique', T.TEAL)])
    a, b = st.columns(2, gap='large')
    with a:
        kit.bar_ranking(alts, rn['scores'], rn['ranks'], title='Classement à t (statique)')
    with b:
        kit.bar_ranking(alts, rf['scores'], rf['ranks'], title=f'Classement prévu à t+{h} (dynamique)')

    kit.section('Limite de référence : propagation de l’erreur de prévision', 'Une erreur de prévision biaise la matrice, donc le classement : on simule des erreurs et on mesure la stabilité du n°1')
    err = st.slider('Erreur relative de prévision (écart-type)', 0.0, 0.5, .10, .01)
    wins, _ = D.error_propagation(pf, method, [err] * len(crits), 300, rank_fn=rank)
    fig = go.Figure(go.Bar(x=alts, y=100 * wins, marker=dict(color=[T.ORANGE if k == wins.max() else T.TEAL for k in wins], cornerradius=6), text=[f'{100 * x:.0f} %' for x in wins], textposition='outside'))
    fig.update_yaxes(title='% de simulations où l’action est n°1', range=[0, 110])
    kit.show(fig, 280, legend=False)
    kit.callout('Le leader prévu reste le n°1 dans **%.0f %%** des simulations.' % (100 * wins.max()) + (' Décision stable.' if wins.max() >= .7 else ' Décision fragile : améliorer la prévision ou élargir le choix.'), 'ok' if wins.max() >= .7 else 'warn')

    with st.expander('Volatilité EWMA (cas particulier de GARCH)'):
        a_sel = st.selectbox('Action', alts, key='dyn_ewma')
        ret = series[a_sel]['Rendement (%)']
        ew = D.ewma_volatility(ret, st.slider('λ (RiskMetrics = 0,94)', .8, .99, .94, .01))
        fig = go.Figure(go.Scatter(y=ew, line=dict(color=T.ORANGE, width=3), name='σ EWMA'))
        kit.show(fig, 240, legend=False)
    kit.course_note('MCDM dynamique', 'Pipeline : **séries temporelles → prévision (modèles statistiques ou ML) → matrice de décision à t+1 → MCDM**. Ici : tendance linéaire, lissage de Holt, AR(p), moyenne mobile ; la volatilité vient d’un modèle EWMA (GARCH non implémenté). Limites : erreurs de prévision qui se propagent, dépendance aux données historiques.')
    state.mark('dynamic')
