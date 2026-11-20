"""Hybrid retrieval for the extensions: BM25 over resume text fused with dense retrieval by reciprocal rank fusion (k=60).

Same method as the post-hoc B3b/B5 variant (eval/baselines.py, eval/posthoc.py); copied here so src/ does not import
eval/. New module: the frozen top-10 pipeline (src/pipeline.py) does not use it.
"""
import re

from rank_bm25 import BM25Okapi

from .retrieve import filters_from_parsed

TOKEN = re.compile(r"[a-z0-9]+")
RRF_K = 60


def tokenize(text):
    return TOKEN.findall(text.lower())


def eligible_ids(parsed, students):
    """Students passing the parsed hard filters (same rules as the retriever's metadata filter)."""
    f = filters_from_parsed(parsed)
    return [sid for sid, s in students.items()
            if (f["min_cgpa"] is None or s["cgpa"] >= f["min_cgpa"])
            and (f["max_backlogs"] is None or s["active_backlogs"] <= f["max_backlogs"])
            and (not f["allowed_branches"] or s["branch"] in f["allowed_branches"])]


class Bm25Index:
    def __init__(self, students):
        self.ids = list(students)
        self.model = BM25Okapi([tokenize(students[s]["resume_text"]) for s in self.ids])

    def rank(self, query, eligible):
        scores = dict(zip(self.ids, self.model.get_scores(tokenize(query))))
        return sorted(eligible, key=lambda s: (-scores[s], s))


def rrf_scores(rankings, k=RRF_K):
    score = {}
    for r in rankings:
        for pos, sid in enumerate(r, 1):
            score[sid] = score.get(sid, 0.0) + 1.0 / (k + pos)
    return score


def hybrid_rank(retriever, bm25, parsed, eligible):
    """Eligible students ranked by RRF of BM25 and dense similarity. Returns [(student_id, rrf_score)], best first."""
    if not eligible:
        return []
    dense = [h["id"] for h in retriever.retrieve(parsed, k=len(eligible))[0]]
    bm = bm25.rank(parsed["semantic_query"], eligible)
    score = rrf_scores([bm, dense])
    return [(s, score[s]) for s in sorted(score, key=lambda s: (-score[s], s))]
