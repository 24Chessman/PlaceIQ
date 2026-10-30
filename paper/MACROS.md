# Macro sheet

Every macro referenced by `paper/OUTLINE.md`, as it renders (values come from `paper/numbers.tex`).

## Abstract

- `\PropNdcgCi` = 0.749 [0.674, 0.818]
- `\DenseNdcgCi` = 0.636 [0.530, 0.733]
- `\AtsStrictRejPct` = 56

## I. Introduction

- `\AtsStrictRejPct` = 56
- `\AtsSynRejPct` = 36
- `\AtsStrictRejFail` = 106
- `\AtsStrictRejTotal` = 190

## III. System

- `\ParserEligFieldsCorrect` = 45
- `\ParserEligFieldsTotal` = 45
- `\TimePerCandidate` = 2.40
- `\TimeRerankPerReq` = 48
- `\CallsFallback` = 1
- `\CallsMain` = 1716

## IV. Dataset and Labels

- `\NStudents` = 500
- `\NRequirements` = 15
- `\NDev` = 5
- `\NTest` = 10
- `\NSkills` = 71
- `\NArchStandard` = 150
- `\NArchParaphrased` = 100
- `\NQualifiedTestMin` = 14
- `\NQualifiedTestMax` = 29
- `\NQualifiedTest` = 190
- `\SpotN` = 20
- `\SpotKappa` = 0.962
- `\SpotExactPct` = 90
- `\SpotBinaryPct` = 95

## VI. Results

- `\PropNdcgCi` = 0.749 [0.674, 0.818]
- `\PropVsDenseNdcgDiffCi` = 0.113 [0.054, 0.177]
- `\PropVsDenseNdcgWlt` = 9/1/0
- `\PropVsAtsStrictNdcgDiffCi` = 0.270 [0.099, 0.477]
- `\PropVsAtsSynNdcgDiffCi` = 0.111 [0.050, 0.177]
- `\PropFirstQualified` = 10
- `\NTest` = 10
- `\PropVsHybridNdcgDiffCi` = 0.031 [-0.031, 0.093]
- `\PropVsHybridNdcgVerdict` = not distinguishable
- `\AtsSynRejPct` = 36
- `\PoolPropTwenty` = 89
- `\PoolQualifiedTotal` = 190
- `\PropFrrtwentyCi` = 0.501 [0.440, 0.560]
- `\ParserEligFieldsCorrect` = 45
- `\ParserEligFieldsTotal` = 45
- `\ParserTestMismatchReqs` = R03, R06, R10
- `\ParserDevMismatchReqs` = R04, R12
- `\ParserFalseRej` = 0

## VII. Post-hoc Analyses (exploratory, designed after seeing the test results)

- `\PoolBFiveTwenty` = 122
- `\PoolPropTwenty` = 89
- `\BFiveVsPropFrrtwentyDiffCi` = -0.187 [-0.242, -0.131]
- `\BFiveVsPropNdcgDiffCi` = 0.022 [-0.047, 0.094]
- `\BFiveVsHybridNdcgDiffCi` = 0.053 [0.000, 0.107]
- `\DOnePosScore` = 81.3
- `\DOneNegScore` = 29.5
- `\DOneAucCi` = 0.886 [0.844, 0.928]

## VIII. Fairness Test

- `\FairOnPairs` = 100
- `\FairOnAbsScoreControlCi` = 3.750 [1.750, 6.350]
- `\FairOnAbsScoreCrossGroupCi` = 2.383 [1.450, 3.433]
- `\FairOffAbsScoreControlCi` = 1.850 [0.950, 2.900]
- `\FairOffAbsScoreCrossGroupCi` = 2.083 [1.233, 3.083]
- `\FairShareFiveMinPct` = 14
- `\FairShareFiveMaxPct` = 17
- `\FairOnAbsSimControlCi` = 0.014 [0.012, 0.016]

## Tables in paper/tables

| file | label | env | columns | caption in main.tex |
|---|---|---|---|---|
| ablations.tex | tab:ablations | table | Variant; nDCG@10; MRR; Recall@10$^{cap}$; FRR@10; FRR@20 | Pre-declared ablations of the proposed method (K=50, oracle eligibility filters, no fairness instruction); none is distinguishable from the main configuration in nDCG@10. |
| archetype_found.tex | tab:archetype | table* | Method; standard; paraphrased; implied; abbreviated\_noisy; sparse\_strong; ineligible\_strong; generalist\_average; stuffed\_weak | Share of qualified students inside the top-20 pool, by resume style (counts in brackets), pooled over the test requirements. |
| ats_rejection.tex | tab:ats | table* | Method; Overall; standard; paraphrased; implied; abbreviated\_noisy; sparse\_strong; other (n); Passers per requirement | Share of qualified students that each keyword rule rejects, pooled over the test requirements, by resume style; ``other'' pools generalist, ineligible-strong and stuffed resumes. Paraphrased resumes contain no keywords by construction. |
| fairness.tex | tab:fair | table | Condition; Metric; Control; Cross-group; Cross$-$control | Name-swap test: control (same-group name) versus cross-group names, with the fairness instruction on and off. |
| main_results.tex | tab:main | table* | Method; nDCG@10; MRR; Recall@10$^{cap}$; FRR@10; FRR@20 | Ranking quality on the \NTest{} test requirements (mean with 95\% bootstrap CI over requirements). P@10 is omitted because it equals capped Recall@10 here: every test requirement has at least \NQualifiedTestMin{} qualified students, so both divide the hits in the top 10 by 10. FRR is one minus capped Recall; lower is better. |
| parser_accuracy.tex | tab:parser | table | Split; min\_cgpa; max\_backlogs; branches; Elig.; Must P; Must R | Parser accuracy against the structured truth: exact match on the three eligibility fields, and precision and recall of the must-have skills after normalisation. |
| posthoc_b5.tex | tab:b5 | table* | Method (post-hoc); nDCG@10; MRR; P@10; Recall@10 (capped); FRR@10; FRR@20 | Post-hoc exploratory: B5 (hybrid retrieval plus the same re-ranker), mean with 95\% bootstrap CI over requirements (dev and test shown separately). |
| posthoc_b5_archetype.tex | tab:b5arch | table* | Pool (post-hoc); standard; paraphrased; implied; abbreviated\_noisy; sparse\_strong; ineligible\_strong; generalist\_average; stuffed\_weak | Post-hoc exploratory: share of qualified students inside the candidate pool, for the dense pool (B4), the hybrid ranking (B3b) and the hybrid pool (B5). |
| posthoc_b5_paired.tex | tab:b5paired | table | Comparison; Metric; Mean diff [CI]; W/L/T (B5); Verdict | Post-hoc exploratory: paired differences of B5 (hybrid retrieval plus the same re-ranker) against B4, B3b and B1c on the test requirements. W/L/T counts requirements where B5 is better: higher for nDCG and Recall, lower for FRR@20. |
| posthoc_d1.tex | tab:d1 | table | Req; Para. qual.; Non-qual.; Score qual.; Score non-qual.; AUC; Top-10 | Post-hoc exploratory: D1, scoring paraphrased resumes with retrieval bypassed (per requirement). |

## Figures in paper/figs

| file | label | axes | caption in main.tex |
|---|---|---|---|
| fig_archetype.pdf (+ .png) | fig:archetype | x: resume style with n (five archetypes plus merged other); y: share of qualified students in the top-20; grouped bars for seven methods, legend below | Share of qualified students inside each method's top-20 list, by resume style ($n$ is the number of qualified students in the group, pooled over the test requirements). |
| fig_fairness.pdf (+ .png) | fig:fair | x: instruction ON/OFF x control/cross-group; y: mean absolute score change (points), 95% CI | Mean absolute score change after replacing the name in the resume header: a same-group name (control) versus names from other groups, with the fairness instruction on and off; 95\% bootstrap CIs over \FairOnPairs{} requirement-candidate pairs. Names only. |
| fig_ndcg10.pdf (+ .png) | fig:ndcg | x: seven methods (B1, B1b, B1c, B2, B3, B3b, B4); y: nDCG@10 mean with 95% CI error bars | Mean nDCG@10 by method with 95\% bootstrap CIs over the \NTest{} test requirements; the proposed method (B4) is highlighted. |
