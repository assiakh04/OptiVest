"""Logique floue et MCDM floue — chapitres 4 et 5 du cours.

Ensembles flous classiques, nombres flous trapézoïdaux/triangulaires, nombres d'intervalle,
ensembles flous intuitionnistes (IFS), pythagoriciens (PFS), q-rung orthopair (q-ROFS) y compris à
valeur d'intervalle, picturaux (PicFS) et hésitants (HFS) ; puis Fuzzy TOPSIS (Chen, 2000),
Fuzzy TOPSIS intuitionniste et évaluation floue d'une alternative isolée.
"""
import numpy as np

EPS = 1e-12


# =========================================================================== fonctions d'appartenance
def trapezoid(x, a, b, c, d):
    x = np.asarray(x, float)
    up = np.where(b > a, (x - a) / max(b - a, EPS), (x >= a).astype(float))
    dn = np.where(d > c, (d - x) / max(d - c, EPS), (x <= d).astype(float))
    return np.clip(np.minimum(np.minimum(up, 1.0), dn), 0, 1)


def triangle(x, a, b, c):
    return trapezoid(x, a, b, b, c)


def gaussian(x, m, sigma):
    x = np.asarray(x, float)
    return np.exp(-((x - m) ** 2) / (2 * max(sigma, EPS) ** 2))


def membership(kind, x, params):
    if kind == 'Trapézoïdale':
        return trapezoid(x, *params)
    if kind == 'Triangulaire':
        return triangle(x, *params)
    return gaussian(x, *params)


def fuzzy_set_properties(x, mu, alpha=0.5):
    """Hauteur, support, noyau, α-coupe, normalisation, convexité d'un ensemble flou discrétisé."""
    x, mu = np.asarray(x, float), np.asarray(mu, float)
    support = x[mu > EPS]
    kernel = x[mu >= 1 - 1e-9]
    cut = x[mu >= alpha - 1e-12]
    # convexité : μ(λx1+(1−λ)x2) ≥ min(μ(x1), μ(x2)) ⇔ μ est quasi-concave (unimodale)
    peak = int(np.argmax(mu))
    convex = bool(np.all(np.diff(mu[:peak + 1]) >= -1e-9) and np.all(np.diff(mu[peak:]) <= 1e-9))
    rng = lambda v: (float(v.min()), float(v.max())) if len(v) else None
    return {'height': float(mu.max()), 'normalized': bool(abs(mu.max() - 1) < 1e-9), 'support': rng(support),
            'kernel': rng(kernel), 'alpha_cut': rng(cut), 'convex': convex}


def complement(mu):
    return 1 - np.asarray(mu, float)


def fuzzy_union(m1, m2):
    return np.maximum(m1, m2)


def fuzzy_intersection(m1, m2):
    return np.minimum(m1, m2)


# =========================================================================== nombres flous trapézoïdaux
def tfn_add(A, B): return tuple(a + b for a, b in zip(A, B))
def tfn_sub(A, B): return (A[0] - B[3], A[1] - B[2], A[2] - B[1], A[3] - B[0])
def tfn_mul(A, B): return tuple(a * b for a, b in zip(A, B))
def tfn_scale(l, A): return tuple(l * a for a in A)
def tfn_div(A, B): return (A[0] / B[3], A[1] / B[2], A[2] / B[1], A[3] / B[0])


def to_trapezoid(t):
    return tuple(t) if len(t) == 4 else (t[0], t[1], t[1], t[2])


# =========================================================================== nombres d'intervalle
def int_add(A, B): return (A[0] + B[0], A[1] + B[1])
def int_sub(A, B): return (A[0] - B[1], A[1] - B[0])
def int_scale(l, A): return (l * A[0], l * A[1])


def int_mul(A, B):
    pr = [A[0] * B[0], A[0] * B[1], A[1] * B[0], A[1] * B[1]]
    return (min(pr), max(pr))


def int_div(A, B):
    if B[0] <= 0 <= B[1]:
        raise ValueError('Division impossible : 0 appartient à B.')
    return (A[0] / B[1], A[1] / B[0])


def int_center(A): return (A[0] + A[1]) / 2
def int_width(A): return (A[1] - A[0]) / 2


# =========================================================================== intuitionniste (IFN)
def ifn_valid(a): return a[0] >= 0 and a[1] >= 0 and a[0] + a[1] <= 1 + 1e-9
def ifn_hesitation(a): return 1 - a[0] - a[1]
def ifn_add(a, b): return (a[0] + b[0] - a[0] * b[0], a[1] * b[1])
def ifn_mul(a, b): return (a[0] * b[0], a[1] + b[1] - a[1] * b[1])
def ifn_scale(l, a): return (1 - (1 - a[0]) ** l, a[1] ** l)
def ifn_power(a, l): return (a[0] ** l, 1 - (1 - a[1]) ** l)
def ifn_score(a): return a[0] - a[1]
def ifn_accuracy(a): return a[0] + a[1]


def ifn_compare(a, b):
    """1 si a > b ; −1 si a < b ; 0 si égaux (score puis fonction de précision)."""
    sa, sb = ifn_score(a), ifn_score(b)
    if abs(sa - sb) > 1e-12:
        return 1 if sa > sb else -1
    ha, hb = ifn_accuracy(a), ifn_accuracy(b)
    if abs(ha - hb) > 1e-12:
        return 1 if ha > hb else -1
    return 0


def ifwa(items, sigma):
    """IFWA_σ(α1,…,αk) = (1 − Π(1−μj)^σj , Π νj^σj)."""
    s = np.asarray(sigma, float)
    s = s / s.sum()
    mu = 1 - np.prod([(1 - a[0]) ** sj for a, sj in zip(items, s)])
    nu = np.prod([a[1] ** sj for a, sj in zip(items, s)])
    return (float(mu), float(nu))


# =========================================================================== pythagoricien / q-ROF / picture
def pfn_valid(a): return a[0] ** 2 + a[1] ** 2 <= 1 + 1e-9
def pfn_hesitation(a): return float(np.sqrt(max(0, 1 - a[0] ** 2 - a[1] ** 2)))
def pfn_score(a): return a[0] ** 2 - a[1] ** 2
def qrof_valid(a, q): return a[0] ** q + a[1] ** q <= 1 + 1e-9
def qrof_hesitation(a, q): return float(max(0, 1 - a[0] ** q - a[1] ** q) ** (1 / q))
def qrof_score(a, q): return a[0] ** q - a[1] ** q


def ivqrof_hesitation(mu, nu, q):
    """Hésitation à valeur d'intervalle : π ∈ [ (1−μU^q−νU^q)^(1/q) , (1−μL^q−νL^q)^(1/q) ]."""
    lo = max(0, 1 - mu[1] ** q - nu[1] ** q) ** (1 / q)
    hi = max(0, 1 - mu[0] ** q - nu[0] ** q) ** (1 / q)
    return (float(lo), float(hi))


def ivqrof_valid(mu, nu, q): return mu[1] ** q + nu[1] ** q <= 1 + 1e-9


def picture_valid(a): return all(v >= 0 for v in a) and sum(a) <= 1 + 1e-9
def picture_refusal(a): return 1 - sum(a)
def picture_add(a, b): return (a[0] + b[0] - a[0] * b[0], a[1] * b[1], a[2] * b[2])
def picture_scale(l, a): return (1 - (1 - a[0]) ** l, a[1] ** l, a[2] ** l)
def picture_power(a, l): return (a[0] ** l, 1 - (1 - a[1]) ** l, 1 - (1 - a[2]) ** l)


# =========================================================================== hésitant
def hfn_score(h): return float(np.mean(h))
def hfn_deviation(h): return float(np.sqrt(np.mean((np.asarray(h) - np.mean(h)) ** 2)))
def hfn_power(h, a): return sorted({round(g ** a, 10) for g in h})
def hfn_scale(a, h): return sorted({round(1 - (1 - g) ** a, 10) for g in h})
def hfn_add(h1, h2): return sorted({round(a + b - a * b, 10) for a in h1 for b in h2})
def hfn_mul(h1, h2): return sorted({round(a * b, 10) for a in h1 for b in h2})


def hfn_compare(h1, h2):
    s1, s2 = hfn_score(h1), hfn_score(h2)
    if abs(s1 - s2) > 1e-12:
        return 1 if s1 > s2 else -1
    d1, d2 = hfn_deviation(h1), hfn_deviation(h2)
    if abs(d1 - d2) > 1e-12:
        return 1 if d1 < d2 else -1
    return 0


def hfn_hamming(h1, h2, extend='max'):
    a, b = sorted(h1), sorted(h2)
    L = max(len(a), len(b))
    pad = (lambda v: v + [max(v) if extend == 'max' else min(v)] * (L - len(v)))
    a, b = sorted(pad(a)), sorted(pad(b))
    return float(np.mean(np.abs(np.array(a) - np.array(b))))


# =========================================================================== échelles linguistiques
# Chen (2000) : 7 niveaux pour évaluer les alternatives et l'importance des critères
RATING_SCALE = {'Très faible': (0, 0, 1), 'Faible': (0, 1, 3), 'Moyen faible': (1, 3, 5), 'Moyen': (3, 5, 7),
                'Moyen bon': (5, 7, 9), 'Bon': (7, 9, 10), 'Très bon': (9, 10, 10)}
WEIGHT_SCALE = {'Très peu important': (0, 0, .1), 'Peu important': (0, .1, .3), 'Assez peu important': (.1, .3, .5),
                'Moyennement important': (.3, .5, .7), 'Assez important': (.5, .7, .9), 'Important': (.7, .9, 1),
                'Très important': (.9, 1, 1)}
# Échelle intuitionniste (μ, ν) — modifiable dans l'application
IFN_SCALE = {'Excellent': (0.90, 0.05), 'Très bon': (0.80, 0.15), 'Bon': (0.65, 0.30), 'Moyen': (0.50, 0.45),
             'Faible': (0.30, 0.65), 'Très faible': (0.10, 0.85)}


# =========================================================================== MCDM floue
def defuzzify(t):
    return float(np.mean(t))


def fuzzy_single_eval(ratings, weights, cmax=None):
    r = np.asarray(ratings, float)                       # (n_crit, 3)
    w = np.asarray(weights, float)
    w = w / w.sum()
    cm = np.asarray(cmax if cmax is not None else r[:, 2], float)
    norm = r / cm[:, None]
    agg = (w[:, None] * norm).sum(axis=0)
    return {'normalized': norm, 'aggregate': agg, 'score': float(agg.mean()), 'width': float(agg[2] - agg[0])}


def fuzzy_topsis(ratings, weights, kinds=None):
    """Fuzzy TOPSIS de Chen (2000), cours : décideurs K, alternatives m, critères n.

    ratings : [K, m, n, 3] ; weights : [K, n, 3] (poids linguistiques par décideur) ; kinds : 'max'/'min' par critère.
    """
    r = np.asarray(ratings, float)
    w = np.asarray(weights, float)
    K, m, n, _ = r.shape
    kinds = kinds or ['max'] * n
    x = r.mean(axis=0)                                  # évaluations collectives (m, n, 3)
    wt = w.mean(axis=0)                                 # poids collectifs (n, 3)
    nm = np.zeros_like(x)
    for j in range(n):
        if kinds[j] == 'max':
            cs = max(x[:, j, 2].max(), EPS)
            nm[:, j, :] = x[:, j, :] / cs
        else:
            am = max(x[:, j, 0].min(), EPS)
            nm[:, j, 0] = am / np.maximum(x[:, j, 2], EPS)
            nm[:, j, 1] = am / np.maximum(x[:, j, 1], EPS)
            nm[:, j, 2] = am / np.maximum(x[:, j, 0], EPS)
    v = nm * wt[None, :, :]                             # produit ⊗ (composante par composante)
    ones, zeros = np.ones(3), np.zeros(3)
    d_plus = np.sqrt(((v - ones) ** 2).mean(axis=2)).sum(axis=1)
    d_minus = np.sqrt(((v - zeros) ** 2).mean(axis=2)).sum(axis=1)
    cc = d_minus / np.maximum(d_plus + d_minus, EPS)
    order = np.argsort(-cc, kind='stable')
    rk = np.empty(m, int)
    rk[order] = np.arange(1, m + 1)
    return {'collective': x, 'collective_weights': wt, 'normalized': nm, 'weighted': v, 'D_plus': d_plus,
            'D_minus': d_minus, 'scores': cc, 'ranks': rk}


def if_topsis(ratings, weights, kinds=None, sigma=None):
    """TOPSIS flou intuitionniste (cours).

    ratings : [K, m, n, 2] (μ, ν) ; weights : [K, n, 2] ; sigma : poids des décideurs.
    """
    r = np.asarray(ratings, float)
    w = np.asarray(weights, float)
    K, m, n, _ = r.shape
    sigma = np.full(K, 1 / K) if sigma is None else np.asarray(sigma, float) / np.sum(sigma)
    kinds = kinds or ['max'] * n
    D = np.zeros((m, n, 2))
    for i in range(m):
        for j in range(n):
            D[i, j] = ifwa([tuple(r[k, i, j]) for k in range(K)], sigma)
    W = np.zeros((n, 2))
    for j in range(n):
        W[j] = ifwa([tuple(w[k, j]) for k in range(K)], sigma)
    Dp = np.zeros_like(D)                               # D' = D ⊗ W
    for i in range(m):
        for j in range(n):
            Dp[i, j] = ifn_mul(tuple(D[i, j]), tuple(W[j]))
    pi = 1 - Dp[:, :, 0] - Dp[:, :, 1]
    Ip, Im = np.zeros((n, 3)), np.zeros((n, 3))
    for j in range(n):
        mu, nu = Dp[:, j, 0], Dp[:, j, 1]
        if kinds[j] == 'max':
            Ip[j] = (mu.max(), nu.min(), 0); Im[j] = (mu.min(), nu.max(), 0)
        else:
            Ip[j] = (mu.min(), nu.max(), 0); Im[j] = (mu.max(), nu.min(), 0)
        Ip[j, 2] = 1 - Ip[j, 0] - Ip[j, 1]
        Im[j, 2] = 1 - Im[j, 0] - Im[j, 1]
    trip = np.dstack([Dp[:, :, 0], Dp[:, :, 1], pi])
    s_plus = ((trip - Ip[None]) ** 2).sum(axis=2).sum(axis=1) / (2 * n)
    s_minus = ((trip - Im[None]) ** 2).sum(axis=2).sum(axis=1) / (2 * n)
    c = s_minus / np.maximum(s_plus + s_minus, EPS)
    order = np.argsort(-c, kind='stable')
    rk = np.empty(m, int)
    rk[order] = np.arange(1, m + 1)
    return {'aggregated': D, 'weights': W, 'weighted': Dp, 'I_plus': Ip, 'I_minus': Im, 'S_plus': s_plus,
            'S_minus': s_minus, 'scores': c, 'ranks': rk}
