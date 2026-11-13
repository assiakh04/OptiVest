"""All project and cashflow inputs are fictional, for educational demonstrations only."""
import copy
from .finance import to_mcdm_project

BASE={
 'study_name':'Programme d’investissement stratégique 2027',
 'budget':30., 'rate':.10, 'currency':'M MAD', 'horizon':5,
 'projects':[
  {'name':'Solaire Atlas','investment':18.,'cashflows':[4.0,5.1,5.9,6.4,7.2],'risk':3.2,'alignment':9.3},
  {'name':'Industrie 4.0','investment':12.,'cashflows':[2.9,3.5,4.1,4.5,4.7],'risk':4.4,'alignment':8.8},
  {'name':'Hub logistique','investment':15.,'cashflows':[3.1,4.0,4.7,5.4,5.8],'risk':5.7,'alignment':7.6},
  {'name':'Plateforme FinTech','investment':7.,'cashflows':[0.8,1.6,2.7,3.8,5.3],'risk':8.1,'alignment':8.4},
  {'name':'Recyclage durable','investment':9.,'cashflows':[2.1,2.8,3.1,3.5,4.0],'risk':4.2,'alignment':9.0},
 ]
}
ALTERNATIVE=copy.deepcopy(BASE)
ALTERNATIVE['study_name']='Innovation et transition durable 2028'
ALTERNATIVE['budget']=24.
ALTERNATIVE['rate']=.12
ALTERNATIVE['projects'][0]['investment']=17.
ALTERNATIVE['projects'][1]['cashflows']=[2.3,3.,3.9,4.9,5.5]
ALTERNATIVE['projects'][3]['cashflows']=[.6,1.2,2.,3.5,6.2]
EXAMPLES={'Investissements stratégiques · 2027':BASE,'Innovation & transition · 2028':ALTERNATIVE}


def initial_study():return copy.deepcopy(BASE)
