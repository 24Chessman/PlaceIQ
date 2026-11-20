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
- **What-if, main part: skill-coverage projection (deterministic, no LLM call).** One checkbox per missing skill ("Assume I gain this skill"). From the re-ranker's matched list and the parsed requirement, the tab shows must-have and nice-to-have skills matched now and after the ticked skills, for example "Currently 3 of 5 required skills; if you gain TypeScript and Figma: 5 of 5." It is arithmetic on the skill lists, not a predicted score or rank, and the tab says so (`src/student_view.py::coverage`, unit-tested).
- **What-if, experimental part: re-score with the model** (collapsed expander "Experimental: re-score with the model"). Each ticked skill appends one short hypothetical project bullet to the resume text, from a fixed template ("Project (hypothetical): built and deployed a small application using X, with hands-on use of X."), and the same re-ranker re-scores it. Labelled "Projection only. It assumes the student genuinely does this work. Not a guarantee." plus "The small model's score can go down when text is added; do not read this as a prediction." (An earlier version appended a single "Additional skills (assumed acquired)" line, which the re-ranker did not credit.)

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

### What-if examples (S216 against R02; one student, one requirement: examples, not measurements)

These examples are the reason the model re-score is experimental and not the headline: it is unreliable on this model.

Before: score 85, matched React, JavaScript, HTML, CSS; missing TypeScript, Figma. The Top-10 cutoff for R02 is 100.

| Assumed skill(s) | Appended text | Score after | Missing after |
|---|---|---|---|
| line "Additional skills (assumed acquired): TypeScript" (first version) | one skills line | 60 | TypeScript, Figma |
| TypeScript | "Project (hypothetical): ..." (current template) | 40 | TypeScript, Figma |
| Figma | same template | 40 | TypeScript, Figma |
| TypeScript and Figma | same template, two bullets | 40 | TypeScript, Figma |
| TypeScript, Figma | variant without the word "(hypothetical)" (not adopted) | 80, 60, 60 | TypeScript, Figma |

In none of these runs did the re-ranker move a skill from missing to matched, and every score went down. The model's explanations say the hypothetical project is "not part of the described work evidence" and shift attention to a React-versus-Vue point in the same resume, so the drop is partly unrelated to the added bullet (temperature 0 does not make the 4B model stable across resume versions). Removing the word "(hypothetical)" gave smaller drops but no credit either, and it would hide that the text is assumed, so the template keeps it. Conclusion for this prototype: the model re-score shows how the re-ranker reacts to added text and is not a reliable prediction of a student's score, so the Student view leads with the deterministic coverage projection. For S216 against R02 the coverage projection reads: required skills 4 of 4 now (the re-ranker lists no missing required skill), nice-to-have skills 0 of 2 now and 2 of 2 if TypeScript and Figma are gained.

In both live checks more than 10 candidates scored 100, so the Top 10 inside that group is decided by the fusion-score tie-break.

## Tests

`scripts/test_extensions.py` (mocked LLM, no Ollama): labelling and threshold, eligibility check, CSV columns, what-if text assembly, suggestion prompt contains no name or contact details, hybrid ranking parity with `eval/baselines.py`. `scripts/test_demo.py` (AppTest) still passes for all 15 samples in both modes; it now expects 6 tabs.
