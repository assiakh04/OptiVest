"""Analyse 2b — Classement par méthodes additives : WSM, WPM, WASPAS, TOPSIS, VIKOR, AHP complet."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine.examples import AHP_CAR
from engine.mcdm import ahp, ahp_hierarchy, rank, ranks, utility
from ui import kit, state, theme as T


def _results_table(p, r, label):
    return kit.sorted_results(p, r, label)


def _contrib_chart(p, contrib, order_ranks):
    order = np.argsort(order_ranks, kind='stable')
    fig = go.Figure()
    for j, c in enumerate(p.criteria):
        fig.add_trace(go.Bar(y=np.array(p.alternatives)[order], x=contrib[order, j], name=c, orientation='h', marker=dict(color=T.CAT[j % 8])))
    fig.update_layout(barmode='stack')
    fig.update_yaxes(autorange='reversed', showgrid=False)
    kit.show(fig, max(260, 48 * len(order) + 70))


def _tab_ws(p):
    kit.section('Méthodes de pondération simple', 'WSM = somme pondérée · WPM = produit pondéré · WASPAS = combinaison des deux')
    c1, c2 = st.columns(2)
    norm = c1.radio('Normalisation', ['ratio', 'minmax'], horizontal=True,
                    format_func=lambda x: 'Ratio de référence (x/x⁺ ; x⁺/x)' if x == 'ratio' else 'Min-max', key='ws_norm')
    lam = c2.slider('λ · part du WSM dans WASPAS', 0.0, 1.0, .5, .05, key='ws_lam')
    kit.formula(r'Q_i^{(1)}=\sum_j w_j r_{ij}\quad;\quad Q_i^{(2)}=\prod_j r_{ij}^{\,w_j}\quad;\quad Q_i=\lambda Q_i^{(1)}+(1-\lambda)Q_i^{(2)}')
    ws, wp, wa = (rank(p, m, norm=norm, lam=lam) for m in ('WSM', 'WPM', 'WASPAS'))
    d = ws['details']
    best = np.array([p.matrix[:, j].max() if k == 'max' else p.matrix[:, j].min() for j, k in enumerate(p.kinds)])
    worst = np.array([p.matrix[:, j].min() if k == 'max' else p.matrix[:, j].max() for j, k in enumerate(p.kinds)])
    leader = p.alternatives[int(np.argmin(wa['ranks']))]
    kit.kpis([('En tête (WASPAS)', leader, f'Q = {wa["scores"].max():.4f}', T.ORANGE), ('Normalisation', d['normalization_mode'].split(' ')[0], d['normalization_mode'], T.TEAL),
              ('λ', f'{lam:.2f}', '1 = 100 % WSM · 0 = 100 % WPM', T.BLUE)])
    a, b = st.columns([1.1, 1], gap='large')
    with a:
        kit.section('Classement WASPAS')
        kit.bar_ranking(p.alternatives, wa['scores'], wa['ranks'])
    with b:
        kit.section('Les trois scores côte à côte')
        df = pd.DataFrame({'Alternative': p.alternatives, 'Q⁽¹⁾ WSM': ws['scores'], 'Rang WSM': ws['ranks'], 'Q⁽²⁾ WPM': wp['scores'],
                           'Rang WPM': wp['ranks'], 'Q WASPAS': wa['scores'], 'Rang WASPAS': wa['ranks']}).sort_values('Rang WASPAS')
        st.dataframe(kit.style_rank(df, ['Rang WSM', 'Rang WPM', 'Rang WASPAS']).format({c: '{:.4f}' for c in df.columns if c.startswith('Q')}),
                     hide_index=True, width='stretch')
        kit.download_csv(df, 'waspas.csv')
    t1, t2, t3 = st.tabs(['Étapes', 'Contributions des critères', 'Sensibilité à λ'])
    with t1:
        st.markdown('**① Solutions idéales positive x⁺ et négative x⁻**')
        st.dataframe(pd.DataFrame([best, worst], index=['x⁺ (meilleure)', 'x⁻ (pire)'], columns=p.criteria), width='stretch')
        st.markdown('**② Matrice normalisée rᵢⱼ**')
        st.dataframe(pd.DataFrame(d['normalization'], index=p.alternatives, columns=p.criteria).round(4), width='stretch')
    with t2:
        st.caption('Contribution wⱼ·rᵢⱼ de chaque critère au score WSM.')
        _contrib_chart(p, d['contributions'], ws['ranks'])
    with t3:
        grid = np.linspace(0, 1, 21)
        fig = go.Figure()
        for i, a_ in enumerate(p.alternatives):
            fig.add_trace(go.Scatter(x=grid, y=[g * ws['scores'][i] + (1 - g) * wp['scores'][i] for g in grid], name=a_, mode='lines',
                                     line=dict(width=3, color=T.CAT[i % 8])))
        fig.add_vline(x=lam, line_dash='dot', line_color=T.INK)
        fig.update_xaxes(title='λ'); fig.update_yaxes(title='Qᵢ')
        kit.show(fig, 340)
    kit.course_note('WSM / WPM / WASPAS', """
Normaliser : bénéfice rᵢⱼ = xᵢⱼ/x⁺ⱼ ; coût rᵢⱼ = x⁺ⱼ/xᵢⱼ. Puis **WSM** Qᵢ⁽¹⁾ = Σ wⱼ rᵢⱼ, **WPM** Qᵢ⁽²⁾ = Π rᵢⱼ^wⱼ, **WASPAS** (Zavadskas et al., 2012) Qᵢ = ½(Qᵢ⁽¹⁾+Qᵢ⁽²⁾) ou λQᵢ⁽¹⁾+(1−λ)Qᵢ⁽²⁾.""")


def _tab_topsis(p):
    kit.section('TOPSIS — Technique for Order Preference by Similarity to an Ideal Solution', 'Meilleure = la plus proche de l’idéal positif ET la plus éloignée de l’idéal négatif')
    r = rank(p, 'TOPSIS')
    d = r['details']
    kit.formula(r'r_{ij}=\frac{x_{ij}}{\sqrt{\sum_i x_{ij}^2}}\;;\; v_{ij}=w_j r_{ij}\;;\; S_i^{\pm}=\sqrt{\sum_j (v_j^{\pm}-v_{ij})^2}\;;\; RC_i^*=\frac{S_i^-}{S_i^-+S_i^+}')
    kit.kpis([('Meilleure alternative', p.alternatives[int(np.argmin(r['ranks']))], f'RC* = {r["scores"].max():.4f}', T.ORANGE),
              ('RC* le plus faible', f'{r["scores"].min():.4f}', p.alternatives[int(np.argmax(r['ranks']))], T.SLATE)])
    a, b = st.columns([1.1, 1], gap='large')
    with a:
        kit.bar_ranking(p.alternatives, r['scores'], r['ranks'])
    with b:
        fig = go.Figure(go.Scatter(x=d['D_plus'], y=d['D_minus'], mode='markers+text', text=p.alternatives, textposition='top center',
                                   marker=dict(size=[14 + 14 * s for s in r['scores']], color=[T.ORANGE if k == 1 else T.TEAL for k in r['ranks']],
                                               line=dict(color='#fff', width=2))))
        fig.update_xaxes(title='Distance à l’idéal positif S⁺ (plus petit = mieux)', showgrid=True, gridcolor='#E6ECF3')
        fig.update_yaxes(title='Distance à l’idéal négatif S⁻ (plus grand = mieux)')
        kit.show(fig, 330, legend=False)
    t1, t2, t3 = st.tabs(['① Normalisation & pondération', '② Idéaux', '③ Distances & proximité'])
    with t1:
        st.dataframe(pd.DataFrame(d['normalized'], index=p.alternatives, columns=p.criteria).round(4), width='stretch')
        st.markdown('**Matrice pondérée vᵢⱼ = wⱼ · rᵢⱼ**')
        st.dataframe(pd.DataFrame(d['weighted'], index=p.alternatives, columns=p.criteria).round(4), width='stretch')
    with t2:
        st.dataframe(pd.DataFrame([d['ideal'], d['anti_ideal']], index=['I⁺ (idéal positif)', 'I⁻ (idéal négatif)'], columns=p.criteria).round(4), width='stretch')
        st.caption('Pour un critère bénéfice : I⁺ = max, I⁻ = min ; l’inverse pour un critère coût.')
    with t3:
        df = pd.DataFrame({'Rang': r['ranks'], 'Alternative': p.alternatives, 'S⁺': d['D_plus'], 'S⁻': d['D_minus'], 'RC*': r['scores']}).sort_values('Rang')
        st.dataframe(kit.style_rank(df, ['Rang']).format({'S⁺': '{:.4f}', 'S⁻': '{:.4f}', 'RC*': '{:.4f}'}), hide_index=True, width='stretch')
        kit.download_csv(df, 'topsis.csv')


def _tab_vikor(p):
    kit.section('VIKOR — solution de compromis', 'Maximise l’utilité de groupe (S) tout en minimisant le regret individuel (R) · plus Q est PETIT, mieux c’est')
    v = st.slider('v · poids de la stratégie « utilité de groupe maximale »', 0.0, 1.0, .5, .05, key='vik_v')
    r = rank(p, 'VIKOR', v=v)
    d = r['details']
    cp = d['compromise']
    m = len(p.alternatives)
    kit.formula(r'S_i=\sum_j w_j\frac{x_j^*-x_{ij}}{x_j^*-x_j^-}\;;\; R_i=\max_j\left[w_j\frac{x_j^*-x_{ij}}{x_j^*-x_j^-}\right]\;;\; Q_i=v\frac{S_i-S^*}{S^--S^*}+(1-v)\frac{R_i-R^*}{R^--R^*}')
    a, b = st.columns([1.1, 1], gap='large')
    with a:
        kit.bar_ranking(p.alternatives, d['Q'], r['ranks'], title='Q (plus petit = meilleur)')
    with b:
        df = pd.DataFrame({'Alternative': p.alternatives, 'S': d['S'], 'R': d['R'], 'Q': d['Q'], 'Rang S': ranks(d['S'], False),
                           'Rang R': ranks(d['R'], False), 'Rang Q': r['ranks']}).sort_values('Rang Q')
        st.dataframe(kit.style_rank(df, ['Rang S', 'Rang R', 'Rang Q']).format({'S': '{:.4f}', 'R': '{:.4f}', 'Q': '{:.4f}'}), hide_index=True, width='stretch')
        kit.download_csv(df, 'vikor.csv')
    kit.section('Conditions d’acceptation de la solution de compromis')
    A1, A2 = p.alternatives[cp['best']], p.alternatives[cp['second']]
    c1, c2 = st.columns(2)
    with c1:
        kit.callout(f'**C1 · Avantage acceptable** : Q({A2}) − Q({A1}) = {cp["gap"]:.3f} ' + ('≥' if cp['C1'] else '<') + f' 1/(m−1) = {cp["DQ"]:.3f}', 'ok' if cp['C1'] else 'warn')
    with c2:
        kit.callout(f'**C2 · Stabilité** : {A1} est ' + ('aussi la meilleure' if cp['C2'] else 'pas la meilleure') + ' selon S et R.', 'ok' if cp['C2'] else 'warn')
    names = [p.alternatives[k] for k in cp['set']]
    if len(names) == 1:
        kit.callout(f'**Solution de compromis : {names[0]}** (les deux conditions sont satisfaites).', 'ok')
    else:
        kit.callout('**Ensemble de solutions de compromis : ' + ', '.join(names) + '**. Une négociation entre décideurs est nécessaire.', 'warn')
    with st.expander('Valeurs de référence x* et x⁻ et termes wⱼ(x*−x)/(x*−x⁻)'):
        st.dataframe(pd.DataFrame([d['best'], d['worst']], index=['x* (meilleure)', 'x⁻ (pire)'], columns=p.criteria), width='stretch')
        st.dataframe(pd.DataFrame(d['terms'], index=p.alternatives, columns=p.criteria).round(4), width='stretch')
    grid = np.linspace(0, 1, 21)
    q_grid = np.array([rank(p, 'VIKOR', v=g)['scores'] for g in grid])
    fig = go.Figure()
    for i, a_ in enumerate(p.alternatives):
        fig.add_trace(go.Scatter(x=grid, y=q_grid[:, i], name=a_, line=dict(width=3, color=T.CAT[i % 8])))
    fig.add_vline(x=v, line_dash='dot', line_color=T.INK)
    fig.update_xaxes(title='v'); fig.update_yaxes(title='Q')
    st.markdown('**Sensibilité du Q au paramètre v**')
    kit.show(fig, 300)
    kit.course_note('VIKOR', """
Classer par S, R et Q (croissant). A′ = meilleure en Q est la solution de compromis si **C1** Q(A″) − Q(A′) ≥ 1/(m−1) et **C2** A′ est aussi la meilleure en S et en R (énoncé de référence).
Sinon : {A′, A″} si seule C2 échoue ; {A′, …, Aₖ} avec Q(Aₖ) − Q(A′) < 1/(m−1) si C1 échoue.""")


def _saaty_from_data(u):
    m = len(u)
    a = np.ones((m, m))
    for i in range(m):
        for j in range(m):
            d = u[i] - u[j]
            a[i, j] = 1 + 8 * d if d >= 0 else 1 / (1 + 8 * (-d))
    return a


def _tab_ahp(p):
    kit.section('AHP complet — hiérarchie objectif › critères › alternatives', 'Priorités locales des alternatives par critère, puis priorités finales Σⱼ wⱼ·wⱼᵢ')
    src = st.radio('Cas traité', ['Projet courant', 'Exemple de référence (achat d’une voiture)'], horizontal=True, key='ahpf_src')
    sample = src.startswith('Exemple')
    if sample:
        crit, alts = AHP_CAR['criteria'], AHP_CAR['alternatives']
        cm0 = np.array(AHP_CAR['criteria_matrix'], float)
        alt0 = [np.array(m_, float) for m_ in AHP_CAR['alt_matrices']]
        tag = 's'
    else:
        crit, alts = p.criteria, p.alternatives
        w0 = np.clip(p.weights / p.weights.max(), 1e-3, None)
        cm0 = np.clip(w0[:, None] / w0[None, :], 1 / 9, 9)
        u = utility(p)
        alt0 = [_saaty_from_data(u[:, j]) for j in range(len(crit))]
        tag = str(hash(tuple(p.criteria + p.alternatives)))
    if len(crit) > 10 or len(alts) > 10:
        st.error('AHP complet : limité à 10 critères et 10 alternatives (table RI de référence).')
        return
    if not sample:
        mode = st.radio('Poids des critères', ['Poids actifs de l’application', 'Matrice de comparaison AHP des critères'], horizontal=True, key='ahpf_mode')
    else:
        mode = 'Matrice de comparaison AHP des critères'
    if mode.startswith('Matrice'):
        st.markdown('**① Comparaison par paires des critères**')
        cm = kit.matrix_editor('ahpm_cm_' + tag, crit, cm0)
    else:
        cm = None
    st.markdown('**② Comparaison par paires des alternatives, critère par critère**')
    if not sample:
        st.caption('Valeurs initiales déduites des données (écart d’utilité min-max traduit sur l’échelle de Saaty 1–9) : modifie-les selon ton jugement d’expert.')
    alt_m = []
    for j, c in enumerate(crit):
        with st.expander(f'Critère « {c} »', expanded=(j == 0 and sample)):
            alt_m.append(kit.matrix_editor(f'ahpm_alt_{tag}_{j}', alts, alt0[j]))
    try:
        if cm is None:
            cm_use = np.ones((len(crit), len(crit)))
            w = p.weights
            # on fabrique une matrice cohérente à partir des poids pour réutiliser ahp_hierarchy
            cm_use = w[:, None] / w[None, :]
        else:
            cm_use = cm
        h = ahp_hierarchy(cm_use, alt_m)
        wts = h['criteria']['weights'] if cm is not None else p.weights
        final = h['local'] @ wts
        rk = ranks(final)
        kit.section('Résultats')
        bad = [crit[j] for j, c in enumerate(h['checks']) if not c['consistent']]
        kit.kpis([('Meilleure alternative', alts[int(np.argmin(rk))], f'priorité finale {final.max():.4f}', T.ORANGE),
                  ('CR des critères', f'{h["criteria"]["cr"]:.3f}' if cm is not None else '—', 'matrice cohérente' if (cm is None or h['criteria']['consistent']) else 'à revoir',
                   T.GREEN if (cm is None or h['criteria']['consistent']) else T.RED),
                  ('Matrices incohérentes', len(bad), ', '.join(bad) if bad else 'toutes CR < 0,1', T.GREEN if not bad else T.RED)])
        if bad:
            kit.callout('Certaines matrices d’alternatives ont un CR ≥ 0,1 : ' + ', '.join(bad) + '.', 'warn')
        a, b = st.columns([1, 1.1], gap='large')
        with a:
            kit.bar_ranking(alts, final, rk)
        with b:
            loc = pd.DataFrame(h['local'], index=alts, columns=crit).round(4)
            loc.loc['Poids du critère'] = np.round(wts, 4)
            st.markdown('**Priorités locales wⱼᵢ et poids wⱼ**')
            st.dataframe(loc, width='stretch')
            st.dataframe(pd.DataFrame({'Rang': rk, 'Alternative': alts, 'Priorité finale': final}).sort_values('Rang'), hide_index=True, width='stretch')
        cr_df = pd.DataFrame({'Critère': crit, 'λmax': [c['lambda_max'] for c in h['checks']], 'CI': [c['ci'] for c in h['checks']],
                              'CR': [c['cr'] for c in h['checks']], 'Cohérent': [c['consistent'] for c in h['checks']]})
        with st.expander('Tests de cohérence des matrices d’alternatives'):
            st.dataframe(cr_df.round(4), hide_index=True, width='stretch')
        # analyse de sensibilité
        kit.section('Analyse de sensibilité (étape 5 de référence)', 'On fait varier le poids d’un critère de 0 à 1 ; les autres restent proportionnels')
        jsel = st.selectbox('Critère à faire varier', crit, key='ahpf_sens_' + tag)
        j = crit.index(jsel)
        grid = np.linspace(0, 1, 21)
        others = wts.copy(); others[j] = 0
        base = others / others.sum()
        fig = go.Figure()
        curves = []
        for g in grid:
            wv = base * (1 - g); wv[j] = g
            curves.append(h['local'] @ wv)
        curves = np.array(curves)
        for i, a_ in enumerate(alts):
            fig.add_trace(go.Scatter(x=grid, y=curves[:, i], name=a_, line=dict(width=3, color=T.CAT[i % 8])))
        fig.add_vline(x=wts[j], line_dash='dot', line_color=T.INK, annotation_text='poids actuel')
        fig.update_xaxes(title=f'Poids de « {jsel} »'); fig.update_yaxes(title='Priorité finale')
        kit.show(fig, 330)
        switch = [g for k_, g in enumerate(grid[1:], 1) if np.argmax(curves[k_]) != np.argmax(curves[k_ - 1])]
        if switch:
            kit.callout(f'Le meilleur choix change quand le poids de « {jsel} » passe par ≈ {switch[0]:.2f} : décision sensible à ce critère.', 'warn')
        else:
            kit.callout(f'Le meilleur choix reste **{alts[int(np.argmax(final))]}** quel que soit le poids de « {jsel} » (décision robuste vis-à-vis de ce critère).', 'ok')
        if not sample:
            st.session_state.ahp_result = {'ranks': rk.tolist(), 'scores': final.tolist(), 'alts': list(alts)}
            state.mark('ahp')
    except Exception as e:
        st.error(str(e))


def render():
    p = state.problem()
    kit.header('F · CLASSEMENT MULTICRITÈRE', 'Méthodes additives (compensatoires)',
               'Un score global agrège les critères : un bon score peut en compenser un mauvais. Applique WSM, WPM, WASPAS, TOPSIS, VIKOR ou AHP complet et détaille chaque étape.',
               ['WSM', 'WPM', 'WASPAS', 'TOPSIS', 'VIKOR', 'AHP'])
    kit.beginner_tip(f'Poids utilisés : **{st.session_state.weight_source}**. Change-les dans la page Pondération : tous les classements se mettent à jour.')
    tabs = st.tabs(['WSM · WPM · WASPAS', 'TOPSIS', 'VIKOR', 'AHP complet'])
    with tabs[0]:
        _tab_ws(p)
    with tabs[1]:
        _tab_topsis(p)
    with tabs[2]:
        _tab_vikor(p)
    with tabs[3]:
        _tab_ahp(p)
    state.mark('additive')
