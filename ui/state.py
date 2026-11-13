"""Etat applicatif du projet, avec intégration des études financières et banque MCDM."""
import copy
import streamlit as st
from engine.finance_examples import initial_study
from engine.finance import to_mcdm_project
from engine.mcdm import parse_project, normalize_weights


def init():
    ss=st.session_state
    if 'study' not in ss:ss.study=initial_study()
    if 'project' not in ss:ss.project=to_mcdm_project(ss.study['projects'],ss.study['rate'])
    ss.setdefault('weight_source','Pondération initiale · expert')
    ss.setdefault('bank',{})
    ss.setdefault('done',set())
    ss.setdefault('beginner',True)
    ss.setdefault('ahp_result',None)
    ss.setdefault('justification','')
    ss.setdefault('example','Investissements stratégiques · 2027')
    ss.setdefault('finance_synced',True)


def sync_study(preserve_weights=True):
    ss=st.session_state
    w=[c['weight'] for c in ss.project['criteria']] if preserve_weights and len(ss.project['criteria'])==5 else None
    ss.project=to_mcdm_project(ss.study['projects'],ss.study['rate'],w)
    ss.finance_synced=True
    ss.ahp_result=None
    for key in list(ss):
        if key.startswith(('sim_','mx_mat_','study_edit_')):del ss[key]


def load_finance_example(name):
    from engine.finance_examples import EXAMPLES
    ss=st.session_state
    ss.study=copy.deepcopy(EXAMPLES[name]);ss.example=name
    ss.project=to_mcdm_project(ss.study['projects'],ss.study['rate'])
    ss.weight_source='Pondération initiale · expert';ss.bank={};ss.done=set();ss.ahp_result=None
    ss.finance_synced=True
    for key in list(ss):
        if key.startswith(('sim_','mx_','fz_','ahpm_','study_edit_')):del ss[key]


def load_example(name):
    # MCDM engine still supports imports without the finance study.
    from engine.examples import EXAMPLES
    ss=st.session_state
    ss.project=copy.deepcopy(EXAMPLES[name]);ss.example=name
    ss.finance_synced=False;ss.weight_source='Pondération importée';ss.bank={};ss.ahp_result=None


def problem():
    try:return parse_project(st.session_state.project)
    except Exception as exc:
        st.error('Le problème est invalide : '+str(exc))
        if st.button('Restaurer l’étude de démonstration'):
            st.session_state.study=initial_study();sync_study(False);st.rerun()
        st.stop()


def set_weights(w,source):
    vals=normalize_weights(w)
    for c,v in zip(st.session_state.project['criteria'],vals):c['weight']=float(v)
    st.session_state.weight_source=source
    st.session_state.bank[source]=[float(v) for v in vals]
    for k in list(st.session_state):
        if k.startswith('sim_'):del st.session_state[k]


def bank_put(source,w):st.session_state.bank[source]=[float(v) for v in normalize_weights(w)]
def mark(key):st.session_state.done.add(key)
