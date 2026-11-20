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


def resume_body(resume_text):
    """Resume without its header line (name, email, phone): used for the suggestion call so no identity reaches the prompt."""
    return "\n".join(resume_text.split("\n")[1:]).strip()


SUGGEST_SCHEMA = {
    "type": "object",
    "properties": {"suggestions": {"type": "array", "maxItems": 8, "items": {
        "type": "object",
        "properties": {"gap": {"type": "string"}, "suggestion": {"type": "string"}},
        "required": ["gap", "suggestion"], "additionalProperties": False}}},
    "required": ["suggestions"], "additionalProperties": False,
}

SUGGEST_SYSTEM = """You are a careful career advisor for a student applying to a company requirement. You get the requirement, the skills the student appears to be missing, and the student's resume (without name or contact details).

Rules:
- Never invent experience and never tell the student to claim skills they do not have.
- Phrase each suggestion as: "If you have done X, add a bullet describing it; if not, learn X by ..." with a concrete way to learn or practise it.
- If the resume only describes a technology indirectly (for example endpoints over a database), suggest naming the technology explicitly (for example REST and SQL) if the student really used it.
- One suggestion per gap, at most two sentences each. Do not mention or guess the student's name, gender, region or college.
Reply with the JSON object only."""


def suggest_improvements(requirement, parsed, resume_text, must_gaps, nice_gaps, chat=None):
    """One LLM call (JSON schema, temperature 0, thinking off, on-disk cached). Returns [{gap, suggestion}]."""
    if chat is None:
        from .llm import chat_json
        chat = chat_json
    user = (f"REQUIREMENT (original text):\n{requirement.strip()}\n\n"
            f"Missing must-have skills: {', '.join(must_gaps) or 'none'}\n"
            f"Missing nice-to-have skills: {', '.join(nice_gaps) or 'none'}\n\n"
            f"RESUME (header removed):\n{resume_body(resume_text)}")
    out, _ = chat([{"role": "system", "content": SUGGEST_SYSTEM}, {"role": "user", "content": user}], SUGGEST_SCHEMA)
    return out["suggestions"]


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
