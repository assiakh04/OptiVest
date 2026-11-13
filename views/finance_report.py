"""Investor-ready report: source-backed financial assumptions, ranked opportunities and allocations."""
import html
import io
import json
import numpy as np
import pandas as pd
import streamlit as st
from engine.finance import evaluate_portfolio,optimize_budget
from engine.mcdm import rank,METHODS,rank_correlation
from ui import kit,state,theme as T


def render():
    kit.header('M · RAPPORT FINAL','Rapport & décision',
               'Réunis les hypothèses financières, les scores MCDM, les contraintes budgétaires et un argumentaire vérifiable dans un document autonome.',
               ['Rapport PDF','HTML','Excel','CSV','JSON'])
    study=st.session_state.study;p=state.problem();rows=evaluate_portfolio(study['projects'],study['rate'])
    results={m:rank(p,m) for m in METHODS}
    ranks=pd.DataFrame({name:r['ranks'] for name,r in results.items()},index=p.alternatives)
    ranks['Rang moyen']=ranks.mean(axis=1)
    lead=str(ranks['Rang moyen'].idxmin())
    alloc=optimize_budget(study['projects'],study['rate'],study['budget'])
    _,corr=rank_correlation(results)
    agree=float(np.mean(corr[np.triu_indices(len(corr),1)]))
    kit.kpis([('Leader MCDM',lead,'rang moyen le plus faible',T.TEAL),
              ('Accord des méthodes',f'{agree:.2f}','Spearman moyen',T.BLUE),
              ('VAN du portefeuille',f'{alloc["total_npv"]:+.2f} M','optimisation sous budget',T.ORANGE),
              ('Capital utilisé',f'{alloc["investment"]:.2f} M','sur '+str(study['budget'])+' M MAD',T.GREEN)])
    kit.section('Construire la recommandation')
    explanation=st.text_area('Justification de la décision',value=st.session_state.justification,height=130,
         placeholder='Résume la stratégie de pondération, la cohérence des classements, les incertitudes et les limites de l’étude…')
    st.session_state.justification=explanation
    kit.section('Données de restitution')
    financial=pd.DataFrame(rows)
    st.dataframe(financial.round(3),width='stretch',hide_index=True)
    st.dataframe(ranks.sort_values('Rang moyen').round(3),width='stretch')
    def esc(t):return html.escape(str(t))
    financ_html=financial.to_html(index=False,border=0,escape=True,na_rep='N/D',float_format=lambda x:f'{x:.3f}')
    rang_html=ranks.to_html(border=0,escape=True,float_format=lambda x:f'{x:.3f}')
    criterion_html=pd.DataFrame({'Critère':p.criteria,'Direction':p.kinds,'Poids':p.weights}).to_html(index=False,border=0,escape=True,float_format=lambda x:f'{x:.3f}')
    selected=', '.join(alloc['selected']) or 'Aucun'
    html_doc=f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>OptiVest · {esc(study['study_name'])}</title>
<style>body{{font-family:Arial,sans-serif;background:#f9fafc;color:#182f44;margin:0;padding:48px;line-height:1.55}}main{{max-width:1050px;margin:auto}}
h1{{font-size:38px;color:#123c50}}h2{{margin-top:38px;color:#218b88}}.hero{{background:#e2f4ef;padding:26px;border-radius:18px}}table{{width:100%;border-collapse:collapse;background:#fff;margin:15px 0}}
th,td{{padding:10px;border-bottom:1px solid #dbe5ec;text-align:left;font-size:13px}}th{{background:#e5eef4}}p{{max-width:900px}}small{{color:#677b88}}</style></head><body><main>
<p>OPTIVEST · INVESTMENT INTELLIGENCE</p><div class="hero"><h1>{esc(study['study_name'])}</h1><p>Rapport d’évaluation et de priorisation de projets d’investissement.</p>
<p>Budget : {study['budget']:.2f} M MAD · Taux d’actualisation : {study['rate']:.1%} · Horizon : {study['horizon']} ans.</p></div>
<h2>Recommandations</h2><p>Leader multicritère selon le rang moyen : <b>{esc(lead)}</b>. Corrélation moyenne des rangs : {agree:.3f}.</p>
<p>Projets retenus par optimisation de VAN sous budget : <b>{esc(selected)}</b>. Investissement retenu : {alloc['investment']:.3f} M MAD. VAN totale : {alloc['total_npv']:.3f} M MAD.</p>
<h2>Indicateurs financiers</h2>{financ_html}<h2>Pondération et orientation</h2>{criterion_html}
<h2>Classements comparés</h2>{rang_html}<h2>Justification</h2><p>{esc(explanation).replace(chr(10),'<br>') or 'À compléter.'}</p>
<h2>Hypothèses et limites</h2><p>Montants fictifs, flux de fin d’année, taux constant, projets supposés indépendants et indivisibles, allocation sous budget simple. Les notes de risque et d’alignement sont subjectives. Les indicateurs VAN et indice de profitabilité peuvent être corrélés. Les classements ne constituent ni une garantie de performance ni un conseil financier.</p>
<small>Généré depuis OptiVest · vérifier chaque donnée avant utilisation.</small></main></body></html>'''
    excel=io.BytesIO()
    with pd.ExcelWriter(excel,engine='openpyxl') as writer:
        financial.to_excel(writer,'Analyse financière',index=False)
        pd.DataFrame({'Critère':p.criteria,'Poids':p.weights,'Sens':p.kinds}).to_excel(writer,'Pondération',index=False)
        ranks.to_excel(writer,'Classements')
        pd.DataFrame({'Projets retenus':alloc['selected']}).to_excel(writer,'Allocation',index=False)
    from engine.pdf_report import build_pdf
    pdf=build_pdf(study,financial,list(zip(p.criteria,p.kinds,p.weights)),ranks,alloc,lead,agree,explanation,st.session_state.get('method_profile'))
    e,a,b,c,d=st.columns(5)
    e.download_button('Rapport PDF',pdf,'OptiVest_rapport.pdf','application/pdf',type='primary',width='stretch')
    a.download_button('Rapport HTML',html_doc.encode('utf-8'),'OptiVest_rapport.html','text/html',width='stretch')
    b.download_button('Excel',excel.getvalue(),'OptiVest_analyse.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',width='stretch')
    c.download_button('CSV',financial.to_csv(index=False).encode('utf-8-sig'),'OptiVest_finance.csv','text/csv',width='stretch')
    d.download_button('JSON',json.dumps(study,ensure_ascii=False,indent=2).encode('utf-8'),'OptiVest_etude.json','application/json',width='stretch')
    kit.callout('Le classement MCDM et le portefeuille qui maximise la VAN sont deux décisions différentes. Une hiérarchie ne résout pas à elle seule les contraintes budgétaires.','tip')
