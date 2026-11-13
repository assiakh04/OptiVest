"""Moteur MCDM — formules du cours « Aide à la décision » (Prof. Lamrani Alaoui, EMI).

Aucune dépendance à Streamlit : tout est testable seul.

Contenu
-------
Pondération subjective : AHP (+ cohérence), BWM (programme linéaire)
Pondération objective  : Entropie, CRITIC ; pondération hybride
Classement additif     : WSM, WPM, WASPAS, TOPSIS, VIKOR (+ conditions de compromis)
Surclassement          : PROMETHEE I / II, ELECTRE III (distillations)
Robustesse             : Spearman, Monte-Carlo, balayage d'un poids, Pareto
"""
from dataclasses import dataclass, replace
import numpy as np
from scipy.optimize import linprog
from scipy.stats import spearmanr, t as student_t

EPS = 1e-12

# Indice aléatoire (RI) de la table du cours (n = 3 … 10)
RI_TABLE = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.56}
# Indice de cohérence BWM (Rezaei, 2015) selon a_BW
BWM_CI = {1: 0.0, 2: 0.44, 3: 1.0, 4: 1.63, 5: 2.3, 6: 3.0, 7: 3.73, 8: 4.47, 9: 5.23}
# Valeurs critiques de Spearman à 5 % (bilatéral), n = 5 … 10
SPEARMAN_CRIT = {5: 1.0, 6: 0.886, 7: 0.786, 8: 0.738, 9: 0.683, 10: 0.648}

METHODS = ['WSM', 'WPM', 'WASPAS', 'TOPSIS', 'VIKOR', 'PROMETHEE II', 'ELECTRE III']
HIGHER_IS_BETTER = {'WSM': True, 'WPM': True, 'WASPAS': True, 'TOPSIS': True, 'VIKOR': False,
                    'PROMETHEE II': True, 'ELECTRE III': True}


# --------------------------------------------------------------------------- problème
@dataclass
class Problem:
    alternatives: list
    criteria: list
    kinds: list          # 'max' (bénéfice) ou 'min' (coût)
    weights: np.ndarray
    matrix: np.ndarray

    def with_weights(self, w):
        return replace(self, weights=normalize_weights(w))

    def with_matrix(self, x):
        return replace(self, matrix=np.asarray(x, float))


def normalize_weights(w):
    w = np.asarray(w, dtype=float)
    if w.ndim != 1 or not np.isfinite(w).all() or np.any(w < 0) or w.sum() <= EPS:
        raise ValueError('Les poids doivent être positifs ou nuls, avec une somme > 0.')
    return w / w.sum()


def parse_project(project):
    alternatives = [str(x).strip() for x in project['alternatives']]
    criteria = [str(c['name']).strip() for c in project['criteria']]
    kinds = [str(c['kind']) for c in project['criteria']]
    if len(alternatives) < 2 or len(criteria) < 2:
        raise ValueError('Ajoute au moins 2 alternatives et 2 critères.')
    if any(not x for x in alternatives + criteria) or len(set(alternatives)) != len(alternatives) \
            or len(set(criteria)) != len(criteria):
        raise ValueError('Les noms des alternatives et des critères doivent être uniques et non vides.')
    if any(k not in ('max', 'min') for k in kinds):
        raise ValueError('Le sens doit être max ou min.')
    x = np.asarray(project['matrix'], float)
    if x.shape != (len(alternatives), len(criteria)) or not np.isfinite(x).all():
        raise ValueError('Vérifie les dimensions et les valeurs numériques de la matrice.')
    return Problem(alternatives, criteria, kinds, normalize_weights([c['weight'] for c in project['criteria']]), x)


# --------------------------------------------------------------------------- normalisations
def utility(p):
    """Min-max : 1 = meilleure valeur du critère, 0 = pire (tient compte du sens)."""
    lo, hi = p.matrix.min(axis=0), p.matrix.max(axis=0)
    span = hi - lo
    z = np.ones_like(p.matrix)
    for j, k in enumerate(p.kinds):
        if span[j] > EPS:
            z[:, j] = (p.matrix[:, j] - lo[j]) / span[j] if k == 'max' else (hi[j] - p.matrix[:, j]) / span[j]
    return z


def ratio(p):
    """Normalisation « ratio » du cours : x/x⁺ (bénéfice) ou x⁺/x (coût)."""
    if np.any(p.matrix <= 0):
        return np.clip(utility(p), EPS, 1), 'min-max (valeurs nulles ou négatives détectées)'
    z = np.zeros_like(p.matrix)
    for j, k in enumerate(p.kinds):
        col = p.matrix[:, j]
        z[:, j] = col / col.max() if k == 'max' else col.min() / col
    return np.maximum(z, EPS), 'ratio : x/x⁺ (bénéfice) et x⁺/x (coût)'


def normalized(p, norm='ratio'):
    if norm == 'minmax':
        return np.clip(utility(p), EPS, 1), 'min-max'
    return ratio(p)


def ranks(scores, higher=True):
    s = np.asarray(scores, float)
    order = np.argsort(-s if higher else s, kind='stable')
    out = np.zeros(len(s), int)
    last, rk = None, 0
    for i, j in enumerate(order):
        if last is None or abs(s[j] - last) > 1e-10:
            rk = i + 1
        out[j] = rk
        last = s[j]
    return out


def _vec(x, n):
    a = np.asarray(x, float)
    return np.full(n, float(a)) if a.ndim == 0 else a


# --------------------------------------------------------------------------- PROMETHEE
PREF_FUNCTIONS = {
    'Usuelle': 'usual', 'En U (quasi-critère)': 'ushape', 'En V (linéaire)': 'vshape',
    'À paliers': 'level', 'Linéaire (q,p)': 'linear', 'Gaussienne': 'gaussian'}


def preference_function(d, kind, q, p):
    d = np.asarray(d, float)
    if kind == 'usual':
        return (d > 0).astype(float)
    if kind == 'ushape':
        return (d > q).astype(float)
    if kind == 'vshape':
        return np.clip(d / max(p, EPS), 0, 1) * (d > 0)
    if kind == 'level':
        return np.where(d <= q, 0.0, np.where(d <= p, 0.5, 1.0))
    if kind == 'linear':
        return np.clip((d - q) / max(p - q, EPS), 0, 1)
    if kind == 'gaussian':
        return np.where(d > 0, 1 - np.exp(-(d ** 2) / (2 * max(p, EPS) ** 2)), 0.0)
    raise ValueError('Fonction de préférence inconnue : ' + str(kind))


def promethee(p, fn='linear', q=0.0, pref=0.3):
    z = utility(p)
    m, n = z.shape
    q, pref = _vec(q, n), _vec(pref, n)
    fns = [fn] * n if isinstance(fn, str) else list(fn)
    pi = np.zeros((m, m))
    for i in range(m):
        for k in range(m):
            if i != k:
                gap = z[i] - z[k]
                pi[i, k] = sum(p.weights[j] * float(preference_function(gap[j], fns[j], q[j], pref[j])) for j in range(n))
    plus = pi.sum(axis=1) / (m - 1)
    minus = pi.sum(axis=0) / (m - 1)
    # PROMETHEE I : relations partielles
    rel = np.full((m, m), 'R', dtype=object)
    for i in range(m):
        for k in range(m):
            if i == k:
                rel[i, k] = '–'
                continue
            ge = plus[i] >= plus[k] - EPS and minus[i] <= minus[k] + EPS
            le = plus[i] <= plus[k] + EPS and minus[i] >= minus[k] - EPS
            if ge and le:
                rel[i, k] = 'I'
            elif ge:
                rel[i, k] = 'P'
            elif le:
                rel[i, k] = 'P⁻'
    return {'phi_plus': plus, 'phi_minus': minus, 'phi': plus - minus, 'preference': pi, 'promethee1': rel}


# --------------------------------------------------------------------------- ELECTRE III
def electre3(p, q=0.05, pref=0.15, veto=0.6):
    """ELECTRE III. Seuils q (indifférence), p (préférence), v (veto) en fraction de l'étendue de chaque critère."""
    x = p.matrix.copy()
    sign = np.array([1.0 if k == 'max' else -1.0 for k in p.kinds])
    g = x * sign
    m, n = g.shape
    span = np.maximum(g.max(axis=0) - g.min(axis=0), EPS)
    q, pref, veto = _vec(q, n) * span, _vec(pref, n) * span, _vec(veto, n) * span
    pref = np.maximum(pref, q + EPS)
    veto = np.maximum(veto, pref + EPS)
    w = p.weights
    conc = np.zeros((m, m))
    cred = np.zeros((m, m))
    disc = np.zeros((m, m, n))
    for a in range(m):
        for b in range(m):
            if a == b:
                continue
            diff = g[b] - g[a]                      # >0 : b meilleur que a
            cj = np.where(diff <= q, 1.0, np.where(diff >= pref, 0.0, (pref - diff) / (pref - q)))
            dj = np.where(diff <= pref, 0.0, np.where(diff >= veto, 1.0, (diff - pref) / (veto - pref)))
            C = float(w @ cj)
            conc[a, b] = C
            disc[a, b] = dj
            s = C
            for j in range(n):
                if dj[j] > C:
                    s *= (1 - dj[j]) / max(1 - C, EPS)
            cred[a, b] = s
    desc = _distill(cred, ascending=False)
    asc = _distill(cred, ascending=True)
    pos_d = np.zeros(m)
    pos_a = np.zeros(m)
    for r, cls in enumerate(desc):
        pos_d[cls] = r + 1
    for r, cls in enumerate(asc):
        pos_a[cls] = r + 1
    rel = np.full((m, m), 'R', dtype=object)
    for a in range(m):
        for b in range(m):
            if a == b:
                rel[a, b] = '–'
                continue
            da, db = pos_d[a] - pos_d[b], pos_a[a] - pos_a[b]
            if da == 0 and db == 0:
                rel[a, b] = 'I'
            elif da <= 0 and db <= 0:
                rel[a, b] = 'P'
            elif da >= 0 and db >= 0:
                rel[a, b] = 'P⁻'
    mean_pos = (pos_d + pos_a) / 2
    net = cred.sum(axis=1) - cred.sum(axis=0)
    return {'concordance': conc, 'credibility': cred, 'discordance': disc, 'descending': desc, 'ascending': asc,
            'pos_desc': pos_d, 'pos_asc': pos_a, 'mean_position': mean_pos, 'relation': rel, 'net_credibility': net,
            'thresholds': {'q': q, 'p': pref, 'v': veto}}


def _s(lam):
    return 0.3 - 0.15 * lam


def _distill(cred, ascending):
    """Distillation descendante (meilleurs d'abord) ou ascendante (pires d'abord). Retourne des classes ordonnées
    de la meilleure à la moins bonne."""
    remaining = list(range(len(cred)))
    classes = []
    while remaining:
        cur = list(remaining)
        lam = max((cred[i, j] for i in cur for j in cur if i != j), default=0.0)
        while len(cur) > 1 and lam > EPS:
            sub = cred[np.ix_(cur, cur)]
            off = sub[~np.eye(len(cur), dtype=bool)]
            thr = lam - _s(lam)
            cands = off[off < thr]
            lam1 = float(cands.max()) if cands.size else 0.0
            q_ = []
            for a in cur:
                out_ = sum(1 for b in cur if b != a and cred[a, b] > lam1 and cred[a, b] > cred[b, a] + _s(cred[a, b]))
                in_ = sum(1 for b in cur if b != a and cred[b, a] > lam1 and cred[b, a] > cred[a, b] + _s(cred[b, a]))
                q_.append(out_ - in_)
            q_ = np.array(q_)
            target = q_.min() if ascending else q_.max()
            nxt = [a for a, v in zip(cur, q_) if v == target]
            if len(nxt) == len(cur):
                if lam1 <= EPS:
                    break
                lam = lam1
                continue
            cur = nxt
            lam = lam1
        classes.append(cur)
        remaining = [a for a in remaining if a not in cur]
    return classes[::-1] if ascending else classes


# --------------------------------------------------------------------------- VIKOR (conditions de compromis)
def vikor_compromise(S, R, Q):
    m = len(Q)
    order = np.argsort(Q, kind='stable')
    a1, a2 = int(order[0]), int(order[1])
    dq = 1.0 / (m - 1)
    c1 = (Q[a2] - Q[a1]) >= dq - 1e-12
    c2 = (S[a1] <= S.min() + 1e-12) and (R[a1] <= R.min() + 1e-12)
    chosen = [a1]
    if not c2:
        chosen.append(a2)
    if not c1:
        chosen += [int(k) for k in order[1:] if Q[k] - Q[a1] < dq - 1e-12 and int(k) not in chosen]
    return {'best': a1, 'second': a2, 'DQ': dq, 'C1': bool(c1), 'C2': bool(c2), 'set': chosen,
            'gap': float(Q[a2] - Q[a1])}


# --------------------------------------------------------------------------- classement (dispatch)
def rank(p, method, v=0.5, lam=0.5, norm='ratio', fn='linear', q=0.0, pref=0.3,
         e_q=0.05, e_p=0.15, e_v=0.6, **_):
    x, w = p.matrix, p.weights
    m, n = x.shape
    if method in ('WSM', 'WPM', 'WASPAS'):
        z, how = normalized(p, norm)
        a = z @ w
        b = np.exp(np.log(z) @ w)
        scores = a if method == 'WSM' else b if method == 'WPM' else lam * a + (1 - lam) * b
        detail = {'normalization': z, 'normalization_mode': how, 'WSM': a, 'WPM': b, 'contributions': z * w, 'lambda': lam}
    elif method == 'TOPSIS':
        d = np.sqrt((x * x).sum(axis=0))
        d = np.where(d < EPS, 1.0, d)
        r = x / d
        vv = r * w
        up = np.array([vv[:, j].max() if k == 'max' else vv[:, j].min() for j, k in enumerate(p.kinds)])
        um = np.array([vv[:, j].min() if k == 'max' else vv[:, j].max() for j, k in enumerate(p.kinds)])
        dp = np.linalg.norm(vv - up, axis=1)
        dm = np.linalg.norm(vv - um, axis=1)
        scores = np.divide(dm, dp + dm, out=np.full(m, .5), where=dp + dm > EPS)
        detail = {'normalized': r, 'weighted': vv, 'ideal': up, 'anti_ideal': um, 'D_plus': dp, 'D_minus': dm}
    elif method == 'VIKOR':
        if not 0 <= v <= 1:
            raise ValueError('v doit être dans [0, 1].')
        best = np.array([x[:, j].max() if k == 'max' else x[:, j].min() for j, k in enumerate(p.kinds)])
        worst = np.array([x[:, j].min() if k == 'max' else x[:, j].max() for j, k in enumerate(p.kinds)])
        den = np.where(np.abs(best - worst) < EPS, 1.0, best - worst)
        terms = w * (best - x) / den
        S, R = terms.sum(axis=1), terms.max(axis=1)
        sr, rr = np.ptp(S), np.ptp(R)
        sn = (S - S.min()) / sr if sr > EPS else np.zeros(m)
        rn = (R - R.min()) / rr if rr > EPS else np.zeros(m)
        scores = v * sn + (1 - v) * rn
        detail = {'S': S, 'R': R, 'Q': scores, 'v': v, 'best': best, 'worst': worst, 'terms': terms,
                  'compromise': vikor_compromise(S, R, scores)}
    elif method == 'PROMETHEE II':
        if m < 2:
            raise ValueError('Au moins 2 alternatives.')
        detail = promethee(p, fn, q, pref)
        scores = detail['phi']
    elif method == 'ELECTRE III':
        detail = electre3(p, e_q, e_p, e_v)
        scores = -detail['mean_position']
    else:
        raise ValueError('Méthode inconnue : ' + str(method))
    higher = HIGHER_IS_BETTER[method]
    return {'method': method, 'scores': scores, 'ranks': ranks(scores, higher), 'higher': higher, 'details': detail}


# --------------------------------------------------------------------------- pondération : AHP
def ahp_from_upper(values, n):
    """Construit la matrice réciproque à partir des valeurs a_ij (i<j) sur l'échelle de Saaty."""
    a = np.ones((n, n))
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            a[i, j] = values[k]
            a[j, i] = 1.0 / values[k]
            k += 1
    return a


def ahp(matrix):
    a = np.asarray(matrix, float)
    n = len(a)
    if a.shape != (n, n) or n < 2 or not np.isfinite(a).all() or np.any(a <= 0):
        raise ValueError('Matrice AHP invalide.')
    if not np.allclose(a * a.T, 1, rtol=.01, atol=.01) or not np.allclose(np.diag(a), 1):
        raise ValueError('La matrice AHP doit être réciproque (a_ji = 1/a_ij, diagonale = 1).')
    s = a.sum(axis=0)                       # somme de chaque colonne
    nm = a / s                              # division par la somme de la colonne
    w = nm.mean(axis=1)                     # moyenne de chaque ligne
    lam = float((s * w).sum())              # λmax = Σ s_i w_i
    ci = max(0.0, (lam - n) / (n - 1))
    ri = RI_TABLE.get(n)
    cr = 0.0 if n <= 2 else (ci / ri if ri else None)
    ev, evec = np.linalg.eig(a)
    k = int(np.argmax(ev.real))
    w_eig = normalize_weights(np.abs(evec[:, k].real))
    return {'weights': w, 'weights_eig': w_eig, 'lambda_max': lam, 'ci': ci, 'ri': ri, 'cr': cr,
            'consistent': cr is None or cr < .1, 'col_sums': s, 'normalized': nm}


def ahp_hierarchy(criteria_matrix, alt_matrices):
    crit = ahp(criteria_matrix)
    locs, checks = [], []
    for a in alt_matrices:
        r = ahp(a)
        locs.append(r['weights'])
        checks.append(r)
    local = np.array(locs).T                # alternatives × critères
    final = local @ crit['weights']
    return {'criteria': crit, 'local': local, 'final': final, 'checks': checks, 'ranks': ranks(final)}


# --------------------------------------------------------------------------- pondération : BWM
def bwm(best, worst, best_to_others, others_to_worst):
    bo = np.asarray(best_to_others, float)
    ow = np.asarray(others_to_worst, float)
    n = len(bo)
    if best == worst or n < 2 or len(ow) != n:
        raise ValueError('Best et Worst doivent être deux critères différents.')
    if np.any(bo < 1) or np.any(bo > 9) or np.any(ow < 1) or np.any(ow > 9):
        raise ValueError('Les comparaisons BWM doivent être comprises entre 1 et 9.')
    if abs(bo[best] - 1) > EPS or abs(ow[worst] - 1) > EPS:
        raise ValueError('Contrôle : a_BB = a_WW = 1.')
    if abs(bo[worst] - ow[best]) > EPS:
        raise ValueError('Contrôle : a_BW (vecteur BO) doit être égal à a_BW (vecteur OW).')
    rows = []
    for j in range(n):
        for sg in (1, -1):
            a = np.zeros(n + 1); a[best] += sg; a[j] -= sg * bo[j]; a[-1] = -1; rows.append(a)
            a = np.zeros(n + 1); a[j] += sg; a[worst] -= sg * ow[j]; a[-1] = -1; rows.append(a)
    A = np.array(rows)
    res = linprog([0] * n + [1], A_ub=A, b_ub=np.zeros(len(A)), A_eq=[[1] * n + [0]], b_eq=[1],
                  bounds=[(0, None)] * (n + 1), method='highs')
    if not res.success:
        raise ValueError('Optimisation BWM impossible : ' + str(res.message))
    xi = float(res.x[-1])
    abw = int(round(bo[worst]))
    ci = BWM_CI.get(abw, None)
    return {'weights': normalize_weights(res.x[:-1]), 'xi': xi, 'A': A, 'cr': (xi / ci if ci else 0.0)}


# --------------------------------------------------------------------------- pondération : objective
def entropy(p, norm='ratio'):
    z, _ = normalized(p, norm)
    pij = z / z.sum(axis=0)
    m = len(z)
    with np.errstate(divide='ignore', invalid='ignore'):
        e = -np.nansum(np.where(pij > 0, pij * np.log(pij), 0.0), axis=0) / np.log(m)
    n = z.shape[1]
    div = np.maximum(0, 1 - e)
    w = div / div.sum() if div.sum() > EPS else np.full(n, 1 / n)
    return {'weights': w, 'entropy': e, 'diversification': 1 - e, 'p': pij}


def critic(p):
    z = utility(p)
    sig = z.std(axis=0, ddof=1)
    n = z.shape[1]
    corr = np.eye(n)
    for j in range(n):
        for k in range(j + 1, n):
            c = 0.0 if sig[j] < EPS or sig[k] < EPS else np.corrcoef(z[:, j], z[:, k])[0, 1]
            corr[j, k] = corr[k, j] = c if np.isfinite(c) else 0.0
    info = sig * np.sum(1 - np.abs(corr), axis=1)
    w = info / info.sum() if info.sum() > EPS else np.full(n, 1 / n)
    return {'weights': w, 'correlation': corr, 'information': info, 'std': sig, 'normalized': z}


def hybrid_weights(subjective, objective, alpha=0.5, mode='linéaire'):
    s, o = normalize_weights(subjective), normalize_weights(objective)
    if mode == 'multiplicatif':
        return normalize_weights(s ** alpha * o ** (1 - alpha))
    return normalize_weights(alpha * s + (1 - alpha) * o)


# --------------------------------------------------------------------------- analyses
def pareto(p):
    z = p.matrix * np.array([1 if k == 'max' else -1 for k in p.kinds])
    keep = np.ones(len(z), bool)
    for i in range(len(z)):
        for j in range(len(z)):
            if i != j and np.all(z[j] >= z[i] - EPS) and np.any(z[j] > z[i] + EPS):
                keep[i] = False
                break
    return keep


def spearman(r1, r2):
    """ρ = 1 − 6Σd²/(n(n²−1)) (formule du cours) ; scipy en cas d'ex æquo."""
    r1, r2 = np.asarray(r1, float), np.asarray(r2, float)
    n = len(r1)
    if len(set(r1)) == n and len(set(r2)) == n:
        return float(1 - 6 * np.sum((r1 - r2) ** 2) / (n * (n * n - 1)))
    c = spearmanr(r1, r2).statistic
    return float(c) if np.isfinite(c) else 1.0


def spearman_significance(rho, n):
    """Seuil de significativité à 5 % (table pour n ≤ 10, sinon approximation t)."""
    if n in SPEARMAN_CRIT:
        return abs(rho) >= SPEARMAN_CRIT[n] - 1e-9, SPEARMAN_CRIT[n]
    if n < 5:
        return False, None
    t = rho * np.sqrt((n - 2) / max(1 - rho ** 2, EPS))
    pval = 2 * (1 - student_t.cdf(abs(t), n - 2))
    return bool(pval < .05), None


def rank_correlation(results):
    keys = list(results)
    C = np.eye(len(keys))
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            C[i, j] = C[j, i] = spearman(results[keys[i]]['ranks'], results[keys[j]]['ranks'])
    return keys, C


def sweep_weight(p, method, j, steps=21, **params):
    """Fait varier le poids du critère j de 0 à 1 (les autres restent proportionnels)."""
    grid = np.linspace(0, 1, steps)
    others = p.weights.copy()
    others[j] = 0
    base = others / others.sum() if others.sum() > EPS else np.full(len(others), 1 / (len(others) - 1))
    base[j] = 0
    scores, rks = [], []
    for g in grid:
        w = base * (1 - g)
        w[j] = g
        r = rank(p.with_weights(w), method, **params)
        scores.append(r['scores'])
        rks.append(r['ranks'])
    return grid, np.array(scores), np.array(rks)


def sensitivity(p, method='TOPSIS', n=200, concentration=40, seed=14, **params):
    """Monte-Carlo : poids tirés par une loi de Dirichlet centrée sur les poids actuels."""
    if not 20 <= n <= 5000 or concentration <= 0:
        raise ValueError('Paramètres de simulation incorrects.')
    rng = np.random.default_rng(seed)
    active = p.weights > EPS
    weights = np.zeros((n, len(p.weights)))
    weights[:, active] = rng.dirichlet(np.maximum(.01, p.weights[active] * concentration), size=n)
    m = len(p.alternatives)
    rk = np.empty((n, m), int)
    for t, w in enumerate(weights):
        rk[t] = rank(p.with_weights(w), method, **params)['ranks']
    accept = np.array([[(rk[:, i] == r).mean() for r in range(1, m + 1)] for i in range(m)])
    return {'win_rate': (rk == 1).mean(axis=0), 'mean_rank': rk.mean(axis=0), 'rank_sd': rk.std(axis=0),
            'weights': weights, 'ranks': rk, 'acceptability': accept}
