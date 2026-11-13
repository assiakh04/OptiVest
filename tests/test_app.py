"""Smoke test : chaque page s'exécute sans exception pour chaque scénario."""
import os
import sys
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.examples import EXAMPLES  # noqa: E402

PAGES = ['home', 'data', 'guide', 'weights', 'additive', 'outrank', 'compare', 'robust', 'single', 'fuzzy_lab', 'fuzzy_mcdm', 'ai_page', 'dynamic', 'report']


@pytest.mark.parametrize('page', PAGES)
@pytest.mark.parametrize('example', list(EXAMPLES)[:3])
def test_page(page, example):
    src = (f"import sys; sys.path.insert(0, {str(ROOT)!r})\nimport streamlit as st\nfrom ui import state\nstate.init()\n"
           f"state.load_example({example!r})\nfrom views import {page}\n{page}.render()\n")
    at = AppTest.from_string(src, default_timeout=240).run()
    assert not at.exception, [e.value for e in at.exception]
