"""Analyse 1 — Formaliser le problème : alternatives, critères, matrice de décision."""
import copy
import io
import json
import numpy as np
import pandas as pd
import streamlit as st
from engine.examples import EXAMPLES
from engine.mcdm import parse_project, pareto, utility
from ui import kit, nav, state, theme as T

STEPS = [('1', 'Identifier le problème', 'Quelle décision ? Quel objectif ?'),
         ('2', 'Élaborer les alternatives', 'Options ou stratégies à comparer'),
         ('3', 'Fixer les critères & collecter', 'Préférences, données, sens max/min'),
         ('4', 'Choisir les méthodes', 'Pondération + classement'),
         ('5', 'Appliquer & comparer', 'Plusieurs méthodes, sensibilité'),
         ('6', 'Décider & justifier', 'Choix argumenté et robuste')]

SCALES = {
    'Échelle 1–5': {'Très faible': 1, 'Faible': 2, 'Moyen': 3, 'Élevé': 4, 'Très élevé': 5},
    'Échelle 1–7': {'Très faible': 1, 'Faible': 2, 'Plutôt faible': 3, 'Moyen': 4, 'Plutôt élevé': 5, 'Élevé': 6, 'Très élevé': 7},
    'Échelle 1–9 (Saaty)': {'Égal': 1, 'Faible': 3, 'Modéré': 5, 'Fort': 7, 'Extrême': 9},
}


def _rebuild(project, alts, crits):
    """Reconstruit la matrice après modification de la structure en conservant les valeurs existantes."""
    old_a, old_c = project['alternatives'], [c['name'] for c in project['criteria']]
    old = np.asarray(project['matrix'], float)
    colmean = {c: float(old[:, j].mean()) for j, c in enumerate(old_c)}
    new = np.zeros((len(alts), len(crits)))
    same_a, same_c = len(alts) == len(old_a), len(crits) == len(old_c)
    for i, a in enumerate(alts):
        for j, c in enumerate(crits):
            ii = i if same_a else (old_a.index(a) if a in old_a else None)
            jj = j if same_c else (old_c.index(c) if c in old_c else None)
            if ii is not None and jj is not None:
                new[i, j] = old[ii, jj]
            else:
                new[i, j] = colmean.get(c, old[:, jj].mean() if jj is not None else 1.0)
    return new.tolist()


def _xlsx(project, p):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as xw:
        pd.DataFrame(p.matrix, index=p.alternatives, columns=p.criteria).to_excel(xw, sheet_name='Matrice')
        pd.DataFrame({'Critère': p.criteria, 'Sens': p.kinds, 'Unité': [c.get('unit', '') for c in project['criteria']],
                      'Poids': p.weights}).to_excel(xw, sheet_name='Critères', index=False)
    return buf.getvalue()


def render():
    p = state.problem()
    project = st.session_state.project
    kit.header('B · PROBLÈME & DONNÉES', 'Problème & données',
               'Formalise le problème de décision : alternatives A₁…Aₘ, critères C₁…Cₙ, sens de préférence et matrice de décision D = (xᵢⱼ).',
               ['Matrice de décision', 'Bénéfice / coût', 'Import-export', 'Diagnostic'])

    t1, t2, t3, t4, t5 = st.tabs(['1 · Scénario', '2 · Structure', '3 · Matrice', '4 · Import / Export', '5 · Diagnostic'])

    # ------------------------------------------------------------------ scénario
    with t1:
        kit.section('Processus de prise de décision', 'Les 6 étapes de référence — cette application suit exactement ce fil rouge')
        html_steps = ''.join(f'<div class="s"><div class="n">{n}</div><div class="t">{t}</div><div class="d">{d}</div></div>' for n, t, d in STEPS)
        st.markdown(f'<div class="stepper">{html_steps}</div>', unsafe_allow_html=True)
        kit.section('Choisir un scénario')
        c1, c2 = st.columns([2, 1])
        with c1:
            choice = st.selectbox('Scénario prêt à l’emploi', list(EXAMPLES), index=list(EXAMPLES).index(st.session_state.example))
        with c2:
            st.write('')
            st.write('')
            if st.button('Charger ce scénario', type='primary', width='stretch'):
                state.load_example(choice)
                st.rerun()
        st.caption(f'{EXAMPLES[choice]["domain"]} — {EXAMPLES[choice]["description"]}')
        kit.section('Documenter le problème')
        name = st.text_input('Question de décision', project['name'], key='mx_name')
        desc = st.text_area('Contexte et objectif', project.get('description', ''), height=90, key='mx_desc')
        if st.button('Enregistrer le contexte'):
            project['name'], project['description'] = name, desc
            st.success('Contexte enregistré.')
            st.rerun()
        kit.course_note('MODM vs MADM', """
- **MODM** (optimisation multi-objectifs) : on optimise simultanément plusieurs fonctions objectifs *f₁(x)…f_k(x)* sous contraintes.
- **MADM** (analyse multi-attributs) : on **classe / sélectionne** parmi *m* alternatives décrites par *n* attributs. C'est le cadre de cette application.
- Attributs **bénéfice** (à maximiser) / **coût** (à minimiser) ; **indépendants** / dépendants (→ ANP) ; **quantitatifs** / qualitatifs (à convertir en échelle numérique).""")

    # ------------------------------------------------------------------ structure
    with t2:
        kit.section('Critères', 'Sens **max** = plus c’est grand, mieux c’est (bénéfice) · **min** = plus c’est petit, mieux c’est (coût)')
        cdf = pd.DataFrame([{'Critère': c['name'], 'Sens': c['kind'], 'Unité': c.get('unit', ''), 'Poids': float(c['weight'])} for c in project['criteria']])
        ce = st.data_editor(cdf, key='mx_crit', num_rows='dynamic', hide_index=True, width='stretch',
                            column_config={'Sens': st.column_config.SelectboxColumn('Sens', options=['max', 'min'], required=True),
                                           'Poids': st.column_config.NumberColumn('Poids', min_value=0.0, step=0.01, format='%.3f')})
        kit.section('Alternatives')
        ae = st.data_editor(pd.DataFrame({'Alternative': project['alternatives']}), key='mx_alts', num_rows='dynamic', hide_index=True, width='stretch')
        if st.button('Appliquer la structure', type='primary'):
            try:
                ce2 = ce.dropna(subset=['Critère'])
                crits = [str(x).strip() for x in ce2['Critère']]
                alts = [str(x).strip() for x in ae['Alternative'].dropna()]
                new = {'name': project['name'], 'description': project.get('description', ''), 'domain': project.get('domain', ''),
                       'alternatives': alts,
                       'criteria': [{'name': str(r['Critère']).strip(), 'kind': r['Sens'] if r['Sens'] in ('max', 'min') else 'max',
                                     'unit': str(r['Unité'] or ''), 'weight': float(r['Poids'] or 0)} for _, r in ce2.iterrows()]}
                new['matrix'] = _rebuild(project, alts, crits)
                parse_project(new)
                st.session_state.project = new
                for k in [k for k in st.session_state if k.startswith('mx_mat')]:
                    del st.session_state[k]
                st.success('Structure appliquée. Complète ou ajuste les valeurs dans l’onglet « Matrice ».')
                st.rerun()
            except Exception as e:
                st.error('Impossible d’appliquer : ' + str(e))
        kit.beginner_tip('Si tu ajoutes une alternative ou un critère, ses valeurs sont initialisées avec la moyenne de la colonne : pense à les corriger dans l’onglet Matrice.')

    # ------------------------------------------------------------------ matrice
    with t3:
        kit.section('Matrice de décision D', 'Une ligne = une alternative · une colonne = un critère · xᵢⱼ = score de Aᵢ selon Cⱼ')
        units = [c.get('unit', '') for c in project['criteria']]
        cfg = {c: st.column_config.NumberColumn(f'{c} ({"↑" if k == "max" else "↓"}{" " + u if u else ""})', format='%.4g')
               for c, k, u in zip(p.criteria, p.kinds, units)}
        frame = pd.DataFrame(p.matrix, index=p.alternatives, columns=p.criteria)
        edited = st.data_editor(frame, key='mx_mat_' + str(hash(tuple(p.alternatives + p.criteria))), column_config=cfg, width='stretch')
        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button('Enregistrer la matrice', type='primary', width='stretch'):
                try:
                    v = edited.to_numpy(float)
                    if not np.isfinite(v).all():
                        raise ValueError('Valeurs manquantes ou non numériques.')
                    project['matrix'] = v.tolist()
                    for k in [k for k in st.session_state if k.startswith('sim_')]:
                        del st.session_state[k]
                    st.success('Matrice enregistrée : toutes les méthodes utiliseront ces valeurs.')
                except Exception as e:
                    st.error(str(e))
        with c2:
            st.caption('Astuce : les valeurs nulles ou négatives font basculer WSM/WPM en normalisation min-max.')
        with st.expander('Convertir des appréciations qualitatives en échelle numérique'):
            st.write('La méthode rappelle que les critères **qualitatifs** doivent être codés en valeurs numériques avant d’appliquer une méthode.')
            sc = st.selectbox('Échelle', list(SCALES))
            qdf = pd.DataFrame({'Appréciation': ['Moyen', 'Élevé', 'Faible']})
            q = st.data_editor(qdf, num_rows='dynamic', hide_index=True, key='mx_qual',
                               column_config={'Appréciation': st.column_config.SelectboxColumn(options=list(SCALES[sc]))})
            q['Valeur numérique'] = q['Appréciation'].map(SCALES[sc])
            st.dataframe(q, hide_index=True)

    # ------------------------------------------------------------------ import/export
    with t4:
        c1, c2 = st.columns(2, gap='large')
        with c1:
            kit.section('Exporter')
            st.download_button('⬇ Projet complet (JSON)', json.dumps(project, ensure_ascii=False, indent=2).encode(), 'optivest_projet.json', 'application/json', width='stretch')
            st.download_button('⬇ Matrice (CSV)', frame.reset_index(names='Alternative').to_csv(index=False).encode('utf-8-sig'), 'matrice.csv', 'text/csv', width='stretch')
            st.download_button('⬇ Classeur Excel (matrice + critères)', _xlsx(project, p), 'optivest_donnees.xlsx',
                               'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', width='stretch')
        with c2:
            kit.section('Importer')
            up = st.file_uploader('Projet JSON, matrice CSV ou classeur Excel', type=['json', 'csv', 'xlsx'])
            if up is not None and st.button('Utiliser ce fichier', type='primary'):
                try:
                    if up.name.endswith('.json'):
                        new = json.load(up)
                    else:
                        df = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up, sheet_name=0)
                        names = df.iloc[:, 0].astype(str).tolist()
                        df = df.iloc[:, 1:].apply(pd.to_numeric)
                        new = {'name': 'Projet importé', 'description': up.name, 'alternatives': names,
                               'criteria': [{'name': str(c), 'kind': 'max', 'unit': '', 'weight': 1 / df.shape[1]} for c in df.columns],
                               'matrix': df.to_numpy(float).tolist()}
                        st.info('Import tabulaire : tous les critères sont mis en « max » — corrige le sens dans l’onglet Structure.')
                    parse_project(new)
                    st.session_state.project = new
                    st.rerun()
                except Exception as e:
                    st.error('Import impossible : ' + str(e))
            kit.callout('Format CSV/Excel attendu : 1ʳᵉ colonne = noms des alternatives, colonnes suivantes = critères numériques.', 'info')

    # ------------------------------------------------------------------ diagnostic
    with t5:
        nd = [p.criteria[j] for j in range(len(p.criteria)) if np.ptp(p.matrix[:, j]) < 1e-12]
        keep = pareto(p)
        kit.kpis([('Alternatives non dominées', int(keep.sum()), 'front de Pareto', T.TEAL),
                  ('Alternatives dominées', int((~keep).sum()), 'éliminables sans regret', T.ORANGE),
                  ('Critères non discriminants', len(nd), ', '.join(nd) if nd else 'aucun', T.AMBER),
                  ('Critères bénéfice / coût', f'{p.kinds.count("max")} / {p.kinds.count("min")}', 'sens de préférence', T.BLUE)])
        a, b = st.columns(2, gap='large')
        with a:
            kit.section('Performances normalisées', '1 = meilleur sur le critère (tient compte du sens)')
            u = utility(p)
            kit.heatmap(u, p.criteria, p.alternatives, fmt='.2f', h=max(280, 46 * len(p.alternatives) + 80), zmin=0, zmax=1)
        with b:
            kit.section('Corrélation entre critères', 'Des critères très corrélés sont dépendants : la méthode renvoie vers ANP')
            if len(p.alternatives) >= 3:
                C = np.corrcoef(p.matrix.T)
                kit.heatmap(np.nan_to_num(C), p.criteria, p.criteria, scale=T.DIV, zmin=-1, zmax=1, h=max(280, 46 * len(p.criteria) + 80))
        kit.section('Profil des alternatives')
        chosen = st.multiselect('Alternatives à comparer', p.alternatives, default=p.alternatives[:3])
        if chosen:
            kit.radar(p.alternatives, p.criteria, utility(p), [p.alternatives.index(x) for x in chosen])
        st.dataframe(pd.DataFrame({'Alternative': p.alternatives, 'Non dominée (Pareto)': keep}), hide_index=True, width='stretch')
