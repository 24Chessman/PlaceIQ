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

`src/student_view.py` and `src/revision.py`: current fit (existing re-ranker), eligibility table (CGPA, branch, backlogs: required vs student, pass/fail; not fixable by editing the resume), gap list (missing must-have and nice-to-have skills), suggestions, a coverage projection and a simulated resume update.

- **Suggestions:** one model call for all missing skills (JSON schema, temperature 0). Per skill it returns why the skill matters for this requirement, one concrete mini-project built on the student's own stack, 2 to 3 learning steps and a sample resume bullet ("use only after you have done the work"). Every entry is validated: placeholder text ("X", "..."), URLs, course or platform names, numbers or outcome words (reduced, improved, faster, ...) in the bullet, generic text that never names the skill (whole-word match), wording that contradicts the skill's label, too-short text. Failed entries are retried once with the reasons; if they still fail the card says "Could not generate a specific suggestion for <skill>". The **Required / Nice-to-have label on each card comes from the parsed requirement and is rendered by the UI**, not written by the model. The resume is sent without its header line (name, email, phone) and no demographic information is sent. The free text is model output and can still contain mistakes or invented details; a person should check it.
- **Coverage projection (deterministic, no LLM call):** one checkbox per missing skill ("Assume I gain this skill"). From the re-ranker's matched list and the parsed requirement it shows must-have and nice-to-have skills matched now and after the ticked skills, e.g. "Currently 3 of 5 required skills; if you gain TypeScript and Figma: 5 of 5." It is arithmetic on the skill lists, not a predicted score or rank, and the tab says so.
- **Simulated resume update and re-score** (button "Re-score with updated resume", directly under the checkboxes): one model call writes one bullet per ticked skill that extends one of the student's real projects (the project title must be copied from the resume and is checked against it; no numbers, outcome claims, URLs or placeholders; skill named as a whole word; one retry; skills that still fail get no bullet). The revised resume (original text with header, plus the bullets in the resume's own list style) is shown next to the original with the additions highlighted and is editable; "Re-score edited text" re-scores whatever is in the box with the same re-ranker. The tab reports before and after score, matched and missing skills and coverage. It is labelled "Simulated bullets, not the student's work. The student must do the work and write it themselves." and "A small model's score is noisy and rewards added text; do not read this as a prediction." The bullet prompts are fixed and were not tuned towards a higher score.
- **Retrieval effect of the revised text:** computed in memory with the same bge-small model and a rebuilt BM25 index with only that student's document replaced, fused with the same RRF (k = 60) against the eligible set. It reports dense similarity, dense, BM25 and hybrid rank before and after, whether the student is in the pool of 50, and where the new score would land in the cached full list (rank by score, group, Top-10 cutoff, threshold; if the student enters the pool, the pool's last member would drop out, which is not simulated). It only reads the existing index: nothing is written to Chroma or to the student data (a unit test fails if a write is attempted).

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

### Simulated resume update: results exactly as they came out (examples, not measurements)

All missing skills were ticked. Same fixed prompts for every run. Hybrid rank is among all eligible students (R02: 319, data-engineer requirement: 247); the pool is the best 50.

| Student, requirement | Bullets written | Score before -> after | Matched before -> after (re-ranker) | Hybrid rank before -> after | In pool |
|---|---|---|---|---|---|
| S243, R02 (ticked React, TypeScript) | none: both bullets failed validation after the retry, so the text did not change | 65 -> 65 | HTML, CSS, JavaScript, Figma -> same | 38 -> 38 | yes -> yes |
| S253, R02 (React, TypeScript, Figma) | 3 (extending Fee Payment Tracker and Weather Dashboard) | 60 -> 100 | JavaScript, HTML, CSS -> React, JavaScript, HTML, CSS | 10 -> 2 (BM25 rank 16 -> 1, dense rank 23 -> 12) | yes -> yes |
| S078, data engineer (ETL Pipelines, Apache Airflow) | 1 (Apache Airflow, extending "online bookstore backend"); the ETL Pipelines bullet failed validation | 65 -> 100 | Python, SQL -> Python, SQL, ETL Pipelines | 11 -> 7 (BM25 rank 21 -> 11) | yes -> yes |

Observations, not conclusions. (1) For S253 and S078 the model's score rose to 100 and it listed a skill as matched; for S078 it credited ETL Pipelines although only an Airflow bullet was added, which is the "rewards added text" behaviour the UI warns about. (2) For S243 the validator rejected every bullet (it also rejected a bullet that copied a Vue sentence without naming React), so nothing was added. (3) The dense similarity moved by 0 to 0.020 and the hybrid rank by up to 8 places, mostly through BM25 because added bullets contain the missing keywords; all three students stayed in the pool. (4) The recomputed hybrid score before the change equals the stored one in the cached list for all three students (a consistency check). (5) Timings on this laptop: bullets 3.5 to 5.4 s, re-score 2.0 to 3.1 s, retrieval effect 0.3 to 0.4 s.

### Earlier what-if attempts (replaced; kept as evidence about the 4B re-ranker)

S216 against R02, before: score 85. Appending one "Additional skills (assumed acquired): TypeScript" line gave 60; appending a generic "Project (hypothetical): ..." bullet gave 40 for TypeScript, 40 for Figma and 40 for both; without the word "(hypothetical)" 80, 60 and 60. No skill moved from missing to matched and every score went down, partly for reasons unrelated to the added text (the model's explanations shifted to a React-versus-Vue point). Generic one-line additions are therefore not used; the current bullets extend a real project of the student.

In both live checks more than 10 candidates scored 100, so the Top 10 inside that group is decided by the fusion-score tie-break.

## Tests

`scripts/test_extensions.py` (mocked LLM, no Ollama, 33 tests): labelling and threshold, eligibility check, CSV columns, coverage arithmetic, the suggestion and bullet validators (placeholders, URLs, course names, numbers and outcome words, whole-word skill match, Required/Nice-to-have wording), retries and fallback messages, prompts contain no name or contact details, revised-text assembly and highlighting, retrieval effect with a fake index that fails on any write, placement in the cached list, hybrid ranking parity with `eval/baselines.py`. `scripts/test_demo.py` (AppTest) still passes for all 15 samples in both modes; it now expects 6 tabs.
