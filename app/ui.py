"""Presentation helpers: HTML cards, chips, funnel, notices and plotly figures."""
import html
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

CSS_PATH = Path(__file__).resolve().parent / "assets" / "style.css"
INDIGO, GREEN, AMBER, RED, GREY = "#3730a3", "#15803d", "#d97706", "#b91c1c", "#9aa3c0"
LOGO = ('<svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true"><rect width="34" height="34" rx="9" fill="#3730a3"/>'
        '<circle cx="13" cy="13" r="4.5" fill="none" stroke="#fff" stroke-width="2"/><path d="M16.5 16.5 L23 23" stroke="#fff" '
        'stroke-width="2.2" stroke-linecap="round"/><path d="M21 9h5M21 13h3" stroke="#c9c6f5" stroke-width="2" stroke-linecap="round"/></svg>')
EMPTY_ICON = ('<svg width="54" height="54" viewBox="0 0 54 54" aria-hidden="true"><rect x="8" y="10" width="38" height="34" rx="7" '
              'fill="none" stroke="#9aa3c0" stroke-width="2.4"/><path d="M16 21h22M16 29h14" stroke="#9aa3c0" stroke-width="2.4" stroke-linecap="round"/></svg>')
E = html.escape


def load_css():
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def brand():
    st.markdown(f'<div class="brand">{LOGO}<div><div class="t">Placement Matcher</div>'
                f'<div class="s">semantic shortlist demo</div></div></div>', unsafe_allow_html=True)


STATUS_TEXT = {"warming": "Local LLM: warming up (first load can take about 2 min)", "ready": "Local LLM: ready",
               "offline": "Local LLM: offline (samples only)"}


def status_badge(status):
    st.markdown(f'<span class="badge {status}"><span class="dot"></span>{STATUS_TEXT[status]}</span>', unsafe_allow_html=True)


def chips(items, kind, label=None):
    if not items:
        return ""
    lab = f'<span class="chiplabel">{E(label)}</span>' if label else ""
    return lab + "".join(f'<span class="chip {kind}">{E(str(i))}</span>' for i in items)


def score_color(score):
    return GREEN if score >= 75 else (AMBER if score >= 50 else RED)


def empty_state(title, text):
    st.markdown(f'<div class="empty">{EMPTY_ICON}<h3>{E(title)}</h3><div>{E(text)}</div></div>', unsafe_allow_html=True)


def notice(kind, text):
    st.markdown(f'<div class="notice {kind}">{text}</div>', unsafe_allow_html=True)


def funnel(n_all, n_elig, n_pool, n_short):
    steps = [(n_all, "all students"), (n_elig, "pass the eligibility filters"), (n_pool, "retrieved pool"), (n_short, "shortlist")]
    st.markdown('<div class="funnel">' + "".join(f'<div class="fstep"><div class="n">{n}</div><div class="l">{E(l)}</div></div>'
                                                 for n, l in steps) + "</div>", unsafe_allow_html=True)


def understood_panel(parsed):
    f = []
    f.append(f'<span class="chip fact">Min CGPA: {parsed["min_cgpa"] if parsed["min_cgpa"] is not None else "no cutoff"}</span>')
    f.append('<span class="chip fact">Branches: ' + (E(", ".join(parsed["allowed_branches"])) if parsed["allowed_branches"] else "any") + "</span>")
    f.append('<span class="chip fact">Max active backlogs: ' + (str(parsed["max_backlogs"]) if parsed["max_backlogs"] is not None else "no limit") + "</span>")
    st.markdown(
        '<div class="panel"><h4>As understood by the system</h4>'
        f'<div style="font-size:1.15rem;font-weight:700;margin-bottom:.5rem">{E(parsed["role_title"])}</div>'
        f'<div class="chips">{chips(parsed["must_have_skills"], "must", "Must have") or "<span class=chiplabel>Must have</span> none stated"}</div>'
        f'<div class="chips">{chips(parsed["nice_to_have_skills"], "nice", "Nice to have") or "<span class=chiplabel>Nice to have</span> none stated"}</div>'
        f'<div class="chips"><span class="chiplabel">Eligibility</span>{"".join(f)}</div></div>', unsafe_allow_html=True)


def candidate_card(rank, student, entry, gt=None, rescued=False, why=None):
    meta = f'{E(student["id"])} &middot; {E(student["branch"])} &middot; CGPA {student["cgpa"]:.2f} &middot; {student["active_backlogs"]} backlog(s)'
    head = (f'<div class="cand-head"><div class="rank">#{rank}</div><div class="who"><div class="name">{E(student["name"])}'
            f'{"<span class=tag-rescued>rescued by semantic matching</span>" if rescued else ""}</div><div class="meta">{meta}</div></div>')
    if entry["score"] is None:
        body = head + "</div>" + '<div class="unscored">This candidate could not be scored (the local model call failed).</div>'
    else:
        c = score_color(entry["score"])
        body = (head + f'<div class="score-box"><div class="score" style="color:{c}">{entry["score"]}</div>'
                f'<div class="bar"><span style="width:{entry["score"]}%;background:{c}"></span></div></div></div>'
                f'<div class="chips">{chips(entry["matched"], "ok", "Matched") or ""}{chips(entry["missing"], "miss", "Missing") or ""}</div>'
                f'<p class="expl">{E(entry["explanation"])}</p>')
    if why:
        body += f'<div class="why">{why}</div>'
    if gt is not None:
        body += f'<span class="gt {"yes" if gt else "no"}">{"Qualified" if gt else "Not qualified"} (ground truth, synthetic data)</span>'
    st.markdown(f'<div class="card{" rescued" if rescued else ""}">{body}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ figures
def _layout(fig, height=360, title=None):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=40 if title else 10, b=10), paper_bgcolor="white", plot_bgcolor="white",
                      font=dict(family="-apple-system, Segoe UI, Roboto, Arial", size=14, color="#1b1f3b"), title=title,
                      legend=dict(orientation="h", y=-0.25))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#eceef6")
    return fig


def ci_bar(df, ylabel, highlight=None, height=360):
    colors = [INDIGO if m == highlight else GREY for m in df.method]
    fig = go.Figure(go.Bar(x=df.name, y=df["mean"], marker_color=colors,
                           error_y=dict(type="data", symmetric=False, array=df.hi - df["mean"], arrayminus=df["mean"] - df.lo, color="#1b1f3b"),
                           text=[f"{v:.2f}" for v in df["mean"]], textposition="outside", cliponaxis=False))
    fig.update_yaxes(title=ylabel, rangemode="tozero")
    return _layout(fig, height)


def archetype_bars(df, methods, names, archetypes):
    fig = go.Figure()
    palette = ["#9aa3c0", "#c3c8de", "#6c74a8", "#3730a3", "#d99a1d", "#7c2d92"]
    for i, m in enumerate(methods):
        d = df[df.method == m].set_index("archetype").reindex(archetypes)
        fig.add_bar(name=names[m], x=archetypes, y=d["share"], marker_color=palette[i % len(palette)])
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="share of qualified students in the top-20", tickformat=".0%", range=[0, 1.05])
    return _layout(fig, 400)


def fairness_bars(summary):
    fig = go.Figure()
    for kind, color, label in (("control", GREY, "Control (same-group name)"), ("cross", RED, "Cross-group name")):
        xs, ys, hi, lo = [], [], [], []
        for cond, name in (("on", "Fairness instruction ON"), ("off", "Fairness instruction OFF")):
            m, a, b = summary[cond]["abs_score_change"][kind]
            xs.append(name); ys.append(m); hi.append(b - m); lo.append(m - a)
        fig.add_bar(name=label, x=xs, y=ys, marker_color=color, error_y=dict(type="data", symmetric=False, array=hi, arrayminus=lo))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="mean |score change| after a name swap (points)", rangemode="tozero")
    return _layout(fig, 360)
