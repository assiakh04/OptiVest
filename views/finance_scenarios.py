"""Financial scenario explorer, dynamic discount-rate and cashflow sensitivity."""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from engine.finance import scenario_analysis,sensitivity_curve,npv
from ui import kit,state,nav,theme as T


def render():
    kit.header('G · SCÉNARIOS & SENSIBILITÉ','Scénarios & sensibilité',
        'Explore les conséquences d’une hausse du taux d’actualisation ou d’une variation des flux prévisionnels. Les scénarios sont des hypothèses, pas des prévisions garanties.',
        ['Optimiste','Central','Prudent','Sensibilité de VAN'])
    study=st.session_state.study
    a,b,c=st.columns(3)
    with a:up=st.slider('Flux optimistes (%)',0,50,12,1)
    with b:down=st.slider('Baisse des flux prudents (%)',0,50,15,1)
    with c:shift=st.slider('Choc sur le taux (points de %)',0.,8.,2.,.5)
    try:
        scenarios=scenario_analysis(study['projects'],study['rate'],(-shift/100,0.,shift/100),(1+up/100,1.,1-down/100))
    except Exception as exc:st.error(str(exc));return
    df=pd.DataFrame(scenarios)
    kit.section('VAN par scénario','Hypothèses simultanées sur les cash-flows et le taux : analyse conditionnelle')
    fig=go.Figure()
    for label,col in zip(['Optimiste','Central','Prudent'],[T.TEAL,T.BLUE,T.ORANGE]):
        part=df[df['Scénario']==label]
        fig.add_bar(x=part['Projet'],y=part['VAN'],name=label,marker_color=col)
    fig.update_layout(barmode='group',yaxis_title='VAN (M MAD)')
    kit.show(fig,390)
    st.dataframe(df.pivot(index='Projet',columns='Scénario',values='VAN').round(3),width='stretch')
    kit.section('Sensibilité au taux d’actualisation','Une variation du taux peut renverser le classement selon la VAN.')
    selection=st.multiselect('Projets à visualiser',[x['name'] for x in study['projects']],default=[x['name'] for x in study['projects']][:3])
    max_rate=min(.40,max(.20,study['rate']+.12))
    fig=go.Figure()
    for i,item in enumerate(study['projects']):
        if item['name'] not in selection:continue
        x,y=sensitivity_curve(item,0,max_rate,75)
        fig.add_trace(go.Scatter(x=x*100,y=y,name=item['name'],mode='lines',line=dict(width=3,color=T.CAT[i%len(T.CAT)])))
    fig.add_vline(x=study['rate']*100,line_dash='dot',line_color=T.ORANGE)
    fig.add_hline(y=0,line_dash='dash',line_color='#9AA6B8')
    fig.update_layout(xaxis_title='Taux d’actualisation (%)',yaxis_title='VAN (M MAD)')
    kit.show(fig,380)
    with st.expander('Hypothèses et limites'):
        st.markdown('''- Les flux sont ajustés proportionnellement, avec le même facteur chaque année.
- Le choc de taux est ajouté/soustrait au taux central ; aucune distribution probabiliste n'est supposée.
- Ce module ne simule pas automatiquement l'inflation, la fiscalité, la dette, les corrélations entre projets ou des coûts de financement variables.
- Une analyse de robustesse multicritère complémentaire est disponible dans « Robustesse MCDM ».''')
    st.divider();nav.link('portfolio','Passer à la sélection sous budget',':material/arrow_forward:')
