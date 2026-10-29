"""Non-LLM baselines. All use the SAME parsed hard filters (eligible set E) as the proposed method.

B1  keyword ATS strict   all parsed must-haves present as case-insensitive word-boundary matches of the exact string
B1b keyword ATS lenient  >= 50% of the must-haves
B1c keyword ATS + syn.   strict, but skills also match their taxonomy aliases (generous: aliases come from the generator)
B2  BM25 over resume text with the parsed semantic_query
B3  dense-only (the retrieval order of the pipeline)
B3b hybrid: reciprocal rank fusion (k=60) of B2 and B3 over eligible students
"""
import math
import re

from rank_bm25 import BM25Okapi

import gen_data as g
from dev_checks import norm_skill
from metrics import passes

TOKEN = re.compile(r"[a-z0-9]+")


def eligible_ids(filters, students):
    return [sid for sid, s in students.items() if passes(s, filters)]


def exact_match(text, skill):
    return re.search(r"(?<!\w)" + re.escape(skill.strip()) + r"(?!\w)", text, re.I) is not None


def syn_match(text, skill):
    """Skill matches if the text contains the canonical name or an alias of every taxonomy skill it maps to;
    skills outside the taxonomy match exactly only."""
    names = norm_skill(skill)
    if not names:
        return exact_match(text, skill)
    return all(any(g.term_pattern(t).search(text) for t in g.skill_terms(n)) for n in names)


def keyword_scan(parsed, students, ids, matcher):
    """Per student: (#must matched, #nice matched, passed_all_must)."""
    must, nice = parsed["must_have_skills"], parsed["nice_to_have_skills"]
    out = {}
    for sid in ids:
        text = students[sid]["resume_text"]
        m = sum(matcher(text, s) for s in must)
        n = sum(matcher(text, s) for s in nice)
        out[sid] = (m, n, m == len(must))
    return out


def ats_ranking(parsed, students, eligible, matcher, min_share):
    """min_share=1.0 strict, 0.5 lenient. Returns (ranking of passers, set of passers)."""
    scan = keyword_scan(parsed, students, eligible, matcher)
    nmust = len(parsed["must_have_skills"])
    passers = [sid for sid, (m, n, ok) in scan.items() if nmust == 0 or m / nmust >= min_share]
    passers.sort(key=lambda sid: (-(scan[sid][0] + scan[sid][1]), sid))
    return passers, set(passers)


def tokenize(text):
    return TOKEN.findall(text.lower())


class Bm25:
    def __init__(self, students):
        self.ids = list(students)
        self.model = BM25Okapi([tokenize(students[s]["resume_text"]) for s in self.ids])

    def rank(self, query, eligible):
        scores = dict(zip(self.ids, self.model.get_scores(tokenize(query))))
        return sorted(eligible, key=lambda s: (-scores[s], s))


def rrf(rankings, k=60):
    score = {}
    for r in rankings:
        for pos, sid in enumerate(r, 1):
            score[sid] = score.get(sid, 0.0) + 1.0 / (k + pos)
    return sorted(score, key=lambda s: (-score[s], s))
