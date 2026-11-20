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

    def test_what_if_text_assembly(self):
        t = sv.what_if_text("Resume line\n", ["SQL", "Docker"])
        self.assertTrue(t.startswith("Resume line"))
        self.assertTrue(t.endswith("Additional skills (assumed acquired): SQL, Docker\n"))

    def test_what_if_rescores_the_modified_text(self):
        seen = []
        out = sv.what_if("req", PARSED, "R", ["SQL"], score_fn=lambda t, p, r: seen.append(r) or dict(score=80))
        self.assertIn("Additional skills (assumed acquired): SQL", seen[0])
        self.assertEqual(out["scored"]["score"], 80)

    def test_position_text(self):
        self.assertIn("at or above the threshold of 60", sv.position_vs(60, 60))
        self.assertIn("below it", sv.position_vs(70, 60, top10_cutoff=85))
        self.assertEqual(sv.top10_cutoff(dict(ranked=[dict(score=i) for i in range(12, 0, -1)], top_n=10)), 3)
        self.assertIsNone(sv.top10_cutoff(dict(ranked=[dict(score=1)], top_n=10)))

    def test_suggestion_prompt_has_no_identity(self):
        seen = {}

        def chat(messages, schema):
            seen["user"] = messages[1]["content"]
            seen["system"] = messages[0]["content"]
            return dict(suggestions=[dict(gap="SQL", suggestion="If you have done it, add a bullet.")]), {}

        resume = "Priya Shah | priya@mail.example | +91 9000000000\nBuilt endpoints over a relational store."
        out = sv.suggest_improvements("req text", PARSED, resume, ["SQL"], ["Docker"], chat=chat)
        self.assertEqual(out[0]["gap"], "SQL")
        for secret in ("Priya", "Shah", "priya@mail", "9000000000"):
            self.assertNotIn(secret, seen["user"])
        self.assertIn("Built endpoints over a relational store.", seen["user"])
        self.assertIn("Never invent experience", seen["system"])


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
