"""Full evaluation. Stages are resumable and write partial results to eval/results/ after every step.

    python eval/run_all.py setup baselines b4 report          # steps 2-5
    python eval/run_all.py ablate                              # step 6: K=50 and oracle filters
    python eval/run_all.py fair_on                             # step 7
    python eval/run_all.py fair_off report                     # step 8 (+ B4 with fairness_instruction=False) and final report
    EVAL_SPLIT=dev python eval/run_all.py setup baselines b4 report   # dry run of the code on the dev requirements

The main configuration lives in src/ and is frozen (git tag frozen-main-config); nothing here changes it.
"""
import csv
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metrics import (ARCHETYPES, HARD, LOGS, RES, ROOT, SPLIT, load_all, metric_row, oracle_filters)  # noqa: E402
from stats import boot_ci, fmt_ci, paired  # noqa: E402
import baselines as bl  # noqa: E402
import fairness as fair  # noqa: E402
from dev_checks import parser_accuracy  # noqa: E402

TEST = SPLIT == "test"
NAMES = {"B1": "B1 ATS strict", "B1b": "B1b ATS lenient (>=50%)", "B1c": "B1c ATS + synonyms", "B2": "B2 BM25",
         "B3": "B3 Dense only", "B3b": "B3b Hybrid (RRF)", "B4": "B4 Proposed (K=20)",
         "B4-K50": "B4 K=50", "B4-oracle": "B4 oracle filters", "B4-noFair": "B4 no fairness instruction"}
BASE_METHODS = ["B1", "B1b", "B1c", "B2", "B3", "B3b"]
MAIN_METHODS = BASE_METHODS + ["B4"]
ABL_METHODS = ["B4", "B4-K50", "B4-oracle", "B4-noFair"]
COLS = [("ndcg10", "nDCG@10"), ("mrr", "MRR"), ("p10", "P@10"), ("recall10", "Recall@10"),
        ("recall10_cap", "Recall@10 (capped)"), ("frr10", "FRR@10"), ("frr20", "FRR@20")]


def load_json(path):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def save_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def gpu_check():
    import ollama
    for m in ollama.Client().ps().models:
        if m.size and m.size_vram < 0.99 * m.size:
            raise SystemExit(f"STOP: {m.model} spilled to CPU ({m.size_vram}/{m.size} bytes in VRAM)")


# ---------------------------------------------------------------- stage 2: parse + retrieval + parser accuracy

def stage_setup(D):
    from src.parser import parse_requirement
    from src import pipeline
    from src.retrieve import filters_from_parsed
    P = load_json(RES / "parsed_all.json") or {}
    for r in D["reqs"] if TEST else [r for r in D["reqs"] if r["split"] == "dev"]:
        if r["id"] not in P:
            parsed, info = parse_requirement(r["text"])
            P[r["id"]] = dict(parsed=parsed, latency=info["latency"], cached=info["cached"])
    save_json(RES / "parsed_all.json", P)

    parsed = {rid: v["parsed"] for rid, v in P.items()}
    out = {}
    for part, ids in (("dev", D["dev_ids"]), ("test", D["test_ids"])):
        ids = [i for i in ids if i in parsed]
        if ids:
            reqs = [r for r in D["reqs"] if r["id"] in ids]
            out[part] = parser_accuracy(reqs, D["rtruth"], parsed)
    save_json(RES / "parser_accuracy.json", out)

    retr = pipeline.retriever()
    rows = []
    for rid in D["ids"]:
        qual = {s for s, v in D["qrels"][rid].items() if v["qualified"]}
        orc = oracle_filters(D["rtruth"][rid])
        pf = filters_from_parsed(parsed[rid])
        wrongly = sorted(s for s in qual if not bl.passes(D["students"][s], pf))
        row = dict(req_id=rid, n_qualified=len(qual), parser_false_rejections=len(wrongly))
        for name, fo in (("parsed", None), ("oracle", orc)):
            for k in (20, 50):
                hits, _ = retr.retrieve(parsed[rid], k=k, filters_override=fo)
                row[f"{name}_top{k}"] = sum(h["id"] in qual for h in hits)
        rows.append(row)
    save_csv(RES / "retrieval.csv", rows)
    print("setup done:", {k: round(v["overall"], 3) for k, v in out.items()})


def save_csv(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------- stage 3: non-LLM baselines

def stage_baselines(D):
    from src import pipeline
    from src.retrieve import filters_from_parsed
    P = load_json(RES / "parsed_all.json")
    students, retr, bm = D["students"], pipeline.retriever(), bl.Bm25(D["students"])
    rankings = defaultdict(dict)
    ats = defaultdict(dict)
    for rid in D["ids"]:
        parsed = P[rid]["parsed"]
        E = bl.eligible_ids(filters_from_parsed(parsed), students)
        dense_full = [h["id"] for h in retr.retrieve(parsed, k=len(students))[0]]
        assert set(dense_full) == set(E), "dense retrieval must cover exactly the eligible set"
        bm_full = bm.rank(parsed["semantic_query"], E)
        rankings["B2"][rid] = bm_full[:20]
        rankings["B3"][rid] = dense_full[:20]
        rankings["B3b"][rid] = bl.rrf([bm_full, dense_full])[:20]
        qual = [s for s, v in D["qrels"][rid].items() if v["qualified"]]
        for name, matcher, share in (("B1", bl.exact_match, 1.0), ("B1b", bl.exact_match, 0.5), ("B1c", bl.syn_match, 1.0)):
            ranking, passers = bl.ats_ranking(parsed, students, E, matcher, share)
            rankings[name][rid] = ranking[:20]
            # rejection rate of qualified students under the keyword rule alone (independent of the filters)
            scan = bl.keyword_scan(parsed, students, qual, matcher)
            nmust = len(parsed["must_have_skills"])
            fail = {s for s, (m, n, ok) in scan.items() if not (nmust == 0 or m / nmust >= share)}
            by = defaultdict(lambda: [0, 0])
            for s in qual:
                by[D["archetype"][s]][1] += 1
                by[D["archetype"][s]][0] += s in fail
            ats[name][rid] = dict(passers=len(passers), qualified=len(qual), qualified_failing=len(fail),
                                  by_archetype={a: v for a, v in by.items()})
    save_json(RES / "baselines.json", dict(rankings=rankings, ats=ats))
    print("baselines done")


# ---------------------------------------------------------------- LLM stages

def stage_llm(D, name, kwfn):
    from src import llm, pipeline
    path = RES / f"{name}.json"
    data = load_json(path) or {}
    todo = [r for r in D["ids"] if r not in data]
    if todo:
        print(f"[{name}] warm-up {llm.warm_up():.1f}s, {len(todo)} requirement(s) to run", flush=True)
    for rid in todo:
        t0 = time.time()
        data[rid] = pipeline.run(D["text"][rid], **kwfn(rid))
        save_json(path, data)
        gpu_check()
        tm = data[rid]["timing"]
        print(f"[{name}] {rid} done in {time.time() - t0:.0f}s (parse {tm['parse_s']:.1f}s, rerank {tm['rerank_s']:.1f}s, "
              f"{tm['n_candidates']} cand)", flush=True)
    return data


def stage_fair(D, cond):
    from src import pipeline
    flag = cond == "on"
    P = load_json(RES / "parsed_all.json")
    parsed = {rid: P[rid]["parsed"] for rid in D["ids"]}
    on = load_json(RES / "b4_k20.json")
    pairs = [(rid, x["id"]) for rid in D["ids"] for x in on[rid]["ranked"][:10]]
    pools_src = on if flag else stage_llm(D, "b4_off", lambda rid: dict(k=20, fairness_instruction=False))
    pools = {rid: pools_src[rid]["ranked"] for rid in D["ids"]}
    variants = fair.make_variants(pairs, D["students"], D["truth"])
    sims = fair.similarity_shifts(variants, D["students"], parsed, pipeline.retriever())
    print(f"[fair_{cond}] {len(pairs)} pairs, {len(variants)} swapped resumes", flush=True)
    rows = fair.run_condition(variants, sims, pools, parsed, D["text"], flag, RES / f"fairness_{cond}.json")
    print(f"[fair_{cond}] done, {sum(not r['cached'] for r in rows)} new LLM calls", flush=True)
    gpu_check()
    return rows


# ---------------------------------------------------------------- reporting helpers

def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def esc(s):
    return str(s).replace("\\", "\\textbackslash{}").replace("_", "\\_").replace("%", "\\%").replace("&", "\\&").replace("#", "\\#")


def tex_table(path, header, rows, colfmt=None):
    colfmt = colfmt or "l" + "c" * (len(header) - 1)
    lines = ["\\begin{tabular}{" + colfmt + "}", "\\toprule", " & ".join(esc(h) for h in header) + " \\\\", "\\midrule"]
    lines += [" & ".join(esc(c) for c in r) + " \\\\" for r in rows]
    lines += ["\\bottomrule", "\\end{tabular}"]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def rankings_all(D):
    base = load_json(RES / "baselines.json")
    r = {m: base["rankings"][m] for m in BASE_METHODS} if base else {}
    for key, fname in (("B4", "b4_k20"), ("B4-K50", "b4_k50"), ("B4-oracle", "b4_oracle"), ("B4-noFair", "b4_off")):
        d = load_json(RES / f"{fname}.json")
        if d and all(rid in d for rid in D["ids"]):
            r[key] = {rid: [x["id"] for x in d[rid]["ranked"]] for rid in D["ids"]}
    return r


def git_hash():
    out = subprocess.run(["git", "rev-parse", "--verify", "-q", "frozen-main-config^{commit}"], cwd=ROOT, capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else "(tag frozen-main-config not found)"


def stage_report(D):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ids = D["ids"]
    R = rankings_all(D)
    per = {m: {rid: metric_row(R[m][rid], D["qrels"][rid]) for rid in ids} for m in R}
    csv_rows = [dict(method=m, req_id=rid, **per[m][rid]) for m in per for rid in ids]
    save_csv(RES / "per_requirement_metrics.csv", csv_rows)
    ci = {m: {c: boot_ci([per[m][rid][c] for rid in ids]) for c, _ in COLS} for m in per}
    md = []  # RESULTS.md sections

    def add(title, body):
        md.append(f"## {title}\n\n{body}\n")

    # ---- main results
    present = [m for m in MAIN_METHODS if m in per]
    rows = [[NAMES[m]] + [fmt_ci(*ci[m][c]) for c, _ in COLS] for m in present]
    hdr = ["Method"] + [n for _, n in COLS]
    add("Main results (mean over the test requirements, 95% bootstrap CI over requirements, 10,000 resamples, seed 42)",
        md_table(hdr, rows) + "\n\nAll rankings are truncated to 20 results (B4 K=50 to 50). Missing slots count as irrelevant. "
        "MRR is the reciprocal rank of the first qualified student in that list. FRR = 1 - capped Recall.")
    if TEST:
        tex_table(ROOT / "paper" / "tables" / "main_results.tex",
                  ["Method", "nDCG@10", "MRR", "P@10", "Recall@10$^{cap}$", "FRR@10", "FRR@20"],
                  [[NAMES[m]] + [f"{ci[m][c][0]:.3f} [{ci[m][c][1]:.3f}, {ci[m][c][2]:.3f}]"
                                 for c in ("ndcg10", "mrr", "p10", "recall10_cap", "frr10", "frr20")] for m in present],
                  colfmt="lcccccc")

    # ---- paired differences
    prow = []
    if "B4" in per:
        for other in ("B3", "B3b", "B1c", "B1"):
            if other not in per:
                continue
            for c, cname in (("ndcg10", "nDCG@10"), ("mrr", "MRR"), ("recall10_cap", "Recall@10 (capped)")):
                p = paired([per["B4"][r][c] for r in ids], [per[other][r][c] for r in ids])
                prow.append([f"B4 vs {other}", cname, fmt_ci(p["diff"], p["lo"], p["hi"]),
                             f"{p['wins']}/{p['losses']}/{p['ties']}", p["verdict"]])
    add("Paired differences (B4 minus baseline, 95% bootstrap CI over requirements)",
        md_table(["Comparison", "Metric", "Mean diff [CI]", "Win/loss/tie", "Verdict"], prow))

    # ---- ATS rejection
    base = load_json(RES / "baselines.json")
    if base:
        ats_rows, ats_tex = [], []
        archs = [a for a in ARCHETYPES if any(base["ats"]["B1"][r]["by_archetype"].get(a, [0, 0])[1] for r in ids)]
        for m in ("B1", "B1b", "B1c"):
            tot_f = sum(base["ats"][m][r]["qualified_failing"] for r in ids)
            tot_q = sum(base["ats"][m][r]["qualified"] for r in ids)
            cells = []
            for a in archs:
                f = sum(base["ats"][m][r]["by_archetype"].get(a, [0, 0])[0] for r in ids)
                q = sum(base["ats"][m][r]["by_archetype"].get(a, [0, 0])[1] for r in ids)
                cells.append(f"{f / q:.0%} ({f}/{q})" if q else "-")
            npass = [base["ats"][m][r]["passers"] for r in ids]
            ats_rows.append([NAMES[m], f"{tot_f / tot_q:.0%} ({tot_f}/{tot_q})"] + cells + [f"{min(npass)}-{max(npass)} (mean {sum(npass) / len(npass):.1f})"])
        hdr = ["Method", "Overall"] + archs + ["Passers per requirement"]
        add("ATS hard-rejection rate: share of qualified students failing the keyword rule (pooled over requirements)",
            md_table(hdr, ats_rows) + "\n\nB1c uses aliases from the generator's own taxonomy, so it is a generous baseline.")
        if TEST:
            tex_table(ROOT / "paper" / "tables" / "ats_rejection.tex", hdr, ats_rows, colfmt="l" + "c" * (len(hdr) - 1))

    # ---- archetype table (share of qualified found in top-20)
    arch_rows, arch_csv, shares = [], [], {}
    qual_by_arch = defaultdict(int)
    for rid in ids:
        for s, v in D["qrels"][rid].items():
            if v["qualified"]:
                qual_by_arch[D["archetype"][s]] += 1
    archs = [a for a in ARCHETYPES if qual_by_arch[a]]
    for m in [x for x in MAIN_METHODS if x in per]:
        cells = []
        for a in archs:
            found = sum(1 for rid in ids for s in R[m][rid][:20] if D["qrels"][rid][s]["qualified"] and D["archetype"][s] == a)
            shares[(m, a)] = found / qual_by_arch[a]
            cells.append(f"{found / qual_by_arch[a]:.0%} ({found}/{qual_by_arch[a]})")
            arch_csv.append(dict(method=m, archetype=a, found_top20=found, qualified=qual_by_arch[a]))
        arch_rows.append([NAMES[m]] + cells)
    save_csv(RES / "archetype_table.csv", arch_csv)
    add("Archetype table: share of qualified students found in the top-20 (pooled over requirements; counts in brackets)",
        md_table(["Method"] + archs, arch_rows))
    if TEST:
        tex_table(ROOT / "paper" / "tables" / "archetype_found.tex", ["Method"] + archs, arch_rows, colfmt="l" + "c" * len(archs))

    # ---- parser accuracy
    pa = load_json(RES / "parser_accuracy.json") or {}
    prow, mism = [], []
    for part, v in pa.items():
        prow.append([part] + [f"{v['per_field'][k]:.0%}" for k in ("min_cgpa", "max_backlogs", "allowed_branches")]
                    + [f"{v['overall']:.0%}", f"{v['must_precision']:.0%}", f"{v['must_recall']:.0%}"])
        mism += [f"- **{part}** {m}" for m in v["mismatches"]]
    add("Parser accuracy (exact match on eligibility fields; must-have skills normalised through the taxonomy)",
        md_table(["Split", "min_cgpa", "max_backlogs", "allowed_branches", "eligibility overall", "must-have precision", "must-have recall"], prow)
        + "\n\nEvery mismatch:\n\n" + ("\n".join(mism) or "none"))
    if TEST and prow:
        tex_table(ROOT / "paper" / "tables" / "parser_accuracy.tex",
                  ["Split", "min\\_cgpa", "max\\_backlogs", "branches", "Elig.", "Must P", "Must R"], prow, colfmt="lcccccc")

    # ---- retrieval
    rt = list(csv.DictReader(open(RES / "retrieval.csv", encoding="utf-8"))) if (RES / "retrieval.csv").exists() else []
    if rt:
        add("Retrieval (qualified students in the pool)",
            md_table(["Req", "Qualified", "Parsed top-20", "Parsed top-50", "Oracle top-20", "Oracle top-50", "Parser-caused false rejections"],
                     [[r["req_id"], r["n_qualified"], r["parsed_top20"], r["parsed_top50"], r["oracle_top20"], r["oracle_top50"],
                       r["parser_false_rejections"]] for r in rt])
            + f"\n\nTotals: parsed top-20 {sum(int(r['parsed_top20']) for r in rt)}, top-50 {sum(int(r['parsed_top50']) for r in rt)}; "
              f"oracle top-20 {sum(int(r['oracle_top20']) for r in rt)}, top-50 {sum(int(r['oracle_top50']) for r in rt)}; "
              f"false rejections {sum(int(r['parser_false_rejections']) for r in rt)}.")

    # ---- ablations
    if "B4" in per:
        arows = []
        for m in [x for x in ABL_METHODS if x in per]:
            arows.append([NAMES[m]] + [fmt_ci(*ci[m][c]) for c in ("ndcg10", "mrr", "recall10_cap", "frr10", "frr20")])
        add("Ablations of B4 (pre-declared: K=50, oracle filters, no fairness instruction)",
            md_table(["Variant", "nDCG@10", "MRR", "Recall@10 (capped)", "FRR@10", "FRR@20"], arows))
        if TEST:
            tex_table(ROOT / "paper" / "tables" / "ablations.tex", ["Variant", "nDCG@10", "MRR", "Recall@10$^{cap}$", "FRR@10", "FRR@20"],
                      arows, colfmt="lccccc")
        drow = []
        for m in ("B4-K50", "B4-oracle", "B4-noFair"):
            if m in per:
                p = paired([per[m][r]["ndcg10"] for r in ids], [per["B4"][r]["ndcg10"] for r in ids])
                drow.append([f"{NAMES[m]} minus B4", fmt_ci(p["diff"], p["lo"], p["hi"]), f"{p['wins']}/{p['losses']}/{p['ties']}", p["verdict"]])
        if drow:
            add("Ablation differences in nDCG@10", md_table(["Comparison", "Mean diff [CI]", "Win/loss/tie", "Verdict"], drow))

    # ---- spot check
    sc_path = ROOT / "data" / "spotcheck_labeled.csv"
    if sc_path.exists():
        from sklearn.metrics import cohen_kappa_score, confusion_matrix
        rows_sc = [r for r in csv.DictReader(open(sc_path, encoding="utf-8-sig")) if r["my_label"].strip() != ""]
        if rows_sc:
            gen = [int(r["generated_label"]) for r in rows_sc]
            mine = [int(float(r["my_label"])) for r in rows_sc]
            kappa = cohen_kappa_score(gen, mine, weights="quadratic", labels=[0, 1, 2, 3])
            exact = sum(a == b for a, b in zip(gen, mine)) / len(gen)
            bg, bm_ = [int(x >= 2) for x in gen], [int(x >= 2) for x in mine]
            cm = confusion_matrix(bg, bm_, labels=[0, 1])
            dis = [f"- {r['req_id']} / {r['student_id']}: generated {r['generated_label']}, my label {r['my_label']}"
                   for r in rows_sc if int(r["generated_label"]) != int(float(r["my_label"]))]
            add("Spot-check agreement (data/spotcheck_labeled.csv)",
                f"n={len(rows_sc)}; quadratic-weighted Cohen's kappa = {kappa:.3f}; exact agreement = {exact:.0%}; "
                f"binary (qualified = relevance >= 2) agreement = {sum(a == b for a, b in zip(bg, bm_)) / len(bg):.0%}.\n\n"
                f"Binary confusion matrix (rows = generated, columns = mine; 0 = not qualified, 1 = qualified): {cm.tolist()}\n\n"
                "Disagreements:\n\n" + ("\n".join(dis) or "none"))
        else:
            add("Spot-check agreement", "data/spotcheck_labeled.csv exists but my_label is empty; skipped.")
    else:
        add("Spot-check agreement", "data/spotcheck_labeled.csv is missing; skipped.")

    # ---- fairness
    fair_summary = {}
    for cond in ("on", "off"):
        rows_f = load_json(RES / f"fairness_{cond}.json")
        if rows_f:
            fair_summary[cond] = fair.summarize(rows_f)
    if fair_summary:
        frows, fraw = [], []
        for cond, s in fair_summary.items():
            label = "instruction ON" if cond == "on" else "instruction OFF"
            for k, name in (("abs_score_change", "mean abs score change (points)"), ("share_ge5", "share of swaps with abs change >= 5"),
                            ("abs_rank_shift", "mean abs rank shift in 20-pool"), ("boundary_crossing", "top-10 boundary-crossing rate"),
                            ("abs_sim_shift", "mean abs cosine-similarity shift (retrieval)")):
                v = s[k]
                frows.append([label, name, fmt_ci(*v["control"]), fmt_ci(*v["cross"]),
                              fmt_ci(v["cross_minus_control"]["diff"], v["cross_minus_control"]["lo"], v["cross_minus_control"]["hi"])
                              + f" ({v['cross_minus_control']['verdict']})"])
            for key, rowsd in (("target group", s["signed_by_target_group"]), ("target gender", s["signed_by_target_gender"]),
                               ("target region", s["signed_by_target_region"]), ("gender transition", s["signed_gender_transition"])):
                for g_, v in rowsd.items():
                    fraw.append([label, key, g_, fmt_ci(*v, digits=2)])
        add("Fairness (name swap): control = different name from the same group, cross = names from other groups; CIs over "
            f"{next(iter(fair_summary.values()))['n_pairs']} requirement-candidate pairs",
            md_table(["Condition", "Metric", "Control", "Cross-group", "Cross minus control"], frows)
            + "\n\nMean SIGNED score change after the swap (new minus original, points; CI over swaps):\n\n"
            + md_table(["Condition", "Grouping", "Value", "Mean signed change [CI]"], fraw)
            + "\n\nTarget-group usage (cross swaps): " + json.dumps(next(iter(fair_summary.values()))["target_group_counts"])
            + "\n\nThis tests names only, not college prestige or other proxies.")
        if TEST:
            tex_table(ROOT / "paper" / "tables" / "fairness.tex", ["Condition", "Metric", "Control", "Cross-group", "Cross$-$control"], frows, colfmt="llccc")
            save_csv(RES / "fairness_raw.csv", [dict(condition=c, **{k: v for k, v in r.items()})
                                                for c in ("on", "off") for r in (load_json(RES / f"fairness_{c}.json") or [])])

    # ---- timings and cache
    b4 = load_json(RES / "b4_k20.json")
    if b4:
        trows = [[rid, f"{v['timing']['parse_s']:.1f}", f"{v['timing']['retrieve_s']:.2f}", f"{v['timing']['rerank_s']:.1f}",
                  f"{v['timing']['rerank_per_candidate_s']:.2f}"] for rid, v in b4.items()]
        n_new = {n: sum(not x["cached"] for rid in d for x in d[rid]["ranked"])
                 for n in ("b4_k20", "b4_k50", "b4_oracle", "b4_off") if (d := load_json(RES / f"{n}.json"))}
        add("Timings (original, uncached latencies) and cache use",
            md_table(["Req", "Parse s", "Retrieve s", "Re-rank s (20 cand.)", "s per candidate"], trows)
            + f"\n\nNew (uncached) re-rank calls per run in this evaluation: {json.dumps(n_new)}. "
              f"Call cache: {sum(1 for _ in open(ROOT / '.cache' / 'llm_cache.jsonl', encoding='utf-8'))} entries.")

    # ---- figures
    figdir = ROOT / "paper" / "figs"
    if TEST:
        figdir.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(7, 3.4))
        means = [ci[m]["ndcg10"][0] for m in present]
        err = [[ci[m]["ndcg10"][0] - ci[m]["ndcg10"][1] for m in present], [ci[m]["ndcg10"][2] - ci[m]["ndcg10"][0] for m in present]]
        ax.bar(range(len(present)), means, yerr=err, capsize=3, color=["#9aa5b1"] * (len(present) - 1) + ["#1f6feb"])
        ax.set_xticks(range(len(present)))
        ax.set_xticklabels([m for m in present])
        ax.set_ylabel("nDCG@10 (mean, 95% CI)")
        ax.set_title("Ranking quality on the 10 test requirements")
        fig.tight_layout()
        for ext in ("pdf", "png"):
            fig.savefig(figdir / f"fig_ndcg10.{ext}", dpi=200)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(8, 3.6))
        w = 0.8 / len(present)
        for i, m in enumerate(present):
            ax.bar([j + i * w for j in range(len(archs))], [shares[(m, a)] for a in archs], w, label=m)
        ax.set_xticks([j + 0.4 - w / 2 for j in range(len(archs))])
        ax.set_xticklabels(archs, rotation=20, ha="right")
        ax.set_ylabel("share of qualified found in top-20")
        ax.legend(ncol=4, fontsize=7)
        fig.tight_layout()
        for ext in ("pdf", "png"):
            fig.savefig(figdir / f"fig_archetype.{ext}", dpi=200)
        plt.close(fig)

        if fair_summary:
            fig, ax = plt.subplots(figsize=(5, 3.4))
            labels, vals, lo, hi, cols = [], [], [], [], []
            for cond in fair_summary:
                for kind, col in (("control", "#9aa5b1"), ("cross", "#d1495b")):
                    m, a, b = fair_summary[cond]["abs_score_change"][kind]
                    labels.append(f"{cond.upper()}\n{kind}")
                    vals.append(m)
                    lo.append(m - a)
                    hi.append(b - m)
                    cols.append(col)
            ax.bar(range(len(vals)), vals, yerr=[lo, hi], capsize=3, color=cols)
            ax.set_xticks(range(len(vals)))
            ax.set_xticklabels(labels)
            ax.set_ylabel("mean |score change| (points)")
            ax.set_title("Name swap: fairness instruction ON vs OFF")
            fig.tight_layout()
            for ext in ("pdf", "png"):
                fig.savefig(figdir / f"fig_fairness.{ext}", dpi=200)
            plt.close(fig)

    head = (f"# Results ({'TEST' if TEST else 'DEV DRY RUN'} split)\n\nFrozen configuration: git tag `frozen-main-config` = `{git_hash()}`. "
            "K=20, qwen3.5:4b-q4_K_M, temperature 0, think off, fairness_instruction=True; the parser and re-ranker prompts in src/ "
            "were not changed after the tag.\n\n")
    foot = ("\n## Deviations and caveats\n\n"
            "- All methods share the parsed hard filters (the same eligible set); the oracle ablation is the only exception.\n"
            "- B1c aliases come from the generator's own taxonomy, so it is a generous baseline; the labels also come from that generator (circular).\n"
            "- Rankings are truncated to 20 (B4 K=50 to 50) before computing MRR, so a method cannot gain MRR from ranks below its pool.\n"
            "- Recall@10 (plain) is bounded by 10/#qualified when a requirement has more than 10 qualified students; the capped variant is the headline.\n"
            "- The fairness test rescored swapped resumes by calling the re-ranker directly (same prompt, requirement text and parsed skills as `pipeline.run`) instead of passing `resume_override` to a full 20-candidate run; pool rank shifts substitute the new score into the stored 20-candidate pool.\n"
            "- Only 10 test requirements: CIs are wide and per-requirement results are noisy.\n"
            "- Temperature 0 with a 4B model: score changes after a name swap include non-name effects of the changed prompt text; the control swap (same-group name) measures that floor.\n"
            "- The fairness test covers names only, not college prestige or other proxies.\n"
            "- **Bug fix after the freeze tag (src/llm.py only).** In the fairness OFF stage one swapped resume (R02 / S087, control swap) made the model loop inside the unbounded `matched_skills` array until the 4096-token context was full (finish reason `length`, invalid JSON), which crashed the stage. `chat_json` now retries once with every schema array capped at 8 items and `num_predict=700`, stored under the ORIGINAL cache key. It was needed for exactly 1 call out of 1716 cached calls; all earlier calls (every main, ablation and fairness-ON result) completed without it, so no previously successful result changed. Fairness OFF was resumed from the saved partial results (20 rows) and the final report regenerated. Prompts, schemas of normal calls, K, model and temperature are unchanged; `git diff frozen-main-config -- src` shows only this change.\n"
            "- GPU use was checked through the Ollama API after every requirement (`size_vram == size`); it stayed 100% GPU.\n")
    if TEST:
        (ROOT / "docs" / "RESULTS.md").write_text(head + "\n".join(md) + foot, encoding="utf-8")
        print("wrote docs/RESULTS.md, paper/tables/*.tex, paper/figs/*")
    else:
        RES.mkdir(parents=True, exist_ok=True)
        (RES / "RESULTS_dev_dry_run.md").write_text(head + "\n".join(md) + foot, encoding="utf-8")
        print("wrote", RES / "RESULTS_dev_dry_run.md")


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    D = load_all()
    for stage in sys.argv[1:]:
        t0 = time.time()
        if stage == "setup":
            stage_setup(D)
        elif stage == "baselines":
            stage_baselines(D)
        elif stage == "b4":
            stage_llm(D, "b4_k20", lambda rid: dict(k=20))
        elif stage == "ablate":
            stage_llm(D, "b4_k50", lambda rid: dict(k=50))
            stage_llm(D, "b4_oracle", lambda rid: dict(k=20, filters_override=oracle_filters(D["rtruth"][rid])))
        elif stage == "fair_on":
            stage_fair(D, "on")
        elif stage == "fair_off":
            stage_fair(D, "off")
        elif stage == "report":
            stage_report(D)
        else:
            raise SystemExit(f"unknown stage {stage}")
        print(f"== stage {stage} finished in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
