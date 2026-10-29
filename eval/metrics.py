"""Shared evaluation helpers: data loading (evaluation code may read truth) and ranking metrics."""
import csv
import json
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "scripts", ROOT / "eval"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.config import DATA  # noqa: E402  (also sets PYTHONUTF8 / HF_HOME)

SPLIT = os.environ.get("EVAL_SPLIT", "test")  # "dev" is a dry run of the evaluation code on the dev requirements
RES = ROOT / "eval" / ("results" if SPLIT == "test" else "results_dev")
LOGS = ROOT / "eval" / "logs"
HARD = ("paraphrased", "implied", "abbreviated_noisy", "sparse_strong")
ARCHETYPES = ["standard", "paraphrased", "implied", "abbreviated_noisy", "sparse_strong", "ineligible_strong",
              "generalist_average", "stuffed_weak"]


def jl(name):
    return [json.loads(l) for l in (DATA / name).read_text(encoding="utf-8").splitlines()]


def load_all():
    students = {s["id"]: s for s in jl("students.jsonl")}
    truth = {t["id"]: t for t in jl("students_truth.jsonl")}
    reqs = jl("requirements.jsonl")
    rtruth = json.loads((DATA / "requirements_truth.json").read_text(encoding="utf-8"))
    qrels = {}
    for row in csv.DictReader(open(DATA / "qrels.csv", encoding="utf-8")):
        qrels.setdefault(row["req_id"], {})[row["student_id"]] = dict(
            eligible=int(row["eligible"]), rel=int(row["relevance"]), qualified=int(row["qualified"]))
    return dict(students=students, truth=truth, reqs=reqs, rtruth=rtruth, qrels=qrels,
                archetype={k: v["archetype"] for k, v in truth.items()},
                test_ids=[r["id"] for r in reqs if r["split"] == "test"],
                ids=[r["id"] for r in reqs if r["split"] == SPLIT],
                dev_ids=[r["id"] for r in reqs if r["split"] == "dev"],
                text={r["id"]: r["text"] for r in reqs})


def passes(s, f):
    """Does a student satisfy hard filters f = {min_cgpa, max_backlogs, allowed_branches}?"""
    return ((f.get("min_cgpa") is None or s["cgpa"] >= f["min_cgpa"])
            and (f.get("max_backlogs") is None or s["active_backlogs"] <= f["max_backlogs"])
            and (not f.get("allowed_branches") or s["branch"] in f["allowed_branches"]))


def oracle_filters(rtruth_entry):
    return dict(min_cgpa=rtruth_entry["min_cgpa"], max_backlogs=rtruth_entry["max_backlogs"],
                allowed_branches=rtruth_entry["allowed_branches"] or [])


def metric_row(ranking, qrel):
    """ranking: list of student ids, best first (may be shorter than 10/20). qrel: {sid: {rel, qualified}}."""
    qual = {s for s, v in qrel.items() if v["qualified"]}
    gains = lambda ids: sum((2 ** qrel[i]["rel"] - 1) / math.log2(n + 2) for n, i in enumerate(ids))
    ideal = sorted(qrel, key=lambda s: -qrel[s]["rel"])[:10]
    idcg = gains(ideal)
    top10, top20 = ranking[:10], ranking[:20]
    h10, h20 = sum(i in qual for i in top10), sum(i in qual for i in top20)
    mrr = next((1 / (n + 1) for n, i in enumerate(ranking) if i in qual), 0.0)
    nq = len(qual)
    r10c = h10 / min(10, nq) if nq else 0.0
    r20c = h20 / min(20, nq) if nq else 0.0
    return dict(ndcg10=gains(top10) / idcg if idcg else 0.0, mrr=mrr, p10=h10 / 10, recall10=h10 / nq if nq else 0.0,
                recall10_cap=r10c, frr10=1 - r10c, recall20_cap=r20c, frr20=1 - r20c, hits10=h10, hits20=h20,
                n_qualified=nq, returned=len(ranking))
