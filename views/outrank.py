"""Analyse 2c — Méthodes de surclassement : PROMETHEE I/II et ELECTRE III."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine.mcdm import PREF_FUNCTIONS, electre3, preference_function, promethee, rank
from ui import kit, state, theme as T

FN_LABELS = list(PREF_FUNCTIONS)


def _rel_style(df):
    def c(v):
        return {'P': 'background-color:#D6F2EF;color:#06504D;font-weight:700', 'P⁻': 'background-color:#FFE3D3;color:#8A3A0B;font-weight:700',
                'I': 'background-color:#FFF3DA;color:#7A4B00;font-weight:700', 'R': 'background-color:#E8EEF5;color:#46576B'}.get(v, '')
    return df.style.map(c)


def _tab_promethee(p):
    n = len(p.criteria)
    kit.section('PROMETHEE — préférences par paires', 'Chaque option est comparée à toutes les autres ; les flux Φ⁺ (puissance) et Φ⁻ (faiblesse) donnent le classement')
    c1, c2, c3 = st.columns(3)
    fn_label = c1.selectbox('Fonction de préférence', FN_LABELS, index=4, key='pm_fn')
    q = c2.slider('Seuil d’indifférence q (fraction de l’étendue)', 0.0, 0.5, 0.05, .01, key='pm_q')
    pr = c3.slider('Seuil de préférence p', 0.02, 1.0, 0.30, .01, key='pm_p')
    pr = max(pr, q + .01)
    fn = PREF_FUNCTIONS[fn_label]
    with st.expander('Paramètres par critère (optionnel)'):
        st.caption('Laisse vide pour appliquer les réglages globaux ci-dessus. Les seuils sont des fractions de l’étendue du critère.')
        base = pd.DataFrame({'Critère': p.criteria, 'Fonction': fn_label, 'q': q, 'p': pr})
        edited = st.data_editor(base, hide_index=True, key='pm_tab_' + str(hash(tuple(p.criteria))) + fn_label + str(q) + str(pr), width='stretch',
                                disabled=['Critère'], column_config={'Fonction': st.column_config.SelectboxColumn(options=FN_LABELS, required=True),
                                                                     'q': st.column_config.NumberColumn(min_value=0.0, max_value=1.0, step=.01),
                                                                     'p': st.column_config.NumberColumn(min_value=0.01, max_value=2.0, step=.01)})
    fns = [PREF_FUNCTIONS[f] for f in edited['Fonction']]
    qs, ps = edited['q'].to_numpy(float), np.maximum(edited['p'].to_numpy(float), edited['q'].to_numpy(float) + 1e-3)
    d = promethee(p, fns, qs, ps)
    scores = d['phi']
    rk = rank(p, 'PROMETHEE II', fn=fns, q=qs, pref=ps)['ranks']
    kit.formula(r'\Phi^+(a)=\frac{1}{m-1}\sum_{b}\pi(a,b)\;;\;\Phi^-(a)=\frac{1}{m-1}\sum_{b}\pi(b,a)\;;\;\Phi(a)=\Phi^+(a)-\Phi^-(a)')
    a, b = st.columns([1.1, 1], gap='large')
    with a:
        kit.bar_ranking(p.alternatives, scores, rk, title='Flux net Φ (PROMETHEE II)')
    with b:
        x = np.linspace(0, 1, 200)
        fig = go.Figure()
        for j, c in enumerate(p.criteria):
            fig.add_trace(go.Scatter(x=x, y=preference_function(x, fns[j], qs[j], ps[j]), name=c, line=dict(width=3, color=T.CAT[j % 8])))
        fig.update_xaxes(title='Écart de performance normalisé d'); fig.update_yaxes(title='P(d)', range=[0, 1.05])
        st.markdown('**Fonctions de préférence P(d)**')
        kit.show(fig, 290)
    df = pd.DataFrame({'Rang': rk, 'Alternative': p.alternatives, 'Φ⁺': d['phi_plus'], 'Φ⁻': d['phi_minus'], 'Φ': scores}).sort_values('Rang')
    st.dataframe(kit.style_rank(df, ['Rang']).format({'Φ⁺': '{:.4f}', 'Φ⁻': '{:.4f}', 'Φ': '{:.4f}'}), hide_index=True, width='stretch')
    t1, t2 = st.tabs(['PROMETHEE I · classement partiel', 'Matrice des préférences π(a,b)'])
    with t1:
        rel = pd.DataFrame(d['promethee1'], index=p.alternatives, columns=p.alternatives)
        st.dataframe(_rel_style(rel), width='stretch')
        st.caption('P : la ligne surclasse la colonne · P⁻ : la colonne surclasse la ligne · I : indifférentes · R : incomparables (Φ⁺ et Φ⁻ se contredisent). PROMETHEE II tranche tous les R grâce au flux net.')
    with t2:
        kit.heatmap(d['preference'], p.alternatives, p.alternatives, fmt='.2f', h=max(300, 46 * len(p.alternatives) + 70))
    kit.course_note('PROMETHEE', 'Méthode de surclassement **sans compensation totale** : π(a,b) = Σⱼ wⱼ Pⱼ(gⱼ(a) − gⱼ(b)). PROMETHEE I → préordre partiel (Φ⁺, Φ⁻) ; PROMETHEE II → préordre complet (Φ net). Dans l’exemple de Spearman de référence, PROMETHEE II inverse A4 et A6 par rapport à TOPSIS.')


def _tab_electre(p):
    n = len(p.criteria)
    kit.section('ELECTRE III — surclassement flou avec seuils et veto', 'Concordance, discordance, degré de crédibilité σ(a,b), puis distillations descendante et ascendante')
    c1, c2, c3 = st.columns(3)
    q = c1.slider('Seuil d’indifférence q', 0.0, 0.4, 0.05, .01, key='el_q', help='Fraction de l’étendue du critère')
    pr = c2.slider('Seuil de préférence p', 0.02, 0.8, 0.15, .01, key='el_p')
    v = c3.slider('Seuil de veto v', 0.05, 1.5, 0.60, .01, key='el_v')
    pr = max(pr, q + .01)
    v = max(v, pr + .01)
    with st.expander('Seuils par critère (optionnel)'):
        base = pd.DataFrame({'Critère': p.criteria, 'q': q, 'p': pr, 'v': v})
        edited = st.data_editor(base, hide_index=True, disabled=['Critère'], width='stretch', key='el_tab_' + str(hash(tuple(p.criteria))) + f'{q}{pr}{v}')
    qs, ps, vs = (edited[k].to_numpy(float) for k in ('q', 'p', 'v'))
    r = rank(p, 'ELECTRE III', e_q=qs, e_p=np.maximum(ps, qs + 1e-3), e_v=np.maximum(vs, ps + 1e-3))
    d = r['details']
    kit.formula(r'C(a,b)=\sum_j w_j c_j(a,b)\;;\;\; \sigma(a,b)=C(a,b)\prod_{j:\,d_j>C}\frac{1-d_j(a,b)}{1-C(a,b)}')
    best = p.alternatives[int(np.argmin(r['ranks']))]
    kit.kpis([('Meilleure position moyenne', best, 'moyenne des rangs desc./asc.', T.ORANGE),
              ('Classes (descendante)', len(d['descending']), 'niveaux de la distillation', T.TEAL),
              ('Relations d’incomparabilité', int((d['relation'] == 'R').sum() // 2), 'paires non comparables', T.AMBER)])
    a, b = st.columns([1, 1], gap='large')
    with a:
        kit.bar_ranking(p.alternatives, -d['mean_position'], r['ranks'], title='Position moyenne (distillations) — barre plus longue = mieux')
    with b:
        fig = go.Figure(go.Scatter(x=d['pos_desc'], y=d['pos_asc'], mode='markers+text', text=p.alternatives, textposition='top center',
                                   marker=dict(size=18, color=[T.ORANGE if k == 1 else T.TEAL for k in r['ranks']], line=dict(color='#fff', width=2))))
        m = len(p.alternatives)
        fig.add_shape(type='line', x0=.5, y0=.5, x1=m + .5, y1=m + .5, line=dict(color=T.LINE, dash='dot'))
        fig.update_xaxes(title='Rang distillation descendante', autorange='reversed', dtick=1, range=[m + .6, .4])
        fig.update_yaxes(title='Rang distillation ascendante', autorange='reversed', dtick=1, range=[m + .6, .4])
        st.markdown('**Préordres : descendant vs ascendant** (près de la diagonale = les deux distillations concordent)')
        kit.show(fig, 330, legend=False)
    t1, t2, t3, t4 = st.tabs(['Concordance & crédibilité', 'Discordance', 'Distillations', 'Relation finale'])
    with t1:
        x1, x2 = st.columns(2)
        with x1:
            st.markdown('**Indice de concordance global C(a,b)**')
            kit.heatmap(d['concordance'], p.alternatives, p.alternatives, zmin=0, zmax=1, h=max(280, 44 * len(p.alternatives) + 70))
        with x2:
            st.markdown('**Degré de crédibilité σ(a,b)**')
            kit.heatmap(d['credibility'], p.alternatives, p.alternatives, zmin=0, zmax=1, h=max(280, 44 * len(p.alternatives) + 70))
    with t2:
        cs = st.selectbox('Critère', p.criteria, key='el_dcrit')
        kit.heatmap(d['discordance'][:, :, p.criteria.index(cs)], p.alternatives, p.alternatives, scale=[[0, '#FFFFFF'], [1, '#E5484D']], zmin=0, zmax=1, h=max(280, 44 * len(p.alternatives) + 70))
        st.caption('dⱼ(a,b) = 0 tant que b ne dépasse pas a de plus que p ; 1 au-delà du veto v. Une discordance supérieure à C réduit la crédibilité.')
    with t3:
        names = p.alternatives
        z1, z2 = st.columns(2)
        with z1:
            st.markdown('**Distillation descendante** (meilleurs d’abord)')
            for k, cls in enumerate(d['descending'], 1):
                st.markdown(f'`{k}` ' + ' · '.join(f'**{names[i]}**' for i in cls))
        with z2:
            st.markdown('**Distillation ascendante** (classée du meilleur au pire)')
            for k, cls in enumerate(d['ascending'], 1):
                st.markdown(f'`{k}` ' + ' · '.join(f'**{names[i]}**' for i in cls))
        st.caption('Seuil de coupure s(λ) = 0,3 − 0,15 λ. Le préordre final est l’intersection des deux distillations.')
    with t4:
        rel = pd.DataFrame(d['relation'], index=p.alternatives, columns=p.alternatives)
        st.dataframe(_rel_style(rel), width='stretch')
        st.caption('P : la ligne est préférée à la colonne · P⁻ : l’inverse · I : indifférentes · R : incomparables. Contrairement aux méthodes additives, ELECTRE III accepte l’incomparabilité.')
    kit.course_note('ELECTRE III', 'Méthode de **surclassement sans compensation** (sécurité, environnement). Seuils q (indifférence), p (préférence), v (veto). a surclasse b si σ(a,b) est assez élevé et nettement supérieur à σ(b,a).')


def render():
    p = state.problem()
    kit.header('F · SURCLASSEMENT', 'Méthodes de surclassement',
               'Sans compensation entre critères : on compare les alternatives deux à deux et l’on accepte l’incomparabilité. Indiqué quand la sécurité ou l’environnement ne doivent pas être « achetés » par un bon prix.',
               ['PROMETHEE I', 'PROMETHEE II', 'ELECTRE III', 'Seuils q · p · v'])
    tabs = st.tabs(['PROMETHEE', 'ELECTRE III'])
    with tabs[0]:
        _tab_promethee(p)
    with tabs[1]:
        _tab_electre(p)
    state.mark('outrank')
