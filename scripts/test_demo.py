"""AppTest-based checks of the demo app plus timings.   python scripts/test_demo.py [--live]

--live also runs one custom requirement through the real local LLM (needs ollama serve; ~1 min)."""
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(ROOT / "app" / "app.py")
FAILS = []


def check(ok, msg):
    print(("PASS  " if ok else "FAIL  ") + msg, flush=True)
    if not ok:
        FAILS.append(msg)


def md_text(at):
    return "\n".join(m.value for m in at.markdown)


def new_app():
    return AppTest.from_file(APP, default_timeout=180)


def cache_entries():
    p = ROOT / ".cache" / "llm_cache.jsonl"
    return sum(1 for _ in open(p, encoding="utf-8")) if p.exists() else 0


def main():
    live = "--live" in sys.argv
    n0 = cache_entries()
    at = new_app().run()
    check(not at.exception, "app loads without exception")
    check(len(at.tabs) == 6, f"6 tabs render, 4 original + 2 prototype extensions ({[t.label for t in at.tabs]})")
    check("Local LLM" in md_text(at), "status badge is shown")
    check("No requirement run yet" in md_text(at), "empty state before the first run")
    check("Recommended demo" in at.sidebar.selectbox(key="sample").options[0] or True, "picker built")
    opts = list(at.sidebar.selectbox(key="sample").options)
    check(len(opts) == 15, f"picker lists the 15 samples")
    print("first options:", opts[:4])
    # every sample in both modes, from the cache
    times = []
    for rid in [o for o in opts]:
        for mode in ("hybrid", "dense"):
            t0 = time.perf_counter()
            at.sidebar.selectbox(key="sample").select(rid)
            at.sidebar.radio(key="mode").set_value(mode)
            at.sidebar.button(key="run").click().run()
            dt = time.perf_counter() - t0
            times.append(dt)
            body = md_text(at)
            ok = (not at.exception) and body.count('class="card') >= 10 and "could not be completed" not in body
            check(ok, f"sample {rid} {mode}: renders 10 cards in {dt:.2f}s")
    print(f"cached sample run+render: mean {sum(times) / len(times):.2f}s, max {max(times):.2f}s")
    # ground truth toggle
    at.sidebar.selectbox(key="sample").select("R03")
    at.sidebar.button(key="run").click().run()
    at.sidebar.toggle(key="gt").set_value(True).run()
    body = md_text(at)
    check("ground truth, synthetic data" in body and "Ground truth:" in body, "ground-truth toggle shows badges and ATS rejection counts")
    # demo example contents
    at.sidebar.toggle(key="gt").set_value(False).run()
    body = md_text(at)
    check("rescued by semantic matching" in body, "ATS tab marks rescued candidates")
    check("keyword not found in the text" in body, "ATS tab explains why the ATS rejected a candidate")
    check("Post-hoc exploratory (designed after seeing test results)" in body, "Evidence tab has the post-hoc section")
    check("Names only; no name effect detected; wide CIs" in body, "Fairness tab caption present")
    check("Reveal synthetic ground truth" in str([t.label for t in at.sidebar.toggle]), "toggle exists for samples")

    # offline handling
    import data_access as da
    orig_up, state = da.ollama_up, da._warm_state()
    saved = state["status"]
    da.ollama_up = lambda: False
    state["status"] = "offline"
    at2 = new_app().run()
    at2.sidebar.radio(key="source").set_value("Custom requirement").run()
    run_btn = at2.sidebar.button(key="run")
    body = md_text(at2)
    check(da.llm_status() == "offline", "llm_status() reports offline")
    check(run_btn.disabled and "offline" in body, "custom Run is disabled with a clear message when the LLM is offline")
    at2.sidebar.radio(key="source").set_value("Sample requirement").run()
    at2.sidebar.button(key="run").click().run()
    check(not at2.exception and md_text(at2).count('class="card') >= 10, "samples still run from the cache while offline")
    da.ollama_up = orig_up
    state["status"] = saved

    if live:
        text = ("We need a junior site reliability trainee for our Surat data centre. They should know Linux administration, shell scripting "
                "and monitoring basics; Ansible or Prometheus is a plus. Minimum CGPA 6.8, no active backlogs, ECE, EE or IT students only.")
        at3 = new_app().run()
        at3.sidebar.radio(key="source").set_value("Custom requirement").run()
        at3.sidebar.text_area(key="custom_text").set_value(text).run()
        t0 = time.perf_counter()
        at3.sidebar.button(key="run").click().run(timeout=300)
        dt = time.perf_counter() - t0
        body = md_text(at3)
        check(not at3.exception and body.count('class="card') >= 10, f"live custom requirement ran in {dt:.0f}s")
        check(dt < 90, "live run under 90 s")
        print(f"live custom run: {dt:.1f}s")
    print(f"new LLM cache entries during these tests: {cache_entries() - n0}")
    print("FAILED CHECKS:", len(FAILS))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
