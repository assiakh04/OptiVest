import copy
import numpy as np
import pytest
from engine.finance import npv,irr,payback,profitability_index,project_metrics,evaluate_portfolio,to_mcdm_project,optimize_budget,scenario_analysis,sensitivity_curve
from engine.finance_examples import BASE
from engine.mcdm import parse_project,rank,METHODS


def test_npv_exact():
    assert npv(100,[60,60],0)==pytest.approx(20)
    assert npv(100,[60,60],.1)==pytest.approx(-100+60/1.1+60/1.1**2)


def test_irr_defined_and_undefined():
    assert irr(100,[110])==pytest.approx(.1,abs=1e-8)
    assert irr(100,[-20,150]) is not None
    assert irr(100,[-10,-20]) is None
    assert irr(100,[230,-132]) is None  # two sign changes


def test_simple_payback():
    assert payback(100,[20,40,50])==pytest.approx(2.8)
    assert payback(100,[10,20]) is None
    assert payback(0,[20])==0


def test_profitability_index():
    assert profitability_index(100,[60,60],0)==pytest.approx(1.2)


def test_finance_to_mcdm():
    rows=evaluate_portfolio(BASE['projects'],BASE['rate'])
    assert len(rows)==5
    assert all(np.isfinite(r['VAN']) for r in rows)
    assert all(r['TRI'] is not None for r in rows)
    p=parse_project(to_mcdm_project(BASE['projects'],BASE['rate']))
    assert p.matrix.shape==(5,5)
    for method in METHODS:
        r=rank(p,method)
        assert len(r['ranks'])==5
        assert np.isfinite(r['scores']).all()


def test_budget_allocation_true_optimum():
    items=[{'name':f'P{i}','investment':inv,'cashflows':[npv0+inv],'risk':3,'alignment':5}
           for i,(inv,npv0) in enumerate([(6,11),(4,8),(5,10)],1)]
    result=optimize_budget(items,0,10)
    # independent additive VAN optimum 11+8 with costs 6+4 =19; other pair 8+10=18
    assert result['total_npv']==pytest.approx(19)
    assert result['investment']==pytest.approx(10)
    assert result['optimal']


def test_study_budget():
    a=optimize_budget(BASE['projects'],BASE['rate'],BASE['budget'])
    assert a['investment']<=BASE['budget']
    assert len(a['selected'])>0
    assert a['optimal']


def test_scenarios_order():
    r=scenario_analysis(BASE['projects'],BASE['rate'])
    assert len(r)==15
    a=[x for x in r if x['Projet']==BASE['projects'][0]['name']]
    assert a[0]['VAN']>a[1]['VAN']>a[2]['VAN']


def test_sensitivity_discount_rate():
    x,y=sensitivity_curve(BASE['projects'][0])
    assert len(x)==40
    assert np.all(np.diff(y)<0)  # because all example cashflows are positive


def test_validation():
    bad=copy.deepcopy(BASE['projects']);bad[0]['investment']=0
    with pytest.raises(ValueError):evaluate_portfolio(bad,.1)
    with pytest.raises(ValueError):npv(-1,[1],.1)
    with pytest.raises(ValueError):optimize_budget(BASE['projects'],.1,-1)
