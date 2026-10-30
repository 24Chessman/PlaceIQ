"""Writes paper/numbers.tex (one \\newcommand per number the paper cites) and paper/numbers_report.md.

Every value is computed from eval/results/* (and read-only data/*) with the same code and seed as the evaluation;
nothing is typed by hand. Values that RESULTS.md also prints are cross-checked against its text; mismatches are listed
in the report and never fixed silently.      python eval/make_paper_numbers.py
"""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metrics import ROOT, load_all  # noqa: E402  (sets sys.path)
import fairness as fair  # noqa: E402
from stats import boot_ci, fmt_ci, paired  # noqa: E402

RES = ROOT / "eval" / "results"
RESULTS_MD = (ROOT / "docs" / "RESULTS.md").read_text(encoding="utf-8")
MACROS, CHECKS = [], []  # (name, value, source) ; (name, string expected in RESULTS.md)

METHOD = {"B1": "AtsStrict", "B1b": "AtsLenient", "B1c": "AtsSyn", "B2": "Bm", "B3": "Dense", "B3b": "Hybrid", "B4": "Prop",
          "B4-K50": "PropKfifty", "B4-oracle": "PropOracle", "B4-noFair": "PropNofair"}
METRIC = {"ndcg10": "Ndcg", "mrr": "Mrr", "p10": "Pten", "recall10": "Rplain", "recall10_cap": "Rcap", "frr10": "Frrten", "frr20": "Frrtwenty"}
ARCH = lambda a: "".join(w.capitalize() for w in a.split("_"))
GRP = lambda g: "".join(w.capitalize() for w in g.split("_"))


def tex_escape(v):
    return str(v).replace("\\", "\\textbackslash{}").replace("%", "\\%").replace("_", "\\_").replace("&", "\\&").replace("#", "\\#")


def add(name, value, src, check=None):
    assert re.fullmatch(r"[A-Za-z]+", name), name
    MACROS.append((name, str(value), src))
    if check is not None:
        CHECKS.append((name, check))


def f3(x):
    return f"{x:.3f}"


def pct(x):
    return f"{x:.0%}"


def add_ci(prefix, vals, src, check=True, digits=3):
    m, lo, hi = boot_ci(vals)
    s = fmt_ci(m, lo, hi, digits)
    add(prefix + "Mean", f"{m:.{digits}f}", src)
    add(prefix + "Lo", f"{lo:.{digits}f}", src)
    add(prefix + "Hi", f"{hi:.{digits}f}", src)
    add(prefix + "Ci", s, src, check=s if check else None)
    return m, lo, hi


def add_paired(prefix, a, b, src, check_metric=True):
    p = paired(a, b)
    s = fmt_ci(p["diff"], p["lo"], p["hi"])
    add(prefix + "Diff", f"{p['diff']:+.3f}", src)
    add(prefix + "DiffCi", s, src, check=s if check_metric else None)
    add(prefix + "Wlt", f"{p['wins']}/{p['losses']}/{p['ties']}", src, check=f"{p['wins']}/{p['losses']}/{p['ties']}" if check_metric else None)
    add(prefix + "Verdict", p["verdict"], src)
    return p


def main():
    D = load_all()
    test, dev = D["test_ids"], D["dev_ids"]
    # ---------------------------------------------------------------- dataset
    n_students = len(D["students"])
    add("NStudents", n_students, "data/students.jsonl")
    add("NRequirements", len(D["reqs"]), "data/requirements.jsonl")
    add("NDev", len(dev), "data/requirements.jsonl")
    add("NTest", len(test), "data/requirements.jsonl")
    for part, ids in (("Dev", dev), ("Test", test)):
        add(f"NQualified{part}", sum(v["qualified"] for r in ids for v in D["qrels"][r].values()), "data/qrels.csv")
    add("NQualifiedTestMin", min(sum(v["qualified"] for v in D["qrels"][r].values()) for r in test), "data/qrels.csv")
    add("NQualifiedTestMax", max(sum(v["qualified"] for v in D["qrels"][r].values()) for r in test), "data/qrels.csv")
    add("NPairs", n_students * len(D["reqs"]), "data/qrels.csv")
    cnt = defaultdict(int)
    for a in D["archetype"].values():
        cnt[a] += 1
    for a, n in cnt.items():
        add(f"NArch{ARCH(a)}", n, "data/students_truth.jsonl")
    add("NSkills", len(json.load(open(ROOT / "data" / "skills_taxonomy.json", encoding="utf-8"))["skills"]), "data/skills_taxonomy.json")

    # ---------------------------------------------------------------- main metrics
    rows = list(csv.DictReader(open(RES / "per_requirement_metrics.csv", encoding="utf-8")))
    per = defaultdict(lambda: defaultdict(dict))
    for r in rows:
        for k, v in r.items():
            if k not in ("method", "req_id"):
                per[r["method"]][k][r["req_id"]] = float(v)
    vec = lambda m, c: [per[m][c][r] for r in sorted(test)]
    src = "eval/results/per_requirement_metrics.csv"
    for m, name in METHOD.items():
        for c, cn in METRIC.items():
            add_ci(f"{name}{cn}", vec(m, c), src, check=(m in ("B1", "B1b", "B1c", "B2", "B3", "B3b", "B4") and c in
                                                       ("ndcg10", "mrr", "p10", "recall10", "recall10_cap", "frr10", "frr20"))
                   or (m.startswith("B4-") and c in ("ndcg10", "mrr", "recall10_cap", "frr10", "frr20")))
    add("PropFirstQualified", sum(v == 1.0 for v in vec("B4", "mrr")), src)  # requirements where rank 1 is qualified (MRR = 1)
    add("PropMrrOneTotal", len(test), src)
    for other in ("B3", "B3b", "B1c", "B1"):
        for c in ("ndcg10", "mrr", "recall10_cap", "frr20"):
            add_paired(f"PropVs{METHOD[other]}{METRIC[c]}", vec("B4", c), vec(other, c), src, check_metric=c != "frr20")
    for m in ("B4-K50", "B4-oracle", "B4-noFair"):
        add_paired(f"{METHOD[m]}VsProp" + "Ndcg", vec(m, "ndcg10"), vec("B4", "ndcg10"), src)

    # ---------------------------------------------------------------- ATS rejection
    base = json.load(open(RES / "baselines.json", encoding="utf-8"))["ats"]
    src = "eval/results/baselines.json"
    archs = ["standard", "paraphrased", "implied", "abbreviated_noisy", "sparse_strong", "ineligible_strong", "generalist_average", "stuffed_weak"]
    for m in ("B1", "B1b", "B1c"):
        f = sum(base[m][r]["qualified_failing"] for r in test)
        q = sum(base[m][r]["qualified"] for r in test)
        add(f"{METHOD[m]}RejFail", f, src)
        add(f"{METHOD[m]}RejTotal", q, src)
        add(f"{METHOD[m]}RejPct", pct(f / q).replace("%", ""), src, check=f"{f / q:.0%} ({f}/{q})")
        npass = [base[m][r]["passers"] for r in test]
        add(f"{METHOD[m]}PassMean", f"{sum(npass) / len(npass):.1f}", src, check=f"mean {sum(npass) / len(npass):.1f}")
        add(f"{METHOD[m]}PassMin", min(npass), src)
        add(f"{METHOD[m]}PassMax", max(npass), src)
        for a in archs:
            fa = sum(base[m][r]["by_archetype"].get(a, [0, 0])[0] for r in test)
            qa = sum(base[m][r]["by_archetype"].get(a, [0, 0])[1] for r in test)
            if qa:
                add(f"{METHOD[m]}Rej{ARCH(a)}Fail", fa, src)
                add(f"{METHOD[m]}Rej{ARCH(a)}Total", qa, src)
                add(f"{METHOD[m]}Rej{ARCH(a)}Pct", f"{100 * fa / qa:.0f}", src, check=f"{fa / qa:.0%} ({fa}/{qa})")

    # ---------------------------------------------------------------- pools and archetype coverage
    ret = list(csv.DictReader(open(RES / "retrieval.csv", encoding="utf-8")))
    src = "eval/results/retrieval.csv"
    for key, nm in (("parsed_top20", "PoolPropTwenty"), ("parsed_top50", "PoolPropFifty"), ("oracle_top20", "PoolOracleTwenty"),
                    ("oracle_top50", "PoolOracleFifty"), ("parser_false_rejections", "ParserFalseRej")):
        add(nm, sum(int(r[key]) for r in ret), src)
    add("PoolQualifiedTotal", sum(int(r["n_qualified"]) for r in ret), src)
    b5m = list(csv.DictReader(open(RES / "posthoc_b5_metrics.csv", encoding="utf-8")))
    add("PoolBFiveTwenty", sum(int(r["hits20"]) for r in b5m if r["split"] == "test"), "eval/results/posthoc_b5_metrics.csv")
    at = list(csv.DictReader(open(RES / "archetype_table.csv", encoding="utf-8")))
    for r in at:
        if r["method"] in METHOD:
            share = int(r["found_top20"]) / int(r["qualified"])
            add(f"Pool{METHOD[r['method']]}{ARCH(r['archetype'])}Found", r["found_top20"], "eval/results/archetype_table.csv")
            add(f"Pool{METHOD[r['method']]}{ARCH(r['archetype'])}Pct", f"{100 * share:.0f}", "eval/results/archetype_table.csv",
                check=f"{share:.0%} ({r['found_top20']}/{r['qualified']})")
    for r in csv.DictReader(open(RES / "posthoc_b5_archetype.csv", encoding="utf-8")):
        if r["method"].startswith("B5"):
            share = int(r["found_in_pool"]) / int(r["qualified"])
            add(f"PoolBFive{ARCH(r['archetype'])}Found", r["found_in_pool"], "eval/results/posthoc_b5_archetype.csv")
            add(f"PoolBFive{ARCH(r['archetype'])}Pct", f"{100 * share:.0f}", "eval/results/posthoc_b5_archetype.csv",
                check=f"{share:.0%} ({r['found_in_pool']}/{r['qualified']})")
    add("ArchParaphrasedQualified", next(int(r["qualified"]) for r in at if r["archetype"] == "paraphrased"), "eval/results/archetype_table.csv")

    # ---------------------------------------------------------------- parser accuracy
    pa = json.load(open(RES / "parser_accuracy.json", encoding="utf-8"))
    src = "eval/results/parser_accuracy.json"
    for part in ("dev", "test"):
        P = pa[part]
        for k, v in P["per_field"].items():
            add(f"Parser{part.capitalize()}{GRP(k)}", pct(v).replace("%", ""), src)
        add(f"Parser{part.capitalize()}EligPct", pct(P["overall"]).replace("%", ""), src, check=pct(P["overall"]))
        add(f"Parser{part.capitalize()}MustPrecPct", pct(P["must_precision"]).replace("%", ""), src, check=pct(P["must_precision"]))
        add(f"Parser{part.capitalize()}MustRecPct", pct(P["must_recall"]).replace("%", ""), src, check=pct(P["must_recall"]))
        ids = sorted({re.match(r"R\d+", x).group(0) for x in P["mismatches"] if "must_have:" in x})
        add(f"Parser{part.capitalize()}MismatchReqs", ", ".join(ids), src)
        add(f"Parser{part.capitalize()}MismatchCount", len(ids), src)
    add("ParserEligFieldsCorrect", sum(round(pa[p]["per_field"][k] * n) for p, n in (("dev", len(dev)), ("test", len(test)))
                                      for k in pa[p]["per_field"]), src)
    add("ParserEligFieldsTotal", 3 * (len(dev) + len(test)), src)

    # ---------------------------------------------------------------- spot check
    from sklearn.metrics import cohen_kappa_score
    sc = [r for r in csv.DictReader(open(ROOT / "data" / "spotcheck_labeled.csv", encoding="utf-8-sig")) if r["my_label"].strip()]
    gen, mine = [int(r["generated_label"]) for r in sc], [int(float(r["my_label"])) for r in sc]
    src = "data/spotcheck_labeled.csv"
    kappa = cohen_kappa_score(gen, mine, weights="quadratic", labels=[0, 1, 2, 3])
    add("SpotN", len(sc), src)
    add("SpotKappa", f"{kappa:.3f}", src, check=f"kappa = {kappa:.3f}")
    add("SpotExactPct", f"{100 * sum(a == b for a, b in zip(gen, mine)) / len(gen):.0f}", src, check=pct(sum(a == b for a, b in zip(gen, mine)) / len(gen)))
    add("SpotBinaryPct", f"{100 * sum((a >= 2) == (b >= 2) for a, b in zip(gen, mine)) / len(gen):.0f}", src,
        check=pct(sum((a >= 2) == (b >= 2) for a, b in zip(gen, mine)) / len(gen)))
    add("SpotDisagreements", sum(a != b for a, b in zip(gen, mine)), src)

    # ---------------------------------------------------------------- B5 and D1
    b5s = list(csv.DictReader(open(RES / "posthoc_b5_summary.csv", encoding="utf-8")))
    src = "eval/results/posthoc_b5_summary.csv"
    for r in b5s:
        part = "Dev" if r["split"].startswith("dev") else "Test"
        s = fmt_ci(float(r["mean"]), float(r["lo"]), float(r["hi"]))
        add(f"BFive{part}{METRIC[r['metric']]}Ci", s, src, check=s)
        add(f"BFive{part}{METRIC[r['metric']]}Mean", f"{float(r['mean']):.3f}", src)
    for r in csv.DictReader(open(RES / "posthoc_b5_paired.csv", encoding="utf-8")):
        other = {"B4": "Prop", "B3b": "Hybrid", "B1c": "AtsSyn"}[r["comparison"].split()[-1]]
        met = {"nDCG@10": "Ndcg", "MRR": "Mrr", "Recall@10 (capped)": "Rcap", "FRR@20": "Frrtwenty"}[r["metric"]]
        pre = f"BFiveVs{other}{met}"
        add(pre + "DiffCi", r["diff_ci"], "eval/results/posthoc_b5_paired.csv", check=r["diff_ci"])
        add(pre + "Wlt", r["win_loss_tie"], "eval/results/posthoc_b5_paired.csv", check=r["win_loss_tie"])
        add(pre + "Verdict", r["verdict"], "eval/results/posthoc_b5_paired.csv")
    d1s = {r["metric"]: r["value"] for r in csv.DictReader(open(RES / "posthoc_d1_summary.csv", encoding="utf-8"))}
    src = "eval/results/posthoc_d1_summary.csv"
    for k, name in (("Mean score, paraphrased-qualified (pooled)", "DOnePosScore"), ("Mean score, non-qualified (pooled)", "DOneNegScore"),
                    ("Mean score, stuffed_weak non-qualified", "DOneStuffedScore"),
                    ("ROC AUC, mean of per-requirement AUCs [95% CI over requirements]", "DOneAucCi"),
                    ("ROC AUC, all candidates pooled", "DOneAucPooled"),
                    ("Paraphrased-qualified in the top 10 of their candidate set", "DOneTopTen")):
        add(name, d1s[k], src, check=d1s[k])
    d1 = list(csv.DictReader(open(RES / "posthoc_d1.csv", encoding="utf-8")))
    add("DOneAucMin", f"{min(float(r['auc']) for r in d1):.3f}", "eval/results/posthoc_d1.csv", check=f"{min(float(r['auc']) for r in d1):.3f}")
    add("DOneAucMax", f"{max(float(r['auc']) for r in d1):.3f}", "eval/results/posthoc_d1.csv", check=f"{max(float(r['auc']) for r in d1):.3f}")
    add("DOneNPositive", sum(int(r["n_paraphrased_qualified"]) for r in d1), "eval/results/posthoc_d1.csv")
    add("DOneNNegative", sum(int(r["n_nonqualified"]) for r in d1), "eval/results/posthoc_d1.csv")

    # ---------------------------------------------------------------- fairness
    src = "eval/results/fairness_on.json / fairness_off.json"
    for cond in ("on", "off"):
        rows_f = json.load(open(RES / f"fairness_{cond}.json", encoding="utf-8"))
        s = fair.summarize(rows_f)
        C = cond.capitalize()
        add(f"Fair{C}Pairs", s["n_pairs"], src)
        add(f"Fair{C}Swaps", s["n_swaps"], src)
        for k, nm in (("abs_score_change", "AbsScore"), ("share_ge5", "ShareFive"), ("abs_rank_shift", "AbsRank"),
                      ("boundary_crossing", "Cross"), ("abs_sim_shift", "AbsSim")):
            v = s[k]
            for kind, kn in (("control", "Control"), ("cross", "CrossGroup")):
                add(f"Fair{C}{nm}{kn}Ci", fmt_ci(*v[kind]), src, check=fmt_ci(*v[kind]))
                add(f"Fair{C}{nm}{kn}Mean", f"{v[kind][0]:.3f}", src)
            d = v["cross_minus_control"]
            add(f"Fair{C}{nm}DiffCi", fmt_ci(d["diff"], d["lo"], d["hi"]), src, check=fmt_ci(d["diff"], d["lo"], d["hi"]))
            add(f"Fair{C}{nm}Verdict", d["verdict"], src)
        for g, v in s["signed_by_target_group"].items():
            add(f"Fair{C}Signed{GRP(g)}Ci", fmt_ci(*v, digits=2), src, check=fmt_ci(*v, digits=2))
        for g, v in s["signed_by_target_gender"].items():
            add(f"Fair{C}Signed{g.capitalize()}Ci", fmt_ci(*v, digits=2), src, check=fmt_ci(*v, digits=2))
        for g, v in s["signed_by_target_region"].items():
            add(f"Fair{C}SignedRegion{GRP(g)}Ci", fmt_ci(*v, digits=2), src, check=fmt_ci(*v, digits=2))
    add("FairShareFiveMinPct", f"{100 * min(float(m[1]) for m in MACROS if re.fullmatch(r'Fair(On|Off)ShareFive(Control|CrossGroup)Mean', m[0])):.0f}", src)
    add("FairShareFiveMaxPct", f"{100 * max(float(m[1]) for m in MACROS if re.fullmatch(r'Fair(On|Off)ShareFive(Control|CrossGroup)Mean', m[0])):.0f}", src)

    # ---------------------------------------------------------------- timings and calls
    b4 = json.load(open(RES / "b4_k20.json", encoding="utf-8"))
    src = "eval/results/b4_k20.json"
    lat = [x["latency"] for r in b4.values() for x in r["ranked"]]
    add("TimePerCandidate", f"{sum(lat) / len(lat):.2f}", src)
    add("TimePerCandidateMin", f"{min(r['timing']['rerank_per_candidate_s'] for r in b4.values()):.2f}", src)
    add("TimePerCandidateMax", f"{max(r['timing']['rerank_per_candidate_s'] for r in b4.values()):.2f}", src)
    add("TimeRerankPerReq", f"{sum(r['timing']['rerank_s'] for r in b4.values()) / len(b4):.0f}", src)
    add("TimeRerankPerReqMin", f"{min(r['timing']['rerank_s'] for r in b4.values()):.0f}", src)
    add("TimeRerankPerReqMax", f"{max(r['timing']['rerank_s'] for r in b4.values()):.0f}", src)
    add("TimeParse", f"{sum(r['timing']['parse_s'] for r in b4.values()) / len(b4):.1f}", src)
    add("TimePosthocWall", json.load(open(RES / "posthoc_meta.json", encoding="utf-8"))["wall_s"], "eval/results/posthoc_meta.json")
    b5 = json.load(open(RES / "posthoc_b5.json", encoding="utf-8"))
    d1j = json.load(open(RES / "posthoc_d1.json", encoding="utf-8"))
    n_post = sum(v["new_calls"] for v in b5.values()) + sum(not r["cached"] for rows_ in d1j.values() for r in rows_)
    add("CallsPosthoc", n_post, "eval/results/posthoc_b5.json + posthoc_d1.json")
    m = re.search(r"Call cache: (\d+) entries", RESULTS_MD)
    add("CallsMain", m.group(1), "docs/RESULTS.md (cache size at the end of the main evaluation)", check=m.group(1))
    cache = ROOT / ".cache" / "llm_cache.jsonl"
    add("CallsFallback", sum('"fallback": true' in l for l in open(cache, encoding="utf-8")), ".cache/llm_cache.jsonl")
    add("CallsFairnessSwaps", len(json.load(open(RES / "fairness_on.json", encoding="utf-8"))) + len(json.load(open(RES / "fairness_off.json", encoding="utf-8"))), src)

    # ---------------------------------------------------------------- write
    out = ["% Generated by eval/make_paper_numbers.py from eval/results/*. Do not edit by hand."]
    out += [f"\\newcommand{{\\{n}}}{{{tex_escape(v)}}}" for n, v, _ in MACROS]
    (ROOT / "paper" / "numbers.tex").write_text("\n".join(out) + "\n", encoding="utf-8")
    bad = [(n, s) for n, s in CHECKS if s not in RESULTS_MD]
    val = {n: v for n, v, _ in MACROS}
    rep = ["# Paper numbers report", "", f"{len(MACROS)} macros written to `paper/numbers.tex` by `eval/make_paper_numbers.py`.", "",
           f"Cross-check against `docs/RESULTS.md`: {len(CHECKS) - len(bad)} of {len(CHECKS)} checked values appear verbatim there.", ""]
    rep += ["### Discrepancies", ""] + ([f"- `\\{n}` = `{val[n]}`: string `{s}` not found in docs/RESULTS.md" for n, s in bad] or ["none"])
    rep += ["", "| macro | value | source |", "|---|---|---|"] + [f"| `\\{n}` | {v.replace('|', '/')} | {s} |" for n, v, s in MACROS]
    (ROOT / "paper" / "numbers_report.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print(f"{len(MACROS)} macros; checked {len(CHECKS)}; discrepancies {len(bad)}")
    for n, s in bad:
        print("DISCREPANCY", n, repr(s))


if __name__ == "__main__":
    main()
