"""Analyse 4 — Laboratoire de logique floue."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine import fuzzy as F
from ui import kit, state, theme as T


def _fmt(t, d=3):
    return '(' + ', '.join(f'{x:.{d}f}' for x in t) + ')'


def _pair(label, mu_default, key, q=1.0):
    """Curseurs (μ, ν) valides : ν ≤ (1 − μ^q)^(1/q)."""
    mu = st.slider(f'{label} · μ (appartenance)', 0.0, 1.0, mu_default[0], .01, key=key + 'm')
    nu_max = float(np.floor((1 - mu ** q) ** (1 / q) * 100) / 100)
    nu = st.slider(f'{label} · ν (non-appartenance)', 0.0, max(nu_max, .01), min(mu_default[1], nu_max), .01, key=key + 'n')
    return mu, nu


def _tab_sets():
    kit.section('Ensemble flou classique', 'μ_A : X → [0, 1] — un élément appartient « un peu, beaucoup, pas du tout »')
    kinds = ['Trapézoïdale', 'Triangulaire', 'Gaussienne']
    c1, c2 = st.columns([1, 2], gap='large')
    with c1:
        preset = st.selectbox('Exemple de référence : « Âge moyen »', ['Âge moyen', 'Jeune', 'Âgé', 'Personnalisé'])
        defaults = {'Âge moyen': ('Trapézoïdale', (20, 30, 50, 60)), 'Jeune': ('Trapézoïdale', (0, 0, 20, 35)), 'Âgé': ('Trapézoïdale', (45, 65, 100, 100)), 'Personnalisé': ('Triangulaire', (10, 40, 70))}
        kind0, par0 = defaults[preset]
        kind = st.selectbox('Fonction d’appartenance', kinds, index=kinds.index(kind0), key='fl_kind' + preset)
        if kind == 'Trapézoïdale':
            pr = [st.number_input(l, value=float(par0[i] if len(par0) == 4 else [10, 30, 50, 70][i]), key=f'fl_t{i}{preset}') for i, l in enumerate('abcd')]
        elif kind == 'Triangulaire':
            pr = [st.number_input(l, value=float(par0[i] if len(par0) == 3 else [20, 40, 60][i]), key=f'fl_g{i}{preset}') for i, l in enumerate('abc')]
        else:
            pr = [st.number_input('Moyenne m', value=40.0, key='fl_gm'), st.number_input('Écart-type σ', value=12.0, min_value=.1, key='fl_gs')]
        alpha = st.slider('Niveau α pour l’α-coupe', 0.0, 1.0, .5, .05)
        x_val = st.slider('Évaluer μ(x) en x =', 0.0, 100.0, 35.0, 1.0)
    x = np.linspace(0, 100, 1001)
    mu = F.membership(kind, x, pr)
    props = F.fuzzy_set_properties(x, mu, alpha)
    with c2:
        fig = go.Figure(go.Scatter(x=x, y=mu, mode='lines', line=dict(color=T.TEAL, width=4), fill='tozeroy', fillcolor='rgba(10,143,139,.12)', name='μ(x)'))
        fig.add_hline(y=alpha, line_dash='dot', line_color=T.ORANGE, annotation_text=f'α = {alpha}')
        if props['alpha_cut']:
            fig.add_vrect(x0=props['alpha_cut'][0], x1=props['alpha_cut'][1], fillcolor=T.ORANGE, opacity=.12, line_width=0)
        mv = float(F.membership(kind, np.array([x_val]), pr)[0])
        fig.add_trace(go.Scatter(x=[x_val], y=[mv], mode='markers+text', text=[f'μ = {mv:.2f}'], textposition='top center', marker=dict(size=13, color=T.ORANGE), name='x'))
        fig.update_xaxes(title='Univers X (ex. âge)'); fig.update_yaxes(range=[0, 1.1], title='μ(x)')
        kit.show(fig, 330, legend=False)
    fmt = lambda r: '—' if r is None else f'[{r[0]:.1f} ; {r[1]:.1f}]'
    kit.kpis([('Hauteur', f'{props["height"]:.2f}', 'normalisé' if props['normalized'] else 'sous-normalisé', T.TEAL), ('Support {μ > 0}', fmt(props['support']), '', T.BLUE),
              ('Noyau {μ = 1}', fmt(props['kernel']), '', T.ORANGE), (f'α-coupe (α={alpha})', fmt(props['alpha_cut']), '', T.AMBER), ('Convexe', 'Oui' if props['convex'] else 'Non', 'μ quasi-concave', T.SLATE)])
    kit.section('Opérations sur deux ensembles', 'Complément 1 − μ · union max · intersection min (opérateurs de Zadeh)')
    j_mu = F.membership('Trapézoïdale', x, (0, 0, 20, 35))
    o_mu = F.membership('Trapézoïdale', x, (45, 65, 100, 100))
    other = st.selectbox('Second ensemble B', ['Jeune', 'Âgé'], key='fl_other')
    mb = j_mu if other == 'Jeune' else o_mu
    fig = go.Figure()
    for name, y, col, dash in [('A', mu, T.TEAL, 'solid'), ('B', mb, T.BLUE, 'solid'), ('A ∪ B (max)', F.fuzzy_union(mu, mb), T.ORANGE, 'dash'),
                               ('A ∩ B (min)', F.fuzzy_intersection(mu, mb), T.AMBER, 'dash'), ('non A', F.complement(mu), T.RED, 'dot')]:
        fig.add_trace(go.Scatter(x=x, y=y, name=name, line=dict(color=col, width=3, dash=dash)))
    kit.show(fig, 300)


def _tab_numbers():
    kit.section('Nombres flous trapézoïdaux (a, b, c, d)', 'Un nombre flou triangulaire est le cas particulier b = c')
    c1, c2 = st.columns(2)
    A = tuple(c1.number_input(f'A · {l}', value=v, key='fa' + l) for l, v in zip('abcd', (1.0, 2.0, 3.0, 4.0)))
    B = tuple(c2.number_input(f'B · {l}', value=v, key='fb' + l) for l, v in zip('abcd', (2.0, 3.0, 3.5, 5.0)))
    lam = st.slider('Scalaire λ', 0.0, 5.0, 2.0, .1)
    ops = {'A ⊕ B': F.tfn_add(A, B), 'A ⊖ B': F.tfn_sub(A, B), 'A ⊗ B': F.tfn_mul(A, B), 'λ·A': F.tfn_scale(lam, A)}
    if min(B) > 0:
        ops['A ⊘ B'] = F.tfn_div(A, B)
    st.dataframe(pd.DataFrame({'Opération': list(ops), 'Résultat (a, b, c, d)': [_fmt(v) for v in ops.values()], 'Défuzzifié (moyenne)': [round(F.defuzzify(v), 3) for v in ops.values()]}), hide_index=True, width='stretch')
    sel = st.multiselect('Tracer', ['A', 'B'] + list(ops), default=['A', 'B', 'A ⊕ B'])
    allv = {'A': A, 'B': B, **ops}
    fig = go.Figure()
    for k, nm in enumerate(sel):
        v = allv[nm]
        fig.add_trace(go.Scatter(x=[v[0], v[1], v[2], v[3]], y=[0, 1, 1, 0], name=nm, mode='lines', line=dict(width=3, color=T.CAT[k % 8]), fill='toself', opacity=.55))
    fig.update_yaxes(title='μ')
    kit.show(fig, 320)
    kit.section('Nombres d’intervalle [aᴸ, aᵁ]')
    d1, d2 = st.columns(2)
    I = (d1.number_input('A · borne basse', value=1.0, key='ia1'), d1.number_input('A · borne haute', value=3.0, key='ia2'))
    J = (d2.number_input('B · borne basse', value=2.0, key='ib1'), d2.number_input('B · borne haute', value=5.0, key='ib2'))
    if I[0] > I[1] or J[0] > J[1]:
        st.error('Borne basse ≤ borne haute requise.')
        return
    rows = {'A + B': F.int_add(I, J), 'A − B': F.int_sub(I, J), 'A × B': F.int_mul(I, J), 'λ·A': F.int_scale(lam, I)}
    try:
        rows['A ÷ B'] = F.int_div(I, J)
    except ValueError:
        pass
    st.dataframe(pd.DataFrame({'Opération': list(rows), 'Intervalle': [f'[{v[0]:.3f} ; {v[1]:.3f}]' for v in rows.values()], 'Centre': [F.int_center(v) for v in rows.values()], 'Demi-largeur': [F.int_width(v) for v in rows.values()]}).round(3), hide_index=True, width='stretch')


def _tab_ifs():
    kit.section('Ensembles flous intuitionnistes (Atanassov)', 'α = (μ, ν) avec μ + ν ≤ 1 · hésitation π = 1 − μ − ν')
    c1, c2 = st.columns(2, gap='large')
    with c1:
        a = _pair('α', (.6, .3), 'if1')
    with c2:
        b = _pair('β', (.5, .4), 'if2')
    lam = st.slider('Exposant / scalaire λ', .1, 5.0, 2.0, .1, key='if_l')
    rows = [('α ⊕ β', F.ifn_add(a, b)), ('α ⊗ β', F.ifn_mul(a, b)), ('λ·α', F.ifn_scale(lam, a)), ('α^λ', F.ifn_power(a, lam))]
    st.dataframe(pd.DataFrame({'Opération': [r[0] for r in rows], '(μ, ν)': [_fmt(r[1]) for r in rows], 'π': [round(F.ifn_hesitation(r[1]), 3) for r in rows], 'Score μ−ν': [round(F.ifn_score(r[1]), 3) for r in rows]}), hide_index=True, width='stretch')
    cmp = F.ifn_compare(a, b)
    kit.callout(f'Score(α) = {F.ifn_score(a):.3f}, Score(β) = {F.ifn_score(b):.3f}, précision h(α) = {F.ifn_accuracy(a):.3f}, h(β) = {F.ifn_accuracy(b):.3f} → ' + ('**α ≻ β**' if cmp > 0 else '**β ≻ α**' if cmp < 0 else '**α ~ β**'), 'info')
    kit.section('Agrégation IFWA', 'IFWA_σ = (1 − Π(1−μⱼ)^σⱼ , Π νⱼ^σⱼ)')
    s = st.slider('Poids du décideur 1 (σ₁) ; σ₂ = 1 − σ₁', 0.0, 1.0, .5, .05)
    r = F.ifwa([a, b], [s, 1 - s])
    st.markdown(f'IFWA(α, β) = **{_fmt(r)}** · score = {F.ifn_score(r):.3f}')
    fig = go.Figure(go.Scatter(x=[0, 1, 0, 0], y=[0, 0, 1, 0], fill='toself', fillcolor='rgba(47,107,255,.08)', line=dict(color=T.BLUE), name='μ + ν ≤ 1'))
    for nm, pt, col in [('α', a, T.TEAL), ('β', b, T.ORANGE), ('IFWA', r, T.AMBER)]:
        fig.add_trace(go.Scatter(x=[pt[0]], y=[pt[1]], mode='markers+text', text=[nm], textposition='top right', marker=dict(size=14, color=col), name=nm))
    fig.update_xaxes(title='μ'); fig.update_yaxes(title='ν', scaleanchor='x')
    kit.show(fig, 330, legend=False)


def _tab_pfs():
    kit.section('Pythagoricien, q-rung orthopair et version à intervalles', 'Contrainte μ^q + ν^q ≤ 1 : plus q est grand, plus l’espace des jugements autorisés s’élargit')
    q = st.slider('Rang q', 1.0, 6.0, 3.0, .5)
    c1, c2 = st.columns([1, 1.4], gap='large')
    with c1:
        a = _pair('Valeur', (.8, .6), 'qr', q)
        st.markdown(f'Contrôle : μ^q + ν^q = **{a[0] ** q + a[1] ** q:.3f}** ≤ 1 ✓')
        kit.kpis([('Hésitation π', f'{F.qrof_hesitation(a, q):.3f}', '(1 − μ^q − ν^q)^(1/q)', T.TEAL), ('Score', f'{F.qrof_score(a, q):.3f}', 'μ^q − ν^q', T.ORANGE)])
        if abs(q - 2) < 1e-9:
            st.caption(f'Pythagoricien (q = 2) : score μ² − ν² = {F.pfn_score(a):.3f}.')
        if a[0] + a[1] > 1:
            kit.callout('Ce couple est **interdit en intuitionniste** (μ+ν > 1) mais valide pour q assez grand.', 'tip')
    with c2:
        t = np.linspace(0, np.pi / 2, 200)
        fig = go.Figure()
        for qq, col, nm in [(1, T.BLUE, 'IFS (q = 1)'), (2, T.TEAL, 'PFS (q = 2)'), (q, T.ORANGE, f'q-ROFS (q = {q:g})')]:
            xs = np.linspace(0, 1, 200)
            ys = (1 - xs ** qq) ** (1 / qq)
            fig.add_trace(go.Scatter(x=xs, y=ys, name=nm, line=dict(width=3, color=col), fill='tozeroy', opacity=.55 if qq == q else .3))
        fig.add_trace(go.Scatter(x=[a[0]], y=[a[1]], mode='markers', marker=dict(size=14, color=T.INK), name='Ta valeur'))
        fig.update_xaxes(title='μ'); fig.update_yaxes(title='ν', range=[0, 1.05], scaleanchor='x')
        kit.show(fig, 340)
    kit.section('q-ROF à valeur d’intervalle (IVq-ROFS)', 'μ = [μᴸ, μᵁ], ν = [νᴸ, νᵁ] avec (μᵁ)^q + (νᵁ)^q ≤ 1')
    c1, c2 = st.columns(2)
    mu = c1.slider('μ = [μᴸ, μᵁ]', 0.0, 1.0, (.5, .7), .01, key='iv_m')
    nu_cap = float(np.floor((1 - mu[1] ** q) ** (1 / q) * 100) / 100)
    nu = c2.slider('ν = [νᴸ, νᵁ]', 0.0, max(nu_cap, .01), (min(.1, nu_cap), min(.3, nu_cap)), .01, key='iv_n')
    h = F.ivqrof_hesitation(mu, nu, q)
    kit.callout(f'Hésitation à valeur d’intervalle : π ∈ **[{h[0]:.3f} ; {h[1]:.3f}]** · validité : ' + ('✓' if F.ivqrof_valid(mu, nu, q) else '✗'), 'info')


def _tab_picture():
    kit.section('Ensembles flous picturaux (PicFS)', 'Trois degrés : positif μ, neutre η, négatif ν · refus ρ = 1 − μ − η − ν (modèle du vote : oui / abstention / non / refus)')
    c1, c2 = st.columns(2, gap='large')
    vals = []
    for col, lab, dflt in [(c1, 'α', (.5, .2, .2)), (c2, 'β', (.4, .3, .1))]:
        with col:
            mu = st.slider(f'{lab} · μ', 0.0, 1.0, dflt[0], .01, key=f'pc{lab}m')
            eta = st.slider(f'{lab} · η', 0.0, round(1 - mu, 2), min(dflt[1], round(1 - mu, 2)), .01, key=f'pc{lab}e')
            nu = st.slider(f'{lab} · ν', 0.0, max(round(1 - mu - eta, 2), 0.01), min(dflt[2], max(round(1 - mu - eta, 2), 0.01)), .01, key=f'pc{lab}n')
            vals.append((mu, eta, nu))
    a, b = vals
    lam = st.slider('λ', .1, 5.0, 2.0, .1, key='pc_l')
    rows = [('α ⊕ β', F.picture_add(a, b)), ('λ·α', F.picture_scale(lam, a)), ('α^λ', F.picture_power(a, lam))]
    st.dataframe(pd.DataFrame({'Opération': [r[0] for r in rows], '(μ, η, ν)': [_fmt(r[1]) for r in rows], 'Refus ρ': [round(F.picture_refusal(r[1]), 3) for r in rows]}), hide_index=True, width='stretch')
    fig = go.Figure(go.Bar(x=['positif μ', 'neutre η', 'négatif ν', 'refus ρ'], y=list(a) + [F.picture_refusal(a)], marker=dict(color=[T.TEAL, T.AMBER, T.RED, T.SLATE], cornerradius=6)))
    kit.show(fig, 260, legend=False)


def _tab_hesitant():
    kit.section('Ensembles flous hésitants (HFS)', 'Un élément peut recevoir plusieurs degrés d’appartenance possibles : h = {γ₁, …, γₗ}')
    ex = st.checkbox('Charger l’exemple de référence : h₁ = {0,2 ; 0,3 ; 0,5 ; 0,8}, h₂ = {0,4 ; 0,6 ; 0,8}, h₃ = {0,3 ; 0,45 ; 0,6}', True)
    default = ['0.2, 0.3, 0.5, 0.8', '0.4, 0.6, 0.8', '0.3, 0.45, 0.6'] if ex else ['0.1, 0.4', '0.3, 0.5, 0.7', '0.6']
    hs = []
    cols = st.columns(3)
    for i, c in enumerate(cols):
        t = c.text_input(f'h{i + 1}', default[i], key=f'hf{i}{ex}')
        try:
            v = sorted({float(x) for x in t.split(',') if x.strip()})
            if not v or min(v) < 0 or max(v) > 1:
                raise ValueError
            hs.append(v)
        except ValueError:
            st.error(f'h{i + 1} invalide (valeurs dans [0,1]).')
            return
    df = pd.DataFrame({'Ensemble': [f'h{i + 1}' for i in range(3)], 'Valeurs': [str(h) for h in hs], 'Score s(h)': [F.hfn_score(h) for h in hs], 'Écart-type σ(h)': [F.hfn_deviation(h) for h in hs]}).round(4)
    st.dataframe(df, hide_index=True, width='stretch')
    order = sorted(range(3), key=lambda i: (-F.hfn_score(hs[i]), F.hfn_deviation(hs[i])))
    kit.callout('Classement (score décroissant ; à score égal, écart-type **le plus faible** préféré) : **' + ' ≻ '.join(f'h{i + 1}' for i in order) + '**', 'ok')
    c1, c2, c3 = st.columns(3)
    lam = c1.number_input('λ', .1, 5.0, 2.0, key='hf_l')
    ext = c2.radio('Extension si longueurs différentes', ['max', 'min'], horizontal=True, help='Optimiste = on répète la plus grande valeur ; pessimiste = la plus petite.')
    rows = [('h₁ ⊕ h₂', F.hfn_add(hs[0], hs[1])), ('h₁ ⊗ h₂', F.hfn_mul(hs[0], hs[1])), ('λ·h₁', F.hfn_scale(lam, hs[0])), ('h₁^λ', F.hfn_power(hs[0], lam))]
    st.dataframe(pd.DataFrame({'Opération': [r[0] for r in rows], 'Résultat': [str([round(x, 3) for x in r[1]]) for r in rows]}), hide_index=True, width='stretch')
    st.markdown(f'Distance de Hamming d(h₁, h₂) = **{F.hfn_hamming(hs[0], hs[1], ext):.4f}** · d(h₁, h₃) = **{F.hfn_hamming(hs[0], hs[2], ext):.4f}** · d(h₂, h₃) = **{F.hfn_hamming(hs[1], hs[2], ext):.4f}**')
    fig = go.Figure()
    for i, h in enumerate(hs):
        fig.add_trace(go.Scatter(x=[f'h{i + 1}'] * len(h), y=h, mode='markers', marker=dict(size=14, color=T.CAT[i], line=dict(color='#fff', width=2)), name=f'h{i + 1}'))
        fig.add_trace(go.Scatter(x=[f'h{i + 1}'], y=[F.hfn_score(h)], mode='markers', marker=dict(size=22, symbol='line-ew', line=dict(width=3, color=T.INK)), showlegend=False))
    fig.update_yaxes(range=[0, 1], title='Degrés d’appartenance (trait = score)')
    kit.show(fig, 300, legend=False)


def render():
    kit.header('I · LOGIQUE FLOUE', 'Laboratoire flou',
               'Manipule chaque famille d’ensembles flous vus à l’étude : classique, nombres flous, intervalles, intuitionniste, pythagoricien, q-rung, pictural et hésitant. '
               'Les curseurs imposent automatiquement les contraintes de validité.',
               ['Ensembles flous', 'TFN / trapèzes', 'IFS', 'PFS · q-ROFS', 'Picturaux', 'Hésitants'])
    tabs = st.tabs(['Ensembles flous', 'Nombres flous & intervalles', 'Intuitionniste', 'Pythagoricien · q-ROF', 'Pictural', 'Hésitant'])
    for t, fn in zip(tabs, (_tab_sets, _tab_numbers, _tab_ifs, _tab_pfs, _tab_picture, _tab_hesitant)):
        with t:
            fn()
    state.mark('fuzzy_lab')
