# Prompt log (tuned on the 5 dev requirements only: R01, R04, R07, R09, R12)

Test requirements were never run. Few-shot examples in the parser prompt are invented (game developer, network support engineer, Java developer) and share no text with any requirement or resume.

## Parser

| Iteration | Change | Eligibility fields (min_cgpa / max_backlogs / allowed_branches) | Must-have precision / recall |
|---|---|---|---|
| 0 | first prompt (schema-constrained JSON, 3 invented examples, branch label mapping, backlog rules) | 100% / 100% / 100% (15/15) | 100% / 93% |

The 90% gate was passed at iteration 0, so the parser prompt was not tuned further. Remaining dev mismatches (not tuned, to avoid fitting dev):
* R04: "Power BI dashboards banana aana chahiye" was put in nice-to-have, truth says must-have.
* R12: an extra must-have "Documentation" that is not in the truth skill list.

## Re-ranker (end-to-end nDCG@10 on dev, preliminary)

| Iteration | Change | nDCG@10 R01 / R04 / R07 / R09 / R12 | Mean | Recall@10 mean |
|---|---|---|---|---|
| dense order (no LLM) | similarity only | .712 / .726 / .978 / .439 / .492 | .669 | - |
| 0 | JSON order score, matched, missing, explanation; score bands only | .895 / .437 / .917 / .417 / .374 | .608 | .25 |
| 1 | evidence first, score last (schema property order); check every must-have one by one; one missing must-have caps the score at 69, half missing at 40 | .784 / .795 / .932 / .564 / .519 | .719 | .32 |

Why iteration 1: with the score written first, the 4B model gave 90-95 to almost everyone (including resumes missing a must-have and a stuffed_weak resume). Writing matched/missing skills before the score and capping the score by the number of missing must-haves spread the scores. Raw outputs of iteration 0 are kept in `eval/dev_run_v0.json`. Only one re-ranker iteration was run; any further change would be fitting 5 requirements.
