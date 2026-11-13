"""Smoke tests des pages financières OptiVest + export PDF."""
import sys
from pathlib import Path
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.finance import evaluate_portfolio, optimize_budget  # noqa: E402
from engine.finance_examples import BASE  # noqa: E402
from engine.pdf_report import build_pdf  # noqa: E402

PAGES = ['home', 'finance_study', 'finance_analysis', 'finance_scenarios', 'finance_portfolio', 'finance_report', 'guide']


@pytest.mark.parametrize('page', PAGES)
def test_finance_page(page):
    src = (f"import sys; sys.path.insert(0, {str(ROOT)!r})\nimport streamlit as st\nfrom ui import state, nav\nstate.init()\n"
           f"from views import {page}\n{page}.render()\n")
    at = AppTest.from_string(src, default_timeout=240).run()
    assert not at.exception, [e.value for e in at.exception]


def test_pdf_export():
    rows = pd.DataFrame(evaluate_portfolio(BASE['projects'], BASE['rate']))
    ranks = pd.DataFrame({'TOPSIS': [1, 2, 3, 4, 5]}, index=[r['name'] for r in BASE['projects']])
    alloc = optimize_budget(BASE['projects'], BASE['rate'], BASE['budget'])
    pdf = build_pdf(BASE, rows, [('VAN', 'max', .5), ('Risque', 'min', .5)], ranks, alloc, 'X', .9, 'ok')
    assert pdf[:4] == b'%PDF' and len(pdf) > 2000
