"""Financial project appraisal: illustrative inputs, transparent real calculations.

Cash flows are net cash flows at year-end, nominal MAD million, constant discount rate.
No advice or live market data. All user supplied values must be independently validated.
"""
from dataclasses import dataclass
from typing import Optional
import numpy as np
from scipy.optimize import brentq, milp, LinearConstraint, Bounds


def npv(initial, cashflows, rate):
    if initial < 0 or rate <= -1 or not np.isfinite(initial) or not np.isfinite(rate):
        raise ValueError('Investissement >= 0 et taux > -100 % requis.')
    cf=np.asarray(cashflows,float)
    if cf.ndim != 1 or not len(cf) or not np.isfinite(cf).all():
        raise ValueError('Flux annuels finis et non vides requis.')
    return float(-initial + sum(float(v)/(1+rate)**t for t,v in enumerate(cf,1)))


def irr(initial, cashflows):
    """Unique IRR only when the full sequence has exactly one sign change."""
    seq=np.r_[-float(initial),np.asarray(cashflows,float)]
    seq=seq[np.abs(seq)>1e-12]
    if len(seq)<2 or np.sum(np.sign(seq[1:])!=np.sign(seq[:-1])) != 1:
        return None
    low=-.999; high=1.
    def f(r): return sum(v/(1+r)**t for t,v in enumerate([-initial,*cashflows]))
    try:
        while f(low)*f(high)>0 and high < 1e5:high=2*high+1
        if f(low)*f(high)>0:return None
        return float(brentq(f,low,high))
    except (ValueError,OverflowError,ZeroDivisionError):return None


def payback(initial,cashflows):
    """Simple payback with interpolation assuming annual cashflow uniform within year."""
    if initial<=0:return 0.
    cum=0.
    for t,flow in enumerate(cashflows,1):
        past=cum;cum+=float(flow)
        if past < initial <= cum and flow>0:return float(t-1+(initial-past)/flow)
    return None


def profitability_index(initial,cashflows,rate):
    if initial<=0:return None
    return float(sum(float(v)/(1+rate)**t for t,v in enumerate(cashflows,1))/initial)


def project_metrics(item,rate):
    cf=np.asarray(item['cashflows'],float)
    initial=float(item['investment'])
    return {'Projet':str(item['name']), 'Investissement':initial,
            'VAN':npv(initial,cf,rate), 'TRI':irr(initial,cf),
            'Payback':payback(initial,cf), 'IP':profitability_index(initial,cf,rate),
            'Risque':float(item['risk']), 'Alignement':float(item['alignment'])}


def evaluate_portfolio(items,rate):
    if len(items)<2:raise ValueError('Deux projets minimum pour le classement.')
    n=len(items[0]['cashflows'])
    names=[]
    for it in items:
        if len(it['cashflows']) != n:raise ValueError('Tous les projets doivent avoir le même horizon annuel.')
        if it['name'] in names:raise ValueError('Les noms des projets doivent être distincts.')
        names.append(it['name'])
        if float(it['investment'])<=0 or not 0<=float(it['risk'])<=10 or not 0<=float(it['alignment'])<=10:
            raise ValueError('Investissement positif ; risque et alignement dans [0,10].')
    return [project_metrics(it,rate) for it in items]


def to_mcdm_project(items,rate,weights=None):
    from engine.mcdm import normalize_weights
    rows=evaluate_portfolio(items,rate)
    # Payback has a documented penalty for projects never recovering investment.
    horizon=len(items[0]['cashflows']); penalty=horizon+1.
    criteria=[('VAN','max','M MAD'),('Indice de profitabilité','max','ratio'),
              ('Risque expert','min','/10'),('Payback','min','ans'),('Alignement stratégique','max','/10')]
    w=normalize_weights(weights if weights is not None else [.34,.16,.23,.14,.13])
    matrix=[[r['VAN'],r['IP'] if r['IP'] is not None else 0.,r['Risque'],
             r['Payback'] if r['Payback'] is not None else penalty,r['Alignement']] for r in rows]
    return {'name':'Prioriser des projets d’investissement','domain':'Finance d’entreprise',
            'description':'Hiérarchiser des projets d’investissement à partir de VAN, indice de profitabilité, risque expert, délai de récupération et alignement. Hypothèses fictives.',
            'alternatives':[r['Projet'] for r in rows],
            'criteria':[{'name':c,'kind':k,'unit':u,'weight':float(v)} for (c,k,u),v in zip(criteria,w)],
            'matrix':matrix}


def optimize_budget(items,rate,budget,score=None,objective='VAN'):
    """0-1 knapsack (projects independent, no synergies), SciPy HiGHS MILP."""
    rows=evaluate_portfolio(items,rate)
    if budget<0:raise ValueError('Budget négatif.')
    amounts=np.array([r['Investissement'] for r in rows])
    if score is not None:
        values=np.asarray(score,float)
    else:
        values=np.array([r['VAN'] for r in rows])
    if not np.isfinite(values).all() or len(values)!=len(items):raise ValueError('Scores invalides.')
    res=milp(c=-values,integrality=np.ones(len(items)),bounds=Bounds(np.zeros(len(items)),np.ones(len(items))),
             constraints=[LinearConstraint(amounts[None,:],-np.inf,budget)],options={'time_limit':12})
    if res.x is None:raise RuntimeError('Aucune solution obtenue par le solveur.')
    x=np.rint(res.x).astype(int)
    return {'selected':[items[i]['name'] for i in range(len(items)) if x[i]],
            'investment':float(x@amounts),'total_npv':float(sum(x[i]*rows[i]['VAN'] for i in range(len(items)))),
            'objective_value':float(x@values),'budget_remaining':float(budget-x@amounts),
            'optimal':bool(res.success),'selection':x}


def scenario_analysis(items,rate,discount_shifts=(-.02,0.,.02),cashflow_factors=(1.12,1.,.85)):
    if len(discount_shifts)!=3 or len(cashflow_factors)!=3:raise ValueError('Trois scénarios nécessaires.')
    output=[]
    for label,shift,factor in zip(['Optimiste','Central','Prudent'],discount_shifts,cashflow_factors):
        r=rate+shift
        if r<=-1:raise ValueError('Taux du scénario invalide.')
        for it in items:
            output.append({'Scénario':label,'Projet':it['name'],
                           'VAN':npv(it['investment'],np.asarray(it['cashflows'])*factor,r),
                           'Taux':r,'Facteur cash-flow':factor})
    return output


def sensitivity_curve(item,rate_min=0,rate_max=.25,n=40):
    if not (rate_min<rate_max and n>=2):raise ValueError('Intervalle invalide.')
    x=np.linspace(rate_min,rate_max,n)
    return x,np.array([npv(item['investment'],item['cashflows'],float(z)) for z in x])
