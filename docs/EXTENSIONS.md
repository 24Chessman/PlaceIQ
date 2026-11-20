# Prototype extensions (demo v2.0)

**Prototype extensions, not evaluated; the paper's evaluation covers the frozen top-10 pipeline only.** Nothing here changes the frozen configuration (`frozen-main-config`), `eval/`, `paper/` or the quick Top-10 path. The parser, retriever and re-ranker (same prompt, Qwen3.5 4B via Ollama, JSON-schema output, temperature 0, thinking off) are reused unchanged, and re-rank results use the same on-disk call cache (`.cache/llm_cache.jsonl`).

## 1. All suited candidates (company view)

`src/extensions.py::shortlist_full(requirement, k_pool=50, threshold=60, top_n=10)`:

1. parse the requirement, apply the hard eligibility filters;
2. hybrid retrieval over the eligible students: BM25 on the parsed semantic query plus dense retrieval, fused by reciprocal rank fusion (k = 60). The code is in `src/hybrid.py` (a copy of the method used by the post-hoc B3b/B5 variant; a test checks it ranks like `eval/baselines.py`);
3. keep the top 50, score every one with the existing re-ranker, sort by score (ties by fusion score);
4. label: first 10 = "Top 10"; the rest with score >= threshold = "Also suited"; otherwise "Below threshold". The threshold slider relabels stored scores without new model calls.

The finished list is also saved under `.cache/full_lists/` (keyed by requirement, model, pool size and fusion setting) so the Student view can compare against the Top-10 cutoff. UI: sidebar button "Run full list (about 2 min)", tab "All suited candidates", CSV download (columns: rank, group, student_id, name, branch, cgpa, backlogs, score, matched, missing, explanation).

Suited = re-ranker score at or above the threshold, among the 50 best candidates from hybrid retrieval. Students outside the pool are not scored. The Top 10 of this view can differ from the Shortlist tab, which uses a dense-only pool.

## 2. Student view

`src/student_view.py`: current fit (existing re-ranker), eligibility table (CGPA, branch, backlogs: required vs student, pass/fail; not fixable by editing the resume), gap list (missing must-have and nice-to-have skills), suggestions and a what-if.

- **Suggestions:** one new model call (JSON schema, temperature 0). The prompt forbids inventing experience or claiming skills the student lacks, asks for "If you have done X, add a bullet describing it; if not, learn X by ...", and asks to name a technology explicitly when the resume only describes it indirectly. The resume is sent without its header line (name, email, phone); no demographic information is sent. The model's learning suggestions are free text and can name resources that do not exist; a person should check them.
- **What-if:** the checked skills are appended to the resume as one marked line, "Additional skills (assumed acquired): ...", and the same re-ranker re-scores it. The result is labelled "Projection only. It assumes the student genuinely has these skills. Not a guarantee."

## Parameters

| Parameter | Value |
|---|---|
| Pool size | 50 |
| Retrieval | hybrid (BM25 + dense), reciprocal rank fusion, k = 60 |
| Threshold ("suited") | 60 (slider, 0-100) |
| Top-N group | 10 |
| Re-ranker | unchanged (Qwen3.5 4B q4_K_M, temperature 0, thinking off, fairness instruction on) |

## Measured in the live check (this laptop, RTX 4050 6 GB, model 100% on GPU)

| Check | Result |
|---|---|
| Full list, R02 (WhatsApp-style frontend request) | 319 eligible, pool 50, 43 suited at threshold 60 (10 Top 10 + 33 also suited, 7 below). 83 s wall-clock for the first call, of which about 59 s is one-time start-up (embedding model, index, BM25) and 24 s is parse, retrieval and re-ranking. Most of its 50 candidates were already in the call cache from the earlier evaluation, so this is **not** a cold time. Repeat: 0.07 s. |
| Full list, custom requirement (junior data engineer, 6.5 CGPA, no backlogs, CSE/IT/ICT) | 247 eligible, pool 50, 34 suited (10 + 24, 16 below). 146 s wall-clock, cold: about 22 s start-up plus 123 s for parse, retrieval and 50 re-ranking calls (about 2.4 s per candidate). Repeat: 0.07 s. |
| Student view, S216 (rank 31 of 50 for R02, list score 85, not in the Top 10) | fit check 0.3 s (cached), suggestions 3.3 s (two suggestions: TypeScript, Figma), what-if re-score 3.2 s. |

Observation from the what-if check: assuming "TypeScript" for S216 changed the score from 85 to 60, and TypeScript stayed in the missing list. The re-ranker rules ask for demonstrated work, so a bare line of assumed skills may not be credited, and the 4B model's score can move for reasons unrelated to the added line. The UI says so when the score does not improve. This is one example, not a measurement of the feature.

In both live checks more than 10 candidates scored 100, so the Top 10 inside that group is decided by the fusion-score tie-break.

## Tests

`scripts/test_extensions.py` (mocked LLM, no Ollama): labelling and threshold, eligibility check, CSV columns, what-if text assembly, suggestion prompt contains no name or contact details, hybrid ranking parity with `eval/baselines.py`. `scripts/test_demo.py` (AppTest) still passes for all 15 samples in both modes; it now expects 6 tabs.
