"""Dev-set checks (may read truth files; the pipeline in src/ never does).

    python eval/dev_checks.py                # reads eval/dev_run.json (written by scripts/run_dev.py)
    python eval/dev_checks.py --parser-only  # parses the 5 dev requirements (cached LLM) and checks only the parser

Only the 5 requirements with split == "dev" are ever touched.
"""
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.config import BRANCHES, DATA  # noqa: E402
import gen_data as g  # noqa: E402  (taxonomy + term matching only)


def jl(name):
    return [json.loads(l) for l in (DATA / name).read_text(encoding="utf-8").splitlines()]


def norm_skill(s):
    low = s.strip().lower()
    for name, sk in g.SK.items():
        if low in [t.lower() for t in [name] + sk["aliases"]]:
            return {name}
    return {name for name in g.SK for t in g.skill_terms(name) if g.term_pattern(t).search(s)}


def norm_set(skills):
    out, unmatched = set(), []
    for s in skills:
        m = norm_skill(s)
        out |= m
        if not m:
            unmatched.append(s)
    return out, unmatched


def load_dev():
    reqs = [r for r in jl("requirements.jsonl") if r["split"] == "dev"]
    truth = json.loads((DATA / "requirements_truth.json").read_text(encoding="utf-8"))
    return reqs, truth


def parser_accuracy(reqs, truth, parsed_by_id):
    rows, mism = [], []
    ok = {"min_cgpa": 0, "max_backlogs": 0, "allowed_branches": 0}
    tp = fp = fn = 0
    for r in reqs:
        t, p = truth[r["id"]], parsed_by_id[r["id"]]
        checks = {
            "min_cgpa": (p["min_cgpa"] is None and t["min_cgpa"] is None)
            or (p["min_cgpa"] is not None and t["min_cgpa"] is not None and abs(p["min_cgpa"] - t["min_cgpa"]) < 1e-9),
            "max_backlogs": p["max_backlogs"] == t["max_backlogs"],
            "allowed_branches": set(p["allowed_branches"]) == set(t["allowed_branches"] or []),
        }
        for k, v in checks.items():
            ok[k] += v
            if not v:
                mism.append(f"{r['id']} {k}: parsed={p[k]!r} truth={t[{'allowed_branches': 'allowed_branches'}.get(k, k)]!r}")
        got, unm = norm_set(p["must_have_skills"])
        want = set(t["must_have"])
        tp, fp, fn = tp + len(got & want), fp + len(got - want), fn + len(want - got)
        if got != want or unm:
            mism.append(f"{r['id']} must_have: parsed={p['must_have_skills']} -> {sorted(got)} | truth={sorted(want)}"
                        + (f" | unnormalised={unm}" if unm else ""))
        ngot, _ = norm_set(p["nice_to_have_skills"])
        if ngot != set(t["nice_to_have"]):
            mism.append(f"{r['id']} nice_to_have (info): parsed={sorted(ngot)} truth={sorted(t['nice_to_have'])}")
    n = len(reqs)
    return dict(per_field={k: v / n for k, v in ok.items()}, overall=sum(ok.values()) / (3 * n),
                must_precision=tp / max(1, tp + fp), must_recall=tp / max(1, tp + fn), mismatches=mism)


def passes(s, f):
    return ((f.get("min_cgpa") is None or s["cgpa"] >= f["min_cgpa"])
            and (f.get("max_backlogs") is None or s["active_backlogs"] <= f["max_backlogs"])
            and (not f.get("allowed_branches") or s["branch"] in f["allowed_branches"]))


def ndcg_at(ranked_ids, rel, k=10):
    dcg = sum(rel[i] / math.log2(n + 2) for n, i in enumerate(ranked_ids[:k]))
    ideal = sorted(rel.values(), reverse=True)[:k]
    idcg = sum(v / math.log2(n + 2) for n, v in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def main():
    reqs, truth = load_dev()
    assert len(reqs) == 5 and all(r["split"] == "dev" for r in reqs)
    if "--parser-only" in sys.argv:
        from src.parser import parse_requirement
        parsed = {r["id"]: parse_requirement(r["text"])[0] for r in reqs}
        run = None
    else:
        run = json.loads((ROOT / "eval" / "dev_run.json").read_text(encoding="utf-8"))
        parsed = {rid: v["parsed"] for rid, v in run["results"].items()}

    print("== a) PARSER ACCURACY (dev)")
    pa = parser_accuracy(reqs, truth, parsed)
    for k, v in pa["per_field"].items():
        print(f"  {k:18s} {v:.0%}")
    print(f"  eligibility overall {pa['overall']:.0%} | must-have precision {pa['must_precision']:.0%} recall {pa['must_recall']:.0%}")
    for m in pa["mismatches"]:
        print("   -", m)
    if run is None:
        return

    from src.pipeline import retriever
    students = {s["id"]: s for s in jl("students.jsonl")}
    qrels = {}
    for row in csv.DictReader(open(DATA / "qrels.csv", encoding="utf-8")):
        qrels.setdefault(row["req_id"], {})[row["student_id"]] = (int(row["relevance"]), int(row["qualified"]))
    ret = retriever()

    print("\n== b) RETRIEVAL (dev): qualified students among retrieved")
    print("  req   filters   top20  top50  prec@20  returned20 | parser-caused false rejections")
    agg = {"parsed": [0, 0, 0], "oracle": [0, 0, 0]}
    for r in reqs:
        rid, t = r["id"], truth[r["id"]]
        qual = {s for s, (rel, q) in qrels[rid].items() if q}
        oracle = dict(min_cgpa=t["min_cgpa"], max_backlogs=t["max_backlogs"], allowed_branches=t["allowed_branches"] or [])
        wrongly = [s for s in qual if not passes(students[s], run["results"][rid]["filters"])]
        for name, fo in (("parsed", None), ("oracle", oracle)):
            h20, _ = ret.retrieve(parsed[rid], k=20, filters_override=fo)
            h50, _ = ret.retrieve(parsed[rid], k=50, filters_override=fo)
            q20 = sum(h["id"] in qual for h in h20)
            q50 = sum(h["id"] in qual for h in h50)
            print(f"  {rid}  {name:8s} {q20:5d} {q50:6d} {q20 / 20:8.2f} {len(h20):10d} | "
                  f"{len(wrongly) if name == 'parsed' else '-'}" + (f" {sorted(wrongly)}" if name == 'parsed' and wrongly else ""))
            agg[name][0] += q20
            agg[name][1] += q50
        agg["parsed"][2] += len(wrongly)
    for name in agg:
        print(f"  TOTAL {name:8s} top20={agg[name][0]} top50={agg[name][1]} precision@20={agg[name][0] / 100:.2f}"
              + (f" false_rejections={agg[name][2]}" if name == "parsed" else ""))

    print("\n== c) END-TO-END (dev, preliminary): final ranking = LLM score, ties by similarity")
    print("  req   nDCG@10 (rerank)  nDCG@10 (dense order)  Recall@10  Recall@10 (capped)  qualified_total")
    tot = []
    for r in reqs:
        rid = r["id"]
        rel = {s: v[0] for s, v in qrels[rid].items()}
        qual = {s for s, v in qrels[rid].items() if v[1]}
        ranked = [x["id"] for x in run["results"][rid]["ranked"]]
        dense = [x["id"] for x in sorted(run["results"][rid]["ranked"], key=lambda x: -x["similarity"])]
        hits = sum(i in qual for i in ranked[:10])
        row = (ndcg_at(ranked, rel), ndcg_at(dense, rel), hits / len(qual), hits / min(10, len(qual)), len(qual))
        tot.append(row)
        print(f"  {rid}   {row[0]:.3f}             {row[1]:.3f}                  {row[2]:.2f}       {row[3]:.2f}                {row[4]}")
    m = [sum(x[i] for x in tot) / len(tot) for i in range(4)]
    print(f"  MEAN  {m[0]:.3f}             {m[1]:.3f}                  {m[2]:.2f}       {m[3]:.2f}")


if __name__ == "__main__":
    main()
