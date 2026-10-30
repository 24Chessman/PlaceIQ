"""POST-HOC EXPLORATORY additions, designed after seeing the test results. Nothing in src/ or in the frozen results changes.

  B5  hybrid retrieval (RRF of BM25 and dense, k=60, top-20 pool, parsed filters) + the unchanged LLM re-ranker.
  D1  diagnostic: can the re-ranker judge paraphrased resumes when retrieval is bypassed?

    python eval/posthoc.py          # runs both (resumable, cached), writes results, tables and the RESULTS.md section
"""
import random
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

from metrics import ARCHETYPES, RES, ROOT, SPLIT, load_all, metric_row  # noqa: E402  (sets sys.path first)
import baselines as bl  # noqa: E402
import run_all as ra  # noqa: E402
from stats import boot_ci, fmt_ci, paired  # noqa: E402

assert SPLIT == "test", "run posthoc.py with the default (test) split"
TAG = "post-hoc exploratory"
COLS = [("ndcg10", "nDCG@10"), ("mrr", "MRR"), ("p10", "P@10"), ("recall10_cap", "Recall@10 (capped)"),
        ("frr10", "FRR@10"), ("frr20", "FRR@20")]
NEW_CALLS = {"b5": 0, "d1": 0}


def rrf_scores(rankings, k=60):
    score = defaultdict(float)
    for r in rankings:
        for pos, sid in enumerate(r, 1):
            score[sid] += 1.0 / (k + pos)
    return score


def stage_b5(D, P):
    from src import llm, pipeline
    from src.rerank import score_candidate
    from src.retrieve import filters_from_parsed
    path = RES / "posthoc_b5.json"
    data = ra.load_json(path) or {}
    ids = D["dev_ids"] + D["test_ids"]
    todo = [r for r in ids if r not in data]
    if todo:
        print(f"[b5] warm-up {llm.warm_up():.1f}s, {len(todo)} requirements", flush=True)
    retr, bm = pipeline.retriever(), bl.Bm25(D["students"])
    for rid in todo:
        t0 = time.time()
        parsed = P[rid]["parsed"]
        E = bl.eligible_ids(filters_from_parsed(parsed), D["students"])
        dense_full = [h["id"] for h in retr.retrieve(parsed, k=len(D["students"]))[0]]
        assert set(dense_full) == set(E)
        bm_full = bm.rank(parsed["semantic_query"], E)
        score = rrf_scores([bm_full, dense_full])
        pool = sorted(score, key=lambda s: (-score[s], s))[:20]
        ranked = []
        for sid in pool:
            out, info = score_candidate(D["text"][rid], parsed, D["students"][sid]["resume_text"], True)
            NEW_CALLS["b5"] += not info["cached"]
            ranked.append(dict(id=sid, score=out["score"], rrf=score[sid], cached=info["cached"], latency=info["latency"]))
        ranked.sort(key=lambda r: (-r["score"], -r["rrf"]))
        data[rid] = dict(pool=pool, ranked=ranked, rerank_s=sum(r["latency"] for r in ranked),
                         new_calls=sum(not r["cached"] for r in ranked))
        ra.save_json(path, data)
        ra.gpu_check()
        print(f"[b5] {rid} done in {time.time() - t0:.0f}s ({data[rid]['new_calls']} new calls)", flush=True)
    return data


def d1_candidates(D, rid):
    q = D["qrels"][rid]
    pos = sorted(s for s, v in q.items() if v["qualified"] and D["archetype"][s] == "paraphrased")
    neg = sorted(s for s, v in q.items() if v["eligible"] and not v["qualified"])
    rng = random.Random(f"42:{rid}")
    stuffed = [s for s in neg if D["archetype"][s] == "stuffed_weak"]
    other = [s for s in neg if D["archetype"][s] != "stuffed_weak"]
    pick = rng.sample(stuffed, min(5, len(stuffed)))
    pick += rng.sample(other, min(15 - len(pick), len(other)))
    return pos, sorted(pick)


def stage_d1(D, P):
    from src import llm
    from src.rerank import score_candidate
    path = RES / "posthoc_d1.json"
    data = ra.load_json(path) or {}
    todo = [r for r in D["test_ids"] if r not in data]
    if todo:
        print(f"[d1] warm-up {llm.warm_up():.1f}s, {len(todo)} requirements", flush=True)
    for rid in todo:
        t0 = time.time()
        pos, neg = d1_candidates(D, rid)
        rows = []
        for sid, label in [(s, 1) for s in pos] + [(s, 0) for s in neg]:
            out, info = score_candidate(D["text"][rid], P[rid]["parsed"], D["students"][sid]["resume_text"], True)
            NEW_CALLS["d1"] += not info["cached"]
            rows.append(dict(id=sid, qualified=label, archetype=D["archetype"][sid], score=out["score"],
                             cached=info["cached"], latency=info["latency"]))
        data[rid] = rows
        ra.save_json(path, data)
        ra.gpu_check()
        print(f"[d1] {rid} done in {time.time() - t0:.0f}s ({len(pos)} paraphrased-qualified, {len(neg)} non-qualified)", flush=True)
    return data


def tex(path, header, rows, colfmt=None):
    ra.tex_table(path, header, rows, colfmt)
    p = Path(path)
    p.write_text(f"% POST-HOC EXPLORATORY (designed after seeing the test results)\n" + p.read_text(encoding="utf-8"), encoding="utf-8")


def report(D, b5, d1, wall):
    test, dev = D["test_ids"], D["dev_ids"]
    out = {}
    per = {rid: metric_row([x["id"] for x in b5[rid]["ranked"]], D["qrels"][rid]) for rid in dev + test}
    ra.save_csv(RES / "posthoc_b5_metrics.csv", [dict(split="dev" if rid in dev else "test", req_id=rid, new_calls=b5[rid]["new_calls"],
                                                     **per[rid]) for rid in dev + test])
    sections = []
    # ---- B5 table dev and test
    summ_rows, csv_rows = [], []
    for name, ids in (("dev (n=5)", dev), ("test (n=10)", test)):
        cells = []
        for c, _ in COLS:
            m = boot_ci([per[r][c] for r in ids])
            cells.append(fmt_ci(*m))
            csv_rows.append(dict(split=name, metric=c, mean=m[0], lo=m[1], hi=m[2]))
        summ_rows.append([f"B5 hybrid + LLM re-rank, {name}"] + cells)
    ra.save_csv(RES / "posthoc_b5_summary.csv", csv_rows)
    sections.append(("B5 (post-hoc exploratory): hybrid retrieval + unchanged LLM re-ranker",
                     ra.md_table(["Method"] + [n for _, n in COLS], summ_rows)
                     + "\n\nPool = top-20 of the RRF (k=60) fusion of BM25 and dense over eligible students; ranking = LLM score, ties by RRF score. "
                       "Mean with 95% bootstrap CI over requirements (10,000 resamples, seed 42); with n=5 the dev CIs are very wide."))
    tex(ROOT / "paper" / "tables" / "posthoc_b5.tex", ["Method (post-hoc)"] + [n for _, n in COLS],
        [[r[0]] + [c for c in r[1:]] for r in summ_rows], colfmt="lcccccc")

    # ---- paired differences on test
    R = ra.rankings_all(D)
    ref = {m: {rid: metric_row(R[m][rid], D["qrels"][rid]) for rid in test} for m in ("B4", "B3b", "B1c")}
    prow = []
    for other in ("B4", "B3b", "B1c"):
        for c, cname in (("ndcg10", "nDCG@10"), ("mrr", "MRR"), ("recall10_cap", "Recall@10 (capped)"), ("frr20", "FRR@20")):
            p = paired([per[r][c] for r in test], [ref[other][r][c] for r in test], lower_is_better=c.startswith("frr"))
            prow.append([f"B5 vs {other}", cname, fmt_ci(p["diff"], p["lo"], p["hi"]), f"{p['wins']}/{p['losses']}/{p['ties']}", p["verdict"]])
    ra.save_csv(RES / "posthoc_b5_paired.csv", [dict(comparison=r[0], metric=r[1], diff_ci=r[2], win_loss_tie=r[3], verdict=r[4]) for r in prow])
    sections.append(("B5 paired differences on test (post-hoc exploratory; B5 minus baseline; FRR: negative = B5 better)",
                     ra.md_table(["Comparison", "Metric", "Mean diff [CI]", "Win/loss/tie of B5", "Verdict"], prow)))
    tex(ROOT / "paper" / "tables" / "posthoc_b5_paired.tex", ["Comparison", "Metric", "Mean diff [CI]", "W/L/T", "Verdict"], prow, colfmt="llccc")

    # ---- qualified in pool per requirement and archetype table
    b4h = {rid: metric_row(R["B4"][rid], D["qrels"][rid]) for rid in test}
    rows = [[rid, per[rid]["n_qualified"], b4h[rid]["hits20"], per[rid]["hits20"]] for rid in test]
    tot_q = sum(r[1] for r in rows)
    rows.append(["Total", tot_q, sum(r[2] for r in rows), sum(r[3] for r in rows)])
    sections.append(("Qualified students in the top-20 pool, test (post-hoc exploratory)",
                     ra.md_table(["Req", "Qualified", "B4 (dense pool)", "B5 (hybrid pool)"], rows)
                     + f"\n\nB4 pool total {rows[-1][2]}/{tot_q}; B5 pool total {rows[-1][3]}/{tot_q}."))
    qual_by_arch = defaultdict(int)
    for rid in test:
        for s, v in D["qrels"][rid].items():
            if v["qualified"]:
                qual_by_arch[D["archetype"][s]] += 1
    archs = [a for a in ARCHETYPES if qual_by_arch[a]]
    arows, acsv = [], []
    for name, key in (("B4 (dense pool)", "B4"), ("B3b hybrid ranking (no LLM)", "B3b"), ("B5 (hybrid pool)", "B5")):
        cells = []
        for a in archs:
            ranking = R[key] if key != "B5" else {rid: [x["id"] for x in b5[rid]["ranked"]] for rid in test}
            f = sum(1 for rid in test for s in ranking[rid][:20] if D["qrels"][rid][s]["qualified"] and D["archetype"][s] == a)
            cells.append(f"{f / qual_by_arch[a]:.0%} ({f}/{qual_by_arch[a]})")
            acsv.append(dict(method=name, archetype=a, found_in_pool=f, qualified=qual_by_arch[a]))
        arows.append([name] + cells)
    ra.save_csv(RES / "posthoc_b5_archetype.csv", acsv)
    sections.append(("Share of qualified students in the pool by archetype, test (post-hoc exploratory)",
                     ra.md_table(["Pool"] + archs, arows)))
    tex(ROOT / "paper" / "tables" / "posthoc_b5_archetype.tex", ["Pool (post-hoc)"] + archs, arows, colfmt="l" + "c" * len(archs))

    # ---- D1
    drows, dcsv, aucs, top10 = [], [], [], []
    allpos, allneg, allscores, alllabels = [], [], [], []
    for rid in test:
        rows_ = d1[rid]
        pos = [r for r in rows_ if r["qualified"]]
        neg = [r for r in rows_ if not r["qualified"]]
        ranked = sorted(rows_, key=lambda r: (-r["score"], r["id"]))
        in10 = sum(r["qualified"] for r in ranked[:10])
        auc = roc_auc_score([r["qualified"] for r in rows_], [r["score"] for r in rows_]) if pos and neg else float("nan")
        mp = float(np.mean([r["score"] for r in pos])) if pos else float("nan")
        mn = float(np.mean([r["score"] for r in neg]))
        stuffed = [r["score"] for r in neg if r["archetype"] == "stuffed_weak"]
        drows.append([rid, len(pos), len(neg), f"{mp:.1f}", f"{mn:.1f}", f"{auc:.3f}", f"{in10}/{len(pos)}"])
        dcsv.append(dict(req_id=rid, n_paraphrased_qualified=len(pos), n_nonqualified=len(neg), mean_score_pos=mp, mean_score_neg=mn,
                         mean_score_stuffed=float(np.mean(stuffed)) if stuffed else float("nan"), auc=auc, pos_in_top10=in10))
        if pos:
            aucs.append(auc)
            top10.append((in10, len(pos)))
        allscores += [r["score"] for r in rows_]
        alllabels += [r["qualified"] for r in rows_]
        allpos += [r["score"] for r in pos]
        allneg += [r["score"] for r in neg]
    ra.save_csv(RES / "posthoc_d1.csv", dcsv)
    am = boot_ci(aucs)
    pooled_auc = roc_auc_score(alllabels, allscores)
    share = sum(a for a, _ in top10) / sum(b for _, b in top10)
    stuffed_all = [r["score"] for rid in test for r in d1[rid] if r["archetype"] == "stuffed_weak"]
    summary = [["Mean score, paraphrased-qualified (pooled)", f"{np.mean(allpos):.1f}"],
               ["Mean score, non-qualified (pooled)", f"{np.mean(allneg):.1f}"],
               ["Mean score, stuffed_weak non-qualified", f"{np.mean(stuffed_all):.1f}"],
               ["ROC AUC, mean of per-requirement AUCs [95% CI over requirements]", fmt_ci(*am)],
               ["ROC AUC, all candidates pooled", f"{pooled_auc:.3f}"],
               ["Paraphrased-qualified in the top 10 of their candidate set", f"{sum(a for a, _ in top10)}/{sum(b for _, b in top10)} ({share:.0%})"]]
    ra.save_csv(RES / "posthoc_d1_summary.csv", [dict(metric=r[0], value=r[1]) for r in summary])
    sections.append(("D1 (post-hoc exploratory): LLM judging of paraphrased resumes with retrieval bypassed",
                     "Candidate set per test requirement: every eligible, qualified `paraphrased` student plus 15 eligible non-qualified students "
                     "(5 from stuffed_weak where available, the rest from other archetypes; sampled with seed 42). Ties in the top-10 share are broken by student id.\n\n"
                     + ra.md_table(["Req", "Paraphrased qualified", "Non-qualified", "Mean score qualified", "Mean score non-qualified", "AUC", "Qualified in top 10"], drows)
                     + "\n\n" + ra.md_table(["Pooled", "Value"], summary)))
    tex(ROOT / "paper" / "tables" / "posthoc_d1.tex", ["Req", "Para. qual.", "Non-qual.", "Score qual.", "Score non-qual.", "AUC", "Top-10"], drows, colfmt="lcccccc")
    return sections, summary


def write_results(sections, wall):
    path = ROOT / "docs" / "RESULTS.md"
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"\n## Post-hoc exploratory \(designed after seeing test results\).*\Z", "\n", text, flags=re.S)
    body = ["\n## Post-hoc exploratory (designed after seeing test results)\n",
            "**These two analyses were designed AFTER the test results were known. They are exploratory, were not pre-declared, and do not "
            "change any frozen main result (B1-B4, ablations, fairness).** Nothing under `src/` was modified; the code is `eval/posthoc.py`. "
            "Commit: POSTHOC_COMMIT (frozen tag `frozen-main-config` is untouched).\n",
            f"New (uncached) LLM calls: B5 {NEW_CALLS['b5']}, D1 {NEW_CALLS['d1']}. Wall time of the first (uncached) run: {wall:.0f} s "
            "(`eval/results/posthoc_meta.json`; log: `eval/logs/posthoc.log`; re-running only rebuilds the report from the cache).\n"]
    for title, content in sections:
        body.append(f"### {title}\n\n{content}\n")
    path.write_text(text.rstrip() + "\n" + "\n".join(body), encoding="utf-8")


def main():
    t0 = time.time()
    D = load_all()
    P = ra.load_json(RES / "parsed_all.json")
    b5 = stage_b5(D, P)
    d1 = stage_d1(D, P)
    sections, _ = report(D, b5, d1, time.time() - t0)
    NEW_CALLS["b5"] = sum(v["new_calls"] for v in b5.values())  # from the saved results, so a report-only rerun keeps them
    NEW_CALLS["d1"] = sum(not r["cached"] for rows in d1.values() for r in rows)
    meta = ra.load_json(RES / "posthoc_meta.json") or {"wall_s": time.time() - t0}
    write_results(sections, meta["wall_s"])
    print(f"new calls: {NEW_CALLS}; total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
