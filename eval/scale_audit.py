"""Estimates the \\resizebox scale of every table float in main.tex and appendix.tex without compiling.

Heuristic: IEEEtran conference, 10 pt body (\\small 9, \\footnotesize 8, \\scriptsize 7), average glyph width 0.48 em, 6 pt
\\tabcolsep on each side of every column, \\columnwidth 252 pt, \\textwidth 516 pt. Treat results as +-10%.
    python eval/scale_audit.py
"""
import re
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "paper"
SIZE = {"normalsize": 10, "small": 9, "footnotesize": 8, "scriptsize": 7}
WIDTH = {"textwidth": 516, "columnwidth": 252}
GLYPH, TABCOLSEP = 0.48, 6


def natural_width(tex, pt):
    rows = [r for r in re.sub(r"\\(toprule|midrule|bottomrule|begin\{tabular\}\{[a-z]*\}|end\{tabular\})", "", tex).split("\\\\") if r.strip() and not r.strip().startswith("%")]
    cells = [[re.sub(r"\\[A-Za-z]+|[\\${}^]", "", c).strip() for c in r.split("&")] for r in rows]
    ncol = max(len(c) for c in cells)
    widths = [max(len(c[i]) if i < len(c) else 0 for c in cells) for i in range(ncol)]
    return sum(w * GLYPH * pt for w in widths) + ncol * 2 * TABCOLSEP, ncol


def audit():
    out = []
    for fname in ("main.tex", "appendix.tex"):
        src = (P / fname).read_text(encoding="utf-8")
        for m in re.finditer(r"\\begin\{(table\*?)\}(\[[^\]]*\])?(.*?)\\end\{\1\}", src, re.S):
            body = m.group(3)
            lab = re.search(r"\\label\{(.*?)\}", body).group(1)
            font = next((f for f in SIZE if "\\" + f in body), "normalsize")
            inp = re.search(r"\\input\{tables/(\w+)\}", body).group(1)
            rb = re.search(r"\\resizebox\{\\(\w+)\}", body)
            nat, ncol = natural_width((P / "tables" / f"{inp}.tex").read_text(encoding="utf-8"), SIZE[font])
            avail = WIDTH[rb.group(1)] if rb else (516 if m.group(1) == "table*" else 252)
            scale = min(1.0, avail / nat)
            out.append((fname, lab, m.group(1), font, "resizebox" if rb else "none", ncol, round(nat), avail, scale, round(scale * SIZE[font], 1)))
    return out


if __name__ == "__main__":
    print("file | label | env | font | resize | cols | natural pt | available pt | scale | effective font pt")
    for r in audit():
        flag = "  <-- below 80%" if r[8] < 0.8 else ""
        fits = "  (overflows, no resizebox!)" if r[4] == "none" and r[6] > r[7] else ""
        print(f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} | {r[7]} | {r[8]:.0%} | {r[9]}{flag}{fits}")
