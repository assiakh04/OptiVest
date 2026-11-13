"""Composants visuels réutilisables (HTML/CSS + graphiques Plotly)."""
import html
import re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from . import theme as T


def _md(text):
    t = html.escape(str(text))
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    return t


def header(kicker, title, subtitle='', chips=()):
    chips_html = ''.join(f'<span class="chip">{html.escape(c)}</span>' for c in chips)
    st.markdown(f'<div class="hero"><div class="kicker">{html.escape(kicker)}</div><h1>{html.escape(title)}</h1>'
                f'<p>{html.escape(subtitle)}</p><div class="chips">{chips_html}</div></div>', unsafe_allow_html=True)


def section(title, sub=None):
    st.markdown(f'<div class="sec"><div class="bar"></div><h3>{html.escape(title)}</h3></div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="sec-sub">{_md(sub)}</div>', unsafe_allow_html=True)


def kpis(items):
    """items : (label, valeur, sous-texte, couleur)"""
    out = ''
    for it in items:
        lab, val, sub = it[0], it[1], (it[2] if len(it) > 2 else '')
        col = it[3] if len(it) > 3 else T.TEAL
        out += f'<div class="kpi" style="--acc:{col}"><div class="lab">{html.escape(str(lab))}</div><div class="val">{html.escape(str(val))}</div><div class="sub">{html.escape(str(sub))}</div></div>'
    st.markdown(f'<div class="kpi-row">{out}</div>', unsafe_allow_html=True)


def callout(text, kind='info', icon=None):
    icons = {'info': 'ℹ️', 'tip': '💡', 'warn': '⚠️', 'ok': '✅', 'bad': '⛔'}
    st.markdown(f'<div class="callout {kind}">{icons[kind] if icon is None else icon} {_md(text)}</div>', unsafe_allow_html=True)


def card(tag, title, text, color='teal'):
    st.markdown(f'<div class="card {color}"><div class="tag">{html.escape(tag)}</div><h4>{html.escape(title)}</h4><p>{_md(text)}</p></div>',
                unsafe_allow_html=True)


def course_note(title, body_md):
    """Rappel du cours replié dans un expander."""
    with st.expander('📘 Définition & méthode · ' + title):
        st.markdown(body_md)


def formula(tex):
    with st.container():
        st.latex(tex)


def beginner_tip(text):
    if st.session_state.get('beginner', True):
        callout(text, 'tip')


# =========================================================================== graphiques
def _base(fig, h=340, legend=True):
    fig.update_layout(height=h, margin=dict(t=30, l=12, r=16, b=26), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      font=dict(family='Inter, sans-serif', color=T.MUTED, size=12), colorway=T.CAT,
                      hoverlabel=dict(bgcolor='#fff', font_color=T.TEXT, bordercolor=T.LINE),
                      legend=dict(orientation='h', y=-.18, x=0) if legend else dict(visible=False))
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=T.LINE, tickfont=dict(color=T.MUTED))
    fig.update_yaxes(showgrid=True, gridcolor='#E6ECF3', zeroline=False, linecolor=T.LINE)
    return fig


def show(fig, h=340, legend=True, key=None):
    st.plotly_chart(_base(fig, h, legend), width='stretch', config={'displaylogo': False, 'displayModeBar': False}, key=key)


def bar_ranking(names, scores, ranks, higher=True, h=None, title=None):
    order = np.argsort(ranks, kind='stable')
    names = np.array(names)[order]
    sc = np.asarray(scores, float)[order]
    rk = np.asarray(ranks)[order]
    colors = [T.ORANGE if r == 1 else T.TEAL if r == 2 else T.BLUE if r == 3 else '#9FB3C8' for r in rk]
    fig = go.Figure(go.Bar(x=sc, y=names, orientation='h', marker=dict(color=colors, cornerradius=6),
                           text=[f'#{r}  ·  {s:.3f}' for r, s in zip(rk, sc)], textposition='outside', cliponaxis=False,
                           hovertemplate='%{y}: %{x:.4f}<extra></extra>'))
    fig.update_yaxes(autorange='reversed', showgrid=False)
    fig.update_xaxes(showgrid=True, gridcolor='#E6ECF3')
    lo, hi = min(0, sc.min()), sc.max()
    pad = (hi - lo) * .25 + 1e-9
    fig.update_xaxes(range=[lo - (pad * .9 if lo < 0 else 0), hi + pad])
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=13, color=T.TEXT)))
    show(fig, h or max(250, 52 * len(names) + 40), legend=False)


def weights_chart(names, w, h=300, color=None):
    order = np.argsort(-np.asarray(w))
    fig = go.Figure(go.Bar(x=[names[i] for i in order], y=[100 * w[i] for i in order],
                           marker=dict(color=[T.CAT[i % 8] for i in order] if color is None else color, cornerradius=6),
                           text=[f'{100 * w[i]:.1f} %' for i in order], textposition='outside', cliponaxis=False))
    fig.update_yaxes(title='Poids (%)', range=[0, max(100 * np.max(w) * 1.25, 5)])
    show(fig, h, legend=False)


def donut(names, w, h=300):
    fig = go.Figure(go.Pie(labels=names, values=w, hole=.64, sort=False, marker=dict(colors=T.CAT, line=dict(color='#fff', width=2)),
                           textinfo='percent', hovertemplate='%{label}: %{percent}<extra></extra>'))
    fig.add_annotation(text='<b>100 %</b><br><span style="font-size:11px">des poids</span>', x=.5, y=.5, showarrow=False,
                       font=dict(size=18, color=T.INK))
    show(fig, h)


def heatmap(z, x, y, scale=None, zmin=None, zmax=None, fmt='.2f', h=360, text=True, reverse_y=True):
    z = np.asarray(z, float)
    fig = go.Figure(go.Heatmap(z=z, x=list(x), y=list(y), colorscale=scale or T.SEQ, zmin=zmin, zmax=zmax,
                               text=np.round(z, 3) if text else None, texttemplate='%{text:' + fmt + '}' if text else None,
                               hovertemplate='%{y} × %{x}: %{z:.3f}<extra></extra>', xgap=3, ygap=3,
                               colorbar=dict(thickness=10, outlinewidth=0)))
    if reverse_y:
        fig.update_yaxes(autorange='reversed')
    fig.update_yaxes(showgrid=False)
    show(fig, h, legend=False)


def radar(names, crits, u, ids=None, h=380):
    ids = list(range(min(3, len(names)))) if ids is None else ids
    fig = go.Figure()
    for k, i in enumerate(ids):
        col = T.CAT[k % 8]
        fig.add_trace(go.Scatterpolar(r=list(u[i]) + [u[i][0]], theta=list(crits) + [crits[0]], name=names[i], fill='toself',
                                      line=dict(color=col, width=2.5), opacity=.7))
    fig.update_layout(polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(range=[0, 1], gridcolor='#DCE5EE', showticklabels=False),
                                 angularaxis=dict(gridcolor='#DCE5EE')))
    show(fig, h)


def rank_table(names, **cols):
    df = pd.DataFrame({'Alternative': names, **cols})
    return df


def style_rank(df, rank_cols):
    def color(v):
        try:
            v = int(v)
        except Exception:
            return ''
        return {1: 'background-color:#FFE3D3;color:#8A3A0B;font-weight:700', 2: 'background-color:#D6F2EF;color:#06504D;font-weight:700',
                3: 'background-color:#DCE7FF;color:#17408F;font-weight:700'}.get(v, '')
    return df.style.map(color, subset=rank_cols)


def sorted_results(p, r, label='Score'):
    df = pd.DataFrame({'Rang': r['ranks'], 'Alternative': p.alternatives, label: r['scores']}).sort_values(['Rang', 'Alternative'])
    return df


def download_csv(df, name, label='Télécharger (CSV)'):
    st.download_button('⬇ ' + label, df.to_csv(index=False).encode('utf-8-sig'), name, 'text/csv')


def matrix_editor(key, labels, init, label='Matrice de comparaison par paires (Saaty)'):
    """Éditeur de matrice réciproque : seule la partie supérieure est saisie ; le reste est calculé (a_ji = 1/a_ij)."""
    n = len(labels)
    init = np.asarray(init, float)
    df = pd.DataFrame(np.round(init, 4), index=labels, columns=labels)
    mask_cfg = {c: st.column_config.NumberColumn(c, min_value=1 / 9, max_value=9.0, step=0.0001, format='%.3f') for c in labels}
    st.caption('Saisis uniquement le triangle au-dessus de la diagonale : le reste est complété automatiquement (a_ji = 1/a_ij).')
    edited = st.data_editor(df, key=key, column_config=mask_cfg, width='stretch')
    a = np.ones((n, n))
    ev = edited.to_numpy(float)
    for i in range(n):
        for j in range(i + 1, n):
            v = ev[i, j] if np.isfinite(ev[i, j]) and ev[i, j] > 0 else 1.0
            a[i, j] = v
            a[j, i] = 1 / v
    return a
