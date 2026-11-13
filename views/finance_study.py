"""Study editor: actual investment cashflow inputs, persistent session state, JSON roundtrip."""
import copy
import json
import numpy as np
import pandas as pd
import streamlit as st
from engine.finance import evaluate_portfolio
from engine.finance_examples import EXAMPLES
from ui import kit,state,nav


def render():
    kit.header('B · ÉTUDE & PROJETS','Étude & projets',
               'Construis une étude financière : budget, horizon, taux d’actualisation, coûts initiaux et flux annuels. Les indicateurs et la matrice multicritère seront recalculés à partir de ces hypothèses.',
               ['Données éditables','Cash-flows annuels','Import JSON','Validation'])
    study=st.session_state.study
    tabs=st.tabs(['01 · Paramètres','02 · Projets & flux','03 · Import / export','04 · Contrôle qualité'])
    with tabs[0]:
        kit.section('Paramètres de l’étude','Les montants sont exprimés en millions de dirhams (M MAD), avec des flux de fin d’année.')
        with st.form('settings_form'):
            name=st.text_input('Nom de l’étude',study['study_name'])
            c1,c2,c3=st.columns(3)
            with c1:budget=st.number_input('Budget disponible (M MAD)',min_value=0.,value=float(study['budget']),step=1.)
            with c2:rate=st.number_input('Taux d’actualisation (%)',min_value=0.,max_value=100.,value=float(study['rate']*100),step=.5)
            with c3:horizon=st.number_input('Horizon (années)',min_value=2,max_value=15,value=int(study['horizon']),step=1)
            saved=st.form_submit_button('Enregistrer les paramètres',type='primary')
        if saved:
            study['study_name']=name.strip() or 'Étude sans titre'
            study['budget']=float(budget);study['rate']=float(rate/100)
            oldh=study['horizon'];study['horizon']=int(horizon)
            if oldh!=horizon:
                for it in study['projects']:
                    it['cashflows']=(it['cashflows']+[0.] * max(0,horizon-len(it['cashflows'])))[:horizon]
            state.sync_study();st.success('Paramètres enregistrés et données recalculées.');st.rerun()
        kit.beginner_tip('Le taux d’actualisation exprime le rendement minimal exigé et la valeur temporelle de l’argent. Il doit être justifié et reste constant dans cette version.')
        st.latex(r'VAN=-I_0+\sum_{t=1}^{T}\frac{CF_t}{(1+r)^t}')
    with tabs[1]:
        kit.section('Saisir les opportunités','Tu peux modifier les investissements, le risque expert (0 à 10), l’alignement (0 à 10) et les flux par année.')
        cols=['Projet','Investissement','Risque','Alignement']+[f'Année {t}' for t in range(1,study['horizon']+1)]
        df=pd.DataFrame([[it['name'],it['investment'],it['risk'],it['alignment'],*it['cashflows']] for it in study['projects']],columns=cols)
        cfg={'Projet':st.column_config.TextColumn(required=True),
             'Investissement':st.column_config.NumberColumn(min_value=0.01,step=1.),
             'Risque':st.column_config.NumberColumn(min_value=0.,max_value=10.,step=.5),
             'Alignement':st.column_config.NumberColumn(min_value=0.,max_value=10.,step=.5)}
        for c in cols[4:]:cfg[c]=st.column_config.NumberColumn(step=.5)
        edited=st.data_editor(df,num_rows='dynamic',hide_index=True,column_config=cfg,width='stretch',key='study_edit_cashflows')
        if st.button('Enregistrer tous les projets',type='primary'):
            try:
                items=[]
                for _,row in edited.iterrows():
                    if row.isna().any():raise ValueError('Certaines cellules sont vides.')
                    items.append({'name':str(row['Projet']).strip(),'investment':float(row['Investissement']),
                                  'risk':float(row['Risque']),'alignment':float(row['Alignement']),
                                  'cashflows':[float(row[f'Année {t}']) for t in range(1,study['horizon']+1)]})
                evaluate_portfolio(items,study['rate'])
                study['projects']=items
                state.sync_study()
                if 'study_edit_cashflows' in st.session_state:del st.session_state['study_edit_cashflows']
                st.success('Projets enregistrés. Les résultats financiers et multicritères sont actualisés.');st.rerun()
            except Exception as exc:st.error('Données incorrectes : '+str(exc))
        kit.beginner_tip('Une année peut avoir un cash-flow négatif. Le TRI n’est affiché que lorsque son calcul est interprétable de façon unique.')
    with tabs[2]:
        kit.section('Sauvegarder et retrouver une étude')
        st.download_button('Télécharger l’étude financière (JSON)',data=json.dumps(study,ensure_ascii=False,indent=2).encode('utf-8'),file_name='optivest_etude.json',mime='application/json')
        up=st.file_uploader('Importer une étude OptiVest au format JSON',type='json')
        if up is not None and st.button('Importer cette étude'):
            try:
                item=json.load(up)
                for req in ['study_name','budget','rate','horizon','projects']:
                    if req not in item:raise ValueError('Champ manquant : '+req)
                if not 2<=int(item['horizon'])<=15:raise ValueError('Horizon hors limites.')
                if not 0<=float(item['rate'])<=1:raise ValueError('Taux attendu entre 0 et 1.')
                if float(item['budget'])<0:raise ValueError('Budget invalide.')
                evaluate_portfolio(item['projects'],item['rate'])
                if len(item['projects'][0]['cashflows'])!=int(item['horizon']):raise ValueError('Horizon incompatible.')
                st.session_state.study=item
                state.sync_study(preserve_weights=False)
                st.success('Étude importée.');st.rerun()
            except Exception as exc:st.error('Import impossible : '+str(exc))
        kit.section('Importer des projets (CSV ou Excel)','Format large : Projet, Investissement, Risque, Alignement, puis une colonne par année (A1, A2, …)')
        h=int(study['horizon'])
        tpl=pd.DataFrame([{'Projet':it['name'],'Investissement':it['investment'],'Risque':it.get('risk',5),'Alignement':it.get('alignment',5),
                           **{f'A{k+1}':v for k,v in enumerate(it['cashflows'])}} for it in study['projects']])
        st.download_button('Télécharger le modèle CSV',tpl.to_csv(index=False).encode('utf-8-sig'),'optivest_modele_projets.csv','text/csv')
        tab=st.file_uploader('Fichier de projets',type=['csv','xlsx'],key='tab_up')
        if tab is not None and st.button('Importer ces projets',key='tab_btn'):
            try:
                df=pd.read_csv(tab,sep=None,engine='python') if tab.name.lower().endswith('csv') else pd.read_excel(tab)
                df.columns=[str(c).strip() for c in df.columns]
                need=['Projet','Investissement']
                miss=[c for c in need if c not in df.columns]
                if miss:raise ValueError('Colonne(s) manquante(s) : '+', '.join(miss))
                years=[c for c in df.columns if c.upper().startswith('A') and c[1:].isdigit()]
                years=sorted(years,key=lambda c:int(c[1:]))
                if len(years)<2:raise ValueError('Au moins deux colonnes de flux (A1, A2, …) sont nécessaires.')
                items=[]
                for _,r in df.iterrows():
                    items.append({'name':str(r['Projet']),'investment':float(r['Investissement']),
                                  'cashflows':[float(r[c]) for c in years],
                                  'risk':float(r['Risque']) if 'Risque' in df.columns else 5.0,
                                  'alignment':float(r['Alignement']) if 'Alignement' in df.columns else 5.0})
                if len({i['name'] for i in items})!=len(items):raise ValueError('Noms de projets en double.')
                if len(items)<2:raise ValueError('Au moins deux projets sont nécessaires.')
                evaluate_portfolio(items,study['rate'])
                study['projects']=items;study['horizon']=len(years)
                state.sync_study(preserve_weights=False)
                st.success(f'{len(items)} projets importés sur {len(years)} années.');st.rerun()
            except Exception as exc:st.error('Import impossible : '+str(exc))
        st.info('Les valeurs de démonstration sont fictives. Les données importées restent dans la session de l’application tant que tu ne les exportes pas.')
    with tabs[3]:
        kit.section('Diagnostic financier')
        try:
            rows=evaluate_portfolio(study['projects'],study['rate'])
            kit.kpis([('Projets',len(rows),'évalués'),('VAN positives',sum(r['VAN']>0 for r in rows),'VAN > 0'),
                      ('TRI non disponibles',sum(r['TRI'] is None for r in rows),'valeurs à examiner')])
            st.dataframe(pd.DataFrame(rows).round(3),width='stretch',hide_index=True)
            risky=[r['Projet'] for r in rows if r['Risque']>=7]
            if risky:kit.callout('Projets à risque expert élevé (≥ 7/10) : '+', '.join(risky),'warn')
        except Exception as exc:st.error(str(exc))
    st.divider();nav.link('financial','Continuer vers l’analyse financière',':material/arrow_forward:')
