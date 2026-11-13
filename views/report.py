"""M · SYNTHÈSE MCDM : synthèse, justification, bonnes pratiques et exports."""
import html
import io
import json
import numpy as np
import pandas as pd
import streamlit as st
from engine.mcdm import METHODS, rank, rank_correlation, sensitivity
from ui import kit, state, theme as T

PRACTICES = [('weights', 'Pondération justifiée (AHP, BWM, entropie, CRITIC ou hybride)'),
             ('additive', 'Au moins une méthode additive appliquée'),
             ('outrank', 'Une méthode de surclassement appliquée pour croiser les résultats'),
             ('compare', 'Plusieurs méthodes comparées (Spearman)'),
             ('robust', 'Analyse de robustesse / sensibilité réalisée')]


def render():
    p = state.problem()
    kit.header('Restitution', 'Rapport & export',
               'Synthèse de la décision : classement consensuel, accord entre méthodes, robustesse et justification écrite — prête à être exportée.',
               ['Synthèse', 'Bonnes pratiques', 'Excel · CSV · HTML · JSON'])
    results = {m: rank(p, m) for m in METHODS}
    _, C = rank_correlation(results)
    agree = float(np.mean(C[np.triu_indices(len(C), 1)]))
    ranks_df = pd.DataFrame({m: r['ranks'] for m, r in results.items()}, index=p.alternatives)
    ranks_df['Rang moyen'] = ranks_df.mean(axis=1)
    final = ranks_df.sort_values('Rang moyen')
    lead = final.index[0]
    s = sensitivity(p, 'TOPSIS', 200, 40)
    stab = float(s['win_rate'][p.alternatives.index(lead)])
    kit.kpis([('Recommandation', lead, f'rang moyen {final.iloc[0]["Rang moyen"]:.2f}', T.ORANGE), ('Accord des méthodes', f'{agree:.2f}', 'ρ de Spearman moyen', T.TEAL),
              ('Stabilité (Monte-Carlo)', f'{100 * stab:.0f} %', f'« {lead} » reste n°1 (TOPSIS)', T.GREEN if stab >= .7 else T.AMBER), ('Poids', st.session_state.weight_source, 'source active', T.BLUE)])
    a, b = st.columns([1.2, 1], gap='large')
    with a:
        kit.section('Classement final')
        m = len(p.alternatives)
        cons = 1 - (final['Rang moyen'] - 1) / max(m - 1, 1)
        kit.bar_ranking(list(final.index), cons.to_numpy(), np.arange(1, m + 1), title='Score de consensus')
    with b:
        kit.section('Bonnes pratiques de référence')
        done = st.session_state.done
        for key, label in PRACTICES:
            st.markdown(('✅ ' if key in done else '⬜ ') + label)
        st.progress(sum(k in done for k, _ in PRACTICES) / len(PRACTICES))
        st.caption('Visite les pages correspondantes pour valider chaque point.')
    kit.section('Justification du choix', 'La méthode insiste : le choix de la méthode et des poids doit être explicitement justifié')
    just = st.text_area('Ton argumentaire', st.session_state.justification, height=140, placeholder='Pourquoi ces poids ? Pourquoi ces méthodes ? Quelles limites ?')
    st.session_state.justification = just

    # ------------------------------------------------------------ exports
    kit.section('Exporter')
    scores_df = pd.DataFrame({'Alternative': p.alternatives, **{f'Score {m}': r['scores'] for m, r in results.items()}})
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as xw:
        pd.DataFrame(p.matrix, index=p.alternatives, columns=p.criteria).to_excel(xw, sheet_name='Matrice')
        pd.DataFrame({'Critère': p.criteria, 'Sens': p.kinds, 'Poids': p.weights}).to_excel(xw, sheet_name='Poids', index=False)
        ranks_df.round(3).to_excel(xw, sheet_name='Rangs')
        scores_df.round(5).to_excel(xw, sheet_name='Scores', index=False)
        pd.DataFrame(C, index=list(results), columns=list(results)).round(3).to_excel(xw, sheet_name='Spearman')
        pd.DataFrame({'Justification': [just]}).to_excel(xw, sheet_name='Justification', index=False)
    rows = ''.join(f'<tr><td>{html.escape(str(i))}</td>' + ''.join(f'<td>{v:.2f}</td>' for v in r) + '</tr>' for i, r in zip(final.index, final.to_numpy()))
    head = ''.join(f'<th>{html.escape(c)}</th>' for c in final.columns)
    wrows = ''.join(f'<tr><td>{html.escape(c)}</td><td>{k}</td><td>{100 * w:.1f} %</td></tr>' for c, k, w in zip(p.criteria, p.kinds, p.weights))
    page = f"""<!doctype html><meta charset=utf-8><title>Rapport OptiVest</title><style>body{{font-family:Segoe UI,Arial;max-width:860px;margin:30px auto;color:#0E2238}}
h1{{color:#0A2540}}h2{{color:#0A8F8B;border-bottom:2px solid #FF7A3D;padding-bottom:4px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #D9E2EC;padding:6px 10px;text-align:center}}th{{background:#0A2540;color:#fff}}</style>
<h1>{html.escape(p_name(st))}</h1><p>{html.escape(st.session_state.project.get('description', ''))}</p>
<h2>Recommandation</h2><p><b>{html.escape(lead)}</b> — rang moyen {final.iloc[0]['Rang moyen']:.2f} ; accord des méthodes ρ = {agree:.2f} ; stabilité Monte-Carlo {100 * stab:.0f} %.</p>
<h2>Poids ({html.escape(st.session_state.weight_source)})</h2><table><tr><th>Critère</th><th>Sens</th><th>Poids</th></tr>{wrows}</table>
<h2>Rangs par méthode</h2><table><tr><th>Alternative</th>{head}</tr>{rows}</table>
<h2>Justification</h2><p>{html.escape(just).replace(chr(10), '<br>') or '—'}</p>"""
    c1, c2, c3, c4 = st.columns(4)
    c1.download_button('⬇ Excel complet', buf.getvalue(), 'optivest_resultats.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', width='stretch', type='primary')
    c2.download_button('⬇ Rapport HTML', page.encode(), 'optivest_rapport.html', 'text/html', width='stretch')
    c3.download_button('⬇ Scores (CSV)', scores_df.to_csv(index=False).encode('utf-8-sig'), 'scores.csv', 'text/csv', width='stretch')
    c4.download_button('⬇ Projet (JSON)', json.dumps(st.session_state.project, ensure_ascii=False, indent=2).encode(), 'projet.json', 'application/json', width='stretch')
    st.dataframe(final.round(2), width='stretch')
    state.mark('report')


def p_name(st_):
    return st_.session_state.project.get('name', 'Projet')
