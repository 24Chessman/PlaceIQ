"""Prototype extension, student view: simulated resume revision, re-score and retrieval effect (not evaluated).

- generate_bullets: one LLM call (JSON schema, temperature 0, thinking off, on-disk cached) writes one bullet per ticked skill that
  EXTENDS a real project from the resume body (the resume header with name, email and phone is never sent). Every bullet is validated,
  rejected ones get one retry that states why, and skills that still fail get no bullet.
- build_revised_text: original resume plus the validated bullets (the header stays in the text that is scored).
- retrieval_effect: what the revised text would do to the student's hybrid (BM25 + dense, RRF k=60) rank, computed in memory with the same
  embedding model. It only READS the existing Chroma index and never writes to it or changes student data.
- place_in_full_list: where a new re-ranker score would land in a cached full list.
"""
import difflib
import re

from .hybrid import RRF_K, Bm25Index, eligible_ids, rrf_scores
from .student_view import BULLET_BAD, OUTCOME_WORDS, PLACEHOLDER_PATTERNS, mentions, resume_body

BULLET_SCHEMA = {
    "type": "object",
    "properties": {"bullets": {"type": "array", "maxItems": 8, "items": {
        "type": "object",
        "properties": {"skill": {"type": "string"}, "extends_project": {"type": "string"}, "bullet": {"type": "string"}},
        "required": ["skill", "extends_project", "bullet"], "additionalProperties": False}}},
    "required": ["bullets"], "additionalProperties": False,
}

BULLET_SYSTEM = """You help a student imagine an updated resume. You get a list of skills and the student's resume without name or contact details.

For EACH skill, write one resume bullet that describes the skill being added to one of the student's REAL projects:
- extends_project: the title of one project, copied exactly from the resume. Choose the project whose stack fits the skill best.
- bullet: one sentence in the student's own style (same tense, tone and length as the bullets already in the resume) describing what was built when that project was extended with the skill.

Rules:
- Use only technologies that already appear in the resume plus the skill itself. Never add other tools, employers, companies, courses or places.
- Describe only what was built, in plain past tense. Do not claim results or outcomes (nothing reduced, improved, increased, faster, fewer, boosted or optimised). No numbers or percentages.
- Write real, specific text. No placeholders such as the letter X, "..." or angle brackets, and no URLs.
- Do not mention or guess the student's name, gender, region or college.
Reply with the JSON object only."""

MIN_BULLET = 40


def _norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", s.lower())).strip()


def validate_bullet(item, skill, body):
    """Problems (empty = valid): the project must be a title that occurs in the resume body, the bullet must name the skill, be long
    enough, and contain no placeholders, URLs, course names, employer-like names, outcome claims or numbers (the skill name itself is
    removed before the digit check)."""
    problems = []
    for key in ("skill", "extends_project", "bullet"):
        if not isinstance(item.get(key), str) or not item[key].strip():
            problems.append(f"{key} is missing")
    if problems:
        return problems
    if item["skill"].strip().lower() != skill.strip().lower():
        problems.append(f"skill is '{item['skill']}', expected '{skill}'")
    if len(_norm(item["extends_project"])) < 3 or _norm(item["extends_project"]) not in _norm(body):
        problems.append("extends_project is not a project title copied from the resume")
    bullet = item["bullet"]
    if len(bullet.strip()) < MIN_BULLET:
        problems.append("bullet is too short")
    if not mentions(bullet, skill):  # whole word: 'reactive' does not count as naming React
        problems.append("bullet never names the skill")
    for pat, msg in PLACEHOLDER_PATTERNS:
        if re.search(pat, bullet):
            problems.append(msg)
    for pat, msg in BULLET_BAD:
        if re.search(pat, bullet):
            problems.append(msg)
    if re.search(r"\d", re.sub(re.escape(skill), "", bullet, flags=re.I)):
        problems.append("bullet contains a number")
    if re.search(OUTCOME_WORDS, bullet):
        problems.append("bullet claims a result or outcome (describe only what was built)")
    return problems


def _bullet_call(chat, resume_text, skills, rejected=None):
    user = f"Skills to add (one bullet each, in this order): {', '.join(skills)}\n\nRESUME (header removed):\n{resume_body(resume_text)}"
    if rejected:
        user += "\n\nYour previous answer was rejected for these reasons; fix them:\n" + "\n".join(f"- {s}: {'; '.join(p)}" for s, p in rejected.items())
    out, _ = chat([{"role": "system", "content": BULLET_SYSTEM}, {"role": "user", "content": user}], BULLET_SCHEMA)
    return {b.get("skill", "").strip().lower(): b for b in out["bullets"] if isinstance(b, dict)}


def generate_bullets(resume_text, skills, chat=None):
    """One dict per skill, in order: dict(skill, ok=True, extends_project, bullet) or dict(skill, ok=False, error). One retry for rejects.
    The prompts are fixed and not tuned towards any score."""
    if chat is None:
        from .llm import chat_json
        chat = chat_json
    skills = list(dict.fromkeys(skills))
    if not skills:
        return []
    body, results, rejected = resume_body(resume_text), {}, {}
    got = _bullet_call(chat, resume_text, skills)
    for s in skills:
        item = got.get(s.lower())
        problems = validate_bullet(item, s, body) if item else ["no entry returned"]
        if problems:
            rejected[s] = problems
        else:
            results[s] = item
    if rejected:
        got = _bullet_call(chat, resume_text, list(rejected), rejected)
        for s in rejected:
            item = got.get(s.lower())
            if item and not validate_bullet(item, s, body):
                results[s] = item
    return [dict(skill=s, ok=True, extends_project=results[s]["extends_project"].strip(), bullet=results[s]["bullet"].strip()) if s in results
            else dict(skill=s, ok=False, error=f"Could not write a bullet for {s}") for s in skills]


def bullet_marker(body):
    """The list marker the resume uses for projects (first of the usual markers found at a line start), else '-'."""
    for line in body.split("\n"):
        m = re.match(r"\s*([-•*–])\s", line)
        if m:
            return m.group(1)
    return "-"


def build_revised_text(resume_text, bullets):
    """Original text (header included) plus one line per validated bullet, in the resume's own list style. Returns (text, added_lines)."""
    ok = [b for b in bullets if b.get("ok")]
    if not ok:
        return resume_text, []
    marker = bullet_marker(resume_body(resume_text))
    added = [f"{marker} {b['extends_project']}: {b['bullet']}" for b in ok]
    return resume_text.rstrip() + "\n\n" + "\n".join(added) + "\n", added


def added_lines(original, revised):
    """Lines of `revised` that are new or changed compared with `original` (used to highlight edits, including the user's own)."""
    a, b = original.split("\n"), revised.split("\n")
    out = []
    for op, _, _, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op in ("insert", "replace"):
            out.extend(line for line in b[j1:j2] if line.strip())
    return out


# ------------------------------------------------------------------ retrieval effect (in memory, read-only)
def _ranks(order):
    return {s: i for i, s in enumerate(order, 1)}


def retrieval_effect(parsed, student_id, revised_text, students, retriever, embed=None, k_pool=50):
    """Hybrid (BM25 + dense, RRF k=60) rank of one student before and after replacing their resume text, among the eligible students.
    Reads dense similarities from the existing index (`retriever.retrieve`), embeds the revised text in memory and rebuilds BM25 with
    only that document replaced. Nothing is written to Chroma or to the student data."""
    elig = eligible_ids(parsed, students)
    if student_id not in elig:
        return dict(eligible=False)
    if embed is None:
        from .index import embedder
        embed = lambda texts: embedder().encode(texts, normalize_embeddings=True)
    from .config import QUERY_PREFIX
    query = retriever.query_text(parsed)
    sims = {h["id"]: h["similarity"] for h in retriever.retrieve(parsed, k=len(elig))[0]}
    qvec, dvec = embed([QUERY_PREFIX + query, revised_text])
    sim_before, sim_after = sims[student_id], float(dvec @ qvec)

    def hybrid(sim_map, index):
        dense = sorted(elig, key=lambda s: (-sim_map[s], s))
        bm = index.rank(query, elig)
        score = rrf_scores([bm, dense], RRF_K)
        order = sorted(score, key=lambda s: (-score[s], s))
        return _ranks(dense)[student_id], _ranks(bm)[student_id], _ranks(order)[student_id], score[student_id]

    d0, b0, h0, r0 = hybrid(sims, Bm25Index(students))
    changed = {**students, student_id: dict(students[student_id], resume_text=revised_text)}
    d1, b1, h1, r1 = hybrid({**sims, student_id: sim_after}, Bm25Index(changed))
    return dict(eligible=True, eligible_count=len(elig), pool=k_pool,
                sim_before=sim_before, sim_after=sim_after, dense_rank_before=d0, dense_rank_after=d1,
                bm25_rank_before=b0, bm25_rank_after=b1, hybrid_rank_before=h0, hybrid_rank_after=h1, rrf_before=r0, rrf_after=r1,
                in_pool_before=h0 <= k_pool, in_pool_after=h1 <= k_pool)


def place_in_full_list(full, student_id, new_score, effect, threshold, top_n=10):
    """Where `new_score` would land in the cached full list: the student's old entry is replaced by the new one if the revised text
    keeps them in the pool of 50, removed if it pushes them out, added if it brings them in (the pool's last member would then drop out,
    which is not simulated). Returns rank by score, group, Top-10 cutoff of the cached list and the threshold relation."""
    rows = [dict(id=r["id"], score=r["score"], rrf=r["rrf"]) for r in full["ranked"] if r["id"] != student_id and r["score"] is not None]
    cutoff = full["ranked"][top_n - 1]["score"] if len(full["ranked"]) >= top_n else None
    if effect.get("in_pool_after"):
        rows.append(dict(id=student_id, score=new_score, rrf=effect["rrf_after"]))
    rows.sort(key=lambda r: (-r["score"], -r["rrf"], r["id"]))
    rank = next((i for i, r in enumerate(rows, 1) if r["id"] == student_id), None)
    if rank is None:
        group = None
    else:
        group = "Top 10" if rank <= top_n else ("Also suited" if new_score >= threshold else "Below threshold")
    return dict(rank=rank, group=group, pool_size=len(rows), top10_cutoff=cutoff, threshold=threshold,
                at_or_above_threshold=new_score >= threshold, entered_pool=bool(effect.get("in_pool_after") and not effect.get("in_pool_before")),
                left_pool=bool(effect.get("in_pool_before") and not effect.get("in_pool_after")))


def placement_text(p, new_score):
    if p["rank"] is None:
        return (f"The revised text would put the student outside the pool of 50, so they would not be scored. "
                f"(A score of {new_score} is {'at or above' if p['at_or_above_threshold'] else 'below'} the threshold of {p['threshold']}.)")
    s = (f"With the new score {new_score} the student would rank {p['rank']} of {p['pool_size']} in the pool by score, group: {p['group']}. "
         f"The threshold is {p['threshold']} ({'at or above' if p['at_or_above_threshold'] else 'below'}).")
    if p["top10_cutoff"] is not None:
        s += f" The Top-10 cutoff of the cached list is {p['top10_cutoff']}."
    if p["entered_pool"]:
        s += " The student would enter the pool; the pool's last member would drop out (not simulated)."
    if p["left_pool"]:
        s += " The student was in the pool before and would leave it."
    return s
