# Results (TEST split)

Frozen configuration: git tag `frozen-main-config` = `69352e4ef40247a2606bf15ea227008af1b8124c`. K=20, qwen3.5:4b-q4_K_M, temperature 0, think off, fairness_instruction=True; the parser and re-ranker prompts in src/ were not changed after the tag.

## Main results (mean over the test requirements, 95% bootstrap CI over requirements, 10,000 resamples, seed 42)

| Method | nDCG@10 | MRR | P@10 | Recall@10 | Recall@10 (capped) | FRR@10 | FRR@20 |
|---|---|---|---|---|---|---|---|
| B1 ATS strict | 0.479 [0.307, 0.633] | 0.650 [0.400, 0.900] | 0.590 [0.370, 0.790] | 0.311 [0.196, 0.417] | 0.590 [0.370, 0.790] | 0.410 [0.210, 0.630] | 0.529 [0.340, 0.716] |
| B1b ATS lenient (>=50%) | 0.607 [0.501, 0.707] | 0.783 [0.617, 0.950] | 0.700 [0.640, 0.750] | 0.386 [0.327, 0.449] | 0.700 [0.640, 0.750] | 0.300 [0.250, 0.360] | 0.397 [0.336, 0.456] |
| B1c ATS + synonyms | 0.639 [0.564, 0.711] | 0.850 [0.700, 1.000] | 0.730 [0.610, 0.830] | 0.389 [0.334, 0.447] | 0.730 [0.610, 0.830] | 0.270 [0.170, 0.390] | 0.338 [0.233, 0.462] |
| B2 BM25 | 0.685 [0.597, 0.774] | 0.900 [0.750, 1.000] | 0.790 [0.670, 0.890] | 0.428 [0.361, 0.507] | 0.790 [0.670, 0.890] | 0.210 [0.110, 0.330] | 0.329 [0.244, 0.410] |
| B3 Dense only | 0.636 [0.530, 0.733] | 0.950 [0.850, 1.000] | 0.620 [0.490, 0.750] | 0.322 [0.276, 0.359] | 0.620 [0.490, 0.750] | 0.380 [0.250, 0.510] | 0.501 [0.440, 0.560] |
| B3b Hybrid (RRF) | 0.718 [0.633, 0.794] | 0.900 [0.750, 1.000] | 0.800 [0.710, 0.890] | 0.428 [0.393, 0.465] | 0.800 [0.710, 0.890] | 0.200 [0.110, 0.290] | 0.314 [0.233, 0.384] |
| B4 Proposed (K=20) | 0.749 [0.674, 0.818] | 1.000 [1.000, 1.000] | 0.760 [0.630, 0.870] | 0.403 [0.344, 0.449] | 0.760 [0.630, 0.870] | 0.240 [0.130, 0.370] | 0.501 [0.440, 0.560] |

All rankings are truncated to 20 results (B4 K=50 to 50). Missing slots count as irrelevant. MRR is the reciprocal rank of the first qualified student in that list. FRR = 1 - capped Recall.

## Paired differences (B4 minus baseline, 95% bootstrap CI over requirements)

| Comparison | Metric | Mean diff [CI] | Win/loss/tie | Verdict |
|---|---|---|---|---|
| B4 vs B3 | nDCG@10 | 0.113 [0.054, 0.177] | 9/1/0 | better |
| B4 vs B3 | MRR | 0.050 [0.000, 0.150] | 1/0/9 | not distinguishable |
| B4 vs B3 | Recall@10 (capped) | 0.140 [0.080, 0.200] | 8/0/2 | better |
| B4 vs B3b | nDCG@10 | 0.031 [-0.031, 0.093] | 7/3/0 | not distinguishable |
| B4 vs B3b | MRR | 0.100 [0.000, 0.250] | 2/0/8 | not distinguishable |
| B4 vs B3b | Recall@10 (capped) | -0.040 [-0.120, 0.040] | 1/3/6 | not distinguishable |
| B4 vs B1c | nDCG@10 | 0.111 [0.050, 0.177] | 9/1/0 | better |
| B4 vs B1c | MRR | 0.150 [0.000, 0.300] | 3/0/7 | not distinguishable |
| B4 vs B1c | Recall@10 (capped) | 0.030 [-0.080, 0.130] | 5/2/3 | not distinguishable |
| B4 vs B1 | nDCG@10 | 0.270 [0.099, 0.477] | 9/1/0 | better |
| B4 vs B1 | MRR | 0.350 [0.100, 0.600] | 5/0/5 | better |
| B4 vs B1 | Recall@10 (capped) | 0.170 [-0.040, 0.410] | 4/2/4 | not distinguishable |

## ATS hard-rejection rate: share of qualified students failing the keyword rule (pooled over requirements)

| Method | Overall | standard | paraphrased | implied | abbreviated_noisy | sparse_strong | ineligible_strong | generalist_average | stuffed_weak | Passers per requirement |
|---|---|---|---|---|---|---|---|---|---|---|
| B1 ATS strict | 56% (106/190) | 22% (17/77) | 100% (51/51) | 56% (10/18) | 86% (18/21) | 36% (4/11) | 0% (0/1) | 38% (3/8) | 100% (3/3) | 0-20 (mean 10.5) |
| B1b ATS lenient (>=50%) | 33% (63/190) | 0% (0/77) | 100% (51/51) | 33% (6/18) | 29% (6/21) | 0% (0/11) | 0% (0/1) | 0% (0/8) | 0% (0/3) | 17-79 (mean 41.4) |
| B1c ATS + synonyms | 36% (68/190) | 5% (4/77) | 100% (51/51) | 44% (8/18) | 5% (1/21) | 0% (0/11) | 0% (0/1) | 12% (1/8) | 100% (3/3) | 3-23 (mean 16.5) |

B1c uses aliases from the generator's own taxonomy, so it is a generous baseline.

## Archetype table: share of qualified students found in the top-20 (pooled over requirements; counts in brackets)

| Method | standard | paraphrased | implied | abbreviated_noisy | sparse_strong | ineligible_strong | generalist_average | stuffed_weak |
|---|---|---|---|---|---|---|---|---|
| B1 ATS strict | 78% (60/77) | 0% (0/51) | 44% (8/18) | 14% (3/21) | 64% (7/11) | 100% (1/1) | 62% (5/8) | 0% (0/3) |
| B1b ATS lenient (>=50%) | 92% (71/77) | 0% (0/51) | 56% (10/18) | 38% (8/21) | 100% (11/11) | 100% (1/1) | 38% (3/8) | 67% (2/3) |
| B1c ATS + synonyms | 94% (72/77) | 0% (0/51) | 56% (10/18) | 90% (19/21) | 100% (11/11) | 100% (1/1) | 62% (5/8) | 0% (0/3) |
| B2 BM25 | 99% (76/77) | 2% (1/51) | 94% (17/18) | 43% (9/21) | 82% (9/11) | 100% (1/1) | 75% (6/8) | 0% (0/3) |
| B3 Dense only | 61% (47/77) | 6% (3/51) | 78% (14/18) | 52% (11/21) | 82% (9/11) | 100% (1/1) | 50% (4/8) | 0% (0/3) |
| B3b Hybrid (RRF) | 94% (72/77) | 4% (2/51) | 94% (17/18) | 57% (12/21) | 100% (11/11) | 100% (1/1) | 88% (7/8) | 0% (0/3) |
| B4 Proposed (K=20) | 61% (47/77) | 6% (3/51) | 78% (14/18) | 52% (11/21) | 82% (9/11) | 100% (1/1) | 50% (4/8) | 0% (0/3) |

## Parser accuracy (exact match on eligibility fields; must-have skills normalised through the taxonomy)

| Split | min_cgpa | max_backlogs | allowed_branches | eligibility overall | must-have precision | must-have recall |
|---|---|---|---|---|---|---|
| dev | 100% | 100% | 100% | 100% | 100% | 93% |
| test | 100% | 100% | 100% | 100% | 96% | 93% |

Every mismatch:

- **dev** R04 must_have: parsed=['SQL', 'Excel'] -> ['Excel', 'SQL'] | truth=['Excel', 'Power BI', 'SQL']
- **dev** R04 nice_to_have (info): parsed=['Pandas', 'Power BI', 'Python'] truth=['Pandas', 'Python']
- **dev** R12 must_have: parsed=['Requirements Gathering', 'Documentation', 'Agile/Scrum', 'Stakeholder Communication'] -> ['Agile/Scrum', 'Requirements Gathering', 'Stakeholder Communication'] | truth=['Agile/Scrum', 'Requirements Gathering', 'Stakeholder Communication'] | unnormalised=['Documentation']
- **test** R03 must_have: parsed=['Node.js', 'Express', 'React', 'MongoDB'] -> ['Express.js', 'MongoDB', 'Node.js', 'React'] | truth=['MongoDB', 'Node.js', 'React']
- **test** R06 must_have: parsed=['SQL', 'ETL'] -> ['ETL Pipelines', 'SQL'] | truth=['Apache Spark', 'ETL Pipelines', 'SQL']
- **test** R06 nice_to_have (info): parsed=['AWS', 'Airflow', 'Apache Kafka', 'Apache Spark'] truth=['AWS', 'Airflow', 'Apache Kafka']
- **test** R10 must_have: parsed=['Network Security', 'Linux Administration'] -> ['Linux', 'Network Security'] | truth=['Linux', 'Network Security', 'Penetration Testing']
- **test** R10 nice_to_have (info): parsed=['Cryptography', 'Penetration Testing', 'Python'] truth=['Cryptography', 'Python']

## Retrieval (qualified students in the pool)

| Req | Qualified | Parsed top-20 | Parsed top-50 | Oracle top-20 | Oracle top-50 | Parser-caused false rejections |
|---|---|---|---|---|---|---|
| R02 | 16 | 5 | 10 | 5 | 10 | 0 |
| R03 | 15 | 7 | 10 | 7 | 10 | 0 |
| R05 | 24 | 11 | 17 | 11 | 17 | 0 |
| R06 | 19 | 10 | 15 | 10 | 15 | 0 |
| R08 | 29 | 14 | 18 | 14 | 18 | 0 |
| R10 | 16 | 9 | 10 | 9 | 10 | 0 |
| R11 | 14 | 6 | 10 | 6 | 10 | 0 |
| R13 | 18 | 9 | 11 | 9 | 11 | 0 |
| R14 | 21 | 10 | 17 | 10 | 17 | 0 |
| R15 | 18 | 8 | 12 | 8 | 12 | 0 |

Totals: parsed top-20 89, top-50 130; oracle top-20 89, top-50 130; false rejections 0.

## Ablations of B4 (pre-declared: K=50, oracle filters, no fairness instruction)

| Variant | nDCG@10 | MRR | Recall@10 (capped) | FRR@10 | FRR@20 |
|---|---|---|---|---|---|
| B4 Proposed (K=20) | 0.749 [0.674, 0.818] | 1.000 [1.000, 1.000] | 0.760 [0.630, 0.870] | 0.240 [0.130, 0.370] | 0.501 [0.440, 0.560] |
| B4 K=50 | 0.763 [0.694, 0.824] | 1.000 [1.000, 1.000] | 0.770 [0.640, 0.860] | 0.230 [0.140, 0.360] | 0.308 [0.237, 0.376] |
| B4 oracle filters | 0.755 [0.679, 0.824] | 1.000 [1.000, 1.000] | 0.770 [0.640, 0.880] | 0.230 [0.120, 0.360] | 0.495 [0.437, 0.554] |
| B4 no fairness instruction | 0.755 [0.661, 0.838] | 0.950 [0.850, 1.000] | 0.760 [0.620, 0.880] | 0.240 [0.120, 0.380] | 0.495 [0.437, 0.554] |

## Ablation differences in nDCG@10

| Comparison | Mean diff [CI] | Win/loss/tie | Verdict |
|---|---|---|---|
| B4 K=50 minus B4 | 0.014 [-0.001, 0.041] | 3/1/6 | not distinguishable |
| B4 oracle filters minus B4 | 0.005 [0.000, 0.016] | 1/0/9 | not distinguishable |
| B4 no fairness instruction minus B4 | 0.006 [-0.028, 0.034] | 4/2/4 | not distinguishable |

## Spot-check agreement (data/spotcheck_labeled.csv)

n=20; quadratic-weighted Cohen's kappa = 0.962; exact agreement = 90%; binary (qualified = relevance >= 2) agreement = 95%.

Binary confusion matrix (rows = generated, columns = mine; 0 = not qualified, 1 = qualified): [[9, 1], [0, 10]]

Disagreements:

- R15 / S369: generated 1, my label 2
- R13 / S424: generated 2, my label 3

## Fairness (name swap): control = different name from the same group, cross = names from other groups; CIs over 100 requirement-candidate pairs

| Condition | Metric | Control | Cross-group | Cross minus control |
|---|---|---|---|---|
| instruction ON | mean abs score change (points) | 3.750 [1.750, 6.350] | 2.383 [1.450, 3.433] | -1.367 [-3.517, 0.250] (not distinguishable) |
| instruction ON | share of swaps with abs change >= 5 | 0.170 [0.100, 0.250] | 0.160 [0.103, 0.223] | -0.010 [-0.073, 0.053] (not distinguishable) |
| instruction ON | mean abs rank shift in 20-pool | 0.710 [0.330, 1.140] | 0.403 [0.220, 0.617] | -0.307 [-0.697, 0.047] (not distinguishable) |
| instruction ON | top-10 boundary-crossing rate | 0.070 [0.020, 0.120] | 0.033 [0.013, 0.060] | -0.037 [-0.083, 0.007] (not distinguishable) |
| instruction ON | mean abs cosine-similarity shift (retrieval) | 0.014 [0.012, 0.016] | 0.014 [0.013, 0.015] | -0.000 [-0.002, 0.002] (not distinguishable) |
| instruction OFF | mean abs score change (points) | 1.850 [0.950, 2.900] | 2.083 [1.233, 3.083] | 0.233 [-0.617, 1.100] (not distinguishable) |
| instruction OFF | share of swaps with abs change >= 5 | 0.150 [0.080, 0.220] | 0.143 [0.090, 0.203] | -0.007 [-0.060, 0.043] (not distinguishable) |
| instruction OFF | mean abs rank shift in 20-pool | 0.580 [0.250, 0.980] | 0.577 [0.283, 0.940] | -0.003 [-0.263, 0.240] (not distinguishable) |
| instruction OFF | top-10 boundary-crossing rate | 0.060 [0.020, 0.110] | 0.063 [0.027, 0.107] | 0.003 [-0.023, 0.030] (not distinguishable) |
| instruction OFF | mean abs cosine-similarity shift (retrieval) | 0.014 [0.012, 0.016] | 0.014 [0.013, 0.015] | -0.000 [-0.002, 0.002] (not distinguishable) |

Mean SIGNED score change after the swap (new minus original, points; CI over swaps):

| Condition | Grouping | Value | Mean signed change [CI] |
|---|---|---|---|
| instruction ON | target group | gujarati_female | -2.31 [-4.52, -0.58] |
| instruction ON | target group | gujarati_male | -0.48 [-1.73, 0.67] |
| instruction ON | target group | north_indian_female | -0.31 [-2.35, 2.04] |
| instruction ON | target group | north_indian_male | -0.58 [-2.50, 1.06] |
| instruction ON | target group | south_indian_female | 1.19 [-0.71, 3.33] |
| instruction ON | target group | south_indian_male | -1.42 [-4.34, 0.85] |
| instruction ON | target gender | female | -0.59 [-1.82, 0.59] |
| instruction ON | target gender | male | -0.83 [-2.04, 0.22] |
| instruction ON | target region | gujarati | -1.39 [-2.64, -0.34] |
| instruction ON | target region | north_indian | -0.45 [-1.83, 0.94] |
| instruction ON | target region | south_indian | -0.26 [-2.11, 1.32] |
| instruction ON | gender transition | male->male | -0.65 [-2.72, 0.87] |
| instruction ON | gender transition | male->female | -0.41 [-2.03, 1.01] |
| instruction ON | gender transition | female->male | -0.90 [-2.43, 0.36] |
| instruction ON | gender transition | female->female | -0.80 [-2.75, 1.16] |
| instruction OFF | target group | gujarati_female | -0.29 [-2.40, 1.35] |
| instruction OFF | target group | gujarati_male | 0.67 [-1.25, 2.88] |
| instruction OFF | target group | north_indian_female | 0.51 [-0.20, 1.43] |
| instruction OFF | target group | north_indian_male | -0.67 [-2.60, 0.87] |
| instruction OFF | target group | south_indian_female | 0.60 [-1.67, 3.33] |
| instruction OFF | target group | south_indian_male | 0.38 [-1.32, 2.08] |
| instruction OFF | target gender | female | 0.24 [-0.80, 1.33] |
| instruction OFF | target gender | male | 0.13 [-0.92, 1.21] |
| instruction OFF | target region | gujarati | 0.19 [-1.20, 1.59] |
| instruction OFF | target region | north_indian | -0.10 [-1.14, 0.84] |
| instruction OFF | target region | south_indian | 0.47 [-0.95, 2.00] |
| instruction OFF | gender transition | male->male | 0.76 [-0.11, 1.85] |
| instruction OFF | gender transition | male->female | 0.41 [-0.34, 1.22] |
| instruction OFF | gender transition | female->male | -0.14 [-1.58, 1.31] |
| instruction OFF | gender transition | female->female | 0.07 [-1.96, 2.17] |

Target-group usage (cross swaps): {"gujarati_female": 52, "gujarati_male": 52, "north_indian_female": 49, "north_indian_male": 52, "south_indian_female": 42, "south_indian_male": 53}

This tests names only, not college prestige or other proxies.

## Timings (original, uncached latencies) and cache use

| Req | Parse s | Retrieve s | Re-rank s (20 cand.) | s per candidate |
|---|---|---|---|---|
| R02 | 3.3 | 0.03 | 47.3 | 2.37 |
| R03 | 2.9 | 0.05 | 51.4 | 2.57 |
| R05 | 2.6 | 0.04 | 51.2 | 2.56 |
| R06 | 2.8 | 0.04 | 49.0 | 2.45 |
| R08 | 2.6 | 0.04 | 44.3 | 2.21 |
| R10 | 2.7 | 0.04 | 48.2 | 2.41 |
| R11 | 2.5 | 0.04 | 45.5 | 2.27 |
| R13 | 2.4 | 0.03 | 49.7 | 2.48 |
| R14 | 2.5 | 0.03 | 47.6 | 2.38 |
| R15 | 2.2 | 0.03 | 46.6 | 2.33 |

New (uncached) re-rank calls per run in this evaluation: {"b4_k20": 200, "b4_k50": 301, "b4_oracle": 0, "b4_off": 200}. Call cache: 1716 entries.

## Deviations and caveats

- All methods share the parsed hard filters (the same eligible set); the oracle ablation is the only exception.
- B1c aliases come from the generator's own taxonomy, so it is a generous baseline; the labels also come from that generator (circular).
- Rankings are truncated to 20 (B4 K=50 to 50) before computing MRR, so a method cannot gain MRR from ranks below its pool.
- Recall@10 (plain) is bounded by 10/#qualified when a requirement has more than 10 qualified students; the capped variant is the headline.
- The fairness test rescored swapped resumes by calling the re-ranker directly (same prompt, requirement text and parsed skills as `pipeline.run`) instead of passing `resume_override` to a full 20-candidate run; pool rank shifts substitute the new score into the stored 20-candidate pool.
- Only 10 test requirements: CIs are wide and per-requirement results are noisy.
- Temperature 0 with a 4B model: score changes after a name swap include non-name effects of the changed prompt text; the control swap (same-group name) measures that floor.
- The fairness test covers names only, not college prestige or other proxies.
- **Bug fix after the freeze tag (src/llm.py only).** In the fairness OFF stage one swapped resume (R02 / S087, control swap) made the model loop inside the unbounded `matched_skills` array until the 4096-token context was full (finish reason `length`, invalid JSON), which crashed the stage. `chat_json` now retries once with every schema array capped at 8 items and `num_predict=700`, stored under the ORIGINAL cache key. It was needed for exactly 1 call out of 1716 cached calls; all earlier calls (every main, ablation and fairness-ON result) completed without it, so no previously successful result changed. Fairness OFF was resumed from the saved partial results (20 rows) and the final report regenerated. Prompts, schemas of normal calls, K, model and temperature are unchanged; `git diff frozen-main-config -- src` shows only this change.
- GPU use was checked through the Ollama API after every requirement (`size_vram == size`); it stayed 100% GPU.
