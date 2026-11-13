"""Tests : on retrouve les résultats des exercices du cours."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import fuzzy as F, single as S
from engine.examples import EXAMPLES, AHP_CAR
from engine.mcdm import (Problem, ahp, ahp_hierarchy, bwm, normalize_weights, parse_project, rank, spearman, entropy, critic, METHODS)


def test_spearman_course():
    t, v, p = [2, 1, 3, 5, 4, 6], [1, 2, 4, 3, 5, 6], [2, 1, 3, 6, 4, 5]
    assert round(spearman(t, v), 2) == 0.77 and round(spearman(t, p), 2) == 0.94 and round(spearman(v, p), 2) == 0.60


def test_bwm_xi():
    r = bwm(0, 3, [1, 3, 4, 8], [8, 5, 3, 1])
    assert abs(r['xi'] - 0.08) < 0.01 and abs(r['weights'].sum() - 1) < 1e-9 and r['weights'].argmax() == 0


def test_ahp_car():
    r = ahp(np.array(AHP_CAR['criteria_matrix']))
    assert r['consistent'] and abs(r['weights'].sum() - 1) < 1e-9
    h = ahp_hierarchy(np.array(AHP_CAR['criteria_matrix']), [np.array(m) for m in AHP_CAR['alt_matrices']])
    assert np.allclose(h['local'][:, 0], [.875, .125], atol=1e-3) and h['final'].argmax() == 0


def test_all_methods_run_everywhere():
    for e in EXAMPLES.values():
        p = parse_project(e)
        for m in METHODS:
            r = rank(p, m)
            assert len(r['ranks']) == len(p.alternatives) and r['ranks'].min() == 1
        assert abs(entropy(p)['weights'].sum() - 1) < 1e-9 and abs(critic(p)['weights'].sum() - 1) < 1e-9


def test_topsis_dominant():
    p = Problem(['A', 'B'], ['x', 'y'], ['max', 'min'], normalize_weights([1, 1]), np.array([[9, 1], [1, 9]], float))
    assert rank(p, 'TOPSIS')['ranks'].tolist() == [1, 2]


def test_roc_course():
    rows = S.roc_table([.85, .78, .71, .69, .62, .54], [1, 1, 1, 0, 0, 0], [.75, .65, .60])
    assert [round(r['J'], 2) for r in rows] == [0.67, 0.67, 0.33]
    assert [round(r['d'], 2) for r in rows] == [0.33, 0.33, 0.67]


def test_fuzzy_single_course():
    r = F.fuzzy_single_eval([(1.0, 1.2, 1.5), (110, 120, 130)], [.6, .4])
    assert abs(r['score'] - 0.863) < 1e-3


def test_hesitant_course():
    h1, h2, h3 = [.2, .3, .5, .8], [.4, .6, .8], [.3, .45, .6]
    assert F.hfn_compare(h2, h1) == 1 and F.hfn_compare(h3, h1) == 1


def test_ifn_ops_valid():
    a, b = (.6, .3), (.5, .4)
    for r in (F.ifn_add(a, b), F.ifn_mul(a, b), F.ifn_scale(2, a), F.ifn_power(a, 2)):
        assert F.ifn_valid(r)
