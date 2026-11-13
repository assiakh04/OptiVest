"""MCDM pour évaluer une alternative isolée (évaluation absolue) — MAUT, seuils, ROC, distance à l'idéal."""
import numpy as np

EPS = 1e-12


def utilities(values, lo, hi, kinds):
    """u_j : (x − x_min)/(x_max − x_min) pour un bénéfice ; (x − x_max)/(x_min − x_max) pour un coût (cours)."""
    v, lo, hi = (np.asarray(a, float) for a in (values, lo, hi))
    if np.any(hi <= lo):
        raise ValueError('Chaque borne max doit être strictement supérieure à la borne min.')
    u = np.array([(v[j] - lo[j]) / (hi[j] - lo[j]) if k == 'max' else (v[j] - hi[j]) / (lo[j] - hi[j])
                  for j, k in enumerate(kinds)])
    return np.clip(u, 0, 1)


def maut(values, lo, hi, kinds, weights, threshold=0.7, classes=(0.8, 0.6, 0.4)):
    """S(A) = Σ w_j u_j(x_j) ; décision Accepter si S ≥ τ ; classe A/B/C/D et niveau de risque."""
    w = np.asarray(weights, float)
    w = w / w.sum()
    u = utilities(values, lo, hi, kinds)
    s = float(u @ w)
    a, b, c = classes
    cls = 'A' if s >= a else 'B' if s >= b else 'C' if s >= c else 'D'
    risk = {'A': 'Faible', 'B': 'Modéré', 'C': 'Élevé', 'D': 'Très élevé'}[cls]
    return {'score': s, 'utility': u, 'contrib': u * w, 'accepted': s >= threshold, 'class': cls, 'risk': risk}


def distance_to_ideal(values, lo, hi, kinds, weights=None):
    """Indice de type TOPSIS pour une alternative unique : C = D⁻ / (D⁺ + D⁻)."""
    u = utilities(values, lo, hi, kinds)
    w = np.full(len(u), 1 / len(u)) if weights is None else np.asarray(weights, float) / np.sum(weights)
    d_plus = float(np.sqrt(np.sum(w * (1 - u) ** 2)))
    d_minus = float(np.sqrt(np.sum(w * u ** 2)))
    return {'D_plus': d_plus, 'D_minus': d_minus, 'C': d_minus / max(d_plus + d_minus, EPS), 'u': u}


def roc_table(scores, labels, thresholds=None):
    """Pour chaque seuil τ : TPR, FPR, distance au point idéal d, indice de Youden J. labels : 1 = accepter."""
    s = np.asarray(scores, float)
    y = np.asarray(labels, int)
    if thresholds is None:
        u = np.unique(s)
        mids = (u[:-1] + u[1:]) / 2
        thresholds = np.r_[u.min() - 1e-6, mids, u.max() + 1e-6]
    rows = []
    P, N = max((y == 1).sum(), 1), max((y == 0).sum(), 1)
    for t in thresholds:
        pred = (s >= t).astype(int)
        tp = int(((pred == 1) & (y == 1)).sum()); fp = int(((pred == 1) & (y == 0)).sum())
        fn = int(((pred == 0) & (y == 1)).sum()); tn = int(((pred == 0) & (y == 0)).sum())
        tpr, fpr = tp / P, fp / N
        rows.append({'seuil': float(t), 'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn, 'TPR': tpr, 'FPR': fpr,
                     'd': float(np.sqrt(fpr ** 2 + (1 - tpr) ** 2)), 'J': tpr - fpr,
                     'exactitude': (tp + tn) / len(y)})
    return rows


def auc(rows):
    pts = sorted({(r['FPR'], r['TPR']) for r in rows} | {(0.0, 0.0), (1.0, 1.0)})
    f, t = zip(*pts)
    return float(np.trapezoid(t, f))


def best_threshold(rows, criterion='youden', cost_fp=1.0, cost_fn=1.0):
    if criterion == 'youden':
        return max(rows, key=lambda r: (round(r['J'], 12), r['seuil']))
    if criterion == 'distance':
        return min(rows, key=lambda r: (round(r['d'], 12), -r['seuil']))
    if criterion == 'exactitude':
        return max(rows, key=lambda r: (round(r['exactitude'], 12), r['seuil']))
    return min(rows, key=lambda r: (cost_fp * r['FP'] + cost_fn * r['FN'], -r['seuil']))
