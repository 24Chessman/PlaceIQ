"""Validate the synthetic dataset and print summary tables.   python scripts/validate_data.py

Exit code 1 if any check fails.
"""
import csv
import json
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

import gen_data as g  # shares taxonomy, term matching and the labelling function with the generator
from scipy.stats import chi2_contingency

DATA = g.DATA
FAILS = []


def check(ok, msg):
    print(("PASS  " if ok else "FAIL  ") + msg)
    if not ok:
        FAILS.append(msg)


def jl(name):
    return [json.loads(line) for line in (DATA / name).read_text(encoding="utf-8").splitlines()]


def find_terms(text, names):
    return [t for n in names for t in g.skill_terms(n) if g.term_pattern(t).search(text)]


def strip_terms(text, names):
    terms = sorted({t for n in names for t in g.skill_terms(n)}, key=len, reverse=True)
    for t in terms:
        text = g.term_pattern(t).sub(" ", text)
    return text


def main():
    # ---------------------------------------------------------------- taxonomy
    skills = g.TAX["skills"]
    names = [s["name"] for s in skills]
    check(len(names) == len(set(names)) and 60 <= len(names) <= 80, f"taxonomy has {len(names)} unique skills")
    check(all(6 <= len(s["evidence"]) <= 10 for s in skills), "every skill has 6-10 evidence sentences")
    check(all(grp_skill in g.SK for s in skills for grp in s["implied_by"] for grp_skill in grp),
          "implied_by references only known skills")
    check({s["family"] for s in skills} == set(g.FAMILIES), "all 12 role families present")
    bad = [(s["name"], t) for s in skills for e in s["evidence"] for t in find_terms(e, names)]
    check(not bad, f"no evidence sentence contains any skill name/alias ({bad[:3]})")

    # ---------------------------------------------------------------- students
    students, truths = jl("students.jsonl"), jl("students_truth.jsonl")
    tr = {t["id"]: t for t in truths}
    check(len(students) == g.N_STUDENTS and [s["id"] for s in students] == [f"S{i:03d}" for i in range(1, g.N_STUDENTS + 1)], f"{g.N_STUDENTS} students S001..S{g.N_STUDENTS}")
    check(all("archetype" not in s and "levels" not in s for s in students), "hidden profile is not inside students.jsonl")
    check(Counter(t["archetype"] for t in truths) == Counter(g.ARCH_COUNTS), "archetype counts match the design")
    fam = Counter(t["family"] for t in truths)
    check(all(fam[f] >= g.MIN_QUOTA for f in g.FAMILIES), f"every role family has >= {g.MIN_QUOTA} students ({dict(fam)})")

    name_bad, edu_bad, wc_bad, para_bad, hid_bad, surf_bad, inel_bad = [], [], [], [], [], [], []
    for s in students:
        t, text = tr[s["id"]], s["resume_text"]
        lines = text.split("\n")
        # name only in the header line (full name and each name part)
        first, last = s["name"].split()
        if text.count(s["name"]) != 1 or s["name"] not in lines[0] or any(
                re.search(rf"\b{p}\b", "\n".join(lines[1:])) for p in (first, last)):
            name_bad.append(s["id"])
        # education line matches structured fields
        cl = [ln for ln in lines if "cgpa" in ln.lower()]
        ok = len(cl) == 1
        if ok:
            ln = cl[0]
            m = re.search(r"\b(\d{1,2}\.\d{2})\b", ln)
            ok &= bool(m) and m.group(1) == f"{s['cgpa']:.2f}"
            ok &= str(s["grad_year"]) in ln
            variants = g.BRANCH_NAMES[s["branch"]]
            ok &= any(re.search(rf"(?<!\w){re.escape(v)}(?!\w)", ln) for v in variants)
            if re.search(r"no active backlog", ln, re.I):
                n = 0
            elif (mm := re.search(r"active backlogs?: (\d+)", ln, re.I)) or (mm := re.search(r"(\d+) active backlog", ln, re.I)):
                n = int(mm.group(1))
            else:
                n = None
            ok &= n == s["active_backlogs"]
        if not ok:
            edu_bad.append(s["id"])
        if not 80 <= len(text.split()) <= 400:
            wc_bad.append((s["id"], len(text.split())))
        # archetype-specific text rules
        if t["archetype"] == "paraphrased" and find_terms(text, names):
            para_bad.append((s["id"], find_terms(text, names)[:3]))
        if t["archetype"] == "implied":
            hidden = [k for k in t["effective_levels"] if k not in t["levels"]]
            if not hidden or find_terms(strip_terms(text, list(t["levels"])), hidden):
                hid_bad.append(s["id"])
        shown = list(t["levels"]) + t.get("claimed_skills", [])
        if t["archetype"] != "stuffed_weak" or t.get("claimed_skills"):
            miss = [k for k in shown if not any(x in text for x in t["surfaces"].get(k, []))]
            if miss:
                surf_bad.append((s["id"], miss[:3]))
        if t["archetype"] == "ineligible_strong" and not (s["cgpa"] < 6.5 or s["active_backlogs"] > 0):
            inel_bad.append(s["id"])
        if t["archetype"] == "stuffed_weak" and any(v > 1 for v in t["effective_levels"].values()):
            inel_bad.append(s["id"])
    check(not name_bad, f"name appears only in the header line ({name_bad[:5]})")
    check(not edu_bad, f"education line matches cgpa/branch/backlogs/grad_year ({edu_bad[:5]})")
    check(not wc_bad, f"resumes are 80-400 words ({wc_bad[:5]})")
    check(not para_bad, f"paraphrased resumes contain no canonical skill name or alias ({para_bad[:3]})")
    check(not hid_bad, f"implied resumes never name their hidden skills ({hid_bad[:5]})")
    check(not surf_bad, f"every true skill is visible in the text ({surf_bad[:3]})")
    check(not inel_bad, f"ineligible_strong fail a typical rule, stuffed_weak true levels <= 1 ({inel_bad[:5]})")
    check(len({s["name"] for s in students}) == g.N_STUDENTS, "names are unique")

    # archetype shares vs name group
    groups = sorted({t["name_group"] for t in truths})
    table = [[sum(1 for t in truths if t["archetype"] == a and t["name_group"] == gr) for gr in groups] for a in g.ARCH_COUNTS]
    p = chi2_contingency(table)[1]
    check(p > 0.05, f"archetype shares independent of name group (chi-square p={p:.3f})")
    sizes = Counter(t["name_group"] for t in truths)
    print("      name groups:", dict(sizes))
    cg = {gr: st.mean(s["cgpa"] for s in students if tr[s["id"]]["name_group"] == gr) for gr in groups}
    print("      mean CGPA by name group:", {k: round(v, 2) for k, v in cg.items()})
    check(max(cg.values()) - min(cg.values()) < 0.35, "mean CGPA similar across name groups")

    # ---------------------------------------------------------------- requirements
    reqs, rt = jl("requirements.jsonl"), json.loads((DATA / "requirements_truth.json").read_text(encoding="utf-8"))
    check(len(reqs) == 15 and Counter(r["split"] for r in reqs) == {"dev": 5, "test": 10}, "15 requirements, 5 dev / 10 test")
    check(len({v["role_family"] for v in rt.values()}) >= 10, f"{len({v['role_family'] for v in rt.values()})} role families covered")
    for r in reqs:
        v = rt[r["id"]]
        missing = [f"{k}:{m}" for k, m in v["text_markers"].items() if m not in r["text"]]
        miss_sk = [k for k in v["must_have"] + v["nice_to_have"] if not find_terms(r["text"], [k])]
        check(not missing and not miss_sk, f"{r['id']} text contains its eligibility rules and all skills ({missing or ''}{miss_sk or ''})")
    for r in reqs:  # eligibility fields carry numbers only when the text has them
        v = rt[r["id"]]
        if v["min_cgpa"] is not None:
            check(re.search(re.escape(f"{v['min_cgpa']:g}"), r["text"]) is not None, f"{r['id']} states cutoff {v['min_cgpa']:g}")

    # ---------------------------------------------------------------- qrels
    qrels = list(csv.DictReader(open(DATA / "qrels.csv", encoding="utf-8")))
    check(len(qrels) == g.N_STUDENTS * 15, "qrels covers every (requirement, student) pair")
    sm = {s["id"]: s for s in students}
    mism = 0
    for row in qrels:
        r = next(x for x in g.REQS if x["id"] == row["req_id"])
        el, rel, extra = g.relevance(r, sm[row["student_id"]], tr[row["student_id"]]["effective_levels"])
        mism += (int(row["eligible"]), int(row["relevance"]), float(row["extra_credit"])) != (int(el), rel, extra)
        mism += int(row["qualified"]) != int(rel >= 2)
    check(mism == 0, "qrels.csv equals the labelling function applied to hidden truth")
    stats = {}
    for r in reqs:
        rows = [x for x in qrels if x["req_id"] == r["id"]]
        q = [x for x in rows if x["qualified"] == "1"]
        h = [x for x in q if tr[x["student_id"]]["archetype"] in g.HARD]
        stats[r["id"]] = (sum(int(x["eligible"]) for x in rows), len(q), len(h))
        check(g.Q_RANGE[0] <= len(q) <= g.Q_RANGE[1], f"{r['id']} qualified={len(q)} within {g.Q_RANGE[0]}..{g.Q_RANGE[1]}")
        check(len(h) >= g.HARD_SHARE * len(q), f"{r['id']} hard-archetype share {len(h)}/{len(q)} >= 40%")
    sc = list(csv.DictReader(open(DATA / "spotcheck.csv", encoding="utf-8-sig")))
    check(len(sc) == 20 and Counter(x["generated_label"] for x in sc) == {"0": 5, "1": 5, "2": 5, "3": 5} and all(x["my_label"] == "" for x in sc),
          "spotcheck.csv: 20 pairs, 5 per relevance level, empty my_label")

    # ---------------------------------------------------------------- stats
    print("\nArchetype counts:", dict(Counter(t["archetype"] for t in truths)))
    print("Branch counts:   ", dict(Counter(s["branch"] for s in students)))
    cgs = [s["cgpa"] for s in students]
    print(f"CGPA mean {st.mean(cgs):.2f} std {st.pstdev(cgs):.2f} min {min(cgs)} max {max(cgs)}; "
          f"backlogs>0: {sum(s['active_backlogs'] > 0 for s in students)}")
    print("Relevance distribution:", dict(sorted(Counter(int(x["relevance"]) for x in qrels).items())))
    print("\nreq   family            eligible  qualified  qualified_hard  hard%")
    for r in reqs:
        e, q, h = stats[r["id"]]
        print(f"{r['id']}   {rt[r['id']]['role_family']:<17} {e:8d} {q:10d} {h:15d} {h / max(1, q):6.0%}")
    print("\nFAILED CHECKS:", len(FAILS))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
