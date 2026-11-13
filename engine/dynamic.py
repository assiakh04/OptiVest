"""MCDM dynamique : séries temporelles → prévision à t+1 → matrice de décision → classement."""
import numpy as np

EPS = 1e-12
FORECASTERS = ['Tendance linéaire', 'Holt (lissage exponentiel)', 'AR(p) moindres carrés', 'Moyenne mobile', 'Naïf (dernière valeur)']


def simulate_assets(T=48, seed=11):
    """Trois actions fictives, séries mensuelles : rendement (%), volatilité (fraction), liquidité (volume).
    Les niveaux de départ reprennent l'exemple du cours : (8 ; 0,25 ; 100), (6 ; 0,15 ; 80), (7 ; 0,20 ; 120)."""
    rng = np.random.default_rng(seed)
    spec = {'Action tech': (8.0, .25, 100.0, .05, 1.4), 'Action énergie': (6.0, .15, 80.0, -.01, .9),
            'Action bancaire': (7.0, .20, 120.0, .02, 1.1)}
    t = np.arange(T)
    data = {}
    for name, (r0, s0, l0, drift, amp) in spec.items():
        ret = r0 + drift * t + amp * np.sin(t / 6 + rng.uniform(0, 3)) + rng.normal(0, .45 * amp, T)
        sig = s0 * (1 + .25 * np.sin(t / 8 + rng.uniform(0, 3)) + rng.normal(0, .06, T))
        liq = l0 * (1 + .12 * np.sin(t / 10 + rng.uniform(0, 3)) + np.cumsum(rng.normal(0, .015, T)))
        data[name] = {'Rendement (%)': ret, 'Volatilité': np.maximum(sig, .01), 'Liquidité': np.maximum(liq, 1)}
    return data


def _linear(y, h=1):
    t = np.arange(len(y))
    b, a = np.polyfit(t, y, 1)
    return float(a + b * (len(y) - 1 + h))


def _holt(y, h=1):
    best = None
    for al in np.linspace(.1, .9, 9):
        for be in np.linspace(.05, .6, 8):
            lvl, tr = y[0], y[1] - y[0]
            sse = 0.0
            for v in y[1:]:
                f = lvl + tr
                sse += (v - f) ** 2
                new = al * v + (1 - al) * (lvl + tr)
                tr = be * (new - lvl) + (1 - be) * tr
                lvl = new
            if best is None or sse < best[0]:
                best = (sse, lvl, tr)
    return float(best[1] + h * best[2])


def _ar(y, p=2, h=1):
    y = np.asarray(y, float)
    mu = y.mean()
    z = y - mu
    if len(z) <= p + 2:
        return float(y[-1])
    X = np.column_stack([z[p - k - 1:len(z) - k - 1] for k in range(p)])
    coef, *_ = np.linalg.lstsq(X, z[p:], rcond=None)
    hist = list(z)
    for _ in range(h):
        hist.append(float(np.dot(coef, hist[-1:-p - 1:-1])))
    return float(mu + hist[-1])


def forecast(y, method='Holt (lissage exponentiel)', h=1, p=2, window=6):
    y = np.asarray(y, float)
    if method == 'Tendance linéaire':
        return _linear(y, h)
    if method.startswith('Holt'):
        return _holt(y, h)
    if method.startswith('AR'):
        return _ar(y, p, h)
    if method == 'Moyenne mobile':
        return float(y[-window:].mean())
    return float(y[-1])


def ewma_volatility(returns, lam=0.94):
    """Volatilité EWMA (RiskMetrics), cas particulier de GARCH(1,1) : σ²_t = λσ²_{t−1} + (1−λ)r²_{t−1}."""
    r = np.asarray(returns, float)
    r = r - r.mean()
    s2 = r[:5].var() + EPS
    out = []
    for v in r:
        s2 = lam * s2 + (1 - lam) * v * v
        out.append(np.sqrt(s2))
    return np.array(out)


def decision_matrix_forecast(series, methods, h=1):
    """series : {alt: {critère: array}} ; methods : {critère: nom de méthode}. Retourne (alts, crits, matrice t+h)."""
    alts = list(series)
    crits = list(next(iter(series.values())))
    X = np.array([[forecast(series[a][c], methods.get(c, FORECASTERS[1]), h) for c in crits] for a in alts])
    return alts, crits, X


def error_propagation(p, base_method, errors, n=300, seed=3, rank_fn=None):
    """Limite du cours : erreur ML → matrice biaisée → classement. Perturbe la matrice prévue par un bruit gaussien
    d'écart-type `errors` (fraction de la valeur, par critère) et mesure la stabilité du rang 1."""
    rng = np.random.default_rng(seed)
    errors = np.asarray(errors, float)
    m = len(p.alternatives)
    wins = np.zeros(m)
    ranks_all = []
    for _ in range(n):
        noisy = p.matrix * (1 + rng.normal(0, errors, size=p.matrix.shape))
        noisy = np.maximum(noisy, EPS)
        r = rank_fn(p.with_matrix(noisy), base_method)['ranks']
        ranks_all.append(r)
        wins[r == 1] += 1
    return wins / n, np.array(ranks_all)
