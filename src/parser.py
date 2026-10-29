"""Requirement text -> structured query + hard eligibility filters, via one schema-constrained LLM call."""
from .config import BRANCHES
from .llm import chat_json

SCHEMA = {
    "type": "object",
    "properties": {
        "role_title": {"type": "string"},
        "must_have_skills": {"type": "array", "items": {"type": "string"}},
        "nice_to_have_skills": {"type": "array", "items": {"type": "string"}},
        "min_cgpa": {"type": ["number", "null"]},
        "allowed_branches": {"type": "array", "items": {"type": "string", "enum": BRANCHES}},
        "max_backlogs": {"type": ["integer", "null"]},
        "semantic_query": {"type": "string"},
    },
    "required": ["role_title", "must_have_skills", "nice_to_have_skills", "min_cgpa", "allowed_branches",
                 "max_backlogs", "semantic_query"],
    "additionalProperties": False,
}

SYSTEM = """You turn a company's free-text hiring requirement into structured JSON for a campus placement system.
The text can be messy: WhatsApp style, Hinglish (Hindi written in English letters), typos, abbreviations, bullet fragments or vague wording. Read it carefully and extract only what it says.

Fields:
- role_title: short job title.
- must_have_skills: skills the text requires (words like must, required, needed, should know, compulsory, strong in, pakka, chahiye). Use short standard names (e.g. "Python", "REST APIs", "Machine Learning"); fix typos and expand abbreviations.
- nice_to_have_skills: skills described as a plus, bonus, advantage, good to have, preferred, "toh aur accha". Do not repeat a must-have here.
- min_cgpa: the minimum CGPA as a number, or null if no CGPA cutoff is stated (also null if the text says CGPA does not matter). "6 se upar", "7+", ">= 6.5" all give a number.
- allowed_branches: the branches the company accepts, using exactly these labels: CSE, IT, ICT, ECE, EE, Mechanical, Civil, M.Sc IT. Map: CS / CSE / computer science -> CSE; IT / information technology -> IT; ICT -> ICT; ECE / electronics and communication -> ECE; EE / electrical -> EE; Mech / mechanical -> Mechanical; Civil -> Civil; MSc IT / M.Sc IT -> M.Sc IT. Use an empty list if the text accepts any branch or names no branch.
- max_backlogs: the maximum number of active backlogs allowed as an integer. "no backlogs", "zero backlogs", "backlog allowed nahi", "no pending backlogs" -> 0; "max 2 backlogs", "one backlog is okay" -> that number. Use null if backlogs are not mentioned or the text says they do not matter.
- semantic_query: one plain-prose paragraph describing the ideal candidate (role, the skills and the kind of hands-on work they should have done). Do not put CGPA, branch or backlog rules in it.

Examples (invented; do not reuse their content):

Input: urgent!! need 2 game dev freshers, unity + c# compulsory, blender ya 3d modelling aata ho toh best. 7.2 cgpa min, max 2 backlogs, only IT/ECE/Mechanical
Output: {"role_title": "Game Developer", "must_have_skills": ["Unity", "C#"], "nice_to_have_skills": ["Blender", "3D Modelling"], "min_cgpa": 7.2, "allowed_branches": ["IT", "ECE", "Mechanical"], "max_backlogs": 2, "semantic_query": "A fresher game developer who has built playable games in Unity with C# scripting and, ideally, has made or imported 3D models in Blender."}

Input: Position: Network Support Engineer. Candidates should have a working knowledge of routing and switching, firewalls and packet analysis. Python scripting is desirable. Minimum CGPA 6.8; no active backlogs permitted; Electronics, Electrical or IT students only.
Output: {"role_title": "Network Support Engineer", "must_have_skills": ["Routing and Switching", "Firewalls", "Packet Analysis"], "nice_to_have_skills": ["Python"], "min_cgpa": 6.8, "allowed_branches": ["ECE", "EE", "IT"], "max_backlogs": 0, "semantic_query": "A network support engineer comfortable configuring routers and switches, setting firewall rules and analysing packet captures, who can also automate routine checks with Python scripts."}

Input: we want good coders who know java and some web stuff, nothing fancy. any branch fine, cgpa is not a criteria
Output: {"role_title": "Java Developer", "must_have_skills": ["Java"], "nice_to_have_skills": ["Web Development"], "min_cgpa": null, "allowed_branches": [], "max_backlogs": null, "semantic_query": "A programmer with solid Java skills who has also built simple web pages or web applications."}

Reply with the JSON object only."""


def parse_requirement(text):
    """Returns (parsed dict, info). parsed follows SCHEMA."""
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Input: {text.strip()}\nOutput:"}]
    parsed, info = chat_json(messages, SCHEMA)
    parsed["allowed_branches"] = list(dict.fromkeys(parsed["allowed_branches"]))
    if set(parsed["allowed_branches"]) == set(BRANCHES):
        parsed["allowed_branches"] = []
    return parsed, info
