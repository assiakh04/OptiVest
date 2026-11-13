"""Analyse 2a — Pondération des critères : manuel, AHP, BWM, Entropie, CRITIC, hybride."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine.examples import AHP_CAR
from engine.mcdm import (RI_TABLE, ahp, bwm, critic, entropy, hybrid_weights, normalize_weights)
from ui import kit, state, theme as T

BWM_COURSE = {'names': ['Qualité', 'Prix', 'Délai', 'RSE'], 'best': 0, 'worst': 3, 'bo': [1, 3, 4, 8], 'ow': [8, 5, 3, 1]}


def _apply(w, source, sample=False):
    if sample:
        st.caption('Exemple pédagogique de référence : non appliqué au projet.')
        return
    if st.button(f'✓ Utiliser ces poids ({source})', type='primary', key='use_' + source):
        state.set_weights(w, source)
        state.mark('weights')
        st.success(f'Poids {source} activés dans toutes les méthodes.')
        st.rerun()


def _weights_df(names, w, extra=None):
    d = {'Critère': names, 'Poids': np.round(w, 4), 'Poids (%)': np.round(100 * np.asarray(w), 2)}
    if extra:
        d.update(extra)
    return pd.DataFrame(d)


def render():
    p = state.problem()
    n = len(p.criteria)
    bank = st.session_state.bank
    for k in [k for k, v in bank.items() if len(v) != n]:
        del bank[k]
    bank.setdefault(st.session_state.weight_source, [float(x) for x in p.weights])
    bank['Entropie'] = [float(x) for x in entropy(p)['weights']]
    bank['CRITIC'] = [float(x) for x in critic(p)['weights']]

    kit.header('E · PONDÉRATION', 'Quels critères comptent le plus ?',
               'Deux familles : méthodes subjectives (AHP, BWM : jugements d’experts) et objectives (Entropie, CRITIC : calculées à partir des données). '
               'En pratique, on combine souvent les deux (poids hybrides).',
               ['AHP + cohérence', 'BWM (programme linéaire)', 'Entropie', 'CRITIC', 'Hybride'])
    kit.kpis([('Poids actifs', st.session_state.weight_source, 'utilisés par toutes les méthodes', T.TEAL),
              ('Critère dominant', p.criteria[int(np.argmax(p.weights))], f'{100 * p.weights.max():.1f} % du poids', T.ORANGE),
              ('Critère le moins pesé', p.criteria[int(np.argmin(p.weights))], f'{100 * p.weights.min():.1f} % du poids', T.BLUE)])

    tabs = st.tabs(['✋ Manuel', '⚖ AHP', '◈ BWM', '📊 Entropie', '🔗 CRITIC', '🧬 Hybride & poids actifs'])

    # =========================================================== MANUEL
    with tabs[0]:
        kit.section('Poids fixés à la main', 'Déplace les curseurs : la normalisation (somme = 1) est automatique.')
        raw = []
        cols = st.columns(2)
        for i, c in enumerate(p.criteria):
            raw.append(cols[i % 2].slider(c, 0, 100, int(round(p.weights[i] * 100)), key=f'mx_w_{i}'))
        if sum(raw) > 0:
            w = normalize_weights(raw)
            kit.weights_chart(p.criteria, w, 240)
            _apply(w, 'Manuel')
        else:
            st.warning('Augmente au moins un poids.')

    # =========================================================== AHP
    with tabs[1]:
        kit.section('AHP — Analytic Hierarchy Process', 'Comparaisons par paires sur l’échelle de Saaty (1 = égal … 9 = extrêmement plus important)')
        src = st.radio('Critères à pondérer', ['Critères du projet', 'Exemple de référence (achat d’une voiture)'], horizontal=True, key='ahp_src')
        sample = src.startswith('Exemple')
        names = AHP_CAR['criteria'] if sample else p.criteria
        if sample:
            init = np.array(AHP_CAR['criteria_matrix'], float)
        else:
            w0 = np.clip(p.weights / p.weights.max(), 1e-3, None)
            init = np.clip(w0[:, None] / w0[None, :], 1 / 9, 9)
        if len(names) > 10:
            st.error('AHP : la table RI de référence s’arrête à n = 10 critères.')
        else:
            A = kit.matrix_editor('ahpm_crit_' + ('s' if sample else str(hash(tuple(p.criteria)))), names, init)
            try:
                r = ahp(A)
                kit.section('Étapes du calcul (méthode approchée de référence)')
                a, b = st.columns(2, gap='large')
                with a:
                    st.markdown('**① Matrice réciproque complète**')
                    st.dataframe(pd.DataFrame(A, index=names, columns=names).round(3), width='stretch')
                    st.markdown('**② Somme de chaque colonne sᵢ**')
                    st.dataframe(pd.DataFrame([r['col_sums']], columns=names, index=['s']).round(3), width='stretch')
                with b:
                    st.markdown('**③ Division par la somme de la colonne → moyenne des lignes = priorités wᵢ**')
                    nm = pd.DataFrame(r['normalized'], index=names, columns=names).round(3)
                    nm['Priorité wᵢ'] = r['weights'].round(4)
                    st.dataframe(nm, width='stretch')
                kit.formula(r'\lambda_{max}=\sum_i s_i\,w_i \quad;\quad CI=\frac{\lambda_{max}-n}{n-1} \quad;\quad CR=\frac{CI}{RI}')
                kit.kpis([('λmax', f'{r["lambda_max"]:.4f}', f'n = {len(names)}', T.TEAL), ('CI', f'{r["ci"]:.4f}', 'indice de cohérence', T.BLUE),
                          ('RI', f'{r["ri"]:.2f}' if r['ri'] is not None else '—', 'table de référence', T.AMBER),
                          ('CR', f'{r["cr"]:.4f}' if r['cr'] is not None else '—', 'CR < 0,1 requis', T.ORANGE if not r['consistent'] else T.GREEN)])
                if r['consistent']:
                    kit.callout(f'**Matrice cohérente** (CR = {r["cr"]:.3f} < 0,1) : les poids peuvent être conservés.', 'ok')
                else:
                    kit.callout(f'**Matrice incohérente** (CR = {r["cr"]:.3f} ≥ 0,1) : revois certaines comparaisons avant de continuer.', 'bad')
                kit.weights_chart(names, r['weights'], 260)
                st.caption('Vérification : le vecteur propre principal (numpy) donne ' + ', '.join(f'{x:.3f}' for x in r['weights_eig']))
                st.session_state['_ahp_w'] = r['weights']
                if r['consistent']:
                    _apply(r['weights'], 'AHP', sample)
                else:
                    st.button('✓ Utiliser ces poids (AHP)', disabled=True, help='Matrice incohérente')
            except Exception as e:
                st.error(str(e))
        kit.course_note('AHP', """
1. Construire la hiérarchie : objectif → critères → alternatives.
2. Comparer les critères par paires (échelle de Saaty), calculer les priorités (vecteur propre, ici approximation par normalisation de colonnes).
3. **Test de cohérence** : λmax, CI, CR = CI/RI ; CR < 0,1 ⇒ matrice cohérente. RI (n=3…10) : 0,58 ; 0,90 ; 1,12 ; 1,24 ; 1,32 ; 1,41 ; 1,45 ; 1,56.
4. Priorités locales des alternatives par critère puis priorités finales Σⱼ wⱼ·wⱼᵢ → voir la page **Méthodes additives › AHP complet**.
5. Analyse de sensibilité sur les poids → page **Robustesse**.""")

    # =========================================================== BWM
    with tabs[2]:
        kit.section('BWM — Best-Worst Method (Rezaei, 2015)', 'Seulement 2n−3 comparaisons, toujours avec le meilleur (Best) ou le pire (Worst) critère')
        src = st.radio('Critères à pondérer', ['Critères du projet', 'Exemple de référence (fournisseur, 4 critères)'], horizontal=True, key='bwm_src')
        sample = src.startswith('Exemple')
        names = BWM_COURSE['names'] if sample else p.criteria
        tag = 's' if sample else str(hash(tuple(p.criteria)))
        c1, c2 = st.columns(2)
        b_def = BWM_COURSE['best'] if sample else int(np.argmax(p.weights))
        w_def = BWM_COURSE['worst'] if sample else int(np.argmin(p.weights))
        best = c1.selectbox('Critère le plus important (Best)', names, index=b_def, key='bwm_b' + tag)
        worst = c2.selectbox('Critère le moins important (Worst)', [x for x in names if x != best],
                             index=max(0, [x for x in names if x != best].index(names[w_def]) if names[w_def] != best else 0), key='bwm_w' + tag)
        bi, wi = names.index(best), names.index(worst)
        a_bw = st.slider(f'{best} est … fois plus important que {worst}  (a_BW)', 1, 9, BWM_COURSE['bo'][3] if sample else 7, key='bwm_abw' + tag)
        bo, ow = np.ones(len(names)), np.ones(len(names))
        ca, cb = st.columns(2, gap='large')
        with ca:
            st.markdown(f'**Best-to-Others** — « combien de fois **{best}** est-il plus important que… »')
            for j, c in enumerate(names):
                if j == bi:
                    bo[j] = 1
                elif j == wi:
                    bo[j] = a_bw
                else:
                    bo[j] = st.slider(c, 1, 9, BWM_COURSE['bo'][j] if sample else 3, key=f'bwm_bo{tag}_{j}')
        with cb:
            st.markdown(f'**Others-to-Worst** — « combien de fois… est-il plus important que **{worst}** »')
            for j, c in enumerate(names):
                if j == wi:
                    ow[j] = 1
                elif j == bi:
                    ow[j] = a_bw
                else:
                    ow[j] = st.slider(c, 1, 9, BWM_COURSE['ow'][j] if sample else 3, key=f'bwm_ow{tag}_{j}')
        try:
            r = bwm(bi, wi, bo, ow)
            kit.formula(r'\min \xi \;\; \text{s.c.}\;\; |w_B-a_{Bj}w_j|\le\xi,\;\; |w_j-a_{jW}w_W|\le\xi,\;\; \sum_j w_j=1,\; w_j\ge0')
            kit.kpis([('ξ* (écart max)', f'{r["xi"]:.4f}', 'proche de 0 = jugements cohérents', T.TEAL),
                      ('Ratio de cohérence', f'{r["cr"]:.3f}', 'ξ* / CI(a_BW) — Rezaei', T.ORANGE),
                      ('Comparaisons', f'{2 * len(names) - 3} (vs {len(names) * (len(names) - 1) // 2} pour AHP)', 'économie d’effort', T.BLUE)])
            kit.callout('Jugements **cohérents** (ξ* faible).' if r['xi'] < .1 else 'ξ* élevé : les jugements sont peu cohérents — revois-les.', 'ok' if r['xi'] < .1 else 'warn')
            a, b = st.columns([1, 1.2], gap='large')
            with a:
                st.dataframe(_weights_df(names, r['weights']), hide_index=True, width='stretch')
            with b:
                kit.weights_chart(names, r['weights'], 250)
            with st.expander('Forme matricielle  A·x ≤ b  (x = (w₁…wₙ, ξ))'):
                st.dataframe(pd.DataFrame(r['A'], columns=[f'w{i + 1}' for i in range(len(names))] + ['ξ']).round(3), width='stretch')
                st.caption('Chaque couple (j) produit 4 inégalités ; le programme est résolu par `scipy.optimize.linprog` (HiGHS).')
            _apply(r['weights'], 'BWM', sample)
        except Exception as e:
            st.error(str(e))
        kit.course_note('BWM', """
- Étapes : choisir **B** et **W** → vecteur **BO** (Best-to-Others) → vecteur **OW** (Others-to-Worst) → résoudre le LP → lire ξ*.
- Contrôles : a_BB = a_WW = 1 ; la note la plus élevée de BO porte sur W.
- Exemple de référence : BO = (1, 3, 4, 8), OW = (8, 5, 3, 1) → ξ* ≈ 0,08 (très proche de 0).""")

    # =========================================================== ENTROPIE
    with tabs[3]:
        kit.section('Entropie de Shannon', 'Un critère qui disperse fortement les alternatives apporte plus d’information → poids élevé')
        norm = st.radio('Normalisation préalable', ['ratio', 'minmax'], horizontal=True,
                        format_func=lambda x: 'Ratio de référence (x/x⁺ ; x⁺/x)' if x == 'ratio' else 'Min-max', key='ent_norm')
        e = entropy(p, norm)
        kit.formula(r'p_{ij}=\frac{d_{ij}}{\sum_i d_{ij}}\;;\quad E_j=-\frac{1}{\ln m}\sum_i p_{ij}\ln p_{ij}\;;\quad w_j=\frac{1-E_j}{n-\sum_k E_k}')
        a, b = st.columns([1.3, 1], gap='large')
        with a:
            st.markdown('**Proportions pᵢⱼ**')
            st.dataframe(pd.DataFrame(e['p'], index=p.alternatives, columns=p.criteria).round(4), width='stretch')
            st.dataframe(_weights_df(p.criteria, e['weights'], {'Entropie Eⱼ': np.round(e['entropy'], 4), 'Diversification 1−Eⱼ': np.round(e['diversification'], 4)}),
                         hide_index=True, width='stretch')
        with b:
            kit.weights_chart(p.criteria, e['weights'], 300)
        bank['Entropie'] = [float(x) for x in e['weights']]
        kit.callout('Entropie élevée (≈ 1) : valeurs uniformes, le critère distingue mal les options → poids faible.', 'tip')
        _apply(e['weights'], 'Entropie')

    # =========================================================== CRITIC
    with tabs[4]:
        kit.section('CRITIC — CRiteria Importance Through Intercriteria Correlation', 'Plus un critère est dispersé et moins il est corrélé aux autres, plus il est important')
        c = critic(p)
        kit.formula(r'C_j=\sigma_j\sum_{k=1}^{n}\left(1-|\rho_{jk}|\right)\quad;\quad w_j=\frac{C_j}{\sum_j C_j}')
        a, b = st.columns([1, 1], gap='large')
        with a:
            st.markdown('**Corrélations ρⱼₖ entre critères (matrice normalisée)**')
            kit.heatmap(c['correlation'], p.criteria, p.criteria, scale=T.DIV, zmin=-1, zmax=1, h=330)
        with b:
            st.markdown('**Indice C et poids**')
            st.dataframe(_weights_df(p.criteria, c['weights'], {'σⱼ': np.round(c['std'], 4), 'Cⱼ': np.round(c['information'], 4)}), hide_index=True, width='stretch')
            kit.weights_chart(p.criteria, c['weights'], 220)
        with st.expander('Matrice normalisée (min-max, sens bénéfice/coût)'):
            st.dataframe(pd.DataFrame(c['normalized'], index=p.alternatives, columns=p.criteria).round(4), width='stretch')
        bank['CRITIC'] = [float(x) for x in c['weights']]
        _apply(c['weights'], 'CRITIC')

    # =========================================================== HYBRIDE
    with tabs[5]:
        kit.section('Poids hybrides', 'Équilibrer expertise (subjectif) et données (objectif) — N.B. de référence')
        sources = list(bank)
        a, b, c3 = st.columns([1, 1, 1])
        s_sub = a.selectbox('Poids subjectifs (expert)', sources, index=sources.index('AHP') if 'AHP' in sources else 0)
        s_obj = b.selectbox('Poids objectifs (données)', sources, index=sources.index('CRITIC'))
        mode = c3.radio('Combinaison', ['linéaire', 'multiplicatif'], horizontal=True)
        alpha = st.slider('α · part des poids subjectifs', 0.0, 1.0, .6, .05)
        hw = hybrid_weights(bank[s_sub], bank[s_obj], alpha, mode)
        kit.formula(r'w_j^{hyb}=\alpha\,w_j^{sub}+(1-\alpha)\,w_j^{obj}' if mode == 'linéaire' else r'w_j^{hyb}\propto (w_j^{sub})^{\alpha}\,(w_j^{obj})^{1-\alpha}')
        bank['Hybride'] = [float(x) for x in hw]
        _apply(hw, 'Hybride')
        kit.section('Comparaison de toutes les pondérations', 'Un critère dont le poids varie beaucoup d’une méthode à l’autre mérite une discussion')
        fig = go.Figure()
        for k, (src_name, wv) in enumerate(bank.items()):
            fig.add_trace(go.Bar(name=src_name, x=p.criteria, y=[100 * v for v in wv], marker=dict(color=T.CAT[k % 8], cornerradius=4)))
        fig.update_layout(barmode='group')
        fig.update_yaxes(title='Poids (%)')
        kit.show(fig, 340)
        tbl = pd.DataFrame({'Critère': p.criteria, **{s: np.round(100 * np.array(v), 1) for s, v in bank.items()}})
        st.dataframe(tbl, hide_index=True, width='stretch')
        kit.section('Choisir directement les poids actifs')
        pick = st.selectbox('Source des poids', list(bank), key='pick_active')
        if st.button('Activer cette pondération', width='content'):
            state.set_weights(bank[pick], pick)
            st.rerun()
        st.caption(f'Poids actifs actuellement : **{st.session_state.weight_source}**')
