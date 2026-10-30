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
| ablations.tex | tab:ablations | table | Variant; nDCG@10; MRR; Recall@10$^{cap}$; FRR@10; FRR@20 | Ablations of the proposed method. TODO caption text. |
| archetype_found.tex | tab:archetype | table* | Method; standard; paraphrased; implied; abbreviated\_noisy; sparse\_strong; ineligible\_strong; generalist\_average; stuffed\_weak | Share of qualified students inside the top-20 pool, by resume style. TODO caption text. |
| ats_rejection.tex | tab:ats | table* | Method; Overall; standard; paraphrased; implied; abbreviated\_noisy; sparse\_strong; ineligible\_strong; generalist\_average; stuffed\_weak; Passers per requirement | Share of qualified students that the keyword rule rejects, by resume style. TODO caption text. |
| fairness.tex | tab:fair | table | Condition; Metric; Control; Cross-group; Cross$-$control | Name-swap test, control versus cross-group. TODO caption text. |
| main_results.tex | tab:main | table* | Method; nDCG@10; MRR; P@10; Recall@10$^{cap}$; FRR@10; FRR@20 | Main results on the test requirements (mean, 95\% bootstrap CI over requirements). TODO caption text. |
| parser_accuracy.tex | tab:parser | table | Split; min\textbackslash{}\_cgpa; max\textbackslash{}\_backlogs; branches; Elig.; Must P; Must R | Parser accuracy. TODO caption text. |
| posthoc_b5.tex | tab:b5 | table* | Method (post-hoc); nDCG@10; MRR; P@10; Recall@10 (capped); FRR@10; FRR@20 | Post-hoc exploratory: hybrid retrieval with the same re-ranker (B5). TODO caption text. |
| posthoc_b5_archetype.tex | tab:b5arch | table* | Pool (post-hoc); standard; paraphrased; implied; abbreviated\_noisy; sparse\_strong; ineligible\_strong; generalist\_average; stuffed\_weak | Post-hoc exploratory: qualified students in the pool, by resume style. TODO caption text. |
| posthoc_b5_paired.tex | tab:b5paired | table | Comparison; Metric; Mean diff [CI]; W/L/T; Verdict | Post-hoc exploratory: B5 paired differences. TODO caption text. |
| posthoc_d1.tex | tab:d1 | table | Req; Para. qual.; Non-qual.; Score qual.; Score non-qual.; AUC; Top-10 | Post-hoc exploratory: D1, re-ranking paraphrased resumes with retrieval bypassed. TODO caption text. |

## Figures in paper/figs

| file | label | axes | caption in main.tex |
|---|---|---|---|
| fig_archetype.pdf (+ .png) | fig:archetype | x: resume archetype; y: share of qualified students in the top-20; grouped bars by method | Qualified students found in the top-20, by resume style and method. TODO. |
| fig_fairness.pdf (+ .png) | fig:fair | x: instruction ON/OFF x control/cross-group; y: mean absolute score change (points), 95% CI | Mean absolute score change after a name swap. TODO. |
| fig_ndcg10.pdf (+ .png) | fig:ndcg | x: method (B1..B4); y: nDCG@10 mean with 95% CI error bars | nDCG@10 by method (95\% CI). TODO. |
