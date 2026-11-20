"""Unit tests for the prototype extensions (mocked LLM, no Ollama needed).   python scripts/test_extensions.py"""
import csv
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import extensions as ex  # noqa: E402
from src import student_view as sv  # noqa: E402
from src.hybrid import Bm25Index, eligible_ids, rrf_scores  # noqa: E402

STUDENTS = {
    f"S{i:03d}": dict(id=f"S{i:03d}", name=f"Name{i}", branch=("CSE" if i % 2 else "ECE"), cgpa=6.0 + i / 10, active_backlogs=0 if i < 5 else 1,
                      resume_text=f"Header Name{i} | mail\nBuilt python services {'sql ' * i} and rest endpoints")
    for i in range(1, 9)
}
PARSED = dict(role_title="Dev", must_have_skills=["Python", "SQL"], nice_to_have_skills=["Docker"], min_cgpa=6.3, allowed_branches=["CSE"],
              max_backlogs=0, semantic_query="python sql backend")


LOOSE = dict(PARSED, min_cgpa=None, allowed_branches=[], max_backlogs=None)


def fake_deps(scores):
    """Re-ranker fake: score by student id from `scores`; hybrid fake: eligible students in id order with descending rrf."""
    return dict(students=STUDENTS, parse=lambda t: LOOSE,
                score=lambda t, p, text: dict(score=scores[text.split(" ")[1]], matched_skills=["Python"], missing_skills=["SQL"], explanation="e. x."),
                hybrid=lambda parsed, elig: [(s, 1.0 / (i + 1)) for i, s in enumerate(elig)], save=False)


class Labelling(unittest.TestCase):
    def ranked(self, scores):
        return ex.label_candidates([dict(id=f"S{i}", score=s) for i, s in enumerate(scores)], threshold=60, top_n=3)

    def test_groups_and_threshold(self):
        r = self.ranked([95, 70, 61, 60, 59, 10])
        self.assertEqual([x["group"] for x in r], ["Top 10"] * 3 + ["Also suited", "Below threshold", "Below threshold"])
        self.assertEqual(ex.count_suited(r), 4)

    def test_top10_is_kept_even_below_threshold(self):
        r = self.ranked([50, 40, 30, 20])
        self.assertEqual([x["group"] for x in r], ["Top 10"] * 3 + ["Below threshold"])

    def test_unscored_is_below_threshold_and_threshold_change_relabels(self):
        r = ex.label_candidates([dict(id="a", score=90), dict(id="b", score=None), dict(id="c", score=75)], threshold=60, top_n=1)
        self.assertEqual([x["group"] for x in r], ["Top 10", "Below threshold", "Also suited"])
        ex.label_candidates(r, threshold=80, top_n=1)
        self.assertEqual(r[2]["group"], "Below threshold")

    def test_shortlist_full_pool_and_counts(self):
        res = ex.shortlist_full("req", k_pool=3, threshold=60, top_n=1, deps=fake_deps({f"Name{i}": 50 + 10 * i for i in range(1, 9)}))
        self.assertEqual(res["pool_size"], 3)
        self.assertEqual(res["eligible_count"], len(eligible_ids(LOOSE, STUDENTS)))
        self.assertEqual(res["ranked"][0]["score"], max(r["score"] for r in res["ranked"]))
        self.assertEqual(res["suited_count"], sum(r["group"] != "Below threshold" for r in res["ranked"]))

    def test_progress_callback(self):
        calls = []
        ex.shortlist_full("req", k_pool=2, deps=fake_deps({f"Name{i}": 70 for i in range(1, 9)}), progress=lambda *a: calls.append(a))
        self.assertEqual([c[0] for c in calls], [0, 1, 2])
        self.assertTrue(all(c[1] == 2 for c in calls))


class Csv(unittest.TestCase):
    def test_columns_and_rows(self):
        r = ex.label_candidates([dict(id="S001", score=88, matched=["Python", "SQL"], missing=[], explanation="Good.")], top_n=1)
        rows = list(csv.reader(io.StringIO(ex.full_list_csv(r, STUDENTS))))
        self.assertEqual(rows[0], ["rank", "group", "student_id", "name", "branch", "cgpa", "backlogs", "score", "matched", "missing", "explanation"])
        self.assertEqual(rows[1][:3], ["1", "Top 10", "S001"])
        self.assertEqual(rows[1][8], "Python; SQL")


class Student(unittest.TestCase):
    def test_eligibility_table(self):
        rows = {r["rule"]: r for r in sv.eligibility_table(PARSED, dict(cgpa=6.0, branch="ECE", active_backlogs=1))}
        self.assertFalse(rows["CGPA"]["passed"])
        self.assertFalse(rows["Branch"]["passed"])
        self.assertFalse(rows["Active backlogs"]["passed"])
        self.assertIn("not fixable by editing the resume", rows["CGPA"]["note"])
        ok = {r["rule"]: r for r in sv.eligibility_table(PARSED, dict(cgpa=7.0, branch="CSE", active_backlogs=0))}
        self.assertTrue(all(r["passed"] for r in ok.values()))
        free = sv.eligibility_table(dict(min_cgpa=None, allowed_branches=[], max_backlogs=None), dict(cgpa=5.0, branch="Civil", active_backlogs=3))
        self.assertTrue(all(r["passed"] for r in free))

    def test_skill_gaps(self):
        must, nice = sv.skill_gaps(PARSED, dict(matched_skills=["python"], missing_skills=["SQL"]))
        self.assertEqual((must, nice), (["SQL"], ["Docker"]))

    def test_coverage_arithmetic(self):
        parsed = dict(must_have_skills=["React", "JavaScript", "HTML/CSS", "TypeScript", "Figma"], nice_to_have_skills=["Docker", "Redis"])
        scored = dict(matched_skills=["react", "JavaScript", "Docker"], missing_skills=["HTML/CSS", "TypeScript", "Figma"])
        now = sv.coverage(parsed, scored)
        self.assertEqual((now["must"]["before"], now["must"]["after"], now["must"]["total"]), (2, 2, 5))
        self.assertEqual((now["nice"]["before"], now["nice"]["total"]), (1, 2))
        both = sv.coverage(parsed, scored, ["TypeScript", "figma", "Redis", "Kubernetes"])  # unknown skill ignored, case-insensitive
        self.assertEqual((both["must"]["before"], both["must"]["after"]), (2, 4))
        self.assertEqual((both["nice"]["before"], both["nice"]["after"]), (1, 2))
        self.assertEqual(both["must"]["gained"], ["TypeScript", "Figma"])
        already = sv.coverage(parsed, scored, ["React"])  # already matched: nothing gained
        self.assertEqual((already["must"]["after"], already["must"]["gained"]), (2, []))

    def test_coverage_text(self):
        parsed = dict(must_have_skills=["A", "B", "C", "D", "E"], nice_to_have_skills=[])
        scored = dict(matched_skills=["A", "B", "C"], missing_skills=["D", "E"])
        lines = sv.coverage_text(sv.coverage(parsed, scored, ["D", "E"]))
        self.assertEqual(lines[0], "Currently 3 of 5 required skills; if you gain D and E: 5 of 5.")
        self.assertEqual(lines[1], "No nice-to-have skills listed in the requirement.")
        self.assertEqual(sv.coverage_text(sv.coverage(parsed, scored))[0], "Currently 3 of 5 required skills.")
        self.assertEqual(sv.coverage_text(sv.coverage(parsed, scored, ["D"]))[0], "Currently 3 of 5 required skills; if you gain D: 4 of 5.")
        three = sv.coverage_text(sv.coverage(dict(must_have_skills=list("ABCD"), nice_to_have_skills=[]), dict(matched_skills=["A"]), ["B", "C", "D"]))
        self.assertIn("if you gain B, C and D: 4 of 4", three[0])

    def test_what_if_text_assembly(self):
        t = sv.what_if_text("Resume line\n", ["SQL", "Docker"])
        self.assertTrue(t.startswith("Resume line\n\n- Project (hypothetical):"))
        lines = t.strip().split("\n")
        self.assertEqual(lines[0], "Resume line")
        self.assertEqual(lines[2], "- Project (hypothetical): built and deployed a small application using SQL, with hands-on use of SQL.")
        self.assertEqual(lines[3], "- Project (hypothetical): built and deployed a small application using Docker, with hands-on use of Docker.")
        self.assertEqual(len(lines), 4)  # one bullet per skill, original text untouched
        self.assertNotIn("assumed acquired", t)

    def test_what_if_rescores_the_modified_text(self):
        seen = []
        out = sv.what_if("req", PARSED, "R", ["SQL"], score_fn=lambda t, p, r: seen.append(r) or dict(score=80))
        self.assertIn("Project (hypothetical): built and deployed a small application using SQL", seen[0])
        self.assertEqual(out["scored"]["score"], 80)

    def test_position_text(self):
        self.assertIn("at or above the threshold of 60", sv.position_vs(60, 60))
        self.assertIn("below it", sv.position_vs(70, 60, top10_cutoff=85))
        self.assertEqual(sv.top10_cutoff(dict(ranked=[dict(score=i) for i in range(12, 0, -1)], top_n=10)), 3)
        self.assertIsNone(sv.top10_cutoff(dict(ranked=[dict(score=1)], top_n=10)))

    def good(self, skill, **over):
        item = dict(skill=skill,
                    why_it_matters=f"This requirement lists {skill} next to React, so frontend work here depends on it.",
                    what_to_build=f"Extend your quiz application so that its score board is rebuilt with {skill}, keeping the existing JavaScript and HTML.",
                    how_to_learn=[f"Read the getting-started section of the official {skill} documentation.",
                                  f"Convert one small module of your project to {skill} and fix every error the tooling reports."],
                    resume_bullet_example=f"Extended the quiz application by rebuilding its score board with {skill} and the existing JavaScript.")
        item.update(over)
        return item

    def test_validator_accepts_a_specific_entry(self):
        self.assertEqual(sv.validate_suggestion(self.good("TypeScript"), "TypeScript"), [])
        self.assertEqual(sv.validate_suggestion(self.good("typescript"), "TypeScript"), [])  # skill match is case-insensitive

    def test_validator_rejects_placeholders_urls_and_courses(self):
        bad = {
            "X placeholder": dict(what_to_build="Build a small application that uses X together with the stack you already have."),
            "ellipsis": dict(what_to_build="Build a small application that uses TypeScript, then learn it by ... and more."),
            "template wording": dict(why_it_matters="If you have done TypeScript work, add a bullet describing it for this requirement."),
            "url": dict(how_to_learn=["Read the guide at https://example.com/typescript for the basics.", "Convert one small module of your project to it."]),
            "course name": dict(how_to_learn=["Complete the official 'TypeScript for Beginners' course on a learning site.", "Convert one small module of your project to it."]),
            "number in bullet": dict(resume_bullet_example="Rebuilt the score board with TypeScript and cut load time by 40 percent."),
            "brackets": dict(what_to_build="Build a small application that uses [tool] together with TypeScript and your stack."),
        }
        for name, over in bad.items():
            self.assertTrue(sv.validate_suggestion(self.good("TypeScript", **over), "TypeScript"), name)

    def test_validator_rejects_short_generic_or_wrong_skill(self):
        self.assertTrue(sv.validate_suggestion(self.good("TypeScript", why_it_matters="Important skill."), "TypeScript"))
        self.assertTrue(sv.validate_suggestion(self.good("TypeScript", how_to_learn=["Read the docs."]), "TypeScript"))
        self.assertTrue(sv.validate_suggestion(self.good("TypeScript", how_to_learn=["a" * 30] * 4), "TypeScript"))
        self.assertTrue(sv.validate_suggestion(self.good("Figma"), "TypeScript"))
        generic = self.good("TypeScript", what_to_build="Build a small application with the tools you already know and show it to a friend.",
                            resume_bullet_example="Built a small application with the tools I already know and showed it to a friend.")
        self.assertIn("never mention the skill", " ".join(sv.validate_suggestion(generic, "TypeScript")))
        self.assertTrue(sv.validate_suggestion({}, "TypeScript"))

    def test_suggestions_valid_first_try_and_prompt_has_no_identity(self):
        seen = []

        def chat(messages, schema):
            seen.append(messages)
            return dict(suggestions=[self.good("SQL"), self.good("Docker")]), {}

        resume = "Priya Shah | priya@mail.example | +91 9000000000\nBuilt endpoints over a relational store."
        out = sv.suggest_improvements("req text", PARSED, resume, ["SQL"], ["Docker"], chat=chat)
        self.assertEqual([(o["skill"], o["ok"]) for o in out], [("SQL", True), ("Docker", True)])
        self.assertEqual(len(seen), 1)  # one call when everything validates
        joined = " ".join(m["content"] for m in seen[0])
        for secret in ("Priya", "Shah", "priya@mail", "9000000000"):
            self.assertNotIn(secret, joined)
        self.assertIn("Built endpoints over a relational store.", joined)
        self.assertIn("Never invent experience", seen[0][0]["content"])

    def test_one_retry_for_rejected_skills_then_fallback_message(self):
        calls = []

        def chat(messages, schema):
            calls.append(messages[1]["content"])
            if len(calls) == 1:  # first answer: SQL good, Docker is the copied template
                return dict(suggestions=[self.good("SQL"), self.good("Docker", what_to_build="If you have done X, add a bullet describing it; if not, learn X by ...")]), {}
            return dict(suggestions=[self.good("Docker", what_to_build="still ... a placeholder")]), {}  # retry also invalid

        out = sv.suggest_improvements("req", PARSED, "h\nbody", ["SQL"], ["Docker"], chat=chat)
        self.assertEqual(len(calls), 2)  # exactly one retry
        self.assertIn("rejected", calls[1])
        self.assertTrue(out[0]["ok"])
        self.assertFalse(out[1]["ok"])
        self.assertEqual(out[1]["error"], "Could not generate a specific suggestion for Docker")

    def test_validator_rejects_outcome_claims_in_the_bullet(self):
        for word in ("reduced", "improved", "increased", "faster", "fewer", "eliminated", "boosted", "optimised", "optimized", "improvement"):
            bullet = f"Rebuilt the score board of the quiz application with TypeScript and {word} the loading code."
            self.assertTrue(any("outcome" in p for p in sv.validate_suggestion(self.good("TypeScript", resume_bullet_example=bullet), "TypeScript")), word)
        ok = "Rebuilt the score board of the quiz application with TypeScript, typing its data models and event handlers."
        self.assertEqual(sv.validate_suggestion(self.good("TypeScript", resume_bullet_example=ok), "TypeScript"), [])

    def test_digit_check_ignores_digits_inside_the_skill_name(self):
        ok = self.good("HTML5", resume_bullet_example="Rebuilt the portfolio page of the quiz application using semantic HTML5 elements and html5 forms.")
        self.assertEqual(sv.validate_suggestion(ok, "HTML5"), [])
        bad = self.good("HTML5", resume_bullet_example="Rebuilt the portfolio page of the quiz application using HTML5 across 3 pages.")
        self.assertIn("bullet contains a number", sv.validate_suggestion(bad, "HTML5"))

    def test_required_label_is_not_contradicted_by_free_text(self):
        mandatory = self.good("TypeScript", why_it_matters="This requirement lists TypeScript as a mandatory skill for the frontend role here.")
        self.assertTrue(any("nice-to-have" in p for p in sv.validate_suggestion(mandatory, "TypeScript", "Nice-to-have")))
        self.assertEqual(sv.validate_suggestion(mandatory, "TypeScript", "Required"), [])  # matches the label
        self.assertEqual(sv.validate_suggestion(mandatory, "TypeScript"), [])  # no label given: not checked
        bonus = self.good("Figma", why_it_matters="This requirement lists Figma as a bonus skill that helps design-to-code work in the role.")
        self.assertTrue(any("required skill optional" in p for p in sv.validate_suggestion(bonus, "Figma", "Required")))
        self.assertEqual(sv.validate_suggestion(bonus, "Figma", "Nice-to-have"), [])

    def test_kind_label_comes_from_the_gap_lists_not_the_model(self):
        def chat(messages, schema):
            return dict(suggestions=[self.good("SQL", kind="Nice-to-have"), self.good("Docker", kind="Required")]), {}  # model-supplied kind is ignored

        out = sv.suggest_improvements("req", PARSED, "h\nbody", ["SQL"], ["Docker"], chat=chat)
        self.assertEqual([(o["skill"], o["kind"]) for o in out], [("SQL", "Required"), ("Docker", "Nice-to-have")])
        failed = sv.suggest_improvements("req", PARSED, "h\nbody", [], ["Docker"], chat=lambda m, s: (dict(suggestions=[]), {}))
        self.assertEqual((failed[0]["ok"], failed[0]["kind"]), (False, "Nice-to-have"))

    def test_retry_can_recover(self):
        calls = []

        def chat(messages, schema):
            calls.append(1)
            return dict(suggestions=[self.good("SQL", resume_bullet_example="Short.")] if len(calls) == 1 else [self.good("SQL")]), {}

        out = sv.suggest_improvements("req", PARSED, "h\nbody", ["SQL"], [], chat=chat)
        self.assertEqual(len(calls), 2)
        self.assertTrue(out[0]["ok"])
        self.assertEqual(sv.suggest_improvements("req", PARSED, "h\nbody", [], [], chat=chat), [])


class Hybrid(unittest.TestCase):
    def test_rrf_and_bm25_ranking(self):
        self.assertAlmostEqual(rrf_scores([["a", "b"], ["b", "a"]])["a"], 1 / 61 + 1 / 62)
        tiny = {"a": dict(resume_text="knows kafka streams"), "b": dict(resume_text="plays cricket"), "c": dict(resume_text="knows spark")}
        self.assertEqual(Bm25Index(tiny).rank("kafka", ["a", "b", "c"])[0], "a")
        self.assertEqual(Bm25Index(tiny).rank("kafka", ["c", "b"]), ["b", "c"])  # ties broken by id

    def test_parity_with_eval_baselines(self):
        """src/hybrid.py must rank exactly like the evaluation code (read-only import of eval/baselines.py)."""
        sys.path[:0] = [str(ROOT / "eval"), str(ROOT / "scripts"), str(ROOT / "app")]
        import baselines as bl
        from src.data import load_students
        students = {s["id"]: s for s in load_students()}
        elig = list(students)[:200]
        q = "backend engineer python rest apis relational database sql"
        self.assertEqual(Bm25Index(students).rank(q, elig), bl.Bm25(students).rank(q, elig))
        self.assertEqual(sorted(rrf_scores([elig, elig[::-1]]).items()), sorted((s, 1 / (60 + elig.index(s) + 1) + 1 / (60 + elig[::-1].index(s) + 1)) for s in elig))


if __name__ == "__main__":
    unittest.main(verbosity=2)
