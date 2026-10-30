# Paper numbers report

796 macros written to `paper/numbers.tex` by `eval/make_paper_numbers.py`.

Cross-check against `docs/RESULTS.md`: 291 of 291 checked values appear verbatim there.

### Discrepancies

none

| macro | value | source |
|---|---|---|
| `\NStudents` | 500 | data/students.jsonl |
| `\NRequirements` | 15 | data/requirements.jsonl |
| `\NDev` | 5 | data/requirements.jsonl |
| `\NTest` | 10 | data/requirements.jsonl |
| `\NQualifiedDev` | 114 | data/qrels.csv |
| `\NQualifiedTest` | 190 | data/qrels.csv |
| `\NQualifiedTestMin` | 14 | data/qrels.csv |
| `\NQualifiedTestMax` | 29 | data/qrels.csv |
| `\NPairs` | 7500 | data/qrels.csv |
| `\NArchParaphrased` | 100 | data/students_truth.jsonl |
| `\NArchSparseStrong` | 40 | data/students_truth.jsonl |
| `\NArchStandard` | 150 | data/students_truth.jsonl |
| `\NArchAbbreviatedNoisy` | 50 | data/students_truth.jsonl |
| `\NArchStuffedWeak` | 50 | data/students_truth.jsonl |
| `\NArchGeneralistAverage` | 25 | data/students_truth.jsonl |
| `\NArchImplied` | 50 | data/students_truth.jsonl |
| `\NArchIneligibleStrong` | 35 | data/students_truth.jsonl |
| `\NSkills` | 71 | data/skills_taxonomy.json |
| `\AtsStrictNdcgMean` | 0.479 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictNdcgLo` | 0.307 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictNdcgHi` | 0.633 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictNdcgCi` | 0.479 [0.307, 0.633] | eval/results/per_requirement_metrics.csv |
| `\AtsStrictMrrMean` | 0.650 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictMrrLo` | 0.400 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictMrrHi` | 0.900 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictMrrCi` | 0.650 [0.400, 0.900] | eval/results/per_requirement_metrics.csv |
| `\AtsStrictPtenMean` | 0.590 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictPtenLo` | 0.370 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictPtenHi` | 0.790 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictPtenCi` | 0.590 [0.370, 0.790] | eval/results/per_requirement_metrics.csv |
| `\AtsStrictRplainMean` | 0.311 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictRplainLo` | 0.196 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictRplainHi` | 0.417 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictRplainCi` | 0.311 [0.196, 0.417] | eval/results/per_requirement_metrics.csv |
| `\AtsStrictRcapMean` | 0.590 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictRcapLo` | 0.370 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictRcapHi` | 0.790 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictRcapCi` | 0.590 [0.370, 0.790] | eval/results/per_requirement_metrics.csv |
| `\AtsStrictFrrtenMean` | 0.410 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictFrrtenLo` | 0.210 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictFrrtenHi` | 0.630 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictFrrtenCi` | 0.410 [0.210, 0.630] | eval/results/per_requirement_metrics.csv |
| `\AtsStrictFrrtwentyMean` | 0.529 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictFrrtwentyLo` | 0.340 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictFrrtwentyHi` | 0.716 | eval/results/per_requirement_metrics.csv |
| `\AtsStrictFrrtwentyCi` | 0.529 [0.340, 0.716] | eval/results/per_requirement_metrics.csv |
| `\AtsLenientNdcgMean` | 0.607 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientNdcgLo` | 0.501 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientNdcgHi` | 0.707 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientNdcgCi` | 0.607 [0.501, 0.707] | eval/results/per_requirement_metrics.csv |
| `\AtsLenientMrrMean` | 0.783 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientMrrLo` | 0.617 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientMrrHi` | 0.950 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientMrrCi` | 0.783 [0.617, 0.950] | eval/results/per_requirement_metrics.csv |
| `\AtsLenientPtenMean` | 0.700 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientPtenLo` | 0.640 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientPtenHi` | 0.750 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientPtenCi` | 0.700 [0.640, 0.750] | eval/results/per_requirement_metrics.csv |
| `\AtsLenientRplainMean` | 0.386 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientRplainLo` | 0.327 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientRplainHi` | 0.449 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientRplainCi` | 0.386 [0.327, 0.449] | eval/results/per_requirement_metrics.csv |
| `\AtsLenientRcapMean` | 0.700 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientRcapLo` | 0.640 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientRcapHi` | 0.750 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientRcapCi` | 0.700 [0.640, 0.750] | eval/results/per_requirement_metrics.csv |
| `\AtsLenientFrrtenMean` | 0.300 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientFrrtenLo` | 0.250 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientFrrtenHi` | 0.360 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientFrrtenCi` | 0.300 [0.250, 0.360] | eval/results/per_requirement_metrics.csv |
| `\AtsLenientFrrtwentyMean` | 0.397 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientFrrtwentyLo` | 0.336 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientFrrtwentyHi` | 0.456 | eval/results/per_requirement_metrics.csv |
| `\AtsLenientFrrtwentyCi` | 0.397 [0.336, 0.456] | eval/results/per_requirement_metrics.csv |
| `\AtsSynNdcgMean` | 0.639 | eval/results/per_requirement_metrics.csv |
| `\AtsSynNdcgLo` | 0.564 | eval/results/per_requirement_metrics.csv |
| `\AtsSynNdcgHi` | 0.711 | eval/results/per_requirement_metrics.csv |
| `\AtsSynNdcgCi` | 0.639 [0.564, 0.711] | eval/results/per_requirement_metrics.csv |
| `\AtsSynMrrMean` | 0.850 | eval/results/per_requirement_metrics.csv |
| `\AtsSynMrrLo` | 0.700 | eval/results/per_requirement_metrics.csv |
| `\AtsSynMrrHi` | 1.000 | eval/results/per_requirement_metrics.csv |
| `\AtsSynMrrCi` | 0.850 [0.700, 1.000] | eval/results/per_requirement_metrics.csv |
| `\AtsSynPtenMean` | 0.730 | eval/results/per_requirement_metrics.csv |
| `\AtsSynPtenLo` | 0.610 | eval/results/per_requirement_metrics.csv |
| `\AtsSynPtenHi` | 0.830 | eval/results/per_requirement_metrics.csv |
| `\AtsSynPtenCi` | 0.730 [0.610, 0.830] | eval/results/per_requirement_metrics.csv |
| `\AtsSynRplainMean` | 0.389 | eval/results/per_requirement_metrics.csv |
| `\AtsSynRplainLo` | 0.334 | eval/results/per_requirement_metrics.csv |
| `\AtsSynRplainHi` | 0.447 | eval/results/per_requirement_metrics.csv |
| `\AtsSynRplainCi` | 0.389 [0.334, 0.447] | eval/results/per_requirement_metrics.csv |
| `\AtsSynRcapMean` | 0.730 | eval/results/per_requirement_metrics.csv |
| `\AtsSynRcapLo` | 0.610 | eval/results/per_requirement_metrics.csv |
| `\AtsSynRcapHi` | 0.830 | eval/results/per_requirement_metrics.csv |
| `\AtsSynRcapCi` | 0.730 [0.610, 0.830] | eval/results/per_requirement_metrics.csv |
| `\AtsSynFrrtenMean` | 0.270 | eval/results/per_requirement_metrics.csv |
| `\AtsSynFrrtenLo` | 0.170 | eval/results/per_requirement_metrics.csv |
| `\AtsSynFrrtenHi` | 0.390 | eval/results/per_requirement_metrics.csv |
| `\AtsSynFrrtenCi` | 0.270 [0.170, 0.390] | eval/results/per_requirement_metrics.csv |
| `\AtsSynFrrtwentyMean` | 0.338 | eval/results/per_requirement_metrics.csv |
| `\AtsSynFrrtwentyLo` | 0.233 | eval/results/per_requirement_metrics.csv |
| `\AtsSynFrrtwentyHi` | 0.462 | eval/results/per_requirement_metrics.csv |
| `\AtsSynFrrtwentyCi` | 0.338 [0.233, 0.462] | eval/results/per_requirement_metrics.csv |
| `\BmNdcgMean` | 0.685 | eval/results/per_requirement_metrics.csv |
| `\BmNdcgLo` | 0.597 | eval/results/per_requirement_metrics.csv |
| `\BmNdcgHi` | 0.774 | eval/results/per_requirement_metrics.csv |
| `\BmNdcgCi` | 0.685 [0.597, 0.774] | eval/results/per_requirement_metrics.csv |
| `\BmMrrMean` | 0.900 | eval/results/per_requirement_metrics.csv |
| `\BmMrrLo` | 0.750 | eval/results/per_requirement_metrics.csv |
| `\BmMrrHi` | 1.000 | eval/results/per_requirement_metrics.csv |
| `\BmMrrCi` | 0.900 [0.750, 1.000] | eval/results/per_requirement_metrics.csv |
| `\BmPtenMean` | 0.790 | eval/results/per_requirement_metrics.csv |
| `\BmPtenLo` | 0.670 | eval/results/per_requirement_metrics.csv |
| `\BmPtenHi` | 0.890 | eval/results/per_requirement_metrics.csv |
| `\BmPtenCi` | 0.790 [0.670, 0.890] | eval/results/per_requirement_metrics.csv |
| `\BmRplainMean` | 0.428 | eval/results/per_requirement_metrics.csv |
| `\BmRplainLo` | 0.361 | eval/results/per_requirement_metrics.csv |
| `\BmRplainHi` | 0.507 | eval/results/per_requirement_metrics.csv |
| `\BmRplainCi` | 0.428 [0.361, 0.507] | eval/results/per_requirement_metrics.csv |
| `\BmRcapMean` | 0.790 | eval/results/per_requirement_metrics.csv |
| `\BmRcapLo` | 0.670 | eval/results/per_requirement_metrics.csv |
| `\BmRcapHi` | 0.890 | eval/results/per_requirement_metrics.csv |
| `\BmRcapCi` | 0.790 [0.670, 0.890] | eval/results/per_requirement_metrics.csv |
| `\BmFrrtenMean` | 0.210 | eval/results/per_requirement_metrics.csv |
| `\BmFrrtenLo` | 0.110 | eval/results/per_requirement_metrics.csv |
| `\BmFrrtenHi` | 0.330 | eval/results/per_requirement_metrics.csv |
| `\BmFrrtenCi` | 0.210 [0.110, 0.330] | eval/results/per_requirement_metrics.csv |
| `\BmFrrtwentyMean` | 0.329 | eval/results/per_requirement_metrics.csv |
| `\BmFrrtwentyLo` | 0.244 | eval/results/per_requirement_metrics.csv |
| `\BmFrrtwentyHi` | 0.410 | eval/results/per_requirement_metrics.csv |
| `\BmFrrtwentyCi` | 0.329 [0.244, 0.410] | eval/results/per_requirement_metrics.csv |
| `\DenseNdcgMean` | 0.636 | eval/results/per_requirement_metrics.csv |
| `\DenseNdcgLo` | 0.530 | eval/results/per_requirement_metrics.csv |
| `\DenseNdcgHi` | 0.733 | eval/results/per_requirement_metrics.csv |
| `\DenseNdcgCi` | 0.636 [0.530, 0.733] | eval/results/per_requirement_metrics.csv |
| `\DenseMrrMean` | 0.950 | eval/results/per_requirement_metrics.csv |
| `\DenseMrrLo` | 0.850 | eval/results/per_requirement_metrics.csv |
| `\DenseMrrHi` | 1.000 | eval/results/per_requirement_metrics.csv |
| `\DenseMrrCi` | 0.950 [0.850, 1.000] | eval/results/per_requirement_metrics.csv |
| `\DensePtenMean` | 0.620 | eval/results/per_requirement_metrics.csv |
| `\DensePtenLo` | 0.490 | eval/results/per_requirement_metrics.csv |
| `\DensePtenHi` | 0.750 | eval/results/per_requirement_metrics.csv |
| `\DensePtenCi` | 0.620 [0.490, 0.750] | eval/results/per_requirement_metrics.csv |
| `\DenseRplainMean` | 0.322 | eval/results/per_requirement_metrics.csv |
| `\DenseRplainLo` | 0.276 | eval/results/per_requirement_metrics.csv |
| `\DenseRplainHi` | 0.359 | eval/results/per_requirement_metrics.csv |
| `\DenseRplainCi` | 0.322 [0.276, 0.359] | eval/results/per_requirement_metrics.csv |
| `\DenseRcapMean` | 0.620 | eval/results/per_requirement_metrics.csv |
| `\DenseRcapLo` | 0.490 | eval/results/per_requirement_metrics.csv |
| `\DenseRcapHi` | 0.750 | eval/results/per_requirement_metrics.csv |
| `\DenseRcapCi` | 0.620 [0.490, 0.750] | eval/results/per_requirement_metrics.csv |
| `\DenseFrrtenMean` | 0.380 | eval/results/per_requirement_metrics.csv |
| `\DenseFrrtenLo` | 0.250 | eval/results/per_requirement_metrics.csv |
| `\DenseFrrtenHi` | 0.510 | eval/results/per_requirement_metrics.csv |
| `\DenseFrrtenCi` | 0.380 [0.250, 0.510] | eval/results/per_requirement_metrics.csv |
| `\DenseFrrtwentyMean` | 0.501 | eval/results/per_requirement_metrics.csv |
| `\DenseFrrtwentyLo` | 0.440 | eval/results/per_requirement_metrics.csv |
| `\DenseFrrtwentyHi` | 0.560 | eval/results/per_requirement_metrics.csv |
| `\DenseFrrtwentyCi` | 0.501 [0.440, 0.560] | eval/results/per_requirement_metrics.csv |
| `\HybridNdcgMean` | 0.718 | eval/results/per_requirement_metrics.csv |
| `\HybridNdcgLo` | 0.633 | eval/results/per_requirement_metrics.csv |
| `\HybridNdcgHi` | 0.794 | eval/results/per_requirement_metrics.csv |
| `\HybridNdcgCi` | 0.718 [0.633, 0.794] | eval/results/per_requirement_metrics.csv |
| `\HybridMrrMean` | 0.900 | eval/results/per_requirement_metrics.csv |
| `\HybridMrrLo` | 0.750 | eval/results/per_requirement_metrics.csv |
| `\HybridMrrHi` | 1.000 | eval/results/per_requirement_metrics.csv |
| `\HybridMrrCi` | 0.900 [0.750, 1.000] | eval/results/per_requirement_metrics.csv |
| `\HybridPtenMean` | 0.800 | eval/results/per_requirement_metrics.csv |
| `\HybridPtenLo` | 0.710 | eval/results/per_requirement_metrics.csv |
| `\HybridPtenHi` | 0.890 | eval/results/per_requirement_metrics.csv |
| `\HybridPtenCi` | 0.800 [0.710, 0.890] | eval/results/per_requirement_metrics.csv |
| `\HybridRplainMean` | 0.428 | eval/results/per_requirement_metrics.csv |
| `\HybridRplainLo` | 0.393 | eval/results/per_requirement_metrics.csv |
| `\HybridRplainHi` | 0.465 | eval/results/per_requirement_metrics.csv |
| `\HybridRplainCi` | 0.428 [0.393, 0.465] | eval/results/per_requirement_metrics.csv |
| `\HybridRcapMean` | 0.800 | eval/results/per_requirement_metrics.csv |
| `\HybridRcapLo` | 0.710 | eval/results/per_requirement_metrics.csv |
| `\HybridRcapHi` | 0.890 | eval/results/per_requirement_metrics.csv |
| `\HybridRcapCi` | 0.800 [0.710, 0.890] | eval/results/per_requirement_metrics.csv |
| `\HybridFrrtenMean` | 0.200 | eval/results/per_requirement_metrics.csv |
| `\HybridFrrtenLo` | 0.110 | eval/results/per_requirement_metrics.csv |
| `\HybridFrrtenHi` | 0.290 | eval/results/per_requirement_metrics.csv |
| `\HybridFrrtenCi` | 0.200 [0.110, 0.290] | eval/results/per_requirement_metrics.csv |
| `\HybridFrrtwentyMean` | 0.314 | eval/results/per_requirement_metrics.csv |
| `\HybridFrrtwentyLo` | 0.233 | eval/results/per_requirement_metrics.csv |
| `\HybridFrrtwentyHi` | 0.384 | eval/results/per_requirement_metrics.csv |
| `\HybridFrrtwentyCi` | 0.314 [0.233, 0.384] | eval/results/per_requirement_metrics.csv |
| `\PropNdcgMean` | 0.749 | eval/results/per_requirement_metrics.csv |
| `\PropNdcgLo` | 0.674 | eval/results/per_requirement_metrics.csv |
| `\PropNdcgHi` | 0.818 | eval/results/per_requirement_metrics.csv |
| `\PropNdcgCi` | 0.749 [0.674, 0.818] | eval/results/per_requirement_metrics.csv |
| `\PropMrrMean` | 1.000 | eval/results/per_requirement_metrics.csv |
| `\PropMrrLo` | 1.000 | eval/results/per_requirement_metrics.csv |
| `\PropMrrHi` | 1.000 | eval/results/per_requirement_metrics.csv |
| `\PropMrrCi` | 1.000 [1.000, 1.000] | eval/results/per_requirement_metrics.csv |
| `\PropPtenMean` | 0.760 | eval/results/per_requirement_metrics.csv |
| `\PropPtenLo` | 0.630 | eval/results/per_requirement_metrics.csv |
| `\PropPtenHi` | 0.870 | eval/results/per_requirement_metrics.csv |
| `\PropPtenCi` | 0.760 [0.630, 0.870] | eval/results/per_requirement_metrics.csv |
| `\PropRplainMean` | 0.403 | eval/results/per_requirement_metrics.csv |
| `\PropRplainLo` | 0.344 | eval/results/per_requirement_metrics.csv |
| `\PropRplainHi` | 0.449 | eval/results/per_requirement_metrics.csv |
| `\PropRplainCi` | 0.403 [0.344, 0.449] | eval/results/per_requirement_metrics.csv |
| `\PropRcapMean` | 0.760 | eval/results/per_requirement_metrics.csv |
| `\PropRcapLo` | 0.630 | eval/results/per_requirement_metrics.csv |
| `\PropRcapHi` | 0.870 | eval/results/per_requirement_metrics.csv |
| `\PropRcapCi` | 0.760 [0.630, 0.870] | eval/results/per_requirement_metrics.csv |
| `\PropFrrtenMean` | 0.240 | eval/results/per_requirement_metrics.csv |
| `\PropFrrtenLo` | 0.130 | eval/results/per_requirement_metrics.csv |
| `\PropFrrtenHi` | 0.370 | eval/results/per_requirement_metrics.csv |
| `\PropFrrtenCi` | 0.240 [0.130, 0.370] | eval/results/per_requirement_metrics.csv |
| `\PropFrrtwentyMean` | 0.501 | eval/results/per_requirement_metrics.csv |
| `\PropFrrtwentyLo` | 0.440 | eval/results/per_requirement_metrics.csv |
| `\PropFrrtwentyHi` | 0.560 | eval/results/per_requirement_metrics.csv |
| `\PropFrrtwentyCi` | 0.501 [0.440, 0.560] | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyNdcgMean` | 0.763 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyNdcgLo` | 0.694 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyNdcgHi` | 0.824 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyNdcgCi` | 0.763 [0.694, 0.824] | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyMrrMean` | 1.000 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyMrrLo` | 1.000 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyMrrHi` | 1.000 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyMrrCi` | 1.000 [1.000, 1.000] | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyPtenMean` | 0.770 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyPtenLo` | 0.640 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyPtenHi` | 0.860 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyPtenCi` | 0.770 [0.640, 0.860] | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyRplainMean` | 0.411 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyRplainLo` | 0.351 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyRplainHi` | 0.458 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyRplainCi` | 0.411 [0.351, 0.458] | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyRcapMean` | 0.770 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyRcapLo` | 0.640 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyRcapHi` | 0.860 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyRcapCi` | 0.770 [0.640, 0.860] | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyFrrtenMean` | 0.230 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyFrrtenLo` | 0.140 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyFrrtenHi` | 0.360 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyFrrtenCi` | 0.230 [0.140, 0.360] | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyFrrtwentyMean` | 0.308 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyFrrtwentyLo` | 0.237 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyFrrtwentyHi` | 0.376 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyFrrtwentyCi` | 0.308 [0.237, 0.376] | eval/results/per_requirement_metrics.csv |
| `\PropOracleNdcgMean` | 0.755 | eval/results/per_requirement_metrics.csv |
| `\PropOracleNdcgLo` | 0.679 | eval/results/per_requirement_metrics.csv |
| `\PropOracleNdcgHi` | 0.824 | eval/results/per_requirement_metrics.csv |
| `\PropOracleNdcgCi` | 0.755 [0.679, 0.824] | eval/results/per_requirement_metrics.csv |
| `\PropOracleMrrMean` | 1.000 | eval/results/per_requirement_metrics.csv |
| `\PropOracleMrrLo` | 1.000 | eval/results/per_requirement_metrics.csv |
| `\PropOracleMrrHi` | 1.000 | eval/results/per_requirement_metrics.csv |
| `\PropOracleMrrCi` | 1.000 [1.000, 1.000] | eval/results/per_requirement_metrics.csv |
| `\PropOraclePtenMean` | 0.770 | eval/results/per_requirement_metrics.csv |
| `\PropOraclePtenLo` | 0.640 | eval/results/per_requirement_metrics.csv |
| `\PropOraclePtenHi` | 0.880 | eval/results/per_requirement_metrics.csv |
| `\PropOraclePtenCi` | 0.770 [0.640, 0.880] | eval/results/per_requirement_metrics.csv |
| `\PropOracleRplainMean` | 0.409 | eval/results/per_requirement_metrics.csv |
| `\PropOracleRplainLo` | 0.346 | eval/results/per_requirement_metrics.csv |
| `\PropOracleRplainHi` | 0.458 | eval/results/per_requirement_metrics.csv |
| `\PropOracleRplainCi` | 0.409 [0.346, 0.458] | eval/results/per_requirement_metrics.csv |
| `\PropOracleRcapMean` | 0.770 | eval/results/per_requirement_metrics.csv |
| `\PropOracleRcapLo` | 0.640 | eval/results/per_requirement_metrics.csv |
| `\PropOracleRcapHi` | 0.880 | eval/results/per_requirement_metrics.csv |
| `\PropOracleRcapCi` | 0.770 [0.640, 0.880] | eval/results/per_requirement_metrics.csv |
| `\PropOracleFrrtenMean` | 0.230 | eval/results/per_requirement_metrics.csv |
| `\PropOracleFrrtenLo` | 0.120 | eval/results/per_requirement_metrics.csv |
| `\PropOracleFrrtenHi` | 0.360 | eval/results/per_requirement_metrics.csv |
| `\PropOracleFrrtenCi` | 0.230 [0.120, 0.360] | eval/results/per_requirement_metrics.csv |
| `\PropOracleFrrtwentyMean` | 0.495 | eval/results/per_requirement_metrics.csv |
| `\PropOracleFrrtwentyLo` | 0.437 | eval/results/per_requirement_metrics.csv |
| `\PropOracleFrrtwentyHi` | 0.554 | eval/results/per_requirement_metrics.csv |
| `\PropOracleFrrtwentyCi` | 0.495 [0.437, 0.554] | eval/results/per_requirement_metrics.csv |
| `\PropNofairNdcgMean` | 0.755 | eval/results/per_requirement_metrics.csv |
| `\PropNofairNdcgLo` | 0.661 | eval/results/per_requirement_metrics.csv |
| `\PropNofairNdcgHi` | 0.838 | eval/results/per_requirement_metrics.csv |
| `\PropNofairNdcgCi` | 0.755 [0.661, 0.838] | eval/results/per_requirement_metrics.csv |
| `\PropNofairMrrMean` | 0.950 | eval/results/per_requirement_metrics.csv |
| `\PropNofairMrrLo` | 0.850 | eval/results/per_requirement_metrics.csv |
| `\PropNofairMrrHi` | 1.000 | eval/results/per_requirement_metrics.csv |
| `\PropNofairMrrCi` | 0.950 [0.850, 1.000] | eval/results/per_requirement_metrics.csv |
| `\PropNofairPtenMean` | 0.760 | eval/results/per_requirement_metrics.csv |
| `\PropNofairPtenLo` | 0.620 | eval/results/per_requirement_metrics.csv |
| `\PropNofairPtenHi` | 0.880 | eval/results/per_requirement_metrics.csv |
| `\PropNofairPtenCi` | 0.760 [0.620, 0.880] | eval/results/per_requirement_metrics.csv |
| `\PropNofairRplainMean` | 0.403 | eval/results/per_requirement_metrics.csv |
| `\PropNofairRplainLo` | 0.337 | eval/results/per_requirement_metrics.csv |
| `\PropNofairRplainHi` | 0.462 | eval/results/per_requirement_metrics.csv |
| `\PropNofairRplainCi` | 0.403 [0.337, 0.462] | eval/results/per_requirement_metrics.csv |
| `\PropNofairRcapMean` | 0.760 | eval/results/per_requirement_metrics.csv |
| `\PropNofairRcapLo` | 0.620 | eval/results/per_requirement_metrics.csv |
| `\PropNofairRcapHi` | 0.880 | eval/results/per_requirement_metrics.csv |
| `\PropNofairRcapCi` | 0.760 [0.620, 0.880] | eval/results/per_requirement_metrics.csv |
| `\PropNofairFrrtenMean` | 0.240 | eval/results/per_requirement_metrics.csv |
| `\PropNofairFrrtenLo` | 0.120 | eval/results/per_requirement_metrics.csv |
| `\PropNofairFrrtenHi` | 0.380 | eval/results/per_requirement_metrics.csv |
| `\PropNofairFrrtenCi` | 0.240 [0.120, 0.380] | eval/results/per_requirement_metrics.csv |
| `\PropNofairFrrtwentyMean` | 0.495 | eval/results/per_requirement_metrics.csv |
| `\PropNofairFrrtwentyLo` | 0.437 | eval/results/per_requirement_metrics.csv |
| `\PropNofairFrrtwentyHi` | 0.554 | eval/results/per_requirement_metrics.csv |
| `\PropNofairFrrtwentyCi` | 0.495 [0.437, 0.554] | eval/results/per_requirement_metrics.csv |
| `\PropFirstQualified` | 10 | eval/results/per_requirement_metrics.csv |
| `\PropMrrOneTotal` | 10 | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseNdcgDiff` | +0.113 | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseNdcgDiffCi` | 0.113 [0.054, 0.177] | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseNdcgWlt` | 9/1/0 | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseNdcgVerdict` | better | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseMrrDiff` | +0.050 | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseMrrDiffCi` | 0.050 [0.000, 0.150] | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseMrrWlt` | 1/0/9 | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseMrrVerdict` | not distinguishable | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseRcapDiff` | +0.140 | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseRcapDiffCi` | 0.140 [0.080, 0.200] | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseRcapWlt` | 8/0/2 | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseRcapVerdict` | better | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseFrrtwentyDiff` | +0.000 | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseFrrtwentyDiffCi` | 0.000 [0.000, 0.000] | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseFrrtwentyWlt` | 0/0/10 | eval/results/per_requirement_metrics.csv |
| `\PropVsDenseFrrtwentyVerdict` | not distinguishable | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridNdcgDiff` | +0.031 | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridNdcgDiffCi` | 0.031 [-0.031, 0.093] | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridNdcgWlt` | 7/3/0 | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridNdcgVerdict` | not distinguishable | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridMrrDiff` | +0.100 | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridMrrDiffCi` | 0.100 [0.000, 0.250] | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridMrrWlt` | 2/0/8 | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridMrrVerdict` | not distinguishable | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridRcapDiff` | -0.040 | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridRcapDiffCi` | -0.040 [-0.120, 0.040] | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridRcapWlt` | 1/3/6 | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridRcapVerdict` | not distinguishable | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridFrrtwentyDiff` | +0.187 | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridFrrtwentyDiffCi` | 0.187 [0.131, 0.242] | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridFrrtwentyWlt` | 0/10/0 | eval/results/per_requirement_metrics.csv |
| `\PropVsHybridFrrtwentyVerdict` | worse | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynNdcgDiff` | +0.111 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynNdcgDiffCi` | 0.111 [0.050, 0.177] | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynNdcgWlt` | 9/1/0 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynNdcgVerdict` | better | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynMrrDiff` | +0.150 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynMrrDiffCi` | 0.150 [0.000, 0.300] | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynMrrWlt` | 3/0/7 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynMrrVerdict` | not distinguishable | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynRcapDiff` | +0.030 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynRcapDiffCi` | 0.030 [-0.080, 0.130] | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynRcapWlt` | 5/2/3 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynRcapVerdict` | not distinguishable | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynFrrtwentyDiff` | +0.162 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynFrrtwentyDiffCi` | 0.162 [0.045, 0.264] | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynFrrtwentyWlt` | 1/9/0 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsSynFrrtwentyVerdict` | worse | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictNdcgDiff` | +0.270 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictNdcgDiffCi` | 0.270 [0.099, 0.477] | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictNdcgWlt` | 9/1/0 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictNdcgVerdict` | better | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictMrrDiff` | +0.350 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictMrrDiffCi` | 0.350 [0.100, 0.600] | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictMrrWlt` | 5/0/5 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictMrrVerdict` | better | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictRcapDiff` | +0.170 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictRcapDiffCi` | 0.170 [-0.040, 0.410] | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictRcapWlt` | 4/2/4 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictRcapVerdict` | not distinguishable | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictFrrtwentyDiff` | -0.028 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictFrrtwentyDiffCi` | -0.028 [-0.219, 0.149] | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictFrrtwentyWlt` | 4/5/1 | eval/results/per_requirement_metrics.csv |
| `\PropVsAtsStrictFrrtwentyVerdict` | not distinguishable | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyVsPropNdcgDiff` | +0.014 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyVsPropNdcgDiffCi` | 0.014 [-0.001, 0.041] | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyVsPropNdcgWlt` | 3/1/6 | eval/results/per_requirement_metrics.csv |
| `\PropKfiftyVsPropNdcgVerdict` | not distinguishable | eval/results/per_requirement_metrics.csv |
| `\PropOracleVsPropNdcgDiff` | +0.005 | eval/results/per_requirement_metrics.csv |
| `\PropOracleVsPropNdcgDiffCi` | 0.005 [0.000, 0.016] | eval/results/per_requirement_metrics.csv |
| `\PropOracleVsPropNdcgWlt` | 1/0/9 | eval/results/per_requirement_metrics.csv |
| `\PropOracleVsPropNdcgVerdict` | not distinguishable | eval/results/per_requirement_metrics.csv |
| `\PropNofairVsPropNdcgDiff` | +0.006 | eval/results/per_requirement_metrics.csv |
| `\PropNofairVsPropNdcgDiffCi` | 0.006 [-0.028, 0.034] | eval/results/per_requirement_metrics.csv |
| `\PropNofairVsPropNdcgWlt` | 4/2/4 | eval/results/per_requirement_metrics.csv |
| `\PropNofairVsPropNdcgVerdict` | not distinguishable | eval/results/per_requirement_metrics.csv |
| `\AtsStrictRejFail` | 106 | eval/results/baselines.json |
| `\AtsStrictRejTotal` | 190 | eval/results/baselines.json |
| `\AtsStrictRejPct` | 56 | eval/results/baselines.json |
| `\AtsStrictPassMean` | 10.5 | eval/results/baselines.json |
| `\AtsStrictPassMin` | 0 | eval/results/baselines.json |
| `\AtsStrictPassMax` | 20 | eval/results/baselines.json |
| `\AtsStrictRejStandardFail` | 17 | eval/results/baselines.json |
| `\AtsStrictRejStandardTotal` | 77 | eval/results/baselines.json |
| `\AtsStrictRejStandardPct` | 22 | eval/results/baselines.json |
| `\AtsStrictRejParaphrasedFail` | 51 | eval/results/baselines.json |
| `\AtsStrictRejParaphrasedTotal` | 51 | eval/results/baselines.json |
| `\AtsStrictRejParaphrasedPct` | 100 | eval/results/baselines.json |
| `\AtsStrictRejImpliedFail` | 10 | eval/results/baselines.json |
| `\AtsStrictRejImpliedTotal` | 18 | eval/results/baselines.json |
| `\AtsStrictRejImpliedPct` | 56 | eval/results/baselines.json |
| `\AtsStrictRejAbbreviatedNoisyFail` | 18 | eval/results/baselines.json |
| `\AtsStrictRejAbbreviatedNoisyTotal` | 21 | eval/results/baselines.json |
| `\AtsStrictRejAbbreviatedNoisyPct` | 86 | eval/results/baselines.json |
| `\AtsStrictRejSparseStrongFail` | 4 | eval/results/baselines.json |
| `\AtsStrictRejSparseStrongTotal` | 11 | eval/results/baselines.json |
| `\AtsStrictRejSparseStrongPct` | 36 | eval/results/baselines.json |
| `\AtsStrictRejIneligibleStrongFail` | 0 | eval/results/baselines.json |
| `\AtsStrictRejIneligibleStrongTotal` | 1 | eval/results/baselines.json |
| `\AtsStrictRejIneligibleStrongPct` | 0 | eval/results/baselines.json |
| `\AtsStrictRejGeneralistAverageFail` | 3 | eval/results/baselines.json |
| `\AtsStrictRejGeneralistAverageTotal` | 8 | eval/results/baselines.json |
| `\AtsStrictRejGeneralistAveragePct` | 38 | eval/results/baselines.json |
| `\AtsStrictRejStuffedWeakFail` | 3 | eval/results/baselines.json |
| `\AtsStrictRejStuffedWeakTotal` | 3 | eval/results/baselines.json |
| `\AtsStrictRejStuffedWeakPct` | 100 | eval/results/baselines.json |
| `\AtsLenientRejFail` | 63 | eval/results/baselines.json |
| `\AtsLenientRejTotal` | 190 | eval/results/baselines.json |
| `\AtsLenientRejPct` | 33 | eval/results/baselines.json |
| `\AtsLenientPassMean` | 41.4 | eval/results/baselines.json |
| `\AtsLenientPassMin` | 17 | eval/results/baselines.json |
| `\AtsLenientPassMax` | 79 | eval/results/baselines.json |
| `\AtsLenientRejStandardFail` | 0 | eval/results/baselines.json |
| `\AtsLenientRejStandardTotal` | 77 | eval/results/baselines.json |
| `\AtsLenientRejStandardPct` | 0 | eval/results/baselines.json |
| `\AtsLenientRejParaphrasedFail` | 51 | eval/results/baselines.json |
| `\AtsLenientRejParaphrasedTotal` | 51 | eval/results/baselines.json |
| `\AtsLenientRejParaphrasedPct` | 100 | eval/results/baselines.json |
| `\AtsLenientRejImpliedFail` | 6 | eval/results/baselines.json |
| `\AtsLenientRejImpliedTotal` | 18 | eval/results/baselines.json |
| `\AtsLenientRejImpliedPct` | 33 | eval/results/baselines.json |
| `\AtsLenientRejAbbreviatedNoisyFail` | 6 | eval/results/baselines.json |
| `\AtsLenientRejAbbreviatedNoisyTotal` | 21 | eval/results/baselines.json |
| `\AtsLenientRejAbbreviatedNoisyPct` | 29 | eval/results/baselines.json |
| `\AtsLenientRejSparseStrongFail` | 0 | eval/results/baselines.json |
| `\AtsLenientRejSparseStrongTotal` | 11 | eval/results/baselines.json |
| `\AtsLenientRejSparseStrongPct` | 0 | eval/results/baselines.json |
| `\AtsLenientRejIneligibleStrongFail` | 0 | eval/results/baselines.json |
| `\AtsLenientRejIneligibleStrongTotal` | 1 | eval/results/baselines.json |
| `\AtsLenientRejIneligibleStrongPct` | 0 | eval/results/baselines.json |
| `\AtsLenientRejGeneralistAverageFail` | 0 | eval/results/baselines.json |
| `\AtsLenientRejGeneralistAverageTotal` | 8 | eval/results/baselines.json |
| `\AtsLenientRejGeneralistAveragePct` | 0 | eval/results/baselines.json |
| `\AtsLenientRejStuffedWeakFail` | 0 | eval/results/baselines.json |
| `\AtsLenientRejStuffedWeakTotal` | 3 | eval/results/baselines.json |
| `\AtsLenientRejStuffedWeakPct` | 0 | eval/results/baselines.json |
| `\AtsSynRejFail` | 68 | eval/results/baselines.json |
| `\AtsSynRejTotal` | 190 | eval/results/baselines.json |
| `\AtsSynRejPct` | 36 | eval/results/baselines.json |
| `\AtsSynPassMean` | 16.5 | eval/results/baselines.json |
| `\AtsSynPassMin` | 3 | eval/results/baselines.json |
| `\AtsSynPassMax` | 23 | eval/results/baselines.json |
| `\AtsSynRejStandardFail` | 4 | eval/results/baselines.json |
| `\AtsSynRejStandardTotal` | 77 | eval/results/baselines.json |
| `\AtsSynRejStandardPct` | 5 | eval/results/baselines.json |
| `\AtsSynRejParaphrasedFail` | 51 | eval/results/baselines.json |
| `\AtsSynRejParaphrasedTotal` | 51 | eval/results/baselines.json |
| `\AtsSynRejParaphrasedPct` | 100 | eval/results/baselines.json |
| `\AtsSynRejImpliedFail` | 8 | eval/results/baselines.json |
| `\AtsSynRejImpliedTotal` | 18 | eval/results/baselines.json |
| `\AtsSynRejImpliedPct` | 44 | eval/results/baselines.json |
| `\AtsSynRejAbbreviatedNoisyFail` | 1 | eval/results/baselines.json |
| `\AtsSynRejAbbreviatedNoisyTotal` | 21 | eval/results/baselines.json |
| `\AtsSynRejAbbreviatedNoisyPct` | 5 | eval/results/baselines.json |
| `\AtsSynRejSparseStrongFail` | 0 | eval/results/baselines.json |
| `\AtsSynRejSparseStrongTotal` | 11 | eval/results/baselines.json |
| `\AtsSynRejSparseStrongPct` | 0 | eval/results/baselines.json |
| `\AtsSynRejIneligibleStrongFail` | 0 | eval/results/baselines.json |
| `\AtsSynRejIneligibleStrongTotal` | 1 | eval/results/baselines.json |
| `\AtsSynRejIneligibleStrongPct` | 0 | eval/results/baselines.json |
| `\AtsSynRejGeneralistAverageFail` | 1 | eval/results/baselines.json |
| `\AtsSynRejGeneralistAverageTotal` | 8 | eval/results/baselines.json |
| `\AtsSynRejGeneralistAveragePct` | 12 | eval/results/baselines.json |
| `\AtsSynRejStuffedWeakFail` | 3 | eval/results/baselines.json |
| `\AtsSynRejStuffedWeakTotal` | 3 | eval/results/baselines.json |
| `\AtsSynRejStuffedWeakPct` | 100 | eval/results/baselines.json |
| `\PoolPropTwenty` | 89 | eval/results/retrieval.csv |
| `\PoolPropFifty` | 130 | eval/results/retrieval.csv |
| `\PoolOracleTwenty` | 89 | eval/results/retrieval.csv |
| `\PoolOracleFifty` | 130 | eval/results/retrieval.csv |
| `\ParserFalseRej` | 0 | eval/results/retrieval.csv |
| `\PoolQualifiedTotal` | 190 | eval/results/retrieval.csv |
| `\PoolBFiveTwenty` | 122 | eval/results/posthoc_b5_metrics.csv |
| `\PoolAtsStrictStandardFound` | 60 | eval/results/archetype_table.csv |
| `\PoolAtsStrictStandardPct` | 78 | eval/results/archetype_table.csv |
| `\PoolAtsStrictParaphrasedFound` | 0 | eval/results/archetype_table.csv |
| `\PoolAtsStrictParaphrasedPct` | 0 | eval/results/archetype_table.csv |
| `\PoolAtsStrictImpliedFound` | 8 | eval/results/archetype_table.csv |
| `\PoolAtsStrictImpliedPct` | 44 | eval/results/archetype_table.csv |
| `\PoolAtsStrictAbbreviatedNoisyFound` | 3 | eval/results/archetype_table.csv |
| `\PoolAtsStrictAbbreviatedNoisyPct` | 14 | eval/results/archetype_table.csv |
| `\PoolAtsStrictSparseStrongFound` | 7 | eval/results/archetype_table.csv |
| `\PoolAtsStrictSparseStrongPct` | 64 | eval/results/archetype_table.csv |
| `\PoolAtsStrictIneligibleStrongFound` | 1 | eval/results/archetype_table.csv |
| `\PoolAtsStrictIneligibleStrongPct` | 100 | eval/results/archetype_table.csv |
| `\PoolAtsStrictGeneralistAverageFound` | 5 | eval/results/archetype_table.csv |
| `\PoolAtsStrictGeneralistAveragePct` | 62 | eval/results/archetype_table.csv |
| `\PoolAtsStrictStuffedWeakFound` | 0 | eval/results/archetype_table.csv |
| `\PoolAtsStrictStuffedWeakPct` | 0 | eval/results/archetype_table.csv |
| `\PoolAtsLenientStandardFound` | 71 | eval/results/archetype_table.csv |
| `\PoolAtsLenientStandardPct` | 92 | eval/results/archetype_table.csv |
| `\PoolAtsLenientParaphrasedFound` | 0 | eval/results/archetype_table.csv |
| `\PoolAtsLenientParaphrasedPct` | 0 | eval/results/archetype_table.csv |
| `\PoolAtsLenientImpliedFound` | 10 | eval/results/archetype_table.csv |
| `\PoolAtsLenientImpliedPct` | 56 | eval/results/archetype_table.csv |
| `\PoolAtsLenientAbbreviatedNoisyFound` | 8 | eval/results/archetype_table.csv |
| `\PoolAtsLenientAbbreviatedNoisyPct` | 38 | eval/results/archetype_table.csv |
| `\PoolAtsLenientSparseStrongFound` | 11 | eval/results/archetype_table.csv |
| `\PoolAtsLenientSparseStrongPct` | 100 | eval/results/archetype_table.csv |
| `\PoolAtsLenientIneligibleStrongFound` | 1 | eval/results/archetype_table.csv |
| `\PoolAtsLenientIneligibleStrongPct` | 100 | eval/results/archetype_table.csv |
| `\PoolAtsLenientGeneralistAverageFound` | 3 | eval/results/archetype_table.csv |
| `\PoolAtsLenientGeneralistAveragePct` | 38 | eval/results/archetype_table.csv |
| `\PoolAtsLenientStuffedWeakFound` | 2 | eval/results/archetype_table.csv |
| `\PoolAtsLenientStuffedWeakPct` | 67 | eval/results/archetype_table.csv |
| `\PoolAtsSynStandardFound` | 72 | eval/results/archetype_table.csv |
| `\PoolAtsSynStandardPct` | 94 | eval/results/archetype_table.csv |
| `\PoolAtsSynParaphrasedFound` | 0 | eval/results/archetype_table.csv |
| `\PoolAtsSynParaphrasedPct` | 0 | eval/results/archetype_table.csv |
| `\PoolAtsSynImpliedFound` | 10 | eval/results/archetype_table.csv |
| `\PoolAtsSynImpliedPct` | 56 | eval/results/archetype_table.csv |
| `\PoolAtsSynAbbreviatedNoisyFound` | 19 | eval/results/archetype_table.csv |
| `\PoolAtsSynAbbreviatedNoisyPct` | 90 | eval/results/archetype_table.csv |
| `\PoolAtsSynSparseStrongFound` | 11 | eval/results/archetype_table.csv |
| `\PoolAtsSynSparseStrongPct` | 100 | eval/results/archetype_table.csv |
| `\PoolAtsSynIneligibleStrongFound` | 1 | eval/results/archetype_table.csv |
| `\PoolAtsSynIneligibleStrongPct` | 100 | eval/results/archetype_table.csv |
| `\PoolAtsSynGeneralistAverageFound` | 5 | eval/results/archetype_table.csv |
| `\PoolAtsSynGeneralistAveragePct` | 62 | eval/results/archetype_table.csv |
| `\PoolAtsSynStuffedWeakFound` | 0 | eval/results/archetype_table.csv |
| `\PoolAtsSynStuffedWeakPct` | 0 | eval/results/archetype_table.csv |
| `\PoolBmStandardFound` | 76 | eval/results/archetype_table.csv |
| `\PoolBmStandardPct` | 99 | eval/results/archetype_table.csv |
| `\PoolBmParaphrasedFound` | 1 | eval/results/archetype_table.csv |
| `\PoolBmParaphrasedPct` | 2 | eval/results/archetype_table.csv |
| `\PoolBmImpliedFound` | 17 | eval/results/archetype_table.csv |
| `\PoolBmImpliedPct` | 94 | eval/results/archetype_table.csv |
| `\PoolBmAbbreviatedNoisyFound` | 9 | eval/results/archetype_table.csv |
| `\PoolBmAbbreviatedNoisyPct` | 43 | eval/results/archetype_table.csv |
| `\PoolBmSparseStrongFound` | 9 | eval/results/archetype_table.csv |
| `\PoolBmSparseStrongPct` | 82 | eval/results/archetype_table.csv |
| `\PoolBmIneligibleStrongFound` | 1 | eval/results/archetype_table.csv |
| `\PoolBmIneligibleStrongPct` | 100 | eval/results/archetype_table.csv |
| `\PoolBmGeneralistAverageFound` | 6 | eval/results/archetype_table.csv |
| `\PoolBmGeneralistAveragePct` | 75 | eval/results/archetype_table.csv |
| `\PoolBmStuffedWeakFound` | 0 | eval/results/archetype_table.csv |
| `\PoolBmStuffedWeakPct` | 0 | eval/results/archetype_table.csv |
| `\PoolDenseStandardFound` | 47 | eval/results/archetype_table.csv |
| `\PoolDenseStandardPct` | 61 | eval/results/archetype_table.csv |
| `\PoolDenseParaphrasedFound` | 3 | eval/results/archetype_table.csv |
| `\PoolDenseParaphrasedPct` | 6 | eval/results/archetype_table.csv |
| `\PoolDenseImpliedFound` | 14 | eval/results/archetype_table.csv |
| `\PoolDenseImpliedPct` | 78 | eval/results/archetype_table.csv |
| `\PoolDenseAbbreviatedNoisyFound` | 11 | eval/results/archetype_table.csv |
| `\PoolDenseAbbreviatedNoisyPct` | 52 | eval/results/archetype_table.csv |
| `\PoolDenseSparseStrongFound` | 9 | eval/results/archetype_table.csv |
| `\PoolDenseSparseStrongPct` | 82 | eval/results/archetype_table.csv |
| `\PoolDenseIneligibleStrongFound` | 1 | eval/results/archetype_table.csv |
| `\PoolDenseIneligibleStrongPct` | 100 | eval/results/archetype_table.csv |
| `\PoolDenseGeneralistAverageFound` | 4 | eval/results/archetype_table.csv |
| `\PoolDenseGeneralistAveragePct` | 50 | eval/results/archetype_table.csv |
| `\PoolDenseStuffedWeakFound` | 0 | eval/results/archetype_table.csv |
| `\PoolDenseStuffedWeakPct` | 0 | eval/results/archetype_table.csv |
| `\PoolHybridStandardFound` | 72 | eval/results/archetype_table.csv |
| `\PoolHybridStandardPct` | 94 | eval/results/archetype_table.csv |
| `\PoolHybridParaphrasedFound` | 2 | eval/results/archetype_table.csv |
| `\PoolHybridParaphrasedPct` | 4 | eval/results/archetype_table.csv |
| `\PoolHybridImpliedFound` | 17 | eval/results/archetype_table.csv |
| `\PoolHybridImpliedPct` | 94 | eval/results/archetype_table.csv |
| `\PoolHybridAbbreviatedNoisyFound` | 12 | eval/results/archetype_table.csv |
| `\PoolHybridAbbreviatedNoisyPct` | 57 | eval/results/archetype_table.csv |
| `\PoolHybridSparseStrongFound` | 11 | eval/results/archetype_table.csv |
| `\PoolHybridSparseStrongPct` | 100 | eval/results/archetype_table.csv |
| `\PoolHybridIneligibleStrongFound` | 1 | eval/results/archetype_table.csv |
| `\PoolHybridIneligibleStrongPct` | 100 | eval/results/archetype_table.csv |
| `\PoolHybridGeneralistAverageFound` | 7 | eval/results/archetype_table.csv |
| `\PoolHybridGeneralistAveragePct` | 88 | eval/results/archetype_table.csv |
| `\PoolHybridStuffedWeakFound` | 0 | eval/results/archetype_table.csv |
| `\PoolHybridStuffedWeakPct` | 0 | eval/results/archetype_table.csv |
| `\PoolPropStandardFound` | 47 | eval/results/archetype_table.csv |
| `\PoolPropStandardPct` | 61 | eval/results/archetype_table.csv |
| `\PoolPropParaphrasedFound` | 3 | eval/results/archetype_table.csv |
| `\PoolPropParaphrasedPct` | 6 | eval/results/archetype_table.csv |
| `\PoolPropImpliedFound` | 14 | eval/results/archetype_table.csv |
| `\PoolPropImpliedPct` | 78 | eval/results/archetype_table.csv |
| `\PoolPropAbbreviatedNoisyFound` | 11 | eval/results/archetype_table.csv |
| `\PoolPropAbbreviatedNoisyPct` | 52 | eval/results/archetype_table.csv |
| `\PoolPropSparseStrongFound` | 9 | eval/results/archetype_table.csv |
| `\PoolPropSparseStrongPct` | 82 | eval/results/archetype_table.csv |
| `\PoolPropIneligibleStrongFound` | 1 | eval/results/archetype_table.csv |
| `\PoolPropIneligibleStrongPct` | 100 | eval/results/archetype_table.csv |
| `\PoolPropGeneralistAverageFound` | 4 | eval/results/archetype_table.csv |
| `\PoolPropGeneralistAveragePct` | 50 | eval/results/archetype_table.csv |
| `\PoolPropStuffedWeakFound` | 0 | eval/results/archetype_table.csv |
| `\PoolPropStuffedWeakPct` | 0 | eval/results/archetype_table.csv |
| `\PoolBFiveStandardFound` | 72 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveStandardPct` | 94 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveParaphrasedFound` | 2 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveParaphrasedPct` | 4 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveImpliedFound` | 17 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveImpliedPct` | 94 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveAbbreviatedNoisyFound` | 12 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveAbbreviatedNoisyPct` | 57 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveSparseStrongFound` | 11 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveSparseStrongPct` | 100 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveIneligibleStrongFound` | 1 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveIneligibleStrongPct` | 100 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveGeneralistAverageFound` | 7 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveGeneralistAveragePct` | 88 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveStuffedWeakFound` | 0 | eval/results/posthoc_b5_archetype.csv |
| `\PoolBFiveStuffedWeakPct` | 0 | eval/results/posthoc_b5_archetype.csv |
| `\AtsSynRejPctExact` | 41 | paper/recheck_report.md (independent recheck: exact taxonomy aliases only, no substring mapping of 'Linux Administration'); typed here, not computed by this script |
| `\ArchParaphrasedQualified` | 51 | eval/results/archetype_table.csv |
| `\ParserDevMinCgpa` | 100 | eval/results/parser_accuracy.json |
| `\ParserDevMaxBacklogs` | 100 | eval/results/parser_accuracy.json |
| `\ParserDevAllowedBranches` | 100 | eval/results/parser_accuracy.json |
| `\ParserDevEligPct` | 100 | eval/results/parser_accuracy.json |
| `\ParserDevMustPrecPct` | 100 | eval/results/parser_accuracy.json |
| `\ParserDevMustRecPct` | 93 | eval/results/parser_accuracy.json |
| `\ParserDevMismatchReqs` | R04, R12 | eval/results/parser_accuracy.json |
| `\ParserDevMismatchCount` | 2 | eval/results/parser_accuracy.json |
| `\ParserTestMinCgpa` | 100 | eval/results/parser_accuracy.json |
| `\ParserTestMaxBacklogs` | 100 | eval/results/parser_accuracy.json |
| `\ParserTestAllowedBranches` | 100 | eval/results/parser_accuracy.json |
| `\ParserTestEligPct` | 100 | eval/results/parser_accuracy.json |
| `\ParserTestMustPrecPct` | 96 | eval/results/parser_accuracy.json |
| `\ParserTestMustRecPct` | 93 | eval/results/parser_accuracy.json |
| `\ParserTestMismatchReqs` | R03, R06, R10 | eval/results/parser_accuracy.json |
| `\ParserTestMismatchCount` | 3 | eval/results/parser_accuracy.json |
| `\ParserEligFieldsCorrect` | 45 | eval/results/parser_accuracy.json |
| `\ParserEligFieldsTotal` | 45 | eval/results/parser_accuracy.json |
| `\SpotN` | 20 | data/spotcheck_labeled.csv |
| `\SpotKappa` | 0.962 | data/spotcheck_labeled.csv |
| `\SpotExactPct` | 90 | data/spotcheck_labeled.csv |
| `\SpotBinaryPct` | 95 | data/spotcheck_labeled.csv |
| `\SpotDisagreements` | 2 | data/spotcheck_labeled.csv |
| `\BFiveDevNdcgCi` | 0.724 [0.574, 0.838] | eval/results/posthoc_b5_summary.csv |
| `\BFiveDevNdcgMean` | 0.724 | eval/results/posthoc_b5_summary.csv |
| `\BFiveDevMrrCi` | 1.000 [1.000, 1.000] | eval/results/posthoc_b5_summary.csv |
| `\BFiveDevMrrMean` | 1.000 | eval/results/posthoc_b5_summary.csv |
| `\BFiveDevPtenCi` | 0.740 [0.540, 0.920] | eval/results/posthoc_b5_summary.csv |
| `\BFiveDevPtenMean` | 0.740 | eval/results/posthoc_b5_summary.csv |
| `\BFiveDevRcapCi` | 0.740 [0.540, 0.920] | eval/results/posthoc_b5_summary.csv |
| `\BFiveDevRcapMean` | 0.740 | eval/results/posthoc_b5_summary.csv |
| `\BFiveDevFrrtenCi` | 0.260 [0.080, 0.460] | eval/results/posthoc_b5_summary.csv |
| `\BFiveDevFrrtenMean` | 0.260 | eval/results/posthoc_b5_summary.csv |
| `\BFiveDevFrrtwentyCi` | 0.393 [0.290, 0.477] | eval/results/posthoc_b5_summary.csv |
| `\BFiveDevFrrtwentyMean` | 0.393 | eval/results/posthoc_b5_summary.csv |
| `\BFiveTestNdcgCi` | 0.772 [0.707, 0.824] | eval/results/posthoc_b5_summary.csv |
| `\BFiveTestNdcgMean` | 0.772 | eval/results/posthoc_b5_summary.csv |
| `\BFiveTestMrrCi` | 1.000 [1.000, 1.000] | eval/results/posthoc_b5_summary.csv |
| `\BFiveTestMrrMean` | 1.000 | eval/results/posthoc_b5_summary.csv |
| `\BFiveTestPtenCi` | 0.860 [0.790, 0.930] | eval/results/posthoc_b5_summary.csv |
| `\BFiveTestPtenMean` | 0.860 | eval/results/posthoc_b5_summary.csv |
| `\BFiveTestRcapCi` | 0.860 [0.790, 0.930] | eval/results/posthoc_b5_summary.csv |
| `\BFiveTestRcapMean` | 0.860 | eval/results/posthoc_b5_summary.csv |
| `\BFiveTestFrrtenCi` | 0.140 [0.070, 0.210] | eval/results/posthoc_b5_summary.csv |
| `\BFiveTestFrrtenMean` | 0.140 | eval/results/posthoc_b5_summary.csv |
| `\BFiveTestFrrtwentyCi` | 0.314 [0.233, 0.384] | eval/results/posthoc_b5_summary.csv |
| `\BFiveTestFrrtwentyMean` | 0.314 | eval/results/posthoc_b5_summary.csv |
| `\BFiveVsPropNdcgDiffCi` | 0.022 [-0.047, 0.094] | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsPropNdcgWlt` | 5/5/0 | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsPropNdcgVerdict` | not distinguishable | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsPropMrrDiffCi` | 0.000 [0.000, 0.000] | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsPropMrrWlt` | 0/0/10 | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsPropMrrVerdict` | not distinguishable | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsPropRcapDiffCi` | 0.100 [-0.000, 0.210] | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsPropRcapWlt` | 6/1/3 | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsPropRcapVerdict` | not distinguishable | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsPropFrrtwentyDiffCi` | -0.187 [-0.242, -0.131] | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsPropFrrtwentyWlt` | 10/0/0 | eval/results/posthoc_b5_paired.csv (corrected from the CSV: lower is better) |
| `\BFiveVsPropFrrtwentyVerdict` | better | eval/results/posthoc_b5_paired.csv (corrected from the CSV: lower is better) |
| `\BFiveVsHybridNdcgDiffCi` | 0.053 [0.000, 0.107] | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsHybridNdcgWlt` | 6/2/2 | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsHybridNdcgVerdict` | better | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsHybridMrrDiffCi` | 0.100 [0.000, 0.250] | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsHybridMrrWlt` | 2/0/8 | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsHybridMrrVerdict` | not distinguishable | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsHybridRcapDiffCi` | 0.060 [0.020, 0.100] | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsHybridRcapWlt` | 5/0/5 | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsHybridRcapVerdict` | better | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsHybridFrrtwentyDiffCi` | 0.000 [0.000, 0.000] | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsHybridFrrtwentyWlt` | 0/0/10 | eval/results/posthoc_b5_paired.csv (corrected from the CSV: lower is better) |
| `\BFiveVsHybridFrrtwentyVerdict` | not distinguishable | eval/results/posthoc_b5_paired.csv (corrected from the CSV: lower is better) |
| `\BFiveVsAtsSynNdcgDiffCi` | 0.133 [0.073, 0.194] | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsAtsSynNdcgWlt` | 9/1/0 | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsAtsSynNdcgVerdict` | better | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsAtsSynMrrDiffCi` | 0.150 [0.000, 0.300] | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsAtsSynMrrWlt` | 3/0/7 | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsAtsSynMrrVerdict` | not distinguishable | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsAtsSynRcapDiffCi` | 0.130 [0.040, 0.220] | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsAtsSynRcapWlt` | 7/1/2 | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsAtsSynRcapVerdict` | better | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsAtsSynFrrtwentyDiffCi` | -0.024 [-0.123, 0.052] | eval/results/posthoc_b5_paired.csv |
| `\BFiveVsAtsSynFrrtwentyWlt` | 2/3/5 | eval/results/posthoc_b5_paired.csv (corrected from the CSV: lower is better) |
| `\BFiveVsAtsSynFrrtwentyVerdict` | not distinguishable | eval/results/posthoc_b5_paired.csv (corrected from the CSV: lower is better) |
| `\DOnePosScore` | 81.3 | eval/results/posthoc_d1_summary.csv |
| `\DOneNegScore` | 29.5 | eval/results/posthoc_d1_summary.csv |
| `\DOneStuffedScore` | 42.8 | eval/results/posthoc_d1_summary.csv |
| `\DOneAucCi` | 0.886 [0.844, 0.928] | eval/results/posthoc_d1_summary.csv |
| `\DOneAucPooled` | 0.879 | eval/results/posthoc_d1_summary.csv |
| `\DOneTopTen` | 49/51 (96%) | eval/results/posthoc_d1_summary.csv |
| `\DOneAucMin` | 0.767 | eval/results/posthoc_d1.csv |
| `\DOneAucMax` | 0.995 | eval/results/posthoc_d1.csv |
| `\DOneNPositive` | 51 | eval/results/posthoc_d1.csv |
| `\DOneNNegative` | 150 | eval/results/posthoc_d1.csv |
| `\FairOnPairs` | 100 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnSwaps` | 400 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsScoreControlCi` | 3.750 [1.750, 6.350] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsScoreControlMean` | 3.750 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsScoreCrossGroupCi` | 2.383 [1.450, 3.433] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsScoreCrossGroupMean` | 2.383 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsScoreDiffCi` | -1.367 [-3.517, 0.250] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsScoreVerdict` | not distinguishable | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnShareFiveControlCi` | 0.170 [0.100, 0.250] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnShareFiveControlMean` | 0.170 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnShareFiveCrossGroupCi` | 0.160 [0.103, 0.223] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnShareFiveCrossGroupMean` | 0.160 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnShareFiveDiffCi` | -0.010 [-0.073, 0.053] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnShareFiveVerdict` | not distinguishable | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsRankControlCi` | 0.710 [0.330, 1.140] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsRankControlMean` | 0.710 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsRankCrossGroupCi` | 0.403 [0.220, 0.617] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsRankCrossGroupMean` | 0.403 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsRankDiffCi` | -0.307 [-0.697, 0.047] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsRankVerdict` | not distinguishable | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnCrossControlCi` | 0.070 [0.020, 0.120] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnCrossControlMean` | 0.070 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnCrossCrossGroupCi` | 0.033 [0.013, 0.060] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnCrossCrossGroupMean` | 0.033 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnCrossDiffCi` | -0.037 [-0.083, 0.007] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnCrossVerdict` | not distinguishable | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsSimControlCi` | 0.014 [0.012, 0.016] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsSimControlMean` | 0.014 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsSimCrossGroupCi` | 0.014 [0.013, 0.015] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsSimCrossGroupMean` | 0.014 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsSimDiffCi` | -0.000 [-0.002, 0.002] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnAbsSimVerdict` | not distinguishable | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnSignedGujaratiFemaleCi` | -2.31 [-4.52, -0.58] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnSignedGujaratiMaleCi` | -0.48 [-1.73, 0.67] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnSignedNorthIndianFemaleCi` | -0.31 [-2.35, 2.04] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnSignedNorthIndianMaleCi` | -0.58 [-2.50, 1.06] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnSignedSouthIndianFemaleCi` | 1.19 [-0.71, 3.33] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnSignedSouthIndianMaleCi` | -1.42 [-4.34, 0.85] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnSignedFemaleCi` | -0.59 [-1.82, 0.59] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnSignedMaleCi` | -0.83 [-2.04, 0.22] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnSignedRegionGujaratiCi` | -1.39 [-2.64, -0.34] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnSignedRegionNorthIndianCi` | -0.45 [-1.83, 0.94] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOnSignedRegionSouthIndianCi` | -0.26 [-2.11, 1.32] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffPairs` | 100 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffSwaps` | 400 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsScoreControlCi` | 1.850 [0.950, 2.900] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsScoreControlMean` | 1.850 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsScoreCrossGroupCi` | 2.083 [1.233, 3.083] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsScoreCrossGroupMean` | 2.083 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsScoreDiffCi` | 0.233 [-0.617, 1.100] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsScoreVerdict` | not distinguishable | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffShareFiveControlCi` | 0.150 [0.080, 0.220] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffShareFiveControlMean` | 0.150 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffShareFiveCrossGroupCi` | 0.143 [0.090, 0.203] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffShareFiveCrossGroupMean` | 0.143 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffShareFiveDiffCi` | -0.007 [-0.060, 0.043] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffShareFiveVerdict` | not distinguishable | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsRankControlCi` | 0.580 [0.250, 0.980] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsRankControlMean` | 0.580 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsRankCrossGroupCi` | 0.577 [0.283, 0.940] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsRankCrossGroupMean` | 0.577 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsRankDiffCi` | -0.003 [-0.263, 0.240] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsRankVerdict` | not distinguishable | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffCrossControlCi` | 0.060 [0.020, 0.110] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffCrossControlMean` | 0.060 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffCrossCrossGroupCi` | 0.063 [0.027, 0.107] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffCrossCrossGroupMean` | 0.063 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffCrossDiffCi` | 0.003 [-0.023, 0.030] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffCrossVerdict` | not distinguishable | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsSimControlCi` | 0.014 [0.012, 0.016] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsSimControlMean` | 0.014 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsSimCrossGroupCi` | 0.014 [0.013, 0.015] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsSimCrossGroupMean` | 0.014 | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsSimDiffCi` | -0.000 [-0.002, 0.002] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffAbsSimVerdict` | not distinguishable | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffSignedGujaratiFemaleCi` | -0.29 [-2.40, 1.35] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffSignedGujaratiMaleCi` | 0.67 [-1.25, 2.88] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffSignedNorthIndianFemaleCi` | 0.51 [-0.20, 1.43] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffSignedNorthIndianMaleCi` | -0.67 [-2.60, 0.87] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffSignedSouthIndianFemaleCi` | 0.60 [-1.67, 3.33] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffSignedSouthIndianMaleCi` | 0.38 [-1.32, 2.08] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffSignedFemaleCi` | 0.24 [-0.80, 1.33] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffSignedMaleCi` | 0.13 [-0.92, 1.21] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffSignedRegionGujaratiCi` | 0.19 [-1.20, 1.59] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffSignedRegionNorthIndianCi` | -0.10 [-1.14, 0.84] | eval/results/fairness_on.json / fairness_off.json |
| `\FairOffSignedRegionSouthIndianCi` | 0.47 [-0.95, 2.00] | eval/results/fairness_on.json / fairness_off.json |
| `\FairShareFiveMinPct` | 14 | eval/results/fairness_on.json / fairness_off.json |
| `\FairShareFiveMaxPct` | 17 | eval/results/fairness_on.json / fairness_off.json |
| `\TimePerCandidate` | 2.40 | eval/results/b4_k20.json |
| `\TimePerCandidateMin` | 2.21 | eval/results/b4_k20.json |
| `\TimePerCandidateMax` | 2.57 | eval/results/b4_k20.json |
| `\TimeRerankPerReq` | 48 | eval/results/b4_k20.json |
| `\TimeRerankPerReqMin` | 44 | eval/results/b4_k20.json |
| `\TimeRerankPerReqMax` | 51 | eval/results/b4_k20.json |
| `\TimeParse` | 2.6 | eval/results/b4_k20.json |
| `\TimePosthocWall` | 562 | eval/results/posthoc_meta.json |
| `\CallsPosthoc` | 207 | eval/results/posthoc_b5.json + posthoc_d1.json |
| `\CallsMain` | 1716 | docs/RESULTS.md (cache size at the end of the main evaluation) |
| `\CallsFallback` | 1 | .cache/llm_cache.jsonl |
| `\CallsFairnessSwaps` | 800 | eval/results/b4_k20.json |
