"""Prototype extension (not evaluated; the paper's evaluation covers the frozen top-10 pipeline only):

shortlist_full: every candidate of a hybrid top-50 pool is scored by the existing re-ranker and labelled
"Top 10" / "Also suited" / "Below threshold" (company view). The student view lives in src/student_view.py.

The parser, retriever and re-ranker (prompt, schema, Qwen3.5 4B via Ollama, temperature 0, thinking off) are reused unchanged.
"""
import csv
import hashlib
import io
import json
import time

from .config import CACHE_DIR, MODEL
from .hybrid import RRF_K, Bm25Index, eligible_ids, hybrid_rank

K_POOL, THRESHOLD, TOP_N = 50, 60, 10
GROUPS = ("Top 10", "Also suited", "Below threshold")
CSV_COLUMNS = ["rank", "group", "student_id", "name", "branch", "cgpa", "backlogs", "score", "matched", "missing", "explanation"]
FULL_DIR = CACHE_DIR / "full_lists"

_state = {}


def _resources():
    """Lazy singletons so importing this module is cheap and tests can inject their own."""
    if "students" not in _state:
        from .data import load_students
        from .pipeline import retriever
        students = {s["id"]: s for s in load_students()}
        _state.update(students=students, retriever=retriever(), bm25=Bm25Index(students))
    return _state


# ------------------------------------------------------------------ labelling and export
def label_candidates(ranked, threshold=THRESHOLD, top_n=TOP_N):
    """Adds r['group'] to a score-sorted list: first top_n = Top 10; the rest with score >= threshold = Also suited;
    everything else (including unscored candidates) = Below threshold. Returns the same list."""
    for i, r in enumerate(ranked):
        if i < top_n:
            r["group"] = GROUPS[0]
        elif r.get("score") is not None and r["score"] >= threshold:
            r["group"] = GROUPS[1]
        else:
            r["group"] = GROUPS[2]
    return ranked


def count_suited(ranked):
    return sum(r["group"] in GROUPS[:2] for r in ranked)


def full_list_csv(ranked, students):
    """CSV text of the full list (columns CSV_COLUMNS). `ranked` must already carry 'group'."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(CSV_COLUMNS)
    for rank, r in enumerate(ranked, 1):
        s = students[r["id"]]
        w.writerow([rank, r["group"], s["id"], s["name"], s["branch"], s["cgpa"], s["active_backlogs"],
                    "" if r["score"] is None else r["score"], "; ".join(r["matched"]), "; ".join(r["missing"]), r["explanation"]])
    return buf.getvalue()


# ------------------------------------------------------------------ company view
def _config_key(requirement, k_pool):
    raw = json.dumps(dict(req=requirement.strip(), model=MODEL, k_pool=k_pool, rrf_k=RRF_K, fairness=True), sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def load_full_list(requirement, k_pool=K_POOL):
    """The saved full list for this requirement and configuration, or None."""
    p = FULL_DIR / f"{_config_key(requirement, k_pool)}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def shortlist_full(requirement, k_pool=K_POOL, threshold=THRESHOLD, top_n=TOP_N, progress=None, deps=None):
    """Parse -> hard filters -> hybrid retrieval -> top k_pool -> existing re-ranker on every pool member -> sorted + labelled.

    progress(i, n, elapsed_s, eta_s) is called before each candidate. Re-rank calls hit the on-disk call cache (src/llm.py),
    and the finished list is saved under .cache/full_lists, so repeat runs are instant.
    deps: dict(students, parse, score, hybrid) to inject fakes in tests; defaults are the real parser, re-ranker and hybrid index.
    """
    if deps is None:
        from .parser import parse_requirement
        from .rerank import score_candidate
        st = _resources()
        deps = dict(students=st["students"], parse=lambda t: parse_requirement(t)[0],
                    score=lambda t, p, text: score_candidate(t, p, text, True)[0],
                    hybrid=lambda parsed, elig: hybrid_rank(st["retriever"], st["bm25"], parsed, elig))
    t0 = time.perf_counter()
    students = deps["students"]
    parsed = deps["parse"](requirement)
    eligible = eligible_ids(parsed, students)
    pool = deps["hybrid"](parsed, eligible)[:k_pool]
    ranked = []
    for i, (sid, rrf) in enumerate(pool, 1):
        if progress:
            el = time.perf_counter() - t0
            progress(i - 1, len(pool), el, (el / (i - 1)) * (len(pool) - i + 1) if i > 1 else None)
        try:
            out = deps["score"](requirement, parsed, students[sid]["resume_text"])
            ranked.append(dict(id=sid, score=out["score"], matched=out["matched_skills"], missing=out["missing_skills"],
                               explanation=out["explanation"], rrf=rrf, error=None))
        except Exception as e:  # one failed call must not lose the whole list
            ranked.append(dict(id=sid, score=None, matched=[], missing=[], explanation="", rrf=rrf, error=str(e)[:200]))
    ranked.sort(key=lambda r: (-(r["score"] if r["score"] is not None else -1), -r["rrf"], r["id"]))
    label_candidates(ranked, threshold, top_n)
    if progress:
        progress(len(pool), len(pool), time.perf_counter() - t0, 0.0)
    result = dict(parsed=parsed, eligible_count=len(eligible), pool_size=len(pool), suited_count=count_suited(ranked),
                  threshold=threshold, top_n=top_n, ranked=ranked, wall_s=time.perf_counter() - t0)
    if deps.get("save", True) and all(r["error"] is None for r in ranked):
        FULL_DIR.mkdir(parents=True, exist_ok=True)
        (FULL_DIR / f"{_config_key(requirement, k_pool)}.json").write_text(json.dumps(result), encoding="utf-8")
    return result
