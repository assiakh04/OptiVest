"""Analyse 2d — Robustesse : sensibilité aux poids, Monte-Carlo, normalisation, Pareto."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine.mcdm import METHODS, pareto, rank, sensitivity, sweep_weight, ranks, spearman
from ui import kit, state, theme as T


def _params(method, key):
    kw = {}
    if method == 'VIKOR':
        kw['v'] = st.slider('v (VIKOR)', 0.0, 1.0, .5, .05, key=key + 'v')
    if method in ('WSM', 'WPM', 'WASPAS'):
        kw['norm'] = st.radio('Normalisation', ['ratio', 'minmax'], horizontal=True, key=key + 'n')
    return kw


def render():
    p = state.problem()
    kit.header('G · ROBUSTESSE', 'La décision tient-elle ?',
               'Les poids sont toujours un peu arbitraires. On les perturbe pour voir si le meilleur choix change : si oui, la décision est fragile.',
               ['Balayage d’un poids', 'Monte-Carlo', 'Normalisation', 'Front de Pareto'])
    method = st.selectbox('Méthode analysée', METHODS, index=3, key='rb_method')
    kw = _params(method, 'rb_')
    t1, t2, t3, t4 = st.tabs(['Balayage d’un poids', 'Monte-Carlo (tous les poids)', 'Effet de la normalisation', 'Pareto'])
    with t1:
        jsel = st.selectbox('Critère dont le poids varie', p.criteria)
        j = p.criteria.index(jsel)
        grid, S, R = sweep_weight(p, method, j, 41, **kw)
        fig = go.Figure()
        for i, a in enumerate(p.alternatives):
            fig.add_trace(go.Scatter(x=grid, y=R[:, i], name=a, mode='lines', line=dict(width=3, color=T.CAT[i % 8], shape='hv')))
        fig.add_vline(x=p.weights[j], line_dash='dot', line_color=T.INK, annotation_text='poids actuel')
        fig.update_yaxes(autorange='reversed', dtick=1, title='Rang'); fig.update_xaxes(title=f'Poids de « {jsel} »')
        kit.show(fig, 360)
        first = R == 1
        winners = [p.alternatives[int(np.argmax(f))] for f in first]
        changes = [grid[k] for k in range(1, len(grid)) if winners[k] != winners[k - 1]]
        if changes:
            kit.callout(f'Le n°1 change **{len(changes)} fois** quand le poids de « {jsel} » varie (premier basculement ≈ {changes[0]:.2f}). Décision sensible à ce critère.', 'warn')
        else:
            kit.callout(f'**{winners[0]}** reste n°1 sur tout l’intervalle de poids de « {jsel} » : décision robuste vis-à-vis de ce critère.', 'ok')
        rows = []
        for jj, c in enumerate(p.criteria):
            g, _, Rr = sweep_weight(p, method, jj, 21, **kw)
            top = [int(np.argmin(r_)) for r_ in Rr]
            rows.append({'Critère': c, 'Nombre de n°1 différents': len(set(top)), 'Robuste': len(set(top)) == 1})
        st.markdown('**Sensibilité critère par critère**')
        st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
    with t2:
        c1, c2, c3 = st.columns(3)
        n = c1.slider('Simulations', 50, 1000, 300, 50)
        conc = c2.slider('Concentration autour des poids actuels', 5, 200, 40, 5, help='Petite = poids très variables ; grande = faibles perturbations')
        seed = c3.number_input('Graine aléatoire', 0, 9999, 14)
        s = sensitivity(p, method, n, conc, int(seed), **kw)
        kit.kpis([('Vainqueur le plus fréquent', p.alternatives[int(np.argmax(s['win_rate']))], f'{100 * s["win_rate"].max():.0f} % des simulations', T.ORANGE),
                  ('Stabilité du n°1', 'Robuste' if s['win_rate'].max() >= .7 else 'Fragile', 'seuil : 70 %', T.GREEN if s['win_rate'].max() >= .7 else T.RED),
                  ('Alternatives qui gagnent au moins une fois', int((s['win_rate'] > 0).sum()), f'sur {len(p.alternatives)}', T.BLUE)])
        a, b = st.columns(2, gap='large')
        with a:
            st.markdown('**Matrice d’acceptabilité des rangs** (probabilité d’obtenir chaque rang)')
            kit.heatmap(100 * s['acceptability'], [f'Rang {r}' for r in range(1, len(p.alternatives) + 1)], p.alternatives, fmt='.0f', h=max(280, 46 * len(p.alternatives) + 70), zmin=0, zmax=100)
        with b:
            st.markdown('**Rang moyen ± écart-type**')
            fig = go.Figure(go.Bar(x=s['mean_rank'], y=p.alternatives, orientation='h', error_x=dict(array=s['rank_sd'], color=T.INK),
                                   marker=dict(color=T.TEAL, cornerradius=6)))
            fig.update_yaxes(autorange='reversed'); fig.update_xaxes(title='Rang moyen')
            kit.show(fig, max(280, 46 * len(p.alternatives) + 70), legend=False)
        with st.expander('Distribution des poids simulés'):
            fig = go.Figure()
            for j, c in enumerate(p.criteria):
                fig.add_trace(go.Box(y=100 * s['weights'][:, j], name=c, marker_color=T.CAT[j % 8]))
            fig.update_yaxes(title='Poids (%)')
            kit.show(fig, 300, legend=False)
        state.mark('robust')
    with t3:
        kit.section('La normalisation change-t-elle le classement ?', 'Compare ratio de référence, min-max et vecteur (TOPSIS) sur les mêmes poids')
        base = {}
        for nm in ('ratio', 'minmax'):
            for m in ('WSM', 'WPM', 'WASPAS'):
                base[f'{m} ({nm})'] = rank(p, m, norm=nm)['ranks']
        base['TOPSIS (vecteur)'] = rank(p, 'TOPSIS')['ranks']
        df = pd.DataFrame(base, index=p.alternatives)
        st.dataframe(kit.style_rank(df, list(df.columns)), width='stretch')
        rho = spearman(df['WSM (ratio)'], df['WSM (minmax)'])
        kit.callout(f'ρ de Spearman entre WSM-ratio et WSM-min-max : **{rho:.2f}**. ' + ('Le choix de normalisation est sans effet notable.' if rho >= .9 else 'La normalisation influence le classement : à justifier explicitement.'),
                    'ok' if rho >= .9 else 'warn')
    with t4:
        keep = pareto(p)
        kit.callout(f'**{int(keep.sum())}** alternative(s) non dominée(s). Une alternative dominée est battue sur tous les critères par une autre : elle ne peut gagner pour aucun jeu de poids.', 'info')
        c1, c2 = st.columns(2)
        cx = c1.selectbox('Axe X', p.criteria, index=0)
        cy = c2.selectbox('Axe Y', p.criteria, index=1)
        i, j = p.criteria.index(cx), p.criteria.index(cy)
        fig = go.Figure(go.Scatter(x=p.matrix[:, i], y=p.matrix[:, j], mode='markers+text', text=p.alternatives, textposition='top center',
                                   marker=dict(size=16, color=[T.TEAL if k else T.SLATE for k in keep], line=dict(color='#fff', width=2))))
        fig.update_xaxes(title=f'{cx} ({"↑ max" if p.kinds[i] == "max" else "↓ min"})', showgrid=True, gridcolor='#E6ECF3')
        fig.update_yaxes(title=f'{cy} ({"↑ max" if p.kinds[j] == "max" else "↓ min"})')
        kit.show(fig, 380, legend=False)
        st.dataframe(pd.DataFrame({'Alternative': p.alternatives, 'Non dominée': keep}), hide_index=True, width='stretch')
