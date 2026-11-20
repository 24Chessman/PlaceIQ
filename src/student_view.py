"""Prototype extension, student view (not evaluated; the paper's evaluation covers the frozen top-10 pipeline only):
eligibility table, skill gaps, improvement suggestions (one extra LLM call) and a what-if re-score. The re-ranker
(prompt, schema, Qwen3.5 4B via Ollama, temperature 0, thinking off) is reused unchanged.
"""
from .extensions import TOP_N

HYPOTHETICAL_TEMPLATE = "Project (hypothetical): built and deployed a small application using {skill}, with hands-on use of {skill}."


def eligibility_table(parsed, student):
    """Rows: rule, required, student, passed, note. A student cannot fix these by editing the resume."""
    note = "not fixable by editing the resume"
    rows = []
    mc = parsed.get("min_cgpa")
    rows.append(dict(rule="CGPA", required="no cutoff" if mc is None else f"at least {mc}", student=f"{student['cgpa']:.2f}",
                     passed=mc is None or student["cgpa"] >= mc, note=note))
    br = parsed.get("allowed_branches") or []
    rows.append(dict(rule="Branch", required="any" if not br else ", ".join(br), student=student["branch"],
                     passed=not br or student["branch"] in br, note=note))
    mb = parsed.get("max_backlogs")
    rows.append(dict(rule="Active backlogs", required="no limit" if mb is None else f"at most {mb}",
                     student=str(student["active_backlogs"]), passed=mb is None or student["active_backlogs"] <= mb, note=note))
    return rows


def skill_gaps(parsed, scored):
    """(missing must-haves, missing nice-to-haves): parsed skills the re-ranker did not list as matched."""
    matched = {m.strip().lower() for m in scored["matched_skills"]}
    must = [s for s in parsed.get("must_have_skills", []) if s.strip().lower() not in matched]
    nice = [s for s in parsed.get("nice_to_have_skills", []) if s.strip().lower() not in matched]
    return must, nice


def coverage(parsed, scored, assumed=()):
    """Deterministic skill-coverage projection (no LLM call): how many must-have / nice-to-have skills are matched now, and how many
    would be if the assumed skills were gained. Arithmetic on the skill lists only, not a predicted score or rank.
    Skills outside the parsed requirement are ignored."""
    matched = {m.strip().lower() for m in scored["matched_skills"]}
    gained = {a.strip().lower() for a in assumed}
    out = {}
    for kind, skills in (("must", parsed.get("must_have_skills", [])), ("nice", parsed.get("nice_to_have_skills", []))):
        keys = [s.strip().lower() for s in skills]
        before = sum(k in matched for k in keys)
        after = sum(k in matched or k in gained for k in keys)
        out[kind] = dict(total=len(keys), before=before, after=after,
                         gained=[s for s in skills if s.strip().lower() in gained and s.strip().lower() not in matched])
    return out


def coverage_text(cov):
    """One sentence per skill group, e.g. 'Currently 3 of 5 required skills; if you gain TypeScript and Figma: 5 of 5.'"""
    def join(items):
        return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]

    lines = []
    for kind, label in (("must", "required"), ("nice", "nice-to-have")):
        c = cov[kind]
        if c["total"] == 0:
            lines.append(f"No {label} skills listed in the requirement.")
        elif c["gained"]:
            lines.append(f"Currently {c['before']} of {c['total']} {label} skills; if you gain {join(c['gained'])}: {c['after']} of {c['total']}.")
        else:
            lines.append(f"Currently {c['before']} of {c['total']} {label} skills.")
    return lines


def resume_body(resume_text):
    """Resume without its header line (name, email, phone): used for the suggestion call so no identity reaches the prompt."""
    return "\n".join(resume_text.split("\n")[1:]).strip()


SUGGEST_SCHEMA = {
    "type": "object",
    "properties": {"suggestions": {"type": "array", "maxItems": 8, "items": {
        "type": "object",
        "properties": {
            "skill": {"type": "string"},
            "why_it_matters": {"type": "string"},
            "what_to_build": {"type": "string"},
            "how_to_learn": {"type": "array", "minItems": 2, "maxItems": 3, "items": {"type": "string"}},
            "resume_bullet_example": {"type": "string"},
        },
        "required": ["skill", "why_it_matters", "what_to_build", "how_to_learn", "resume_bullet_example"],
        "additionalProperties": False}}},
    "required": ["suggestions"], "additionalProperties": False,
}

SUGGEST_SYSTEM = """You are a careful career advisor for a student applying to a company requirement. You get the requirement, a list of skills the student is missing, and the student's resume without name or contact details.

For EACH missing skill, write one entry with these fields:
- skill: the skill name exactly as given.
- why_it_matters: one sentence that ties the skill to THIS requirement (its role, its other skills), not a general statement.
- what_to_build: one concrete mini-project. Say what it does, which tools it uses, and build it on the student's existing stack and projects from the resume where possible (extend one of their real projects). Name real technologies only.
- how_to_learn: 2 to 3 concrete steps, each a specific action (what to read in the official documentation, what small exercise to do, what to deploy), in order.
- resume_bullet_example: one sample resume bullet the student may use ONLY AFTER the work is done. It must describe what was built in the mini-project from what_to_build. No numbers, no percentages, no employer or company names, no claims of results or outcomes.

Rules:
- Never invent experience and never tell the student to claim skills they do not have.
- If the resume seems to describe the skill's work without naming the technology, say in why_it_matters to name the technology explicitly if they really used it.
- Write real, specific text. Do not use placeholders such as the letter X, "..." or angle brackets. Do not give URLs. Do not name courses, tutorials, books or certificates; refer to the official documentation of the technology instead.
- Do not say whether the skill is required, mandatory, optional or a bonus: the app shows that label itself.
- The bullet describes only what was built, in plain past tense. It must not claim results or outcomes (nothing reduced, improved, increased, faster, fewer, boosted or optimised).
- Do not mention or guess the student's name, gender, region or college.
Reply with the JSON object only."""

MIN_LEN = dict(why_it_matters=40, what_to_build=60, resume_bullet_example=40, step=25)
PLACEHOLDER_PATTERNS = [
    (r"\bX\b", "contains the placeholder 'X'"),
    (r"\.\.\.|…", "contains '...'"),
    (r"[<>{}\[\]]", "contains brackets or braces"),
    (r"(?i)https?://|www\.|\.com\b|\.org\b", "contains a URL"),
    (r"(?i)\bif you have (done|used|created)\b", "copies the template wording"),
    (r"(?i)\b(tbd|lorem|placeholder|your project name|your company)\b", "contains placeholder wording"),
    (r"(?i)\b(courses?|tutorials?|bootcamps?|certificat\w*|specialization|udemy|coursera|youtube|freecodecamp)\b", "names a course, tutorial or platform"),
]
BULLET_BAD = [(r"(?i)\b(at|for|with)\s+[A-Z][a-z]+ (Inc|Ltd|Technologies|Systems|Labs|Solutions)\b", "bullet names an employer")]
OUTCOME_WORDS = r"(?i)\b(reduc\w*|improv\w*|increas\w*|faster|fewer|eliminat\w*|boost\w*|optimi[sz]\w*)\b"
# the Required / Nice-to-have label is rendered by the UI from the parsed requirement; free text must not contradict it
REQUIRED_WORDS = r"(?i)\b(mandatory|required|requires|must[- ]have|essential|compulsory)\b"
OPTIONAL_WORDS = r"(?i)\b(bonus|nice[- ]to[- ]have|optional|desirable|preferred|a plus)\b"


def validate_suggestion(item, skill, kind=None):
    """Returns a list of problems (empty = valid): placeholder patterns, URLs, course names, wrong skill, too-short or generic text,
    result/outcome claims or numbers in the bullet (the skill name itself is removed before the digit check), and wording that
    contradicts kind ("Required" / "Nice-to-have", taken from the parsed requirement)."""
    import re
    problems = []
    for key in ("skill", "why_it_matters", "what_to_build", "resume_bullet_example"):
        if not isinstance(item.get(key), str) or not item[key].strip():
            problems.append(f"{key} is missing")
    steps = item.get("how_to_learn")
    if not isinstance(steps, list) or not 2 <= len(steps) <= 3 or not all(isinstance(s, str) for s in steps):
        problems.append("how_to_learn must have 2 to 3 steps")
        steps = []
    if problems:
        return problems
    if item["skill"].strip().lower() != skill.strip().lower():
        problems.append(f"skill is '{item['skill']}', expected '{skill}'")
    for key, n in (("why_it_matters", MIN_LEN["why_it_matters"]), ("what_to_build", MIN_LEN["what_to_build"]), ("resume_bullet_example", MIN_LEN["resume_bullet_example"])):
        if len(item[key].strip()) < n:
            problems.append(f"{key} is too short")
    if any(len(s.strip()) < MIN_LEN["step"] for s in steps):
        problems.append("a how_to_learn step is too short")
    text = " ".join([item["why_it_matters"], item["what_to_build"], *steps, item["resume_bullet_example"]])
    for pat, msg in PLACEHOLDER_PATTERNS:
        if re.search(pat, text):
            problems.append(msg)
    for pat, msg in BULLET_BAD:
        if re.search(pat, item["resume_bullet_example"]):
            problems.append(msg)
    if re.search(r"\d", re.sub(re.escape(skill), "", item["resume_bullet_example"], flags=re.I)):
        problems.append("bullet contains a number")
    if re.search(OUTCOME_WORDS, item["resume_bullet_example"]):
        problems.append("bullet claims a result or outcome (describe only what was built)")
    if kind == "Nice-to-have" and re.search(REQUIRED_WORDS, text):
        problems.append("calls a nice-to-have skill required or mandatory")
    if kind == "Required" and re.search(OPTIONAL_WORDS, text):
        problems.append("calls a required skill optional or a bonus")
    tokens = [t for t in re.split(r"[^a-z0-9+#.]+", skill.lower()) if len(t) > 1]
    if tokens and not any(t in (item["what_to_build"] + " " + item["resume_bullet_example"]).lower() for t in tokens):
        problems.append("what_to_build and the bullet never mention the skill (generic text)")
    return problems


def _suggest_call(chat, requirement, resume_text, gaps, rejected=None):
    user = (f"REQUIREMENT (original text):\n{requirement.strip()}\n\n"
            f"Missing skills (write one entry for each, in this order): {', '.join(gaps)}\n\n"
            f"RESUME (header removed):\n{resume_body(resume_text)}")
    if rejected:
        user += "\n\nYour previous answer was rejected for these reasons; write specific text and fix them:\n" + \
                "\n".join(f"- {s}: {'; '.join(p)}" for s, p in rejected.items())
    out, _ = chat([{"role": "system", "content": SUGGEST_SYSTEM}, {"role": "user", "content": user}], SUGGEST_SCHEMA)
    return {s.get("skill", "").strip().lower(): s for s in out["suggestions"] if isinstance(s, dict)}


def suggest_improvements(requirement, parsed, resume_text, must_gaps, nice_gaps, chat=None):
    """One LLM call for all gaps (JSON schema, temperature 0, thinking off, on-disk cached); every entry is validated; skills that fail
    are retried once in a second call that states why they were rejected. Returns one dict per gap, in order: the validated entry
    plus ok=True, or dict(skill, ok=False, error='Could not generate a specific suggestion for <skill>'). Every entry carries
    kind = "Required" or "Nice-to-have", set here from the gap lists (i.e. the parsed requirement), never by the model."""
    if chat is None:
        from .llm import chat_json
        chat = chat_json
    gaps = list(dict.fromkeys(must_gaps + nice_gaps))
    if not gaps:
        return []
    kinds = {g: ("Required" if g in must_gaps else "Nice-to-have") for g in gaps}
    results, rejected = {}, {}
    got = _suggest_call(chat, requirement, resume_text, gaps)
    for g in gaps:
        item = got.get(g.lower())
        problems = validate_suggestion(item, g, kinds[g]) if item else ["no entry returned"]
        if problems:
            rejected[g] = problems
        else:
            results[g] = item
    if rejected:
        got = _suggest_call(chat, requirement, resume_text, list(rejected), rejected)
        for g in rejected:
            item = got.get(g.lower())
            if item and not validate_suggestion(item, g, kinds[g]):
                results[g] = item
    return [dict(results[g], ok=True, kind=kinds[g]) if g in results
            else dict(skill=g, ok=False, kind=kinds[g], error=f"Could not generate a specific suggestion for {g}") for g in gaps]


def what_if_text(resume_text, assumed_skills):
    """Resume with one short hypothetical project bullet per assumed skill appended (the re-ranker credits described work, not a
    bare skills line). Every added line starts with 'Project (hypothetical):'; the original text is untouched."""
    bullets = "\n".join("- " + HYPOTHETICAL_TEMPLATE.format(skill=s) for s in assumed_skills)
    return resume_text.rstrip() + "\n\n" + bullets + "\n"


def position_vs(score, threshold, top10_cutoff=None):
    """Plain-language position of a score against the threshold and (if known) the Top-10 cutoff (score of rank 10)."""
    s = f"Score {score} is {'at or above' if score >= threshold else 'below'} the threshold of {threshold}."
    if top10_cutoff is not None:
        s += f" The Top-10 cutoff for this requirement is {top10_cutoff}: this score would be {'at or above' if score >= top10_cutoff else 'below'} it."
    return s


def what_if(requirement, parsed, resume_text, assumed_skills, score_fn=None):
    """Re-scores the resume with the assumed skills appended, using the same re-ranker. Returns dict(text, scored)."""
    if score_fn is None:
        from .rerank import score_candidate
        score_fn = lambda t, p, r: score_candidate(t, p, r, True)[0]
    text = what_if_text(resume_text, assumed_skills)
    return dict(text=text, scored=score_fn(requirement, parsed, text))


def top10_cutoff(full):
    """Score of the 10th candidate in a full list, or None."""
    r = full["ranked"] if full else []
    return r[full.get("top_n", TOP_N) - 1]["score"] if len(r) >= full.get("top_n", TOP_N) else None
