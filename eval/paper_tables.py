"""Regenerates the paper tables/figure that changed in 'paper: PlaceIQ, table fixes, batch 1' from the existing results.
No new computation of results: it only re-reads eval/results/* and re-formats. Original results files are never written.

  paper/tables/main_results.tex, ats_rejection.tex, parser_accuracy.tex, posthoc_b5_paired.tex
  paper/figs/fig_archetype.pdf/.png
  paper/corrected/posthoc_b5_paired_corrected.csv  (the original CSV keeps the inverted FRR labels; see the erratum)
"""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metrics import ROOT  # noqa: E402
from stats import boot_ci, fmt_ci  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RES, PAPER = ROOT / "eval" / "results", ROOT / "paper"
NAMES = {"B1": "B1 ATS strict", "B1b": "B1b ATS lenient", "B1c": "B1c ATS + synonyms", "B2": "B2 BM25", "B3": "B3 Dense only",
         "B3b": "B3b Hybrid (RRF)", "B4": "B4 Proposed (K=20)"}
ESC = str.maketrans({"%": "\\%", "_": "\\_", "&": "\\&", "#": "\\#"})
esc = lambda s: str(s).translate(ESC)


def write_tex(name, header, rows, colfmt, head_comment=""):
    lines = ([head_comment] if head_comment else []) + ["\\begin{tabular}{" + colfmt + "}", "\\toprule",
                                                         " & ".join(header) + " \\\\", "\\midrule"]
    lines += [" & ".join(esc(c) for c in r) + " \\\\" for r in rows]
    lines += ["\\bottomrule", "\\end{tabular}"]
    (PAPER / "tables" / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def per_requirement():
    per = defaultdict(lambda: defaultdict(dict))
    for r in csv.DictReader(open(RES / "per_requirement_metrics.csv", encoding="utf-8")):
        for k, v in r.items():
            if k not in ("method", "req_id"):
                per[r["method"]][k][r["req_id"]] = float(v)
    return per


def main_results():
    per = per_requirement()
    cols = [("ndcg10", "nDCG@10"), ("mrr", "MRR"), ("recall10_cap", "Recall@10$^{cap}$"), ("frr10", "FRR@10"), ("frr20", "FRR@20")]
    rows = [[NAMES[m]] + [fmt_ci(*boot_ci(list(per[m][c].values()))) for c, _ in cols] for m in NAMES]
    # P@10 is dropped: it equals capped Recall@10 whenever every requirement has >= 10 qualified students
    for m in NAMES:
        assert all(abs(per[m]["p10"][r] - per[m]["recall10_cap"][r]) < 1e-12 for r in per[m]["p10"])
    write_tex("main_results.tex", ["Method"] + [h for _, h in cols], rows, "lccccc")


def ablations():
    """Means only: four columns must fit one column of the page without \resizebox, so the CIs are left to the text/RESULTS.md."""
    per = per_requirement()
    variants = {"B4": "B4 main (K=20)", "B4-K50": "K=50", "B4-oracle": "Oracle filters", "B4-noFair": "No fairness instr."}
    mean = lambda m, c: sum(per[m][c].values()) / len(per[m][c])
    assert all(abs(mean(m, "mrr") - 1.0) < 1e-12 for m in variants if m != "B4-noFair") and abs(mean("B4-noFair", "mrr") - 0.95) < 1e-12
    for m in variants:
        assert all(abs(per[m]["frr10"][r] - (1 - per[m]["recall10_cap"][r])) < 1e-12 for r in per[m]["frr10"])
    rows = [[v, f"{mean(m, 'ndcg10'):.3f}", f"{mean(m, 'recall10_cap'):.3f}", f"{mean(m, 'frr20'):.3f}"] for m, v in variants.items()]
    write_tex("ablations.tex", ["Variant", "nDCG@10", "Recall@10 (capped)", "FRR@20"], rows, "lccc")


def ats_rejection():
    base = json.load(open(RES / "baselines.json", encoding="utf-8"))["ats"]
    ids = sorted(base["B1"])
    keep = ["standard", "paraphrased", "implied", "abbreviated_noisy", "sparse_strong"]
    other = ["generalist_average", "ineligible_strong", "stuffed_weak"]
    names = {"B1": "B1 ATS strict", "B1b": "B1b ATS lenient (>=50\\%)", "B1c": "B1c ATS + synonyms"}
    rows = []
    for m in ("B1", "B1b", "B1c"):
        def cell(archs):
            f = sum(base[m][r]["by_archetype"].get(a, [0, 0])[0] for r in ids for a in archs)
            q = sum(base[m][r]["by_archetype"].get(a, [0, 0])[1] for r in ids for a in archs)
            return f"{f / q:.0%} ({f}/{q})"
        tot_f = sum(base[m][r]["qualified_failing"] for r in ids)
        tot_q = sum(base[m][r]["qualified"] for r in ids)
        npass = [base[m][r]["passers"] for r in ids]
        rows.append([names[m].replace("\\%", "%"), f"{tot_f / tot_q:.0%} ({tot_f}/{tot_q})"] + [cell([a]) for a in keep] + [cell(other)]
                    + [f"{min(npass)}-{max(npass)} (mean {sum(npass) / len(npass):.1f})"])
    write_tex("ats_rejection.tex", ["Method", "Overall", "standard", "paraphrased", "implied", "abbrev.\\ noisy", "sparse strong",
                                    "other (n)", "Passers/req."], rows, "lcccccccc")


def parser_accuracy():
    pa = json.load(open(RES / "parser_accuracy.json", encoding="utf-8"))
    rows = [[part] + [f"{v['per_field'][k]:.0%}" for k in ("min_cgpa", "max_backlogs", "allowed_branches")] +
            [f"{v['overall']:.0%}", f"{v['must_precision']:.0%}", f"{v['must_recall']:.0%}"] for part, v in pa.items()]
    write_tex("parser_accuracy.tex", ["Split", "min\\_cgpa", "max\\_backlogs", "branches", "Elig.", "Must P", "Must R"], rows, "lcccccc")


def fixed_paired_rows():
    """Corrected rows of eval/results/posthoc_b5_paired.csv: FRR is lower-is-better, so wins and losses are swapped and the
    verdict word is recomputed from the CI. MRR rows are dropped for the paper table (kept in the corrected CSV)."""
    out = []
    for r in csv.DictReader(open(RES / "posthoc_b5_paired.csv", encoding="utf-8")):
        w, l, t = r["win_loss_tie"].split("/")
        lo, hi = (float(x) for x in re.findall(r"-?\d+\.\d+", r["diff_ci"])[1:3])
        wlt, verdict = r["win_loss_tie"], r["verdict"]
        if r["metric"].startswith("FRR"):
            wlt = f"{l}/{w}/{t}"
            verdict = "not distinguishable" if lo <= 0 <= hi else ("better" if hi < 0 else "worse")
        out.append(dict(comparison=r["comparison"], metric=r["metric"], diff_ci=r["diff_ci"], win_loss_tie=wlt, verdict=verdict,
                        original_win_loss_tie=r["win_loss_tie"], original_verdict=r["verdict"]))
    return out


def posthoc_b5_paired():
    rows = fixed_paired_rows()
    (PAPER / "corrected").mkdir(exist_ok=True)
    with open(PAPER / "corrected" / "posthoc_b5_paired_corrected.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    short = {"Recall@10 (capped)": "Recall@10$^{cap}$"}  # same label as the main table; keeps the column narrow
    shown = [[r["comparison"], short.get(r["metric"], r["metric"]), r["diff_ci"], r["win_loss_tie"], r["verdict"]] for r in rows if r["metric"] != "MRR"]
    write_tex("posthoc_b5_paired.tex", ["Comparison", "Metric", "Mean diff [CI]", "W/L/T (B5)", "Verdict"], shown, "llccc",
              "% POST-HOC EXPLORATORY (designed after seeing the test results). FRR rows: lower is better.")


def fig_archetype():
    rows = list(csv.DictReader(open(RES / "archetype_table.csv", encoding="utf-8")))
    groups = ["standard", "paraphrased", "implied", "abbreviated_noisy", "sparse_strong", "other"]
    merge = {"generalist_average": "other", "ineligible_strong": "other", "stuffed_weak": "other"}
    found, qual = defaultdict(int), {}
    for r in rows:
        g = merge.get(r["archetype"], r["archetype"])
        found[(r["method"], g)] += int(r["found_top20"])
    for r in rows:
        if r["method"] == "B1":
            g = merge.get(r["archetype"], r["archetype"])
            qual[g] = qual.get(g, 0) + int(r["qualified"])
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    w = 0.8 / len(NAMES)
    palette = ["#c3c8de", "#9aa3c0", "#6c74a8", "#b9a46b", "#d99a1d", "#7c2d92", "#3730a3"]
    for i, m in enumerate(NAMES):
        ax.bar([j + i * w for j in range(len(groups))], [found[(m, g)] / qual[g] for g in groups], w, label=NAMES[m], color=palette[i])
    ax.set_xticks([j + 0.4 - w / 2 for j in range(len(groups))])
    ax.set_xticklabels([f"{g.replace('_', ' ')}\n(n={qual[g]})" for g in groups], fontsize=8)
    ax.set_ylabel("share of qualified students in the top 20")
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=4, fontsize=7, frameon=False)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(PAPER / "figs" / f"fig_archetype.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main_results()
    ablations()
    ats_rejection()
    parser_accuracy()
    posthoc_b5_paired()
    fig_archetype()
    print("tables and figure written")
