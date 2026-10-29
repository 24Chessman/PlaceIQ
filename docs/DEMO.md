# Demo guide (Streamlit app)

Everything runs on this laptop: a local language model (Ollama) and a local embedding model. No resume or requirement leaves the machine. Students and resumes are synthetic. The app only imports from `src/` and `eval/` and reads `eval/results/`; it recomputes nothing and changes no frozen output (`docs/hashes_before.txt` was compared before and after the tests).

## How to start

1. In a separate window start the model server (leave it open):
   `set OLLAMA_MODELS=D:\ai-cache\ollama` then `ollama serve`
2. Double-click `scripts\run_demo.bat` (or run it from a terminal). It sets all cache variables to D:, checks that port 11434 answers, activates the venv and runs `streamlit run app\app.py`. The browser opens at http://localhost:8501.
3. Check the sidebar badge. "Local LLM: warming up (first load can take about 2 min)" turns into "ready". Wait for **ready** before a live custom requirement. Sample requirements do not need it.

## What the screens show

| Tab | Content |
|---|---|
| Shortlist | funnel (all students, pass eligibility, pool of 20, shortlist of 10), how the system understood the requirement, ten candidate cards with score, matched and missing skills, explanation, resume, CSV download |
| Keyword ATS vs Ours | strict keyword ATS (baseline B1) next to our shortlist; candidates the ATS would have rejected are highlighted with the missing keywords |
| Evidence | the final test results (nDCG@10 with CIs, ATS rejection by resume style, share of qualified students found by style, ablations) and the post-hoc exploratory B5 and D1 results, clearly marked |
| Fairness and limits | name-swap result with the honest caption, and the limitations list |

Retrieval mode: the default is the **hybrid post-hoc variant** (BM25 + dense), labelled as post-hoc; "Dense only" is the paper's main configuration. Both use the same unchanged re-ranker, K=20, shortlist 10.

## 5-minute demo script

**0:00 Set the scene.** "Placement cells filter resumes by keywords. We ask whether a local model can read what a student actually did." Point at the sidebar: on-device badge, nothing leaves the laptop.

**0:30 Pick "Recommended demo: Associate Business Analyst (R12)", press Run** (instant, cached). Notice the funnel (500 students, about 295 eligible, 20, 10), the "As understood by the system" panel (the messy text became must-have chips and eligibility facts) and the cards: score colour bars, green matched and red missing chips, a two-sentence explanation. Open one resume to show the evidence behind a score. Switch on "Reveal synthetic ground truth" and show the Qualified badges.

**1:45 Open "Keyword ATS vs Ours".** Say: "The strict keyword filter passes nobody for this request. All ten of our candidates are marked as rescued, and each card says which keywords it could not find." The audience should notice that those students describe the work in other words.

**2:45 Pick the full-stack request (R03), Run, go to the same tab.** "Different style, same story: the ATS passes 3 of 297 eligible students and rejects 7 of our top 10."

**3:30 Pick the data-analyst request (R04), Run.** "Here the keyword filter does fine: it passes 37 students and rejects none of our top 10. The method is not always better; it helps when the wording differs from the keywords."

**4:00 Evidence tab.** Show the nDCG@10 chart and read the takeaway honestly: the LLM re-ranker beats dense-only, but is not distinguishable from a hybrid ranking without an LLM. Show the archetype chart: the gap is for resumes that only describe the work, and it is a retrieval problem; the post-hoc diagnostic (clearly marked) shows the re-ranker judges them well when retrieval is bypassed.

**4:40 Fairness and limits.** "Names only, no name effect detected, wide intervals. Synthetic data, labels from the same generator, 10 test requirements, a human reviews every shortlist."

**Optional (needs Ollama ready, about 50 s):** paste a new requirement under "Custom requirement" and watch the progress bar ("Scoring candidate i/20").

## If Ollama is down

The badge shows "offline (samples only)". All 15 sample requirements still run in both modes because every model call is cached; custom requirements are disabled with a message. Start `ollama serve` and the badge recovers by itself (the page re-checks every few seconds).

## Troubleshooting

* Badge stays on "warming up": the first model load from D: can take about 2 minutes; check `ollama ps` shows 100% GPU.
* "The run could not be completed" on a sample: the call cache (`.cache\llm_cache.jsonl`) is missing; start Ollama and run again (it re-scores and refills the cache).
* Slow custom run (more than about 90 s): another program is using the GPU; close it and check `ollama ps` (it must say 100% GPU).
* Model download or HF errors: the embedding model must already be in `D:\ai-cache\hf`; run the demo once with internet if it was deleted.
* Port 8501 busy: `streamlit run app\app.py --server.port 8502`.

## Disclosure about the demo examples

The four recommended examples were chosen from cached outputs **where the strict keyword ATS visibly struggles** (R03, R12, R05: at least 3 of our top 10 rejected by the ATS in both retrieval modes) plus **one where it does well** (R04: 0 of our top 10 rejected). They are not typical: across all 15 requirements the ATS rejects 0 to 10 of our top 10. The Evidence tab holds the complete numbers, including the cases where our method is not distinguishable from simpler baselines.

| Example | Style | ATS passes (of eligible) | Our top 10 rejected by ATS (hybrid / dense) |
|---|---|---|---|
| R03 | bullet list | 3 of 297 | 7 / 8 |
| R12 | formal paragraph | 0 of 295 | 10 / 10 |
| R05 | typos, informal | 12 of 323 | 3 / 4 |
| R04 | Hinglish | 37 of 488 | 0 / 0 (contrast case) |

Other requirements: R09, R10, R14 (ATS passes nobody, 10/10), R01 4/4, R13 5/4, R02 4/8, R06 2/5, R07 2/3, R11 2/5, R08 0/1, R15 1/3.

## Tests

`python scripts\test_demo.py --live` (AppTest): app loads, 4 tabs, all 15 samples in both modes from the cache, ground-truth toggle, rescued-candidate explanations, offline handling, and one live custom requirement. See the end of this file for the last results.

### Last test results

* 36 checks, 0 failures. All 15 samples x 2 modes render 10 cards from the cache: mean 0.55 s, max 0.78 s (run + render).
* Live custom requirement after warm-up: 52 s (limit 90 s), 21 new cache entries (1 parse + 20 candidate scores). `ollama ps` stayed 100% GPU.
* `docs/hashes_before.txt` vs the files in `eval/results` and `paper/tables` afterwards: 32 files, identical. `src/` unchanged by this step.
* Not tested: visual rendering in a real browser (the server boots and answers HTTP 200; the CSS was written against Streamlit's documented selectors and should be checked once by eye before the demo).
