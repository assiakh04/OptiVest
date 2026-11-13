"""Analyse 5 — MCDM floues : évaluation floue d'une alternative, Fuzzy TOPSIS (Chen), IF-TOPSIS."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine import fuzzy as F
from engine.mcdm import rank, spearman, utility
from ui import kit, state, theme as T

R_LEVELS, W_LEVELS, I_LEVELS = list(F.RATING_SCALE), list(F.WEIGHT_SCALE), list(F.IFN_SCALE)


def _fmt(t):
    return '(' + ', '.join(f'{x:g}' if abs(x) >= 10 else f'{x:.2f}' for x in t) + ')'


def _tab_single():
    kit.section('Évaluation floue d’une alternative', 'Pas de comparaison : on obtient un score flou agrégé puis défuzzifié, à comparer à un seuil')
    base = pd.DataFrame({'Critère': ['Coût (k€)', 'Délai (jours)'], 'a': [1.0, 110.0], 'b': [1.2, 120.0], 'c': [1.5, 130.0], 'Poids': [.6, .4]})
    st.caption('Exemple de référence : coûts triangulaires (1,0 ; 1,2 ; 1,5) et (110 ; 120 ; 130), poids 0,6 et 0,4. Modifie ou ajoute des critères.')
    ed = st.data_editor(base, num_rows='dynamic', hide_index=True, width='stretch', key='fs_tab')
    ed = ed.dropna()
    if ed.empty or (ed['a'] > ed['b']).any() or (ed['b'] > ed['c']).any() or ed['Poids'].sum() <= 0:
        st.error('Chaque ligne doit vérifier a ≤ b ≤ c, avec des poids positifs.')
        return
    r = F.fuzzy_single_eval(ed[['a', 'b', 'c']].to_numpy(float), ed['Poids'].to_numpy(float))
    kit.formula(r'\tilde r_j=\left(\tfrac{a_j}{c_j^{max}},\tfrac{b_j}{c_j^{max}},\tfrac{c_j}{c_j^{max}}\right)\;;\;\; \tilde S=\sum_j w_j\,\tilde r_j\;;\;\; S=\tfrac{a+b+c}{3}')
    thr = st.slider('Seuil d’acceptation sur le score défuzzifié', 0.0, 1.0, .8, .01)
    kit.kpis([('TFN agrégé S̃', _fmt(r['aggregate']), 'score flou', T.TEAL), ('Score défuzzifié', f'{r["score"]:.3f}', '(a+b+c)/3', T.ORANGE),
              ('Largeur (incertitude)', f'{r["width"]:.3f}', 'c − a', T.AMBER), ('Décision', 'ACCEPTER' if r['score'] >= thr else 'REFUSER', f'seuil {thr:.2f}', T.GREEN if r['score'] >= thr else T.RED)])
    st.dataframe(pd.DataFrame(r['normalized'], index=ed['Critère'], columns=['a/c_max', 'b/c_max', 'c/c_max']).round(3), width='stretch')
    fig = go.Figure()
    for k, (nm, v) in enumerate(zip(ed['Critère'], r['normalized'])):
        fig.add_trace(go.Scatter(x=list(v), y=[0, 1, 0], name=nm, line=dict(width=2, color=T.CAT[k % 8], dash='dot')))
    fig.add_trace(go.Scatter(x=list(r['aggregate']), y=[0, 1, 0], name='S̃ agrégé', fill='toself', line=dict(width=4, color=T.ORANGE), opacity=.7))
    fig.add_vline(x=thr, line_dash='dash', line_color=T.INK)
    fig.update_xaxes(title='Valeur normalisée'); fig.update_yaxes(title='μ')
    kit.show(fig, 320)


def _default_levels(p, K):
    u = utility(p)
    idx = np.rint(u * 6).astype(int)
    out = []
    for k in range(K):
        jit = np.zeros_like(idx) if k == 0 else (np.add.outer(np.arange(len(p.alternatives)), np.arange(len(p.criteria)) + k) % 3 - 1)
        out.append(np.clip(idx + jit * (k > 0), 0, 6))
    return out


def _dm_inputs(p, K, levels, default_idx, tag, weight_levels, wdef):
    ratings = []
    tabs = st.tabs([f'Décideur {k + 1}' for k in range(K)])
    for k, t in enumerate(tabs):
        with t:
            df = pd.DataFrame(default_idx[k], index=p.alternatives, columns=p.criteria)
            e = st.data_editor(df, key=f'fz_{tag}_r{k}_{hash(tuple(p.alternatives + p.criteria))}', width='stretch',
                               column_config={c: st.column_config.SelectboxColumn(options=levels, required=True) for c in p.criteria})
            ratings.append(e)
    st.markdown('**Importance des critères par décideur**')
    wdf = pd.DataFrame([[weight_levels[wdef[j]] for j in range(len(p.criteria))] for _ in range(K)], index=[f'Décideur {k + 1}' for k in range(K)], columns=p.criteria)
    we = st.data_editor(wdf, key=f'fz_{tag}_w{K}_{hash(tuple(p.criteria))}', width='stretch',
                        column_config={c: st.column_config.SelectboxColumn(options=weight_levels, required=True) for c in p.criteria})
    return ratings, we


def _tab_topsis(p):
    kit.section('Fuzzy TOPSIS de Chen (2000) — décision de groupe', 'Évaluations et poids en termes linguistiques → nombres triangulaires → TOPSIS flou')
    K = st.slider('Nombre de décideurs', 1, 5, 3, key='fz_K')
    c1, c2 = st.columns(2)
    with c1.expander('Échelle linguistique des évaluations'):
        st.dataframe(pd.DataFrame({'Terme': R_LEVELS, 'TFN': [_fmt(F.RATING_SCALE[l]) for l in R_LEVELS]}), hide_index=True)
    with c2.expander('Échelle linguistique de l’importance'):
        st.dataframe(pd.DataFrame({'Terme': W_LEVELS, 'TFN': [_fmt(F.WEIGHT_SCALE[l]) for l in W_LEVELS]}), hide_index=True)
    idx = _default_levels(p, K)
    wdef = np.clip(np.rint(p.weights / p.weights.max() * 6).astype(int), 0, 6)
    st.caption('Les évaluations initiales sont déduites de la matrice du projet (avec de légères divergences entre décideurs) : modifie-les librement.')
    ratings, we = _dm_inputs(p, K, R_LEVELS, [[[R_LEVELS[v] for v in row] for row in m] for m in idx], 'tp', W_LEVELS, wdef)
    R = np.array([[[F.RATING_SCALE[x] for x in row] for row in r.to_numpy()] for r in ratings], float)
    W = np.array([[F.WEIGHT_SCALE[x] for x in row] for row in we.to_numpy()], float)
    res = F.fuzzy_topsis(R, W, p.kinds)
    crisp = rank(p, 'TOPSIS')['ranks']
    rho = spearman(res['ranks'], crisp) if len(crisp) > 2 else 1.0
    kit.formula(r'\tilde r_{ij}=\left(\tfrac{a_{ij}}{c_j^*},\tfrac{b_{ij}}{c_j^*},\tfrac{c_{ij}}{c_j^*}\right)\;;\;\tilde v_{ij}=\tilde r_{ij}\otimes\tilde w_j\;;\;d(\tilde x,\tilde y)=\sqrt{\tfrac13\sum_k (x_k-y_k)^2}\;;\;CC_i=\frac{d_i^-}{d_i^-+d_i^*}')
    kit.kpis([('Meilleure alternative', p.alternatives[int(np.argmin(res['ranks']))], f'CCᵢ = {res["scores"].max():.4f}', T.ORANGE),
              ('Accord avec TOPSIS classique', f'{rho:.2f}', 'ρ de Spearman', T.TEAL if rho >= .7 else T.AMBER)])
    a, b = st.columns([1.1, 1], gap='large')
    with a:
        kit.bar_ranking(p.alternatives, res['scores'], res['ranks'], title='Coefficient de proximité CCᵢ')
    with b:
        df = pd.DataFrame({'Rang': res['ranks'], 'Alternative': p.alternatives, 'd*': res['D_plus'], 'd⁻': res['D_minus'], 'CC': res['scores'], 'Rang TOPSIS classique': crisp}).sort_values('Rang')
        st.dataframe(kit.style_rank(df, ['Rang', 'Rang TOPSIS classique']).format({'d*': '{:.3f}', 'd⁻': '{:.3f}', 'CC': '{:.4f}'}), hide_index=True, width='stretch')
    with st.expander('Détail des étapes'):
        st.markdown('**① Évaluations collectives (moyenne des décideurs)**')
        st.dataframe(pd.DataFrame([[_fmt(res['collective'][i, j]) for j in range(len(p.criteria))] for i in range(len(p.alternatives))], index=p.alternatives, columns=p.criteria), width='stretch')
        st.markdown('**② Poids collectifs**')
        st.dataframe(pd.DataFrame([[_fmt(w) for w in res['collective_weights']]], columns=p.criteria, index=['w̃']), width='stretch')
        st.markdown('**③ Matrice normalisée puis pondérée ṽᵢⱼ**')
        st.dataframe(pd.DataFrame([[_fmt(res['weighted'][i, j]) for j in range(len(p.criteria))] for i in range(len(p.alternatives))], index=p.alternatives, columns=p.criteria), width='stretch')
    kit.course_note('Fuzzy TOPSIS', 'Critère coût : r̃ = (a⁻/c, a⁻/b, a⁻/a) avec a⁻ = min des a. Solutions idéales floues v* = (1,1,1) et v⁻ = (0,0,0). Distance entre TFN : √(⅓Σ(xₖ−yₖ)²).')


def _tab_if(p):
    kit.section('TOPSIS flou intuitionniste (IF-TOPSIS)', 'Chaque jugement est un couple (μ, ν) ; l’hésitation π = 1 − μ − ν est prise en compte dans les distances')
    K = st.slider('Nombre de décideurs', 1, 5, 3, key='if_K')
    with st.expander('Échelle linguistique intuitionniste (modifiable)'):
        sc = st.data_editor(pd.DataFrame({'Terme': I_LEVELS, 'μ': [F.IFN_SCALE[l][0] for l in I_LEVELS], 'ν': [F.IFN_SCALE[l][1] for l in I_LEVELS]}), hide_index=True, disabled=['Terme'], key='if_scale')
    scale = {r['Terme']: (float(r['μ']), float(r['ν'])) for _, r in sc.iterrows()}
    if any(m + n_ > 1 + 1e-9 or m < 0 or n_ < 0 for m, n_ in scale.values()):
        st.error('Chaque terme doit vérifier μ + ν ≤ 1.')
        return
    u = utility(p)
    idx = np.rint((1 - u) * 5).astype(int)
    levels_default = []
    for k in range(K):
        jit = 0 if k == 0 else (np.add.outer(np.arange(len(p.alternatives)), np.arange(len(p.criteria)) + k) % 3 - 1)
        levels_default.append(np.clip(idx + jit, 0, 5))
    wdef = np.clip(5 - np.rint(p.weights / p.weights.max() * 5).astype(int), 0, 5)
    ratings, we = _dm_inputs(p, K, I_LEVELS, [[[I_LEVELS[v] for v in row] for row in m] for m in levels_default], 'if', I_LEVELS, wdef)
    sigma = [st.slider(f'Poids du décideur {k + 1}', .05, 1.0, 1 / K if False else .5, .05, key=f'if_s{k}') for k in range(K)] if K > 1 else [1.0]
    R = np.array([[[scale[x] for x in row] for row in r.to_numpy()] for r in ratings], float)
    W = np.array([[scale[x] for x in row] for row in we.to_numpy()], float)
    res = F.if_topsis(R, W, p.kinds, sigma)
    crisp = rank(p, 'TOPSIS')['ranks']
    rho = spearman(res['ranks'], crisp) if len(crisp) > 2 else 1.0
    kit.formula(r'D=\mathrm{IFWA}_\sigma(D^{(k)})\;;\; D'+"'"+r'=D\otimes W\;;\; S^{\pm}_i=\tfrac{1}{2n}\sum_j\left[(\Delta\mu)^2+(\Delta\nu)^2+(\Delta\pi)^2\right]\;;\; C_i=\frac{S_i^-}{S_i^-+S_i^+}')
    kit.kpis([('Meilleure alternative', p.alternatives[int(np.argmin(res['ranks']))], f'Cᵢ = {res["scores"].max():.4f}', T.ORANGE), ('Accord avec TOPSIS classique', f'{rho:.2f}', 'ρ de Spearman', T.TEAL if rho >= .7 else T.AMBER)])
    a, b = st.columns([1.1, 1], gap='large')
    with a:
        kit.bar_ranking(p.alternatives, res['scores'], res['ranks'], title='Indice de proximité Cᵢ')
    with b:
        df = pd.DataFrame({'Rang': res['ranks'], 'Alternative': p.alternatives, 'S⁺': res['S_plus'], 'S⁻': res['S_minus'], 'C': res['scores']}).sort_values('Rang')
        st.dataframe(kit.style_rank(df, ['Rang']).format({'S⁺': '{:.4f}', 'S⁻': '{:.4f}', 'C': '{:.4f}'}), hide_index=True, width='stretch')
    with st.expander('Détail : agrégation IFWA, matrice pondérée, solutions idéales'):
        st.markdown('**Matrice agrégée D (μ, ν)**')
        st.dataframe(pd.DataFrame([[_fmt(res['aggregated'][i, j]) for j in range(len(p.criteria))] for i in range(len(p.alternatives))], index=p.alternatives, columns=p.criteria), width='stretch')
        st.markdown('**Poids agrégés W et idéaux I⁺ / I⁻ (μ, ν, π)**')
        st.dataframe(pd.DataFrame({'W (μ, ν)': [_fmt(w) for w in res['weights']], 'I⁺': [_fmt(x) for x in res['I_plus']], 'I⁻': [_fmt(x) for x in res['I_minus']]}, index=p.criteria).T, width='stretch')


def render():
    p = state.problem()
    kit.header('I · FUZZY MCDM', 'Décider avec des jugements imprécis',
               'Quand les évaluations sont linguistiques (« bon », « moyennement important ») ou que les décideurs hésitent, on remplace les nombres exacts par des nombres flous.',
               ['Alternative unique floue', 'Fuzzy TOPSIS (Chen)', 'IF-TOPSIS', 'Décision de groupe'])
    tabs = st.tabs(['Alternative unique (TFN)', 'Fuzzy TOPSIS · groupe', 'IF-TOPSIS · intuitionniste'])
    with tabs[0]:
        _tab_single()
    with tabs[1]:
        _tab_topsis(p)
    with tabs[2]:
        _tab_if(p)
    state.mark('fuzzy_mcdm')
