"""Static checks for paper/ (no LaTeX needed): inputs and figures exist, macros used in main.tex/appendix.tex/OUTLINE.md exist,
bib keys resolve, then builds paper/overleaf.zip.   python eval/check_paper.py"""
import re
import zipfile
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "paper"
main = (P / "main.tex").read_text(encoding="utf-8")
appendix = (P / "appendix.tex").read_text(encoding="utf-8")
source = main + "\n" + appendix
outline = (P / "OUTLINE.md").read_text(encoding="utf-8")
macros = set(re.findall(r"\\newcommand\{\\([A-Za-z]+)\}", (P / "numbers.tex").read_text(encoding="utf-8")))
keys = set(re.findall(r"@\w+\{([^,\s]+),", (P / "refs.bib").read_text(encoding="utf-8")))
errs = []
for f in re.findall(r"\\input\{([^}]+)\}", source):
    if not (P / (f if f.endswith(".tex") else f + ".tex")).exists():
        errs.append(f"missing \\input {f}")
for f in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", source):
    if not (P / f).exists():
        errs.append(f"missing figure {f}")
used = set(re.findall(r"\\([A-Z][A-Za-z]+)", " ".join(re.findall(r"`([^`]*)`", outline))))
for m in sorted(used):
    if m not in macros and m not in ("papertitle", "cite"):
        errs.append(f"OUTLINE macro \\{m} not defined in numbers.tex")
for grp in re.findall(r"\\cite\{([^}]+)\}", outline + source):
    for k in grp.split(","):
        if k.strip() not in keys:
            errs.append(f"cite key {k.strip()} not in refs.bib")
body = re.sub(r"^\s*%.*$", "", source, flags=re.M)
for m in sorted(set(re.findall(r"\\([A-Z][A-Za-z]+)(?![A-Za-z])", body))):
    if m not in macros and not m.startswith("IEEE") and m not in ("LaTeX",):
        errs.append(f"main/appendix uses undefined macro \\{m}")
print("macros:", len(macros), "| bib entries:", len(keys), "| outline macros used:", len(used))
print("static check:", "OK" if not errs else "\n".join(errs))
files = ["main.tex", "appendix.tex", "numbers.tex", "refs.bib"] + [f"tables/{p.name}" for p in sorted((P / "tables").glob("*.tex"))] + \
        [f"figs/{p.name}" for p in sorted((P / "figs").glob("*")) if p.suffix in (".pdf", ".png")]
with zipfile.ZipFile(P / "overleaf.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in files:
        z.write(P / f, f)
print("overleaf.zip:", len(files), "files")
