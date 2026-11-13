"""OptiVest · Financial Investment Decision Intelligence · Streamlit app."""
from pathlib import Path
import html
import streamlit as st

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='OptiVest · Investment Intelligence',page_icon='💠',layout='wide',initial_sidebar_state='expanded')
from ui import nav,state,theme

st.markdown('<style>'+theme.CSS+'</style>',unsafe_allow_html=True)
state.init()
st.logo(str(ROOT / 'assets/logo.svg'), icon_image=str(ROOT / 'assets/icon.svg'), size='large')
nav.PAGES.clear()

def page(key,mod,title,icon,default=False):
    import importlib
    fn=importlib.import_module('views.'+mod).render
    pg=st.Page(fn,title=title,icon=icon,url_path=key,default=default)
    nav.PAGES[key]=pg
    return pg

groups={
    '01 · COMMENCER':[
        page('home','home','Vue d’ensemble',':material/dashboard:',True),
        page('study','finance_study','Étude & projets',':material/folder_open:'),
        page('financial','finance_analysis','Analyse financière',':material/monitoring:'),
    ],
    '02 · DÉCISION MCDM':[
        page('guide','guide','Choisir la méthode',':material/alt_route:'),
        page('weights','weights','Pondération',':material/balance:'),
        page('additive','additive','Classement MCDM',':material/leaderboard:'),
        page('outrank','outrank','Surclassement',':material/hub:'),
        page('compare','compare','Comparaison des rangs',':material/compare_arrows:'),
    ],
    '03 · RISQUE ET ARBITRAGE':[
        page('scenarios','finance_scenarios','Scénarios financiers',':material/query_stats:'),
        page('robust','robust','Robustesse MCDM',':material/shield:'),
        page('portfolio','finance_portfolio','Allocation du budget',':material/account_balance_wallet:'),
    ],
    '04 · SPÉCIALISÉES':[
        page('single','single','Projet individuel',':material/target:'),
        page('fuzzy_lab','fuzzy_lab','Laboratoire flou',':material/blur_on:'),
        page('fuzzy_mcdm','fuzzy_mcdm','Classements flous',':material/grain:'),
        page('ai','ai_page','IA & explicabilité',':material/psychology:'),
        page('dynamic','dynamic','Analyse dynamique',':material/timeline:'),
    ],
    '05 · RESTITUTION':[
        page('invest_report','finance_report','Rapport d’investissement',':material/article:'),
    ],
}

current=st.navigation(groups,expanded=True)
with st.sidebar:
    study=st.session_state.study
    st.markdown(f'<div class="side-card"><div class="t">ÉTUDE ACTIVE</div><div class="v">{html.escape(study["study_name"])}</div><div class="s">{len(study["projects"])} projets · Budget {study["budget"]:.1f} M MAD<br>Poids : {html.escape(st.session_state.weight_source)}</div></div>',unsafe_allow_html=True)
    _all=set(st.session_state.get('done',set()))
    _tot=len(nav.PAGES)-1
    st.markdown(f'<div class="side-card"><div class="t">PARCOURS</div><div class="v">{len(_all)} analyses explorées</div><div class="ov-prog"><i style="width:{min(100,100*len(_all)/max(_tot,1)):.0f}%"></i></div><div class="s">de l’étude au rapport final</div></div>',unsafe_allow_html=True)
    st.toggle('Afficher les explications',key='beginner',help='Définitions, conseils et hypothèses visibles dans chaque module.')
    st.caption('Démonstration financière · Données fictives · Calculs locaux')

current.run()
st.markdown('<div class="footer">OptiVest · Analyse financière et aide multicritère à la décision · Les calculs dépendent des hypothèses, des préférences et des données saisies.</div>',unsafe_allow_html=True)
