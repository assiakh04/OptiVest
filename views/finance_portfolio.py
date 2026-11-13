"""Investment allocation under budget constraint: real 0-1 MILP."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine.finance import evaluate_portfolio,optimize_budget
from engine.mcdm import rank
from ui import kit,state,nav,theme as T


def render():
    kit.header('L · ALLOCATION BUDGÉTAIRE','Optimiser le portefeuille de projets',
        'Le classement mesure l’attractivité relative des projets ; l’allocation sélectionne une combinaison finançable, sous un budget maximal.',
        ['Optimisation binaire','Budget limité','VAN totale','Choix traçables'])
    study=st.session_state.study;p=state.problem();rows=evaluate_portfolio(study['projects'],study['rate'])
    col1,col2=st.columns(2)
    with col1: budget=st.number_input('Budget à allouer (M MAD)',min_value=0.,value=float(study['budget']),step=1.)
    with col2: objective=st.selectbox('Objectif du portefeuille',['Maximiser la VAN totale','Maximiser la somme des scores TOPSIS'])
    if 'TOPSIS' in objective:
        r=rank(p,'TOPSIS');vals=r['scores']
        kit.callout('Sommer des coefficients TOPSIS est une heuristique académique de préférence : ce n’est ni la VAN financière ni une utilité monétaire validée.','warn')
    else: vals=None
    result=optimize_budget(study['projects'],study['rate'],budget,score=vals)
    kit.kpis([('Projets financés',len(result['selected']),'retenus sous contrainte',T.TEAL),
              ('Capital mobilisé',f'{result["investment"]:.2f} M','du budget sélectionné',T.BLUE),
              ('Budget restant',f'{result["budget_remaining"]:.2f} M','non investi',T.ORANGE),
              ('VAN des projets retenus',f'{result["total_npv"]:+.2f} M','somme des VAN sélectionnées',T.GREEN)])
    df=pd.DataFrame(rows)
    df['Décision']=df['Projet'].map(lambda n:'✓ Retenir' if n in result['selected'] else '— Non retenu')
    df['Investissement cumulé']=np.nan
    st.dataframe(df[['Projet','Investissement','VAN','Risque','Décision']].round(3),width='stretch',hide_index=True)
    fig=go.Figure(go.Bar(x=df['Projet'],y=df['Investissement'],
                   marker_color=[T.TEAL if n in result['selected'] else '#CED8E3' for n in df['Projet']],
                   text=df['Investissement'].map(lambda n:f'{n:.1f} M'),textposition='outside'))
    fig.update_layout(yaxis_title='Investissement (M MAD)')
    kit.show(fig,350,False)
    kit.section('Utilisation du capital','Budget alloué, capital mobilisé et reliquat')
    sel_inv=[r['Investissement'] for r in rows if r['Projet'] in result['selected']]
    fig2=go.Figure()
    base=0.
    for r in rows:
        if r['Projet'] in result['selected']:
            fig2.add_trace(go.Bar(x=[r['Investissement']],y=['Capital'],orientation='h',name=r['Projet'],
                marker=dict(color=T.CAT[rows.index(r)%len(T.CAT)]),text=f'{r["Projet"]}<br>{r["Investissement"]:.1f} M',textposition='inside'))
    fig2.add_trace(go.Bar(x=[max(result['budget_remaining'],0)],y=['Capital'],orientation='h',name='Reliquat',marker=dict(color='#E3E9F2'),
                          text=f'Reliquat {result["budget_remaining"]:.1f} M',textposition='inside'))
    fig2.update_layout(barmode='stack',xaxis_title='Millions MAD (budget = '+f'{budget:.1f})',yaxis=dict(visible=False))
    kit.show(fig2,210,True)
    kit.section('Classement individuel vs portefeuille optimisé','Un projet bien classé n’est pas forcément retenu : le portefeuille dépend aussi de son coût')
    cons=rank(p,'TOPSIS')['ranks']
    cmp_df=pd.DataFrame({'Projet':[r['Projet'] for r in rows],'Rang TOPSIS':cons,'Rang par VAN':pd.Series([r['VAN'] for r in rows]).rank(ascending=False,method='min').astype(int),
                         'Investissement':[r['Investissement'] for r in rows],'VAN':[r['VAN'] for r in rows],
                         'Portefeuille':['✓ Retenu' if r['Projet'] in result['selected'] else '— Écarté' for r in rows]}).sort_values('Rang TOPSIS')
    st.dataframe(cmp_df.round(3),width='stretch',hide_index=True)
    top_out=[n for n,rk in zip(cmp_df['Projet'],cmp_df['Rang TOPSIS']) if rk<=2 and n not in result['selected']]
    if top_out:kit.callout('Projet(s) bien classé(s) mais non retenu(s) sous ce budget : **'+', '.join(top_out)+'**. Raison probable : un coût d’investissement élevé par rapport à la VAN apportée.','info')
    else:kit.callout('Les projets les mieux classés sont tous retenus : classement individuel et portefeuille convergent.','ok')
    st.info('Projets sélectionnés : '+(', '.join(result['selected']) if result['selected'] else 'aucun')+'.')
    with st.expander('Modèle d’optimisation et hypothèses',expanded=True):
        st.markdown('L’application utilise une optimisation linéaire en nombres entiers (0/1).')
        st.latex(r'\max \sum_{i=1}^{m} VAN_i x_i\quad\text{s.c.}\quad\sum_{i=1}^{m} I_i x_i\le B,\qquad x_i\in\{0,1\}')
        st.markdown('En mode « score TOPSIS », le coefficient `VANᵢ` de l’objectif est remplacé par le score `TOPSISᵢ`.')
        st.caption('Hypothèses : projets indépendants, entièrement finançables ou non, sans synergie, dépendance, exclusivité ou calendrier de capital. Le budget est une contrainte et non un critère à compter deux fois.')
        if not result['optimal']:st.warning('Le solveur n’a pas certifié l’optimalité avant sa limite de calcul.')
    st.divider();nav.link('invest_report','Préparer le rapport de décision',':material/arrow_forward:')
