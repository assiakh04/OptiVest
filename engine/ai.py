"""MCDM × IA : classification supervisée (scénario 1), XAI/Shapley pour re-pondérer (scénario 2),
extraction de scores par LLM (prompt + simulateur hors-ligne)."""
import itertools
import json
import math
import re
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, confusion_matrix

EPS = 1e-12


# =========================================================================== données synthétiques
def augment(p, n=400, seed=7, spread=0.15):
    """Génère n alternatives fictives autour de la matrice (bruit gaussien proportionnel à l'étendue de chaque critère).
    Nécessaire : la matrice de décision compte trop peu de lignes pour entraîner un modèle."""
    rng = np.random.default_rng(seed)
    x = p.matrix
    lo, hi = x.min(axis=0), x.max(axis=0)
    span = np.maximum(hi - lo, EPS)
    base = x[rng.integers(0, len(x), n)]
    syn = base + rng.normal(0, spread * span, size=base.shape)
    return np.clip(syn, lo - .15 * span, hi + .15 * span)


def mcdm_score(x, p, lo=None, hi=None):
    """Score additif (WSM) avec normalisation min-max sur les bornes de la matrice d'origine (en %, ∈ [0,1])."""
    lo = p.matrix.min(axis=0) if lo is None else lo
    hi = p.matrix.max(axis=0) if hi is None else hi
    span = np.maximum(hi - lo, EPS)
    z = np.clip((x - lo) / span, 0, 1)
    for j, k in enumerate(p.kinds):
        if k == 'min':
            z[:, j] = 1 - z[:, j]
    return z @ p.weights


def label_by_score(s, bounds=(0.75, 0.55, 0.35)):
    return np.array(['A' if v >= bounds[0] else 'B' if v >= bounds[1] else 'C' if v >= bounds[2] else 'D' for v in s])


CLASSIFIERS = {'Random Forest': lambda: RandomForestClassifier(n_estimators=150, random_state=1),
               'Arbre de décision': lambda: DecisionTreeClassifier(max_depth=5, random_state=1),
               'Régression logistique': lambda: LogisticRegression(max_iter=1000),
               'KNN': lambda: KNeighborsClassifier(n_neighbors=7)}


def train_classifier(p, name='Random Forest', n=400, bounds=None, seed=7):
    """Scénario 1 : MCDM → étiquettes A/B/C/D → modèle supervisé → prédiction d'une nouvelle alternative."""
    X = augment(p, n, seed)
    s = mcdm_score(X, p)
    if bounds is None:                       # classes A/B/C/D = quartiles du score MCDM
        bounds = tuple(float(v) for v in np.quantile(s, [.75, .5, .25]))
    y = label_by_score(s, bounds)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.25, random_state=seed)
    model = CLASSIFIERS[name]()
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    labels = sorted(set(y))
    return {'model': model, 'accuracy': float(accuracy_score(yte, pred)), 'labels': labels,
            'confusion': confusion_matrix(yte, pred, labels=labels), 'n_train': len(Xtr), 'n_test': len(Xte),
            'class_counts': {l: int((y == l).sum()) for l in labels},
            'bounds': bounds, 'original_scores': mcdm_score(p.matrix, p),
            'original_labels': label_by_score(mcdm_score(p.matrix, p), bounds)}


# =========================================================================== XAI : Shapley exact
def shapley_values(predict, x, background, max_features=10):
    """Valeurs de Shapley exactes (version « interventionnelle ») pour un petit nombre de critères.
    φ_j = Σ_S |S|!(n−|S|−1)!/n! · [v(S∪{j}) − v(S)], avec v(S) = E_bg[f(x_S, bg_{S̄})]."""
    n = len(x)
    if n > max_features:
        raise ValueError(f'Shapley exact limité à {max_features} critères.')
    cache = {}

    def v(mask):
        if mask not in cache:
            z = background.copy()
            idx = [i for i in range(n) if mask >> i & 1]
            z[:, idx] = x[idx]
            cache[mask] = float(predict(z).mean())
        return cache[mask]

    phi = np.zeros(n)
    fact = math.factorial
    for j in range(n):
        rest = [i for i in range(n) if i != j]
        for r in range(n):
            for sub in itertools.combinations(rest, r):
                mask = sum(1 << i for i in sub)
                wgt = fact(r) * fact(n - r - 1) / fact(n)
                phi[j] += wgt * (v(mask | 1 << j) - v(mask))
    return phi, v(0)


def xai_reweight(p, w_ahp, model_name='Random Forest', alpha=0.6, n=400, seed=7):
    """Scénario 2 : Ŝ = f(x) apprise sur le score MCDM ; SHAP → |φ| ; w_new = α·w_AHP + (1−α)·|φ|/Σ|φ|."""
    X = augment(p, n, seed)
    y = mcdm_score(X, p)
    models = {'Random Forest': lambda: RandomForestRegressor(n_estimators=120, random_state=1, min_samples_leaf=2),
              'Gradient Boosting': lambda: GradientBoostingRegressor(random_state=1),
              'Ridge (linéaire)': lambda: Ridge(alpha=1.0)}
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.25, random_state=seed)
    model = models[model_name]()
    model.fit(Xtr, ytr)
    r2 = float(model.score(Xte, yte))
    bg = Xtr[np.random.default_rng(seed).choice(len(Xtr), size=min(40, len(Xtr)), replace=False)]
    local, base = [], 0.0
    for row in p.matrix:
        phi, base = shapley_values(model.predict, row, bg)
        local.append(phi)
    local = np.array(local)
    glob = np.abs(local).mean(axis=0)
    share = glob / max(glob.sum(), EPS)
    w_new = alpha * np.asarray(w_ahp) + (1 - alpha) * share
    w_new = w_new / w_new.sum()
    return {'r2': r2, 'local': local, 'global': glob, 'share': share, 'w_new': w_new, 'base': base,
            'pred': model.predict(p.matrix)}


# =========================================================================== LLM comme extracteur de scores
DEFAULT_RUBRIC = {
    'Expérience technique': {'kind': 'max', 'rubric': "0 = aucune expérience ; 5 = 3-5 ans ; 8 = 7+ ans avec certifications ; 10 = expertise reconnue",
                             'keywords': ['ans', 'expérience', 'python', 'java', 'développement', 'pmp', 'certifi', 'ingénieur']},
    'Communication / leadership': {'kind': 'max', 'rubric': "0 = aucune trace ; 5 = travail en équipe ; 8 = management avec références ; 10 = leadership démontré",
                                   'keywords': ['équipe', 'management', 'manager', 'leader', 'présent', 'communication', 'coordin']},
    'Adéquation salariale': {'kind': 'min', 'rubric': "Critère coût : plus la prétention est haute, plus le score d'adéquation est bas (score inversé)",
                             'keywords': ['€', 'prétention', 'salaire', 'k€', 'mad', 'dh']},
}

SAMPLE_CV = ("Ingénieur logiciel avec 7 ans d'expérience en développement Python et Java, management d'une équipe de "
             "5 personnes, certifié PMP. Prétentions : 85 000 €/an.")


def build_prompt(text, criteria):
    """Prompt prêt à coller dans n'importe quel LLM : f_LLM(T, C) → s ∈ [0,10]^n + justification."""
    lines = '\n'.join(f"- {c} (critère {'coût : score inversé' if d['kind']=='min' else 'bénéfice'}) : {d['rubric']}"
                      for c, d in criteria.items())
    schema = '{"scores": {' + ', '.join(f'"{c}": <0-10>' for c in criteria) + '}, "justifications": {' + \
             ', '.join(f'"{c}": "<phrase>"' for c in criteria) + '}}'
    return (f"Tu es un évaluateur expert. Lis le texte puis attribue un score de 0 à 10 à chaque critère en suivant la rubrique.\n"
            f"Critères et rubriques :\n{lines}\n\nTexte :\n\"\"\"\n{text}\n\"\"\"\n\n"
            f"Réponds UNIQUEMENT avec ce JSON :\n{schema}")


def simulate_extract(text, criteria):
    """Simulateur déterministe hors-ligne (règles + mots-clés) : illustre le format de sortie d'un LLM fine-tuné.
    Ce n'est PAS un LLM : sert à tester la chaîne texte → scores → MCDM sans clé API."""
    t = text.lower()
    scores, why = {}, {}
    yrs = [int(x) for x in re.findall(r'(\d+)\s*ans', t)]
    sal = [int(x.replace(' ', '').replace(' ', '')) for x in re.findall(r'(\d[\d  ]{3,})\s*(?:€|eur|mad|dh)', t)]
    team = re.findall(r'équipe de (\d+)', t)
    for c, d in criteria.items():
        hits = sum(k in t for k in d['keywords'])
        if 'xp' in c.lower() or 'expérience' in c.lower() or 'technique' in c.lower():
            s = min(10, (yrs[0] if yrs else 0) * .7 + 2 * ('pmp' in t or 'certifi' in t) + hits * .3)
            why[c] = f"{yrs[0] if yrs else 0} ans détectés, {hits} mots-clés pertinents."
        elif 'comm' in c.lower() or 'lead' in c.lower():
            s = min(10, 3 + 1.2 * hits + (int(team[0]) * .3 if team else 0))
            why[c] = f"{hits} indices de leadership/équipe détectés."
        elif 'sal' in c.lower() or 'coût' in c.lower():
            amount = sal[0] if sal else 0
            s = 10 - min(10, amount / 12000) if amount else 5
            why[c] = f"Prétention détectée : {amount or 'non précisée'} → score inversé (critère coût)."
        else:
            s = min(10, 3 + 1.5 * hits)
            why[c] = f"{hits} mots-clés détectés."
        scores[c] = round(float(max(0, min(10, s))), 1)
    return {'scores': scores, 'justifications': why}


def parse_llm_json(raw, criteria):
    m = re.search(r'\{.*\}', raw, re.S)
    if not m:
        raise ValueError('Aucun JSON trouvé dans la réponse.')
    data = json.loads(m.group(0))
    sc = data.get('scores', data)
    out = {}
    for c in criteria:
        if c not in sc:
            raise ValueError(f'Critère manquant dans le JSON : {c}')
        v = float(sc[c])
        if not 0 <= v <= 10:
            raise ValueError(f'Score hors [0, 10] pour {c}')
        out[c] = v
    return {'scores': out, 'justifications': data.get('justifications', {})}
