"""Data and pipeline access for the demo app. Imports from src/ and eval/ (nothing is modified or recomputed there);
reads eval/results only. The synthetic ground truth (qrels.csv) is read here, never in src/."""
import csv
import json
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "scripts", ROOT / "eval", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import httpx  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src import llm  # noqa: E402  (importing src.config sets PYTHONUTF8 / HF_HOME on D:)
from src.config import K_RETRIEVE, MODEL  # noqa: E402
from src.data import load_students  # noqa: E402
from src.parser import parse_requirement  # noqa: E402
from src.rerank import score_candidate  # noqa: E402
from src.retrieve import Retriever, filters_from_parsed  # noqa: E402

import baselines as bl  # noqa: E402  (eval/: strict keyword ATS = B1, BM25)
import fairness as fair  # noqa: E402
from posthoc import rrf_scores  # noqa: E402  (eval/: RRF fusion used by B5)
from stats import boot_ci  # noqa: E402

RES = ROOT / "eval" / "results"
SHORTLIST = 10
OLLAMA_URL = "http://127.0.0.1:11434/api/tags"

# Chosen from cached outputs only (hybrid mode, strict ATS): see docs/DEMO.md for the numbers.
DEMO_EXAMPLES = {
    "R03": "Bullet-style full-stack request: the strict filter passes 3 of 297 eligible students and rejects 7 of our top 10",
    "R12": "Formal business-analyst paragraph: the strict filter passes nobody, all 10 of our top 10 are rejected",
    "R05": "Typo-laden ML request: keywords miss spelling variants, 3 of our top 10 rejected",
    "R04": "Hinglish data-analyst request: the keyword filter does well here (0 of our top 10 rejected), a fair contrast case",
}


# ------------------------------------------------------------------ LLM status
def ollama_up():
    try:
        return httpx.get(OLLAMA_URL, timeout=1.5).status_code == 200
    except Exception:
        return False


def _warm(state):
    try:
        if not ollama_up():
            state["status"] = "offline"
            return
        state["status"] = "warming"
        state["cold_load_s"] = llm.warm_up()
        state["status"] = "ready"
    except Exception:
        state["status"] = "offline"


@st.cache_resource
def _warm_state():
    state = {"status": "warming", "thread": None}
    state["thread"] = threading.Thread(target=_warm, args=(state,), daemon=True)
    state["thread"].start()
    return state


def llm_status():
    """'warming' | 'ready' | 'offline'. Offline is re-checked so the badge recovers when ollama serve is started."""
    state = _warm_state()
    if state["status"] == "offline" and ollama_up() and not (state["thread"] and state["thread"].is_alive()):
        state["status"] = "warming"
        state["thread"] = threading.Thread(target=_warm, args=(state,), daemon=True)
        state["thread"].start()
    return state["status"]


# ------------------------------------------------------------------ cached resources
@st.cache_resource
def resources():
    students = {s["id"]: s for s in load_students()}
    return dict(students=students, retriever=Retriever(), bm25=bl.Bm25(students))


@st.cache_data
def requirements():
    """[{id, text}] only: no truth fields and no dev/test split."""
    rows = [json.loads(line) for line in (ROOT / "data" / "requirements.jsonl").read_text(encoding="utf-8").splitlines()]
    return [{"id": r["id"], "text": r["text"]} for r in rows]


@st.cache_data
def requirement_title(rid, text):
    try:
        return parse_requirement(text)[0]["role_title"]
    except Exception:
        return " ".join(text.split()[:6]) + "..."


@st.cache_data
def qualified_set(req_id):
    """Synthetic ground truth, only for the reveal toggle on sample requirements."""
    with open(ROOT / "data" / "qrels.csv", encoding="utf-8") as f:
        return {r["student_id"] for r in csv.DictReader(f) if r["req_id"] == req_id and r["qualified"] == "1"}


# ------------------------------------------------------------------ pipeline
def run_pipeline(text, mode, progress=None):
    """mode: 'hybrid' (post-hoc B5 variant) or 'dense' (paper main configuration). Re-ranker unchanged, K=20, shortlist 10.
    progress(i, n, message) is called while scoring. Raises on parser/LLM failure of the whole run."""
    res = resources()
    students = res["students"]
    t0 = time.perf_counter()
    if progress:
        progress(0, K_RETRIEVE, "Reading the requirement")
    parsed, _ = parse_requirement(text)
    filters = filters_from_parsed(parsed)
    eligible = bl.eligible_ids(filters, students)
    out = dict(mode=mode, text=text, parsed=parsed, filters=filters, n_students=len(students), eligible=eligible,
               ranked=[], pool=[], ats=None)
    if not eligible:
        out["empty"] = True
        return out
    if progress:
        progress(0, K_RETRIEVE, "Retrieving candidates")
    dense = res["retriever"].retrieve(parsed, k=len(eligible))[0]
    sim = {h["id"]: h["similarity"] for h in dense}
    if mode == "hybrid":
        bm_full = res["bm25"].rank(parsed["semantic_query"], eligible)
        tie = rrf_scores([bm_full, [h["id"] for h in dense]])
    else:
        tie = sim
    pool = sorted(tie, key=lambda s: (-tie[s], s))[:K_RETRIEVE]
    out["pool"] = pool
    ranked = []
    for i, sid in enumerate(pool, 1):
        if progress:
            progress(i - 1, len(pool), f"Scoring candidate {i}/{len(pool)}")
        try:
            r, info = score_candidate(text, parsed, students[sid]["resume_text"], True)
            ranked.append(dict(id=sid, score=r["score"], matched=r["matched_skills"], missing=r["missing_skills"],
                               explanation=r["explanation"], tie=tie[sid], cached=info["cached"], error=None))
        except Exception as e:  # one failed call must not crash the run
            ranked.append(dict(id=sid, score=None, matched=[], missing=[], explanation="", tie=tie[sid], cached=False,
                               error=str(e)[:200]))
    ranked.sort(key=lambda r: (-(r["score"] if r["score"] is not None else -1), -r["tie"]))
    out["ranked"] = ranked
    # strict keyword ATS (same code as baseline B1) on the same eligible students
    ats_rank, passers = bl.ats_ranking(parsed, students, eligible, bl.exact_match, 1.0)
    out["ats"] = dict(ranking=ats_rank, passers=sorted(passers))
    out["seconds"] = time.perf_counter() - t0
    if progress:
        progress(len(pool), len(pool), "Done")
    return out


def missing_keywords(parsed, text):
    return [s for s in parsed["must_have_skills"] if not bl.exact_match(text, s)]


def ats_rejects_qualified(res_obj, req_id):
    """Ground-truth mode: how many qualified students does the strict ATS reject for this requirement."""
    qual = qualified_set(req_id)
    passers = set(res_obj["ats"]["passers"])
    return len(qual), len([s for s in qual if s not in passers])


# ------------------------------------------------------------------ evidence (reads eval/results only)
METHOD_NAMES = {"B1": "B1 Keyword ATS (strict)", "B1b": "B1b ATS (lenient)", "B1c": "B1c ATS + synonyms", "B2": "B2 BM25",
                "B3": "B3 Dense only", "B3b": "B3b Hybrid (RRF)", "B4": "B4 Dense + LLM re-rank (paper main)",
                "B4-K50": "B4 with K=50", "B4-oracle": "B4 with oracle filters", "B4-noFair": "B4 without fairness instruction"}


@st.cache_data
def per_requirement():
    return pd.read_csv(RES / "per_requirement_metrics.csv")


def method_ci(methods, metric):
    df = per_requirement()
    rows = []
    for m in methods:
        v = df[df.method == m][metric].tolist()
        mean, lo, hi = boot_ci(v)
        rows.append(dict(method=m, name=METHOD_NAMES[m], mean=mean, lo=lo, hi=hi))
    return pd.DataFrame(rows)


def main_table(methods, cols=("ndcg10", "mrr", "p10", "recall10_cap", "frr10", "frr20")):
    out = []
    for m in methods:
        row = {"Method": METHOD_NAMES[m]}
        for c in cols:
            mean, lo, hi = boot_ci(per_requirement()[per_requirement().method == m][c].tolist())
            row[{"ndcg10": "nDCG@10", "mrr": "MRR", "p10": "P@10", "recall10_cap": "Recall@10 (capped)",
                 "frr10": "FRR@10", "frr20": "FRR@20"}[c]] = f"{mean:.3f} [{lo:.3f}, {hi:.3f}]"
        out.append(row)
    return pd.DataFrame(out)


@st.cache_data
def ats_rejection_by_archetype():
    base = json.loads((RES / "baselines.json").read_text(encoding="utf-8"))["ats"]
    rows = []
    archs = ["standard", "paraphrased", "implied", "abbreviated_noisy", "sparse_strong", "generalist_average"]
    for m in ("B1", "B1b", "B1c"):
        row = {"Method": METHOD_NAMES[m]}
        tot_f = sum(v["qualified_failing"] for v in base[m].values())
        tot_q = sum(v["qualified"] for v in base[m].values())
        row["Overall"] = f"{tot_f / tot_q:.0%} ({tot_f}/{tot_q})"
        for a in archs:
            f = sum(v["by_archetype"].get(a, [0, 0])[0] for v in base[m].values())
            q = sum(v["by_archetype"].get(a, [0, 0])[1] for v in base[m].values())
            row[a] = f"{f / q:.0%} ({f}/{q})" if q else "-"
        rows.append(row)
    return pd.DataFrame(rows)


@st.cache_data
def archetype_share():
    df = pd.read_csv(RES / "archetype_table.csv")
    df["share"] = df.found_top20 / df.qualified
    return df


@st.cache_data
def posthoc_tables():
    return dict(b5=pd.read_csv(RES / "posthoc_b5_summary.csv"), paired=pd.read_csv(RES / "posthoc_b5_paired.csv"),
                arch=pd.read_csv(RES / "posthoc_b5_archetype.csv"), metrics=pd.read_csv(RES / "posthoc_b5_metrics.csv"),
                d1=pd.read_csv(RES / "posthoc_d1.csv"), d1s=pd.read_csv(RES / "posthoc_d1_summary.csv"))


@st.cache_data
def fairness_summary():
    out = {}
    for cond in ("on", "off"):
        rows = json.loads((RES / f"fairness_{cond}.json").read_text(encoding="utf-8"))
        out[cond] = fair.summarize(rows)
    return out


@st.cache_data
def retrieval_pool_totals():
    df = pd.read_csv(RES / "retrieval.csv")
    return int(df.parsed_top20.sum()), int(df.n_qualified.sum())
