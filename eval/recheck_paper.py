"""Builds paper/MACROS.md and paper/recheck_report.md and independently rechecks every macro used by paper/OUTLINE.md.

The recheck deliberately does NOT import eval/make_paper_numbers.py, eval/stats.py or eval/metrics.py: it re-reads the
results files with its own code (own bootstrap, own kappa, own AUC, own ATS regex on the raw resumes).
    python eval/recheck_paper.py
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
P, RES, DATA = ROOT / "paper", ROOT / "eval" / "results", ROOT / "data"


# ---------------------------------------------------------------- tiny independent toolbox
def boot(v, n=10000):
    v = np.asarray(v, float)
    r = np.random.default_rng(42)
    means = v[r.integers(0, len(v), size=(n, len(v)))].mean(axis=1)
    return v.mean(), np.percentile(means, 2.5), np.percentile(means, 97.5)


def ci(v, d=3):
    m, lo, hi = boot(v)
    return f"{m:.{d}f} [{lo:.{d}f}, {hi:.{d}f}]"


def pair(a, b):
    d = np.asarray(a, float) - np.asarray(b, float)
    m, lo, hi = boot(d)
    w, l = int((d > 1e-9).sum()), int((d < -1e-9).sum())
    return f"{m:.3f} [{lo:.3f}, {hi:.3f}]", f"{w}/{l}/{len(d) - w - l}", "not distinguishable" if lo <= 0 <= hi else ("better" if m > 0 else "worse")


def auc(y, s):
    y, s = np.asarray(y), np.asarray(s, float)
    pos, neg = s[y == 1], s[y == 0]
    return float(np.mean([(p > q) + 0.5 * (p == q) for p in pos for q in neg]))


def qwk(a, b, k=4):
    O = np.zeros((k, k))
    for x, y in zip(a, b):
        O[x, y] += 1
    W = np.array([[(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)])
    E = np.outer(O.sum(1), O.sum(0)) / O.sum()
    return 1 - (W * O).sum() / (W * E).sum()


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")]


# ---------------------------------------------------------------- load
numbers = {m.group(1): m.group(2) for m in re.finditer(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}$", (P / "numbers.tex").read_text(encoding="utf-8"), re.M)}
render = lambda v: v.replace("\\%", "%").replace("\\_", "_").replace("\\&", "&").replace("\\#", "#")
outline = (P / "OUTLINE.md").read_text(encoding="utf-8")
main_tex = (P / "main.tex").read_text(encoding="utf-8")

students, truth, reqs = jl(DATA / "students.jsonl"), {t["id"]: t for t in jl(DATA / "students_truth.jsonl")}, jl(DATA / "requirements.jsonl")
split = {r["id"]: r["split"] for r in reqs}
test = sorted(r for r, s in split.items() if s == "test")
dev = sorted(r for r, s in split.items() if s == "dev")
qrels = defaultdict(dict)
for r in csv.DictReader(open(DATA / "qrels.csv", encoding="utf-8")):
    qrels[r["req_id"]][r["student_id"]] = (int(r["eligible"]), int(r["relevance"]), int(r["qualified"]))
pr = defaultdict(lambda: defaultdict(dict))
for r in csv.DictReader(open(RES / "per_requirement_metrics.csv", encoding="utf-8")):
    for k, v in r.items():
        if k not in ("method", "req_id"):
            pr[r["method"]][k][r["req_id"]] = float(v)
vec = lambda m, k: [pr[m][k][r] for r in test]
b5 = {(r["split"], r["req_id"]): r for r in csv.DictReader(open(RES / "posthoc_b5_metrics.csv", encoding="utf-8"))}
b5vec = lambda k: [float(b5[("test", r)][k]) for r in test]
parsed = {k: v["parsed"] for k, v in json.load(open(RES / "parsed_all.json", encoding="utf-8")).items()}
rtruth = json.load(open(DATA / "requirements_truth.json", encoding="utf-8"))
tax = json.load(open(DATA / "skills_taxonomy.json", encoding="utf-8"))["skills"]
text = {s["id"]: s["resume_text"] for s in students}
b4 = json.load(open(RES / "b4_k20.json", encoding="utf-8"))
fair = {c: json.load(open(RES / f"fairness_{c}.json", encoding="utf-8")) for c in ("on", "off")}
d1 = json.load(open(RES / "posthoc_d1.json", encoding="utf-8"))


def strict_rejection(syn):
    fail = tot = 0
    for rid in test:
        must = parsed[rid]["must_have_skills"]
        for sid, (el, rel, q) in qrels[rid].items():
            if not q:
                continue
            tot += 1
            ok = True
            for sk in must:
                terms = [sk]
                if syn:
                    for t in tax:
                        names = [t["name"]] + t["aliases"]
                        if sk.strip().lower() in [n.lower() for n in names]:
                            terms = names
                            break
                ok &= any(re.search(r"(?<!\w)" + re.escape(t.strip()) + r"(?!\w)", text[sid], re.I) for t in terms)
            fail += not ok
    return fail, tot


def fair_stats(cond):
    pairs = defaultdict(lambda: {"c": [], "x": []})
    for r in fair[cond]:
        pairs[(r["rid"], r["sid"])]["c" if r["variant"] == "control" else "x"].append(r)
    out = {}
    for name, fn in (("abs", lambda r: abs(r["delta"])), ("ge5", lambda r: float(abs(r["delta"]) >= 5)), ("sim", lambda r: abs(r["sim_delta"]))):
        out[name] = {k: [np.mean([fn(r) for r in v[k]]) for v in pairs.values()] for k in ("c", "x")}
    return out, len(pairs)


# ---------------------------------------------------------------- independent values
exp = {}
exp["NStudents"] = str(len(students))
exp["NRequirements"] = str(len(reqs))
exp["NDev"], exp["NTest"] = str(len(dev)), str(len(test))
exp["NSkills"] = str(len(tax))
for a in ("Standard", "Paraphrased"):
    exp[f"NArch{a}"] = str(sum(t["archetype"] == a.lower() for t in truth.values()))
qt = [sum(v[2] for v in qrels[r].values()) for r in test]
exp["NQualifiedTest"], exp["NQualifiedTestMin"], exp["NQualifiedTestMax"] = str(sum(qt)), str(min(qt)), str(max(qt))
f, t = strict_rejection(False)
exp["AtsStrictRejFail"], exp["AtsStrictRejTotal"], exp["AtsStrictRejPct"] = str(f), str(t), f"{100 * f / t:.0f}"
f, t = strict_rejection(True)
exp["AtsSynRejPct"] = f"{100 * f / t:.0f}"
exp["PropNdcgCi"], exp["DenseNdcgCi"] = ci(vec("B4", "ndcg10")), ci(vec("B3", "ndcg10"))
exp["PropFrrtwentyCi"] = ci(vec("B4", "frr20"))
for key, other in (("Dense", "B3"), ("AtsStrict", "B1"), ("AtsSyn", "B1c"), ("Hybrid", "B3b")):
    d, w, v = pair(vec("B4", "ndcg10"), vec(other, "ndcg10"))
    exp[f"PropVs{key}NdcgDiffCi"], exp[f"PropVs{key}NdcgWlt"], exp[f"PropVs{key}NdcgVerdict"] = d, w, v
exp["PropFirstQualified"] = str(sum(v == 1.0 for v in vec("B4", "mrr")))
exp["PoolPropTwenty"] = str(int(sum(vec("B4", "hits20"))))
exp["PoolBFiveTwenty"] = str(int(sum(b5vec("hits20"))))
exp["PoolQualifiedTotal"] = str(sum(qt))
exp["BFiveVsPropFrrtwentyDiffCi"] = pair(b5vec("frr20"), vec("B4", "frr20"))[0]
exp["BFiveVsPropNdcgDiffCi"] = pair(b5vec("ndcg10"), vec("B4", "ndcg10"))[0]
exp["BFiveVsHybridNdcgDiffCi"] = pair(b5vec("ndcg10"), vec("B3b", "ndcg10"))[0]
# parser (own comparison of parsed vs truth)
ok = 0
for rid in dev + test:
    p, tr = parsed[rid], rtruth[rid]
    ok += (p["min_cgpa"] == tr["min_cgpa"]) + (p["max_backlogs"] == tr["max_backlogs"]) + (set(p["allowed_branches"]) == set(tr["allowed_branches"] or []))
exp["ParserEligFieldsCorrect"], exp["ParserEligFieldsTotal"] = str(ok), str(3 * (len(dev) + len(test)))
pa = json.load(open(RES / "parser_accuracy.json", encoding="utf-8"))
for part in ("dev", "test"):
    exp[f"Parser{part.capitalize()}MismatchReqs"] = ", ".join(sorted({x.split()[0] for x in pa[part]["mismatches"] if "must_have:" in x}))
exp["ParserFalseRej"] = str(sum(int(r["parser_false_rejections"]) for r in csv.DictReader(open(RES / "retrieval.csv", encoding="utf-8"))))
# spot check
sc = [r for r in csv.DictReader(open(DATA / "spotcheck_labeled.csv", encoding="utf-8-sig")) if r["my_label"].strip()]
g, m = [int(r["generated_label"]) for r in sc], [int(float(r["my_label"])) for r in sc]
exp["SpotN"], exp["SpotKappa"] = str(len(sc)), f"{qwk(g, m):.3f}"
exp["SpotExactPct"] = f"{100 * np.mean([a == b for a, b in zip(g, m)]):.0f}"
exp["SpotBinaryPct"] = f"{100 * np.mean([(a >= 2) == (b >= 2) for a, b in zip(g, m)]):.0f}"
# timing and calls
lat = [x["latency"] for r in b4.values() for x in r["ranked"]]
exp["TimePerCandidate"] = f"{np.mean(lat):.2f}"
exp["TimeRerankPerReq"] = f"{np.mean([sum(x['latency'] for x in r['ranked']) for r in b4.values()]):.0f}"
exp["CallsFallback"] = str(sum(json.loads(l).get("fallback", False) for l in open(ROOT / ".cache" / "llm_cache.jsonl", encoding="utf-8")))
# D1
pos = [x["score"] for rows in d1.values() for x in rows if x["qualified"]]
neg = [x["score"] for rows in d1.values() for x in rows if not x["qualified"]]
exp["DOnePosScore"], exp["DOneNegScore"] = f"{np.mean(pos):.1f}", f"{np.mean(neg):.1f}"
exp["DOneAucCi"] = ci([auc([x["qualified"] for x in d1[r]], [x["score"] for x in d1[r]]) for r in sorted(d1)])
# fairness
for c, C in (("on", "On"), ("off", "Off")):
    fs, n = fair_stats(c)
    exp[f"Fair{C}Pairs"] = str(n)
    exp[f"Fair{C}AbsScoreControlCi"], exp[f"Fair{C}AbsScoreCrossGroupCi"] = ci(fs["abs"]["c"]), ci(fs["abs"]["x"])
    if c == "on":
        exp["FairOnAbsSimControlCi"] = ci(fs["sim"]["c"])
shares = [np.mean(fair_stats(c)[0]["ge5"][k]) for c in ("on", "off") for k in ("c", "x")]
exp["FairShareFiveMinPct"], exp["FairShareFiveMaxPct"] = f"{100 * min(shares):.0f}", f"{100 * max(shares):.0f}"

# ---------------------------------------------------------------- outline macros, grouped by section
sections, cur = [], None
for line in outline.splitlines():
    if line.startswith("## "):
        cur = [line[3:], []]
        sections.append(cur)
    elif cur and "CLAIM RULES" not in cur[0]:
        for blk in re.findall(r"`([^`]*)`", line):
            for mac in re.findall(r"\\([A-Z][A-Za-z]+)", blk):
                if mac in numbers and mac not in cur[1]:
                    cur[1].append(mac)
used = [m for _, ms in sections for m in ms]
macros_md = ["# Macro sheet", "", "Every macro referenced by `paper/OUTLINE.md`, as it renders (values come from `paper/numbers.tex`).", ""]
for title, ms in sections:
    if ms:
        macros_md += [f"## {title}", ""] + [f"- `\\{m}` = {render(numbers[m])}" for m in ms] + [""]

# tables and figures
macros_md += ["## Tables in paper/tables", "", "| file | label | env | columns | caption in main.tex |", "|---|---|---|---|---|"]
for tf in sorted((P / "tables").glob("*.tex")):
    body = tf.read_text(encoding="utf-8")
    hdr = re.search(r"\\toprule\s*\n(.*?)\\\\", body, re.S)
    cols = [c.strip() for c in hdr.group(1).split("&")] if hdr else []
    m = re.search(r"\\begin\{(table\*?)\}.*?\\caption\{(.*?)\}\s*\\label\{(.*?)\}.*?\\input\{tables/" + tf.stem + r"\}", main_tex, re.S)
    if m:
        env, cap, lab = m.group(1), m.group(2), m.group(3)
        # the regex may start at an earlier float; take the last begin before the input
        seg = main_tex[:main_tex.index("tables/" + tf.stem + "}")]
        env = re.findall(r"\\begin\{(table\*?)\}", seg)[-1]
        cap = re.findall(r"\\caption\{(.*?)\}\s*\n", seg)[-1]
        lab = re.findall(r"\\label\{(.*?)\}", seg)[-1]
    else:
        env, cap, lab = "(not placed)", "none", "none"
    macros_md.append(f"| {tf.name} | {lab} | {env} | {'; '.join(cols).replace('|', '/')} | {cap} |")
axes = {"fig_ndcg10": "x: method (B1..B4); y: nDCG@10 mean with 95% CI error bars",
        "fig_archetype": "x: resume archetype; y: share of qualified students in the top-20; grouped bars by method",
        "fig_fairness": "x: instruction ON/OFF x control/cross-group; y: mean absolute score change (points), 95% CI"}
macros_md += ["", "## Figures in paper/figs", "", "| file | label | axes | caption in main.tex |", "|---|---|---|---|"]
for ff in sorted((P / "figs").glob("*.pdf")):
    tail = main_tex[main_tex.index(f"figs/{ff.name}"):]
    cap = re.search(r"\\caption\{(.*?)\}\s*\n", tail).group(1)
    lab = re.search(r"\\label\{(.*?)\}", tail).group(1)
    macros_md.append(f"| {ff.name} (+ .png) | {lab} | {axes[ff.stem]} | {cap} |")
(P / "MACROS.md").write_text("\n".join(macros_md) + "\n", encoding="utf-8")

# ---------------------------------------------------------------- compare
rows, bad, missing = [], [], []
for mac in used:
    if mac not in exp:
        missing.append(mac)
        continue
    got, want = render(numbers[mac]), exp[mac]
    rows.append((mac, got, want, got == want))
    if got != want:
        bad.append((mac, got, want))
rep = [f"# Independent recheck", "", f"{len(used)} macros are used by OUTLINE.md; {len(rows)} rechecked with separate code, "
       f"{sum(r[3] for r in rows)} match, {len(bad)} mismatch, {len(missing)} without an independent path.", ""]
rep += ["## Mismatches", ""] + ([f"- `\\{m}`: paper value `{g_}` vs recheck `{w}`" for m, g_, w in bad] or ["none"])
rep += ["", "## No independent recheck available", ""] + ([f"- `\\{m}` = {render(numbers[m])}" for m in missing] or ["none"])
rep += ["", "## Matches", ""] + [f"- `\\{m}` = {g_}" for m, g_, w, ok_ in rows if ok_]
(P / "recheck_report.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
print("\n".join(rep[:3]))
print("MISMATCH:", bad)
print("NO RECHECK PATH:", missing)
