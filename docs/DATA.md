# Synthetic dataset

Everything is produced by deterministic code (`SEED = 42`, no LLM, no network). One command regenerates it:

```
python scripts/gen_data.py        # writes data/*, docs/balance_log.md, prints the balancing summary
python scripts/validate_data.py   # all checks + stats tables, exit code 1 on any failure
```

| File | Content |
|---|---|
| `data/skills_taxonomy.json` | 71 skills in 12 role families, hand-written: aliases, `implied_by` relations, 6-7 evidence sentences per skill that contain no skill name or alias |
| `data/name_pools.json` | 6 name groups (Gujarati / North Indian / South Indian x male-coded / female-coded), 43 first names each |
| `data/students.jsonl` | 500 students: id, name, branch, cgpa, active_backlogs, grad_year, resume_text |
| `data/students_truth.jsonl` | hidden profile: archetype, name group, family, true skill levels, effective levels, text surfaces. Never read it in the pipeline under test |
| `data/requirements.jsonl`, `requirements_truth.json` | 15 free-text requirements (5 dev / 10 test) and their structured truth |
| `data/qrels.csv` | all 500 x 15 pairs: eligible, relevance 0-3, qualified, extra_credit |
| `data/spotcheck.csv` | 20 pairs (5 per relevance level) with an empty `my_label` column for manual review |
| `docs/balance_log.md` | every balancing round: quotas and counts per requirement |

## How students are generated

1. **Archetype** (fixed counts, shuffled over student ids): standard 150, paraphrased 100, implied 50, abbreviated_noisy 50, sparse_strong 40, stuffed_weak 50, ineligible_strong 35, generalist_average 25 (30/20/10/10/8/10/7/5 %).
2. **Role family** from a quota (see Balancing). **Branch** is drawn given the family (software families mostly CSE/IT/ICT/M.Sc IT, embedded mostly ECE/EE, data/BA/QA more mixed incl. Mechanical/Civil). CGPA ~ N(7.8, 0.85) clipped to 5.5-9.8, active backlogs mostly 0 (about 6%, 40% if CGPA < 6.5), grad year 2026-2028.
3. **Skills**: each family has several hand-ordered stacks (e.g. Python+Django+PostgreSQL+REST APIs+Docker+Redis). A student keeps the first four skills of a stack plus a random part of the rest, with levels 1/2/3 (basic/working/strong); 65% also get a second, shallower profile (levels 1-2) from another family. Implied skills are materialised explicitly for every archetype except `implied`.
4. **Names** are assigned independently of archetype, skills and CGPA: inside each archetype students sorted by CGPA are cut into blocks of six and each block receives the six name groups in random order. Validation: chi-square test of archetype x name group (p = 1.0), mean CGPA per group within 0.06.
5. **Resume text**: header line (the only place the name appears) -> education line (parsed back and asserted against the structured fields) -> sections (skills, projects, internship, achievements, extras, objective) in random order, 80-400 words, random section titles and bullets, distractor lines (hobbies, generic objectives, declarations). Skills are shown through the archetype's rendering mode:

| Archetype | Rendering |
|---|---|
| standard | skills listed by canonical name, projects with matching tech line and evidence sentences |
| paraphrased | no skill section; every skill only through evidence sentences; no canonical name or alias anywhere in the text (asserted) |
| implied | lists tools that imply a skill (Spring Boot, PostgreSQL, Django...) but never names the implied skills (Java, SQL, Python...), asserted |
| abbreviated_noisy | aliases, abbreviations ("ec2", "dockerfile", "continuous integration"), typos, lowercase and "n"/"&" informal wording |
| sparse_strong | 120-170 words, strong skills in one line, one project, one internship line |
| stuffed_weak | 24-34 skills copied from many families, generic coursework projects with no evidence, true levels 0-1 |
| ineligible_strong | strong skills (standard rendering) but CGPA < 6.5 or active backlogs > 0 |
| generalist_average | modest levels across two families |

Every true skill must be visible in the text by a recorded surface string (name, alias, typo or evidence sentence); the validator asserts it.

## Labelling function (`relevance()` in `gen_data.py`)

Inputs: the requirement's structured truth and the student's **effective** levels (explicit levels closed under `implied_by`, group level = minimum of its members).

* not eligible (CGPA below minimum, branch not allowed, backlogs above maximum; each rule applies only if the requirement states it) -> relevance 0, qualified = false
* 3: all must-haves at effective level >= 2
* 2: all must-haves at level >= 1
* 1: at least half of the must-haves at level >= 1
* 0: otherwise
* `qualified = relevance >= 2`; nice-to-haves only produce `extra_credit` = mean(nice levels) / 3, a tie-break that never changes relevance.

`validate_data.py` recomputes `qrels.csv` from the hidden truth and compares.

## Balancing (quota-based, run by `gen_data.py`)

* Every role family is guaranteed 35 students; the remaining 80 are spread in proportion to the family weights (`FAMILY_W`). Each student has its own random streams, so a student's profile and text change only if its family changes. When a quota changes, only the lowest-priority students of shrinking families are moved to growing ones.
* Loop (max 10 rounds): generate, count qualified students per requirement. A requirement is "low" if it has fewer than 8 qualified or fewer than 40% of them from the hard archetypes (paraphrased, implied, abbreviated_noisy, sparse_strong). The quota of its family is raised by about 10% and the data regenerated. The range is **8-40 qualified per requirement**. Upper-bound misses are reported, never fixed by shrinking a quota.
* **Result: converged after 2 rounds.** Final quotas: backend 45, frontend 38, fullstack 47, data_analysis 40, ml 41, data_engineering 38, devops_cloud 51, qa_testing 40, mobile 40, cybersecurity 41, embedded_iot 37, business_analysis 42. Per-round tables are in `balance_log.md`.

## Known limitations

* **Circularity.** Resumes, skill levels and labels all come from the same generator and the same taxonomy. The labels are "correct" by construction; a method that learns the generator's templates (evidence sentences, stacks) will look better than it would on real resumes. Results show relative method differences, not absolute placement accuracy.
* **Template text.** About 430 evidence sentences are reused with light variation, so resumes are repetitive; vocabulary and style are much narrower than real resumes. The "paraphrase" test only measures robustness to the paraphrases written in the taxonomy.
* **Simplified requirements** (frozen after the first balancing attempts failed): R03, R07, R12 and R13 have 3 must-haves (the fourth skill became a nice-to-have); R09 was changed from an Android/Kotlin role to a React Native role (an Android role gave implied-skill archetypes no way to qualify); CGPA cutoffs were lowered in R03 (6.5), R05 (7), R13 (6.5) and R14 (7). Requirement texts and `requirements_truth.json` match each other and were not edited after that.
* **Taxonomy change to hit the range.** With 500 students R02 (React + JavaScript + HTML/CSS) had 71-81 qualified because React and Next.js imply all three. The `React/Angular/Vue.js -> HTML/CSS` implication was removed (HTML/CSS is now never implied), and a DevOps stack starting from Raspberry Pi (implies Linux) was added so `implied` students can qualify for R07. This is a change to which skills students hold, not to the labelling function or thresholds.
* Small cells: several requirements have only 12-20 qualified students (R06 and R07 at 42% hard share, close to the 40% floor), so per-requirement metrics are noisy.
* Names are only a coarse, stereotyped proxy for regional/gender groups and are used solely for a name-swap fairness test.
* The `spotcheck.csv` labels are generated labels, not human labels; `my_label` is for your manual audit.
