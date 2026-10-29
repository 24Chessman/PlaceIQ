"""LLM re-ranking: score, matched/missing skills and a short explanation for each retrieved candidate."""
from .llm import chat_json

SCHEMA = {  # property order matters: the model writes the evidence first and the score last
    "type": "object",
    "properties": {
        "matched_skills": {"type": "array", "items": {"type": "string"}},
        "missing_skills": {"type": "array", "items": {"type": "string"}},
        "explanation": {"type": "string", "maxLength": 400},
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
    },
    "required": ["matched_skills", "missing_skills", "explanation", "score"],
    "additionalProperties": False,
}

FAIRNESS_LINE = ("- Ignore the student's name, gender, region and college prestige. They must not change the score; "
                 "judge only demonstrated skills and stated eligibility facts.\n")

SYSTEM = """You are a careful technical recruiter helping a campus placement cell. You get a company's hiring requirement, the skills extracted from it, and one student's resume. Score how well the student fits the role.

Rules:
- Judge only skills the resume actually demonstrates through projects, internships or described work. A skill counts when the work described clearly requires it, even if the exact keyword never appears (for example, building a service whose endpoints a mobile app calls demonstrates REST API skills; packaging an app so it runs identically on every laptop demonstrates Docker).
- Skills implied by a tool the student used count too (someone who built web apps with Django has used Python).
- Ignore keyword lists that are not backed by evidence. A long skills list with generic coursework projects and no described work is NOT evidence. Work described as a small tutorial or basic exercise earns only partial credit.
- If the resume clearly states a CGPA, active-backlog count or branch that violates the requirement's eligibility rules, give a score of at most 10 and name the broken rule.
{fairness}- Check every must-have skill one by one against the resume. A must-have with no evidence goes into missing_skills, however good the rest of the resume is.
- Score from 0 to 100 AFTER listing matched and missing skills: 85-100 every must-have is clearly demonstrated (and some nice-to-haves); 60-84 every must-have is shown but some only weakly; with one must-have missing the score is at most 69; with half or more of the must-haves missing at most 40; nothing relevant, or a broken eligibility rule, at most 9.
- matched_skills: required or nice-to-have skills the resume demonstrates. missing_skills: must-have skills it does not demonstrate.
- explanation: at most two short, concrete sentences citing the evidence (or its absence).
Reply with the JSON object only."""


def build_messages(requirement_text, parsed, resume_text, fairness_instruction=True):
    system = SYSTEM.replace("{fairness}", FAIRNESS_LINE if fairness_instruction else "")
    elig = []
    if parsed.get("min_cgpa") is not None:
        elig.append(f"minimum CGPA {parsed['min_cgpa']}")
    if parsed.get("max_backlogs") is not None:
        elig.append(f"at most {parsed['max_backlogs']} active backlogs")
    if parsed.get("allowed_branches"):
        elig.append("branches: " + ", ".join(parsed["allowed_branches"]))
    user = (f"REQUIREMENT (original text):\n{requirement_text.strip()}\n\n"
            f"Must-have skills: {', '.join(parsed.get('must_have_skills', [])) or 'none listed'}\n"
            f"Nice-to-have skills: {', '.join(parsed.get('nice_to_have_skills', [])) or 'none listed'}\n"
            f"Eligibility rules: {'; '.join(elig) or 'none'}\n\n"
            f"RESUME:\n{resume_text.strip()}")
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def score_candidate(requirement_text, parsed, resume_text, fairness_instruction=True):
    return chat_json(build_messages(requirement_text, parsed, resume_text, fairness_instruction), SCHEMA)
