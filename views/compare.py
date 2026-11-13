"""Analyse 2d — Comparaison des méthodes et corrélation de Spearman."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine.examples import SPEARMAN_COURSE
from engine.mcdm import METHODS, rank, rank_correlation, spearman, spearman_significance
from ui import kit, state, theme as T


def render():
    p = state.problem()
    kit.header('G · COMPARAISON DES MÉTHODES', 'Comparer les méthodes',
               'Appliquer plusieurs méthodes est une bonne pratique de référence : si elles s’accordent, la décision est solide. '
               'La corrélation de Spearman mesure cet accord : ρ = 1 − 6Σd² / (n(n²−1)).',
               ['Rangs par méthode', 'ρ de Spearman', 'Test de significativité', 'Exemple de référence'])
    t1, t2 = st.tabs(['Mon projet', 'Exemple Spearman de référence'])
    with t1:
        chosen = st.multiselect('Méthodes comparées', METHODS, default=METHODS)
        if len(chosen) < 2:
            st.info('Choisis au moins deux méthodes.')
            return
        res = {m: rank(p, m) for m in chosen}
        ahp_r = st.session_state.get('ahp_result')
        if ahp_r and ahp_r['alts'] == p.alternatives and st.checkbox('Inclure AHP complet (calculé dans la page Méthodes additives)', True):
            res['AHP'] = {'ranks': np.array(ahp_r['ranks']), 'scores': np.array(ahp_r['scores'])}
        ranks_df = pd.DataFrame({m: r['ranks'] for m, r in res.items()}, index=p.alternatives)
        ranks_df['Rang moyen'] = ranks_df.mean(axis=1)
        ranks_df['Meilleur rang'] = ranks_df.drop(columns='Rang moyen').min(axis=1)
        ranks_df['Pire rang'] = ranks_df.drop(columns=['Rang moyen', 'Meilleur rang']).max(axis=1)
        keys, C = rank_correlation(res)
        agree = float(np.mean(C[np.triu_indices(len(C), 1)]))
        lead = ranks_df['Rang moyen'].idxmin()
        kit.kpis([('Leader consensuel', lead, f'rang moyen {ranks_df.loc[lead, "Rang moyen"]:.2f}', T.ORANGE),
                  ('Accord moyen (ρ)', f'{agree:.2f}', 'fort ≥ 0,8 · moyen ≥ 0,5', T.TEAL),
                  ('Premier selon', f'{sum(1 for m in keys if res[m]["ranks"][p.alternatives.index(lead)] == 1)} / {len(keys)}', 'méthodes', T.BLUE)])
        a, b = st.columns([1.1, 1], gap='large')
        with a:
            kit.section('Rangs par méthode')
            show = ranks_df.sort_values('Rang moyen')
            st.dataframe(kit.style_rank(show, keys).format({'Rang moyen': '{:.2f}'}), width='stretch')
            kit.download_csv(show.reset_index(names='Alternative'), 'comparaison_rangs.csv')
        with b:
            kit.section('Évolution du rang (bump chart)')
            fig = go.Figure()
            for i, a_ in enumerate(p.alternatives):
                fig.add_trace(go.Scatter(x=keys, y=[res[m]['ranks'][i] for m in keys], name=a_, mode='lines+markers',
                                         line=dict(width=3, color=T.CAT[i % 8]), marker=dict(size=9)))
            fig.update_yaxes(autorange='reversed', dtick=1, title='Rang')
            kit.show(fig, 330)
        kit.section('Matrice de corrélation de Spearman', 'Les cases bordées de « ✓ » dépassent le seuil de significativité à 5 % (table de référence pour n ≤ 10)')
        n = len(p.alternatives)
        txt = [[f'{C[i, j]:.2f}' + (' ✓' if i != j and spearman_significance(C[i, j], n)[0] else '') for j in range(len(keys))] for i in range(len(keys))]
        fig = go.Figure(go.Heatmap(z=C, x=keys, y=keys, zmin=-1, zmax=1, colorscale=T.DIV, text=txt, texttemplate='%{text}', xgap=3, ygap=3, colorbar=dict(thickness=10)))
        fig.update_yaxes(autorange='reversed')
        kit.show(fig, max(340, 50 * len(keys) + 80), legend=False)
        crit = spearman_significance(.9, n)[1]
        if crit:
            st.caption(f'Valeur critique de ρ à 5 % pour n = {n} : {crit}.')
        # diagnostic automatique
        kit.section('Lecture automatique')
        groups = {}
        for i, m in enumerate(keys):
            for j in range(i + 1, len(keys)):
                if C[i, j] < 0:
                    groups.setdefault('neg', []).append((m, keys[j], C[i, j]))
        if agree >= .8:
            kit.callout('**Accord fort** : les méthodes convergent, la décision est robuste au choix de la méthode.', 'ok')
        elif groups.get('neg'):
            ratio_based = {'WSM', 'WPM', 'WASPAS', 'TOPSIS'} & set(keys)
            minmax_based = {'VIKOR', 'PROMETHEE II', 'ELECTRE III'} & set(keys)
            if ratio_based and minmax_based:
                kit.callout('**Désaccord structurel** : les méthodes à normalisation par ratio/vecteur (WSM, WPM, WASPAS, TOPSIS) s’opposent à celles qui utilisent l’étendue (VIKOR, PROMETHEE, ELECTRE). '
                            'C’est typique quand des critères ont des valeurs proches en valeur relative mais très dispersées en étendue. Vérifie la normalisation et les seuils avant de conclure.', 'warn')
            else:
                kit.callout('Certaines méthodes se contredisent (ρ < 0) : explique pourquoi avant de décider.', 'warn')
        else:
            kit.callout('**Accord moyen** : le haut du classement est probablement stable, le bas l’est moins.', 'info')
        stable = ranks_df[ranks_df['Pire rang'] - ranks_df['Meilleur rang'] <= 1].index.tolist()
        if stable:
            st.write('Alternatives au rang très stable (écart ≤ 1 entre méthodes) : **' + ', '.join(stable) + '**.')
        state.mark('compare')
    with t2:
        kit.section('Reproduire l’exemple de référence', 'A1…A6 classées par TOPSIS, VIKOR et PROMETHEE II : la méthode trouve ρ(T,V) = 0,77 · ρ(T,P) = 0,94 · ρ(V,P) = 0,60')
        df = pd.DataFrame(SPEARMAN_COURSE)
        edited = st.data_editor(df, hide_index=True, disabled=['Alternative'], width='stretch', key='sp_course')
        cols = ['TOPSIS', 'VIKOR', 'PROMETHEE II']
        C = np.array([[spearman(edited[a], edited[b]) for b in cols] for a in cols])
        kit.heatmap(C, cols, cols, scale=T.DIV, zmin=-1, zmax=1, h=300)
        n = len(df)
        for i in range(3):
            for j in range(i + 1, 3):
                ok, crit = spearman_significance(C[i, j], n)
                st.markdown(f'ρ({cols[i]}, {cols[j]}) = **{C[i, j]:.2f}** — ' + ('significatif' if ok else 'non significatif') + f' à 5 % (seuil {crit}).')
        kit.course_note('Spearman', 'ρ = 1 − 6Σdᵢ² / (n(n²−1)). Interprétation : proche de 1 → classements très proches ; proche de 0 → peu de lien ; négatif → classements opposés. Pour n = 6, ρ ≥ 0,886 est significatif à 5 %.')
