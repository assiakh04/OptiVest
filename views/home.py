"""OptiVest: finance-first interactive landing page and investment dashboard."""
import html
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine.finance import evaluate_portfolio, optimize_budget
from engine.mcdm import rank, METHODS, rank_correlation
from engine.finance_examples import EXAMPLES
from ui import kit, state, nav, theme as T


def _animated_hero(title,subtitle,big='',big_label='',small=''):
    st.markdown(f'''<div class="ov-hero">
      <div class="ov-hero-copy"><div class="ov-kicker"><span class="ov-live"></span> INVESTMENT DECISION INTELLIGENCE</div>
      <h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p>
      <div class="ov-pills"><span>◆ Analyse financière</span><span>◆ Décision multicritère</span><span>◆ Risque & scénarios</span></div></div>
      <div class="ov-art" aria-hidden="true"><div class="ov-orbit ov-orbit-one"></div><div class="ov-orbit ov-orbit-two"></div>
       <div class="ov-sphere"></div><div class="ov-particle ov-p1"></div><div class="ov-particle ov-p2"></div><div class="ov-particle ov-p3"></div>
       <div class="ov-float ov-float-one"><strong>{html.escape(big)}</strong><small>{html.escape(big_label)}</small></div>
       <div class="ov-float ov-float-two"><div class="ov-bars"><i></i><i></i><i></i><i></i><i></i></div><small>{html.escape(small)}</small></div>
      </div></div>''',unsafe_allow_html=True)


def render():
    study=st.session_state.study
    _rows0=evaluate_portfolio(study['projects'],study['rate'])
    _tot=sum(r['VAN'] for r in _rows0)
    _hero=dict(big=f'{_tot:+.1f} M MAD',big_label=f'VAN cumulée · taux {100*study["rate"]:.1f} %',
               small=f'{len(_rows0)} projets · budget {study["budget"]:.0f} M')
    _animated_hero('Décider mieux. Investir plus intelligemment.',
        'Du cash-flow à la recommandation : analyse tes projets d’investissement, hiérarchise les opportunités et teste la solidité de tes décisions dans un seul espace.',**_hero)
    if st.session_state.get('beginner',True):
        kit.callout('Commence par **Étude & projets**, renseigne tes flux financiers, puis passe à **Analyse financière**, **Pondération**, **Classement**, **Robustesse** et **Rapport**.','tip')
    c1,c2,c3=st.columns([1.3,1,1])
    with c1:
        choice=st.selectbox('Étude de démonstration',list(EXAMPLES),index=list(EXAMPLES).index(st.session_state.example) if st.session_state.example in EXAMPLES else 0)
    with c2:
        st.markdown('<div style="height:27px"></div>',unsafe_allow_html=True)
        if st.button('Charger cette étude',type='primary',width='stretch'):
            state.load_finance_example(choice);st.rerun()
    with c3:
        st.markdown('<div style="height:27px"></div>',unsafe_allow_html=True)
        nav.link('study','Créer / modifier une étude',':material/add_circle:')
    rows=evaluate_portfolio(study['projects'],study['rate'])
    positive=sum(r['VAN']>0 for r in rows)
    p=state.problem()
    results={m:rank(p,m) for m in METHODS}
    mean_rank=np.mean([r['ranks'] for r in results.values()],axis=0)
    lead=p.alternatives[int(np.argmin(mean_rank))]
    budget_result=optimize_budget(study['projects'],study['rate'],study['budget'])
    kit.kpis([('Budget disponible',f'{study["budget"]:.1f} M MAD','plafond d’investissement',T.TEAL),
             ('Projets analysés',len(rows),f'{positive} VAN positives',T.BLUE),
             ('VAN cumulées',f'{sum(r["VAN"] for r in rows):+.2f} M','somme descriptive, sans contrainte de budget',T.ORANGE),
             ('Leader multicritère',lead,'premier au rang moyen',T.AMBER),
             ('Budget optimisé',f'{budget_result["investment"]:.1f} M','maximisation de la VAN sous budget',T.GREEN)])
    a,b=st.columns([1.25,1],gap='large')
    with a:
        kit.section('Valeur actuelle nette · par projet','En millions de MAD · données de démonstration fictives')
        colors=[T.TEAL if x['VAN']>=0 else T.ORANGE for x in rows]
        fig=go.Figure(go.Bar(x=[r['VAN'] for r in rows],y=[r['Projet'] for r in rows],orientation='h',
                marker=dict(color=colors,cornerradius=8),text=[f'{r["VAN"]:+.2f} M' for r in rows],textposition='outside',cliponaxis=False))
        fig.update_yaxes(autorange='reversed',showgrid=False)
        fig.update_xaxes(title='VAN · millions MAD')
        kit.show(fig,345,False)
    with b:
        kit.section('Priorités de décision', 'Pondération actuellement utilisée par les modèles MCDM')
        kit.donut(p.criteria,p.weights,345)
    a,b=st.columns([1.15,1],gap='large')
    with a:
        kit.section('Performance des projets · flux nets annuels','Les flux sont éditables dans Étude & projets')
        fig=go.Figure()
        for i,it in enumerate(study['projects']):
            fig.add_trace(go.Scatter(x=list(range(1,len(it['cashflows'])+1)),y=it['cashflows'],mode='lines+markers',name=it['name'],
                                     line=dict(width=3,color=T.CAT[i%len(T.CAT)],shape='spline'),marker=dict(size=7)))
        fig.update_layout(xaxis_title='Année',yaxis_title='Cash-flow · M MAD')
        kit.show(fig,355,True)
    with b:
        kit.section('Premier diagnostic', 'Lecture synthétique avant le choix')
        best=max(rows,key=lambda r:r['VAN'])
        kit.card('RENTABILITÉ',best['Projet'],f'VAN la plus élevée : {best["VAN"]:+.2f} M MAD. Ne suffit pas à déterminer le meilleur projet.','teal')
        kit.card('ALLOCATION',f'{len(budget_result["selected"])} projets sélectionnés',
                 f'Optimisation de la VAN totale, indépendance supposée. Budget restant : {budget_result["budget_remaining"]:.2f} M MAD.','blue')
        kit.callout('Les critères VAN et indice de profitabilité sont liés. Les pondérer tous les deux peut surreprésenter la rentabilité : vérifie les poids et teste la robustesse.','warn')
    kit.section('Ton parcours de décision','Un itinéraire simple ; les méthodes spécialisées restent accessibles dans la barre latérale')
    steps=[('01','Définir les projets','Investissement, flux de trésorerie, risque','study'),
           ('02','Évaluer la finance','VAN, TRI, payback, IP','financial'),
           ('03','Pondérer & classer','AHP, BWM, TOPSIS, VIKOR','weights'),
           ('04','Tester & arbitrer','Scénarios, budget et robustesse','scenarios'),
           ('05','Présenter la décision','Rapport, preuves et hypothèses','invest_report')]
    cols=st.columns(5)
    for col,(num,title,desc,target) in zip(cols,steps):
        with col:
            kit.card('ÉTAPE '+num,title,desc,'teal' if num in ('01','05') else 'blue')
            nav.link(target,'Ouvrir',':material/arrow_forward:')
    kit.section('Classements croisés','Un rang 1 indique la meilleure position pour une méthode, pas une probabilité de succès')
    matrix=pd.DataFrame({m:result['ranks'] for m,result in results.items()},index=p.alternatives)
    kit.heatmap(matrix.values,matrix.columns,matrix.index,scale=[[0,'#FFA67E'],[.5,'#F4EBEC'],[1,'#87C8C6']],fmt='d',h=350)
    st.caption('Ces résultats reposent sur les hypothèses de l’étude. Les simulations et les préférences doivent être validées avant toute décision financière réelle.')
