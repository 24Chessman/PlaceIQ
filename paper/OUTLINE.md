# Paper outline: \papertitle (IEEEtran conference, 5-6 pages)

Macros are in `numbers.tex`; tables in `tables/`, figures in `figs/`. All claims follow the claim rules at the end.

| Section | Pages |
|---|---|
| Abstract | 0.15 |
| I. Introduction | 0.6 |
| II. Related Work | 0.5 |
| III. System | 0.8 |
| IV. Dataset and Labels | 0.7 |
| V. Experimental Setup | 0.6 |
| VI. Results | 1.1 |
| VII. Post-hoc Analyses | 0.5 |
| VIII. Fairness Test | 0.5 |
| IX. Discussion and Limitations | 0.5 |
| X. Conclusion | 0.15 |
| References | 0.3 |

## Abstract
- One paragraph: problem (keyword filters in campus placement), pipeline (LLM parse, filtered retrieval, LLM re-rank with explanations, runs on a laptop), headline results (nDCG@10 `\PropNdcgCi` vs `\DenseNdcgCi`; strict ATS rejects `\AtsStrictRejPct`% of qualified students), honest caveats (synthetic, post-hoc B5/D1, names-only fairness).

## I. Introduction
- P1 Claim: strict keyword matching rejects qualified students whose resumes use other words. Support: `\AtsStrictRejPct`, `\AtsSynRejPct` (still rejects this share with synonyms), `\AtsStrictRejFail`/`\AtsStrictRejTotal`. State that the 100% rejection of paraphrased resumes is a design property of the generator (they contain no keywords), not a finding.
- P2 Claim: a small local pipeline (4B model, 6 GB GPU) with explanations; contributions: synthetic benchmark with hidden-truth labels, frozen-configuration evaluation, name-swap test, clearly labelled post-hoc diagnostics.
- P3 Roadmap.

## II. Related Work
- Lexical, dense retrieval and fusion: `\cite{robertson2009bm25,cormack2009rrf,karpukhin2020dpr,reimers2019sbert,xiao2024cpack}`.
- LLM re-ranking: `\cite{sun2023rankgpt}`.
- Resume-job matching: `\cite{yu2025confitv2,jouanneau2026personjob}`; those use real, mostly proprietary data, ours is synthetic.
- Name-based bias in hiring and in screening models: `\cite{bertrand2004emily,wilson2024resume}`.

## III. System
- P1 Pipeline overview (figure TODO: pipeline diagram). Parser: schema-constrained JSON, eligibility as hard filters, no taxonomy given to the model. Support: `\ParserEligFieldsCorrect` of `\ParserEligFieldsTotal`.
- P2 Retrieval: bge-small embeddings, Chroma metadata filters, whole resumes (no resume over 512 tokens). `\cite{xiao2024cpack,chroma}`.
- P3 Re-ranker: evidence first, score last; rules for implied skills, unsupported keyword lists, eligibility; K=20, shortlist 10; local model `\cite{ollama,qwen35ollama}`. Timing: `\TimePerCandidate` s per candidate, `\TimeRerankPerReq` s per requirement.
- P4 Reproducibility: call cache, frozen git tag; the single post-freeze code change (retry with capped arrays, used for `\CallsFallback` of `\CallsMain` calls).

## IV. Dataset and Labels
- P1 Generator: `\NStudents` students, `\NRequirements` requirements (`\NDev` dev, `\NTest` test), `\NSkills` skills, 8 resume archetypes (counts `\NArchStandard`, `\NArchParaphrased`, and so on). Everything is synthetic.
- P2 Labels: deterministic function of hidden skill levels (relevance 0-3, qualified = 2 or more); labels come from the same generator (circularity). Qualified per test requirement `\NQualifiedTestMin` to `\NQualifiedTestMax`, total `\NQualifiedTest`.
- P3 Disclosures: quota-based balancing; taxonomy edits (R02: HTML/CSS no longer implied by React/Angular/Vue; R07: a devops stack starting from Raspberry Pi); requirement simplifications (3 must-haves in R03, R07, R12, R13; R09 is React Native; lowered CGPA cutoffs).
- P4 Human spot-check: `\SpotN` pairs, one labeller who used a rule derived from the labelling function, kappa `\SpotKappa`, exact `\SpotExactPct`%, binary `\SpotBinaryPct`%; small and not independent.

## V. Experimental Setup
- P1 Methods B1, B1b, B1c (aliases from the generator's own taxonomy: generous baseline), B2, B3, B3b, B4 and the pre-declared ablations (K=50, oracle filters, no fairness instruction). All use the same parsed hard filters.
- P2 Metrics: nDCG@10, MRR, P@10, capped Recall@10, FRR@10/20; mean over test requirements with 95% bootstrap CI over requirements (10,000 resamples, seed 42); paired differences.
- P3 Protocol: prompts tuned on 5 dev requirements only; test split run once with the frozen configuration; post-hoc analyses (B5, D1) designed after seeing test results.

## VI. Results
- P1 Main table (`tables/main_results.tex`, `figs/fig_ndcg10`): B4 has the highest mean nDCG@10 `\PropNdcgCi`; it improves over dense-only B3 (`\PropVsDenseNdcgDiffCi`, W/L/T `\PropVsDenseNdcgWlt`) and over the keyword variants B1 and B1c (`\PropVsAtsStrictNdcgDiffCi`, `\PropVsAtsSynNdcgDiffCi`); CIs exclude 0. A qualified candidate is ranked first for `\PropFirstQualified` of `\NTest` requirements.
- P2 NOT better than hybrid: B4 vs B3b `\PropVsHybridNdcgDiffCi` (`\PropVsHybridNdcgVerdict`). Say so explicitly.
- P3 ATS rejection (`tables/ats_rejection.tex`): a large share of qualified students is rejected and it depends strongly on resume style; still `\AtsSynRejPct`% with synonyms. Paraphrased = design property.
- P4 Pool coverage (`tables/archetype_found.tex`, `figs/fig_archetype`): B4's pool holds `\PoolPropTwenty` of `\PoolQualifiedTotal` qualified students (FRR@20 `\PropFrrtwentyCi`), worse than the hybrid ranking and ATS with synonyms; only the implied archetype clearly favours dense/B4. Do not claim "finds candidates the ATS misses" in general.
- P5 Parser and ablations (`tables/parser_accuracy.tex`, `tables/ablations.tex`): eligibility fields `\ParserEligFieldsCorrect` of `\ParserEligFieldsTotal` correct (small sample); skill mismatches in `\ParserTestMismatchReqs` (test) and `\ParserDevMismatchReqs` (dev); parser-caused false rejections `\ParserFalseRej`; K=50, oracle filters and no fairness instruction are not distinguishable from B4 in nDCG@10.

## VII. Post-hoc Analyses (exploratory, designed after seeing the test results)
- P1 B5 hybrid retrieval + re-ranker (`tables/posthoc_b5.tex`, `posthoc_b5_paired.tex`, `posthoc_b5_archetype.tex`): pool coverage rises (`\PoolBFiveTwenty` vs `\PoolPropTwenty`, FRR@20 `\BFiveVsPropFrrtwentyDiffCi`, all 10 requirements); nDCG@10 not distinguishable from B4 (`\BFiveVsPropNdcgDiffCi`); vs B3b marginal (`\BFiveVsHybridNdcgDiffCi`, lower bound 0.000).
- P2 D1 diagnostic (`tables/posthoc_d1.tex`): with retrieval bypassed the re-ranker separates paraphrased-qualified from non-qualified resumes (mean scores `\DOnePosScore` vs `\DOneNegScore`, AUC `\DOneAucCi`), so the paraphrase failure in the main pipeline comes from retrieval. Reasons retrieval misses them are hypotheses. Do not cite the top-10 share as strong evidence (small candidate sets).

## VIII. Fairness Test
- P1 Design: top-10 of each test requirement (`\FairOnPairs` pairs), control (same-group name) and cross-group swaps, header only changed, instruction ON and OFF; names only, no college prestige or other proxies.
- P2 Result (`tables/fairness.tex`, `figs/fig_fairness`): no name effect detected; control changes the score as much as cross-group (`\FairOnAbsScoreControlCi` vs `\FairOnAbsScoreCrossGroupCi`; OFF `\FairOffAbsScoreControlCi` vs `\FairOffAbsScoreCrossGroupCi`); `\FairShareFiveMinPct` to `\FairShareFiveMaxPct`% of header-only swaps moved the score by 5 or more points; wide CIs; similarity shift identical (`\FairOnAbsSimControlCi`). Not "no bias" and not "fair".

## IX. Discussion and Limitations
- P1 What the evidence supports: re-ranking helps over dense and keyword baselines; hybrid retrieval raises coverage; retrieval is the bottleneck for paraphrases.
- P2 Limitations: synthetic data, circular labels, one-labeller spot-check, 10 test requirements and wide CIs, generous B1c, taxonomy and requirement edits, one post-freeze code fix, names-only fairness, no statement about real-world accuracy or placement outcomes, decision support only.

## X. Conclusion
- Three sentences: what was built, what was found (within the claim rules), what is needed next (real resumes, human-labelled data, retrieval for paraphrases).

## CLAIM RULES
Allowed: strict ATS rejects a large share and it depends on resume style (still `\AtsSynRejPct`% with synonyms; paraphrase 100% is a design property); B4 beats B3 and the keyword variants (paired CIs exclude 0) and ranks a qualified candidate first for 10 of 10; hybrid raises pool coverage (post-hoc); the re-ranker separates paraphrased resumes with retrieval bypassed (AUC) and the failure is in retrieval (reasons are hypotheses); parser accurate on 45 of 45 eligibility fields (small sample); no name effect detected, control as large as cross-group, wide CIs.

Not allowed: "better than hybrid search"; "finds candidates the ATS misses" in general; "no bias" or "fair" (say "no name effect detected" and mention the 14-17% of header-only swaps that moved the score by 5 or more points); real-world accuracy or outcomes; "49 of 51 in the top 10" as strong evidence.

Must disclose: synthetic data and same-generator labels; 20-pair single-labeller spot-check (kappa 0.962, rule derived from the labelling function); taxonomy edits, requirement simplifications, quota balancing; B1c uses generator aliases; one `src/llm.py` change after the freeze (1 of 1716 calls); B5 and D1 post-hoc; prompts tuned on 5 dev requirements, test run once; names-only fairness.
