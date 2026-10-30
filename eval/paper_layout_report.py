"""Prints the section/float order of paper/main.tex (appendix expanded), checks that nothing follows the bibliography, and writes
docs/hashes_paper.txt after comparing eval/results with docs/hashes_before.txt.   python eval/paper_layout_report.py"""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
main = (ROOT / "paper" / "main.tex").read_text(encoding="utf-8")
src = main.replace("\\input{appendix}", (ROOT / "paper" / "appendix.tex").read_text(encoding="utf-8"))
pat = r"\\section\{(.*?)\}|\\begin\{(table\*?|figure)\}(\[[^\]]*\]).*?\\label\{(.*?)\}|\\FloatBarrier|\\bibliography\{|\\appendices"
print("section / float order:")
for m in re.finditer(pat, src, re.S):
    if m.group(1):
        print("  SECTION", m.group(1))
    elif m.group(2):
        print("      ", m.group(2), m.group(3), m.group(4))
    else:
        print("     ", m.group(0))
tail = src[src.index("\\bibliographystyle"):].split()
print("tail of main.tex:", tail)
assert tail == ["\\bibliographystyle{IEEEtran}", "\\bibliography{refs}", "\\end{document}"], "nothing may follow the bibliography"


def h(d):
    return {p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / d).rglob("*")) if p.is_file()}


def rel(d):
    return {k.replace(ROOT.as_posix() + "/", ""): v for k, v in h(d).items()}


before = {l.split("  ")[1]: l.split("  ")[0] for l in (ROOT / "docs" / "hashes_before.txt").read_text(encoding="utf-8").splitlines()}
prev = {l.split("  ")[1]: l.split("  ")[0] for l in (ROOT / "docs" / "hashes_paper.txt").read_text(encoding="utf-8").splitlines()[1:]}
res, tab = rel("eval/results"), rel("paper/tables")
print("eval/results identical to hashes_before:", all(before.get(k) == v for k, v in res.items()) and len(res) == sum(k.startswith("eval/results") for k in before))
print("table files changed in this batch:", [Path(k).name for k, v in tab.items() if prev.get(k) != v])
lines = ["# SHA-256 after 'paper: layout fixes' (eval/results must equal docs/hashes_before.txt)"] + [f"{v}  {k}" for k, v in {**res, **tab}.items()]
(ROOT / "docs" / "hashes_paper.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
