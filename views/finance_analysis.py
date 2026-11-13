"""Transparent investment appraisal, dynamic charts, MCDM input projection."""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from engine.finance import evaluate_portfolio, sensitivity_curve
from ui import kit, state, nav, theme as T


def render():
    kit.header('C · ANALYSE FINANCIÈRE','Comprendre la valeur de chaque investissement',
        'Calcule automatiquement les indicateurs à partir des flux financiers réels saisis dans l’étude. Les hypothèses, formules et limites restent visibles.',
        ['VAN','TRI','Payback','Indice de profitabilité'])
    study=st.session_state.study
    rows=evaluate_portfolio(study['projects'],study['rate'])
    df=pd.DataFrame(rows)
    k1,k2,k3,k4=st.columns(4)
    k1.metric('Taux d’actualisation',f'{study["rate"]:.1%}')
    k2.metric('VAN totale descriptive',f'{df["VAN"].sum():+.2f} M MAD')
    k3.metric('Projets avec VAN > 0',f'{(df["VAN"]>0).sum()} / {len(df)}')
    k4.metric('Projet à VAN maximale',df.loc[df['VAN'].idxmax(),'Projet'])
    st.markdown('#### Tableau financier recalculé')
    display=df.copy()
    display['TRI']=display['TRI'].map(lambda x:'N/D' if pd.isna(x) else f'{100*x:.2f} %')
    display['Payback']=display['Payback'].map(lambda x:'Non récupéré' if pd.isna(x) else f'{x:.2f} ans')
    st.dataframe(display.round(3),width='stretch',hide_index=True)
    a,b=st.columns([1.15,1])
    with a:
        kit.section('Valeur créée par projet','Plus la VAN est élevée, plus la valeur créée est importante selon le taux retenu')
        fig=go.Figure(go.Bar(x=df['VAN'],y=df['Projet'],orientation='h',
                     marker_color=[T.TEAL if v>=0 else T.ORANGE for v in df['VAN']],text=df['VAN'].map(lambda v:f'{v:+.2f} M'),textposition='outside'))
        fig.update_yaxes(autorange='reversed',showgrid=False)
        kit.show(fig,350,False)
    with b:
        kit.section('Rentabilité vs risque','Taille des points proportionnelle au capital requis')
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=df['Risque'],y=df['VAN'],mode='markers+text',text=df['Projet'],textposition='top center',
                        marker=dict(size=10+df['Investissement']*1.6,color=df['Alignement'],colorscale=[[0,'#E8A9BA'],[1,'#74CBB4']],showscale=True,
                                    colorbar=dict(title='Alignement')),hovertemplate='%{text}<br>Risque : %{x:.1f}<br>VAN : %{y:.2f} M<extra></extra>'))
        fig.update_layout(xaxis_title='Risque expert (0–10)',yaxis_title='VAN (M MAD)')
        kit.show(fig,350,False)
    kit.section('Examiner un projet dans le détail')
    choice=st.selectbox('Projet à étudier',list(df['Projet']))
    it=next(p for p in study['projects'] if p['name']==choice)
    r=next(r for r in rows if r['Projet']==choice)
    a,b=st.columns([1.05,1],gap='large')
    with a:
        periods=list(range(0,study['horizon']+1))
        discounted=[-it['investment']]+[cf/(1+study['rate'])**t for t,cf in enumerate(it['cashflows'],1)]
        cumulative=np.cumsum(discounted)
        fig=go.Figure()
        fig.add_trace(go.Bar(x=periods,y=[-it['investment'],*it['cashflows']],name='Flux non actualisés',marker_color=T.TEAL))
        fig.add_trace(go.Scatter(x=periods,y=cumulative,mode='lines+markers',name='Cumul actualisé',line=dict(color=T.ORANGE,width=4),yaxis='y2'))
        fig.update_layout(xaxis_title='Année (0 = investissement initial)',yaxis_title='Cash-flow M MAD',
            yaxis2=dict(overlaying='y',side='right',title='Cumul actualisé (M MAD)'),legend=dict(orientation='h',y=-.25))
        kit.show(fig,410)
    with b:
        st.markdown(f'### {choice}')
        kit.kpis([('VAN',f'{r["VAN"]:+.2f} M','valeur actuelle nette'),
                  ('TRI',f'{100*r["TRI"]:.1f} %' if r['TRI'] is not None else 'N/D','taux qui annule la VAN'),
                  ('Payback',f'{r["Payback"]:.2f} ans' if r['Payback'] is not None else 'Non atteint','non actualisé')])
        kit.callout('Un TRI élevé ne suffit pas pour choisir entre des projets mutuellement exclusifs. La VAN reste un indicateur important de création de valeur.','info')
        with st.expander('Définitions, formules et interprétation',expanded=True):
            st.markdown('**VAN :** somme des flux actualisés moins l’investissement initial.')
            st.latex(r'VAN=-I_0+\sum_{t=1}^{T}\frac{CF_t}{(1+r)^t}')
            st.markdown('**TRI :** taux `r` tel que `VAN(r)=0`. N/D lorsque le TRI n’est pas unique ou calculable.')
            st.markdown('**Payback simple :** première date à laquelle le cumul des flux non actualisés atteint le capital initial (interpolation annuelle).')
            st.markdown('**Indice de profitabilité :** valeur actuelle des flux futurs divisée par l’investissement initial.')
            st.latex(r'IP=\frac{\sum_{t=1}^T CF_t/(1+r)^t}{I_0}')
    kit.section('Matrice multicritère calculée','Les indicateurs ci-dessous alimentent directement TOPSIS, VIKOR et les autres méthodes.')
    p=state.problem()
    st.dataframe(pd.DataFrame(p.matrix,columns=p.criteria,index=p.alternatives).round(3),width='stretch')
    kit.callout('Payback non atteint : pénalité fixée à horizon + 1 an. Risque et alignement : notes expertes, non estimations statistiques. VAN et IP corrélés : veille à éviter leur double comptage.','warn')
    st.divider();nav.link('weights','Pondérer les critères',':material/arrow_forward:')
