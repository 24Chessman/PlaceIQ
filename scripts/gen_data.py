"""Regenerate the whole synthetic dataset deterministically (SEED=42). No LLM, no network.

    python scripts/gen_data.py

Writes data/: students.jsonl, students_truth.jsonl, requirements.jsonl, requirements_truth.json,
qrels.csv, spotcheck.csv. Reads data/skills_taxonomy.json and data/name_pools.json (hand-written).
Labelling function: see relevance() and docs/DATA.md.
"""
import csv
import json
import random
import re
from collections import Counter, defaultdict
from math import ceil
from pathlib import Path

SEED = 42
N_STUDENTS = 500
MIN_QUOTA = 35  # guaranteed students per role family
MAX_ROUNDS = 10
Q_RANGE = (8, 40)  # allowed qualified students per requirement
HARD_SHARE = 0.4
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

TAX = json.loads((DATA / "skills_taxonomy.json").read_text(encoding="utf-8"))
SK = {s["name"]: s for s in TAX["skills"]}
FAMILIES = TAX["families"]
NAME_POOLS = json.loads((DATA / "name_pools.json").read_text(encoding="utf-8"))

DUAL_P = 0.65  # share of students with a second, shallower skill profile
ARCH_COUNTS = {
    "standard": 150, "paraphrased": 100, "implied": 50, "abbreviated_noisy": 50,
    "sparse_strong": 40, "stuffed_weak": 50, "ineligible_strong": 35, "generalist_average": 25,
}
HARD = ("paraphrased", "implied", "abbreviated_noisy", "sparse_strong")

# ---------------------------------------------------------------- skills helpers


def effective(levels):
    """Closure of explicit levels under implied_by (group level = min of its members)."""
    eff = {k: v for k, v in levels.items() if v > 0}
    changed = True
    while changed:
        changed = False
        for s in TAX["skills"]:
            for grp in s["implied_by"]:
                lv = min(eff.get(g, 0) for g in grp)
                if lv > eff.get(s["name"], 0):
                    eff[s["name"]] = lv
                    changed = True
    return eff


def skill_terms(name):
    return [name] + SK[name]["aliases"]


def term_pattern(t):
    # only the single letter "C" is case-sensitive; '.' before a term blocks "js" inside "Node.js"
    return re.compile(r"(?<![\w+#.])" + re.escape(t) + r"(?![\w+#])", 0 if t == "C" else re.I)


# ---------------------------------------------------------------- student model

BRANCH_NAMES = {
    "CSE": ["Computer Science and Engineering", "Computer Science & Engineering", "CSE"],
    "IT": ["Information Technology", "IT"],
    "ICT": ["Information and Communication Technology", "ICT"],
    "ECE": ["Electronics and Communication Engineering", "Electronics & Communication Engineering", "ECE"],
    "EE": ["Electrical Engineering", "EE"],
    "Mechanical": ["Mechanical Engineering", "Mechanical"],
    "Civil": ["Civil Engineering", "Civil"],
    "M.Sc IT": ["M.Sc. (IT)", "M.Sc IT", "Master of Science in Information Technology"],
}
FAMILY_W = {  # family popularity: the share of students above the guaranteed minimum (order = FAMILIES)
    "software": [18.4, 4.8, 22, 9.8, 10.7, 6.3, 9.8, 8.8, 9.3, 11.5, 2.8, 12.6],
}
_SW = {"CSE": 35, "IT": 22, "ICT": 14, "ECE": 10, "EE": 3, "Mechanical": 3, "Civil": 1, "M.Sc IT": 12}
_MIXED = {"CSE": 22, "IT": 16, "ICT": 10, "ECE": 14, "EE": 8, "Mechanical": 10, "Civil": 8, "M.Sc IT": 12}
_SEC = {"CSE": 30, "IT": 20, "ICT": 12, "ECE": 20, "EE": 4, "Mechanical": 2, "Civil": 0, "M.Sc IT": 12}
BRANCH_MIX = {f: _SW for f in FAMILIES}  # branch is drawn given the family
BRANCH_MIX.update({
    "embedded_iot": {"CSE": 12, "IT": 4, "ICT": 4, "ECE": 40, "EE": 22, "Mechanical": 10, "Civil": 1, "M.Sc IT": 2},
    "data_analysis": _MIXED, "business_analysis": _MIXED, "qa_testing": _MIXED,
    "cybersecurity": _SEC, "devops_cloud": _SEC,
})
STACKS = {  # ordered by centrality; the first four are always kept
    "backend": [
        ["Python", "Django", "PostgreSQL", "REST APIs", "Docker", "Redis"],
        ["Python", "Flask", "SQL", "REST APIs", "MongoDB", "Docker"],
        ["Python", "FastAPI", "PostgreSQL", "REST APIs", "Redis", "AWS"],
        ["Java", "Spring Boot", "Microservices", "SQL", "REST APIs", "Docker"],
        ["Node.js", "Express.js", "REST APIs", "MongoDB", "Redis", "Docker"],
        ["Java", "Spring Boot", "Microservices", "PostgreSQL", "Apache Kafka"],
    ],
    "frontend": [
        ["JavaScript", "React", "HTML/CSS", "TypeScript", "Figma"],
        ["JavaScript", "Angular", "TypeScript", "HTML/CSS"],
        ["JavaScript", "Vue.js", "HTML/CSS", "Figma"],
        ["React", "JavaScript", "HTML/CSS", "REST APIs", "TypeScript"],
    ],
    "fullstack": [
        ["Node.js", "React", "MongoDB", "REST APIs", "JavaScript", "Authentication"],
        ["Next.js", "PostgreSQL", "TypeScript", "React", "Authentication", "Docker"],
        ["Next.js", "PostgreSQL", "TypeScript", "Docker", "Authentication"],
        ["Python", "Django", "React", "PostgreSQL", "JavaScript", "REST APIs"],
        ["Node.js", "Express.js", "Angular", "MongoDB", "Authentication"],
        ["Node.js", "React", "MongoDB", "Express.js", "Docker"],
    ],
    "data_analysis": [
        ["SQL", "Excel", "Power BI", "Statistics", "Data Visualization"],
        ["Python", "Pandas", "SQL", "Excel", "Tableau", "Statistics"],
        ["Excel", "SQL", "Power BI", "Data Visualization", "Statistics"],
        ["Python", "Pandas", "Statistics", "Data Visualization", "SQL"],
    ],
    "ml": [
        ["Python", "Machine Learning", "scikit-learn", "Pandas", "Statistics"],
        ["Python", "Deep Learning", "PyTorch", "Machine Learning", "Computer Vision"],
        ["Python", "NLP", "Deep Learning", "TensorFlow", "Machine Learning"],
        ["Python", "NLP", "PyTorch", "scikit-learn", "Machine Learning"],
    ],
    "data_engineering": [
        ["SQL", "ETL Pipelines", "Apache Spark", "Python", "Airflow"],
        ["SQL", "Apache Spark", "Airflow", "Apache Kafka", "Python", "Data Warehousing"],
        ["SQL", "Data Warehousing", "ETL Pipelines", "Apache Spark", "AWS"],
    ],
    "devops_cloud": [
        ["Linux", "Docker", "CI/CD", "AWS", "Kubernetes", "Terraform"],
        ["Linux", "Docker", "CI/CD", "AWS", "Python"],
        ["Linux", "Docker", "CI/CD", "Kubernetes", "AWS", "Terraform"],
        ["Raspberry Pi", "Docker", "CI/CD", "AWS", "Kubernetes"],  # home-lab route into DevOps (Linux is implied)
    ],
    "qa_testing": [
        ["Manual Testing", "Selenium", "API Testing", "Test Automation", "Java"],
        ["Manual Testing", "API Testing", "Selenium", "Test Automation", "Python"],
        ["Manual Testing", "Selenium", "API Testing", "SQL"],
    ],
    "mobile": [
        ["Android", "Kotlin", "REST APIs", "Java"],
        ["Android", "Kotlin", "REST APIs", "Flutter"],
        ["Flutter", "REST APIs", "Android"],
        ["React Native", "JavaScript", "REST APIs", "React"],
    ],
    "cybersecurity": [
        ["Network Security", "Linux", "Penetration Testing", "Vulnerability Assessment", "Python"],
        ["Network Security", "Linux", "Penetration Testing", "Cryptography"],
        ["Network Security", "Linux", "Cryptography", "Python"],
    ],
    "embedded_iot": [
        ["C", "Arduino", "MQTT", "Raspberry Pi", "Python"],
        ["C", "Arduino", "MQTT", "Raspberry Pi", "C++"],
        ["C", "C++", "RTOS", "Arduino"],
        ["C", "C++", "RTOS", "Linux"],
    ],
    "business_analysis": [
        ["Requirements Gathering", "Agile/Scrum", "JIRA", "Stakeholder Communication", "Process Modeling"],
        ["Agile/Scrum", "JIRA", "Requirements Gathering", "Stakeholder Communication", "Excel"],
        ["Requirements Gathering", "Stakeholder Communication", "Process Modeling", "SQL", "Excel"],
    ],
}
STACK_W = {  # relative popularity of the stacks above (same order); unlisted families are uniform
    "backend": [3, 1.5, 1.5, 4, 1, 3],
    "fullstack": [6, 4, 4, 1, 1, 5],
    "ml": [2.5, 1, 2.5, 4.5],
    "mobile": [1.5, 1, 1, 3],
    "embedded_iot": [3, 3, 1, 1],
}
CROSS = ["SQL", "Docker", "Linux", "Python", "JavaScript", "REST APIs", "Excel", "JIRA", "Statistics", "Java", "AWS"]
FAMILY_ROLE = {
    "backend": "Backend Development", "frontend": "Frontend Development", "fullstack": "Web Development",
    "data_analysis": "Data Analyst", "ml": "AI Research", "data_engineering": "Data Engineering",
    "devops_cloud": "DevOps", "qa_testing": "QA", "mobile": "Mobile App", "cybersecurity": "Security",
    "embedded_iot": "Embedded Systems", "business_analysis": "Business Analysis",
}
PROJECT_TITLES = {
    "backend": ["Online Bookstore Backend", "Hostel Complaint Portal", "Fee Payment Tracker", "Student Marks Service", "Event Registration System", "Inventory Management Service"],
    "frontend": ["Personal Portfolio Site", "Restaurant Menu Website", "Weather Dashboard", "Quiz Application UI", "College Fest Landing Page"],
    "fullstack": ["Campus Marketplace", "Blog Platform", "Expense Sharing App", "Job Board", "Online Course Portal"],
    "data_analysis": ["Sales Performance Review", "Customer Churn Study", "Covid Trend Report", "Student Result Analysis", "Retail Basket Analysis"],
    "ml": ["Loan Default Predictor", "Review Sentiment Classifier", "Crop Disease Detector", "House Price Estimator", "Resume Screening Assistant"],
    "data_engineering": ["Sales Reporting Refresh", "Log Processing Job", "Clickstream Aggregator", "Order Events Feed", "Nightly Reporting Loader"],
    "devops_cloud": ["Automated Deployment Setup", "Home Lab Server", "Monitoring Dashboard Setup", "Release Automation Project"],
    "qa_testing": ["Test Plan for Shopping Site", "Bug Hunt on Booking Portal", "Regression Suite for Banking Demo", "Quality Review of Ticketing App"],
    "mobile": ["Expense Tracker App", "Campus Navigator", "Habit Tracker", "Ride Share Prototype"],
    "cybersecurity": ["Lab Network Hardening", "CTF Practice Writeups", "Web App Security Review", "Incident Response Drill"],
    "embedded_iot": ["Smart Plant Watering", "Line Following Robot", "Home Automation Board", "Weather Station"],
    "business_analysis": ["Process Improvement Case Study", "Library System Requirements Pack", "Hospital Billing Workflow Redesign", "Business Case Competition Entry"],
}
GENERIC_PROJECTS = [
    ("Library Management System", "Developed as a mini project in a group of four as part of the semester curriculum."),
    ("Online Quiz Application", "Made for the practical examination under the guidance of the department faculty."),
    ("Attendance Register", "Group mini project submitted in the fifth semester; I handled the documentation and presentation."),
    ("Hotel Booking System", "Academic project completed with classmates; learned a lot about teamwork and deadlines."),
    ("Student Information Portal", "Collaborated with three friends on this assignment and presented it to the examiner."),
    ("Bus Pass Management", "Semester project, report and presentation prepared as per university guidelines."),
]
COMPANIES = ["Lumen Softworks", "Orbit Digital", "Tarang Systems", "BrightPath Technologies", "Pixelnest Solutions",
             "Vertex Infosoft", "Zenith Data Labs", "Mintleaf Technologies", "Harbor Light Systems", "Quillon Labs"]
COLLEGES = ["Narmada Institute of Technology", "Sabarmati College of Engineering", "Tapi Valley Institute of Engineering",
            "Vindhya Engineering College", "Kaveri School of Technology", "Godavari Institute of Science and Technology"]
OBJECTIVES = [
    "Seeking an entry-level role where I can apply what I have learnt and keep growing.",
    "Motivated final-year student looking for a challenging opportunity with a supportive team.",
    "Eager to contribute to real-world problems while learning from experienced colleagues.",
    "Hardworking and punctual; I enjoy teamwork and picking up new things quickly.",
]
ACHIEVEMENTS = [
    "Secured first place in the inter-department quiz.",
    "Completed 200+ practice problems on a competitive-programming website.",
    "Selected for the university cultural fest organising committee.",
    "Awarded a merit scholarship for academic performance in semester 3.",
    "Participated in a 24-hour hackathon organised by the college.",
    "Completed an NPTEL course on soft skills with an Elite certificate.",
    "Runner-up in a state-level paper presentation contest.",
    "Cleared a national-level aptitude olympiad round.",
]
STUFFED_ACHIEVEMENTS = [
    "Highly passionate about cutting-edge technologies and continuous learning.",
    "Quick learner who can pick up any new technology within days.",
    "Certified in multiple technologies through online platforms.",
    "Attended several webinars and workshops on emerging trends.",
]
EXTRAS = [
    "Member of the college photography club.",
    "Volunteer at NSS blood donation camps.",
    "Play cricket for the department team.",
    "Languages: English, Hindi, Gujarati.",
    "Hobbies: reading, sketching, travelling.",
    "Organised the registration desk for the technical fest.",
    "Learning the guitar in my free time.",
    "Treasurer of the literary society.",
]
TRAILERS = ["References available on request.", "I hereby declare that the information above is true to the best of my knowledge.", ""]
SECTION_TITLES = {
    "education": ["EDUCATION", "Education", "Academics"],
    "skills": ["SKILLS", "Technical Skills", "Skill Set"],
    "projects": ["PROJECTS", "Academic Projects", "Things I Built"],
    "internship": ["INTERNSHIP", "Experience", "Training"],
    "achievements": ["ACHIEVEMENTS", "Awards & Achievements", "Highlights"],
    "extras": ["EXTRA-CURRICULARS", "Interests", "Beyond the Classroom"],
    "objective": ["OBJECTIVE", "Career Objective", "About Me"],
}
CFG = {  # cap = max evidence sentences, nskills = max explicit skills
    "standard": dict(cap=10, nskills=10, nproj=(2, 3), intern=.55, tech=True, skills=True, cover=False),
    "paraphrased": dict(cap=10, nskills=8, nproj=(2, 3), intern=.55, tech=False, skills=False, cover=True),
    "implied": dict(cap=9, nskills=8, nproj=(2, 3), intern=.5, tech=True, skills=True, cover=False),
    "abbreviated_noisy": dict(cap=8, nskills=8, nproj=(2, 3), intern=.4, tech=True, skills=True, cover=False),
    "sparse_strong": dict(cap=3, nskills=5, nproj=(1, 1), intern=.6, tech=True, skills=True, cover=False),
    "ineligible_strong": dict(cap=10, nskills=8, nproj=(2, 3), intern=.55, tech=True, skills=True, cover=False),
    "generalist_average": dict(cap=6, nskills=7, nproj=(2, 2), intern=.3, tech=True, skills=True, cover=False),
    "stuffed_weak": dict(cap=0, nskills=0, nproj=(2, 3), intern=.4, tech=False, skills=True, cover=False),
}


def typo(rng, w):
    if len(w) < 4:
        return w
    i = rng.randrange(1, len(w) - 1)
    op = rng.choice(["swap", "drop", "dup"])
    if op == "swap":
        return w[:i] + w[i + 1] + w[i] + w[i + 2:]
    if op == "drop":
        return w[:i] + w[i + 1:]
    return w[:i] + w[i] + w[i:]


def lower_first(s):
    return s[0].lower() + s[1:]


def surface(rng, skill, style):
    s = SK[skill]
    if style == "canon":
        return s["name"]
    r = rng.random()  # noisy: aliases, typos, informal casing
    if r < .55:
        out = rng.choice(s["aliases"] or [s["name"]])
    elif r < .8:
        out = typo(rng, rng.choice(s["aliases"] + [s["name"]]))
    else:
        out = s["name"]
    return out.lower() if rng.random() < .6 else out


def noisify(rng, sent):
    sent = sent.replace(" and ", rng.choice([" and ", " n ", " & "]))
    words = sent.split(" ")
    for i, w in enumerate(words):
        if len(w) > 5 and w.isalpha() and rng.random() < .06:
            words[i] = typo(rng, w)
    sent = " ".join(words)
    return lower_first(sent) if rng.random() < .4 else sent


# ---------------------------------------------------------------- levels per archetype


def stack_levels(rng, family, mode, partial=None):
    stack = rng.choices(STACKS[family], STACK_W.get(family))[0]
    k = len(stack) if rng.random() < .6 else rng.randint(min(4, len(stack)), len(stack))
    keep = stack[:4] + sorted(rng.sample(stack[4:], k - 4), key=stack.index) if len(stack) > 4 else list(stack)
    if partial:
        keep = keep[:partial]
    lv = {}
    for i, s in enumerate(keep):
        if mode == "strong":
            lv[s] = 3 if i < 3 else rng.choice([2, 3])
        elif mode == "modest":
            lv[s] = rng.choice([1, 2, 2])
        elif i < 2:
            lv[s] = rng.choices([2, 3], [.4, .6])[0]
        else:
            lv[s] = rng.choices([1, 2, 3], [.25, .4, .35])[0]
    if mode != "modest" and rng.random() < .3:
        extra = rng.choice([c for c in CROSS if c not in lv])
        lv[extra] = 2 if mode == "strong" else rng.choice([1, 2])
    return lv


def prune(rng, lv, cap):
    while len(lv) > cap:
        cands = [s for s in lv if s not in effective({k: v for k, v in lv.items() if k != s})]
        if not cands:
            break
        del lv[min(cands, key=lambda s: (lv[s], rng.random()))]
    return lv


def hide_implied(lv):
    out, hidden = dict(lv), []
    for s in list(lv):
        rest = {k: v for k, v in out.items() if k != s}
        if effective(rest).get(s, 0) >= lv[s]:
            del out[s]
            hidden.append(s)
    return out, hidden


def build_levels(rng, arch, family):
    """Returns (explicit levels, claimed skills for stuffed_weak)."""
    if arch == "stuffed_weak":
        claimed = rng.sample(list(SK), rng.randint(24, 34))
        lv = {s: 1 for s in rng.sample(claimed, rng.choice([0, 1, 1, 2]))}
        return lv, claimed
    if arch == "implied":
        for _ in range(40):
            lv, hidden = hide_implied(stack_levels(rng, family, "normal"))
            if hidden and len(lv) >= 2:
                return lv, None
        lv, _ = hide_implied(stack_levels(rng, "backend", "normal"))
        return lv, None
    if arch == "generalist_average":
        other = rng.choice([f for f in FAMILIES if f != family])
        lv = stack_levels(rng, family, "modest", partial=3)
        for s, v in stack_levels(rng, other, "modest", partial=3).items():
            lv.setdefault(s, v)
    else:
        mode = "strong" if arch in ("sparse_strong", "ineligible_strong") else "normal"
        if arch != "sparse_strong" and rng.random() < DUAL_P:  # second, shallower profile
            other = rng.choices([f for f in FAMILIES if f != family], [FAMILY_W["software"][i] for i, f in enumerate(FAMILIES) if f != family])[0]
            lv = stack_levels(rng, family, mode, partial=4)
            for s, v in stack_levels(rng, other, "modest", partial=4).items():
                lv.setdefault(s, v)
        else:
            lv = stack_levels(rng, family, mode)
    lv = effective(lv)  # visible archetypes show implied skills explicitly
    return prune(rng, lv, CFG[arch]["nskills"]), None


# ---------------------------------------------------------------- resume text

HEDGE1 = ["As a small coursework exercise, ", "In a weekend tutorial project, ", "While learning the basics, "]
EMPH3 = ["", "", "In my main project, ", "Across several projects, "]


def edu_line(rng, rec):
    b, n = rec["branch"], rec["active_backlogs"]
    bname = rng.choice(BRANCH_NAMES[b])
    prog = bname if b == "M.Sc IT" else f"{rng.choice(['B.E.', 'B.Tech'])} in {bname}"
    college, year, cg = rng.choice(COLLEGES), rec["grad_year"], f"{rec['cgpa']:.2f}"
    if n == 0:
        bk = rng.choice(["No active backlogs", "Active backlogs: 0", "0 active backlogs"])
    else:
        bk = rng.choice([f"Active backlogs: {n}", f"{n} active backlog{'s' if n > 1 else ''}"])
    return rng.choice([
        f"{prog}, {college} | CGPA: {cg}/10 | Graduating {year} | {bk}",
        f"{college} - {prog}, expected {year}. CGPA {cg}. {bk}.",
        f"{prog} ({year}) from {college}; {cg} CGPA; {bk}",
    ])


def make_resume(rng, rec, arch, lv, claimed, family):
    cfg, surf = CFG[arch], defaultdict(list)
    noisy = arch == "abbreviated_noisy"
    style = "noisy" if noisy else "canon"
    bullet = rng.choice(["-", "•", "*", "–"])
    sections = {}

    # --- evidence sentences
    items = []
    if cfg["cap"]:
        order = sorted(lv, key=lambda s: (-lv[s], rng.random()))
        pool = {s: rng.sample(SK[s]["evidence"], len(SK[s]["evidence"])) for s in order}

        def decorate(s, sent, first):
            if lv[s] == 1:
                sent = rng.choice(HEDGE1) + lower_first(sent)
            elif lv[s] == 3 and first:
                pre = rng.choice(EMPH3)
                sent = pre + lower_first(sent) if pre else sent
            return noisify(rng, sent) if noisy else sent

        for s in order:
            if len(items) < cfg["cap"] or cfg["cover"]:
                items.append((s, decorate(s, pool[s][0], True)))
        for s in order:
            if lv[s] == 3 and len(items) < cfg["cap"]:
                items.append((s, decorate(s, pool[s][1], False)))
        items.sort(key=lambda it: (FAMILIES.index(SK[it[0]]["family"]), it[0]))
        for s, t in items:
            surf[s].append(t)

    # --- skills section
    if cfg["skills"]:
        if arch == "stuffed_weak":
            names = []
            for s in claimed:
                nm = SK[s]["name"] if rng.random() < .75 else rng.choice(SK[s]["aliases"] or [s])
                names.append(nm)
                surf[s].append(nm)
            half = len(names) // 2
            sections["skills"] = ["Technical Skills: " + ", ".join(names[:half]),
                                  "Also familiar with: " + ", ".join(names[half:])]
        else:
            order = sorted(lv, key=lambda s: (-lv[s], s))
            nm = {s: surface(rng, s, style) for s in order}
            for s in order:
                surf[s].append(nm[s])
            if noisy:
                parts = []
                for s in order:
                    parts.append(nm[s] + (" (basic)" if lv[s] == 1 and rng.random() < .5 else ""))
                line = parts[0]
                for p in parts[1:]:
                    line += rng.choice([", ", ", ", " / ", " n ", " & "]) + p
                sections["skills"] = [rng.choice(["skills - ", "skills: ", "tech i know: "]) + line]
            elif arch == "sparse_strong":
                sections["skills"] = ["Skills: " + " • ".join(nm[s] for s in order)]
            else:
                t = rng.randrange(3)
                groups = [[nm[s] for s in order if lv[s] == L] for L in (3, 2, 1)]
                if t == 0:
                    sections["skills"] = ["Technical Skills: " + ", ".join(nm[s] for s in order)]
                elif t == 1:
                    labels = ["Strong", "Working knowledge", "Basic"]
                    sections["skills"] = [f"{lab}: {', '.join(g)}" for lab, g in zip(labels, groups) if g]
                else:
                    verbs = ["Proficient in", "Comfortable with", "Familiar with"]
                    sections["skills"] = [" ".join(f"{v} {', '.join(g)}." for v, g in zip(verbs, groups) if g)]

    # --- projects + internship
    has_intern = rng.random() < cfg["intern"]
    nproj = rng.randint(*cfg["nproj"])
    if arch == "stuffed_weak":
        gp = rng.sample(GENERIC_PROJECTS, nproj)
        sections["projects"] = [f"{bullet} {t} - {d}" for t, d in gp]
        if has_intern:
            sections["internship"] = [f"Summer Intern, {rng.choice(COMPANIES)} ({rng.choice(['4 weeks', '6 weeks'])}). "
                                      "Observed the team, attended meetings and helped with documentation."]
    else:
        nchunks = max(1, min(nproj + (1 if has_intern else 0), len(items)))
        size, extra = divmod(len(items), nchunks)
        chunks, pos = [], 0
        for i in range(nchunks):
            n = size + (1 if i < extra else 0)
            chunks.append(items[pos:pos + n])
            pos += n
        intern_chunk = chunks.pop() if has_intern and len(chunks) > 0 and nchunks > 1 else None
        if has_intern and intern_chunk is None and chunks:
            intern_chunk, chunks = chunks[0], []
        proj_lines = []
        for ch in chunks:
            if not ch:
                continue
            fam = SK[ch[0][0]]["family"]
            title = rng.choice(PROJECT_TITLES[fam])
            body = " ".join(t for _, t in ch)
            tech = []
            if cfg["tech"]:
                for s in dict.fromkeys(s for s, _ in ch):
                    nm = surface(rng, s, style)
                    surf[s].append(nm)
                    tech.append(nm)
            if noisy:
                tt = title.lower()
                proj_lines.append(f"{bullet} {tt} - made using {' n '.join(tech)}. {body}")
            elif tech:
                k = rng.randrange(3)
                proj_lines.append([f"{bullet} {title} - {body} Tech: {', '.join(tech)}.",
                                   f"{bullet} {title} ({', '.join(tech)}): {body}",
                                   f"{bullet} {title}\n  {body}\n  Stack: {', '.join(tech)}"][k])
            else:
                k = rng.randrange(3)
                proj_lines.append([f"{bullet} {title} - {body}", f"{bullet} {title}: {body}",
                                   f"{bullet} {title}\n  {body}"][k])
        if proj_lines:
            sections["projects"] = proj_lines
        if intern_chunk:
            fam = SK[intern_chunk[0][0]]["family"]
            role = f"{FAMILY_ROLE[fam]} Intern"
            head = f"{role}, {rng.choice(COMPANIES)} ({rng.choice(['6 weeks', '2 months', '3 months', '6 months'])})"
            body = " ".join(t for _, t in intern_chunk)
            if noisy:
                head = head.lower()
            sections["internship"] = [head + ". " + body]

    # --- distractors and noise
    if arch == "stuffed_weak":
        sections["achievements"] = rng.sample(STUFFED_ACHIEVEMENTS, rng.randint(2, 3))
    elif rng.random() < .6:
        sections["achievements"] = rng.sample(ACHIEVEMENTS, rng.randint(1, 2))
    sections["extras"] = rng.sample(EXTRAS, rng.randint(1, 3))
    sections["objective"] = [rng.choice(OBJECTIVES)]

    # --- assemble (drop optional sections until within 80..400 words)
    tstyle = rng.randrange(3)
    email = f"{rec['id'].lower()}@mail.example"
    phone = "+91 9" + "".join(str(rng.randrange(10)) for _ in range(9))
    header = rng.choice([
        f"{rec['name']} | {email} | {phone}",
        f"{rec['name']} - {phone} - {email}",
        f"Name: {rec['name']} | Email: {email} | Mobile: {phone}",
        f"RESUME OF {rec['name']} ({email}, {phone})",
    ])
    edu = edu_line(rng, rec)
    keys = list(sections)
    rng.shuffle(keys)
    trailer = rng.choice(TRAILERS)

    def render(drop):
        lines = [header, "", SECTION_TITLES["education"][tstyle], edu, ""]
        for k in keys:
            if k in sections and k not in drop:
                lines += [SECTION_TITLES[k][tstyle], *sections[k], ""]
        if trailer and "trailer" not in drop:
            lines.append(trailer)
        text = "\n".join(lines).strip() + "\n"
        return lower_first_noisy(text) if noisy else text

    def lower_first_noisy(t):
        return t  # noise is applied at sentence level; headings stay intact

    drop = []
    for k in ("trailer", "extras", "achievements", "objective"):
        if len(render(drop).split()) <= 400:
            break
        drop.append(k)
    text = render(drop)
    return text, {s: v for s, v in surf.items()}, items


# ---------------------------------------------------------------- students


def make_plan():
    """Fixed, quota-independent plan: archetype per student and a priority order used to move students."""
    rng = random.Random(SEED)
    archs = [a for a, c in ARCH_COUNTS.items() for _ in range(c)]
    assert len(archs) == N_STUDENTS
    rng.shuffle(archs)
    return dict(archs=archs, order=rng.sample(range(N_STUDENTS), N_STUDENTS), fam_of=None)


def compute_quotas(floors):
    """Every family gets its floor; the rest is spread by FAMILY_W (largest remainder)."""
    rest = N_STUDENTS - sum(floors.values())
    assert rest >= 0, "family floors exceed the number of students"
    w = FAMILY_W["software"]
    raw = {f: rest * w[i] / sum(w) for i, f in enumerate(FAMILIES)}
    q = {f: floors[f] + int(raw[f]) for f in FAMILIES}
    for f in sorted(FAMILIES, key=lambda f: raw[f] - int(raw[f]), reverse=True)[:N_STUDENTS - sum(q.values())]:
        q[f] += 1
    return q


def assign_families(plan, quotas):
    """First call: consecutive blocks of the priority order. Later calls move only the lowest-priority
    students of families that shrink to families that grow, so everyone else keeps family and text."""
    order = plan["order"]
    if plan["fam_of"] is None:
        plan["fam_of"], pos = {}, 0
        for f in FAMILIES:
            for i in order[pos:pos + quotas[f]]:
                plan["fam_of"][i] = f
            pos += quotas[f]
        return
    fam_of, cur, pool = plan["fam_of"], Counter(plan["fam_of"].values()), []
    for f in FAMILIES:
        if cur[f] > quotas[f]:
            pool += [i for i in order if fam_of[i] == f][quotas[f] - cur[f]:]
    for f in FAMILIES:
        for _ in range(max(0, quotas[f] - cur[f])):
            fam_of[pool.pop(0)] = f


def generate_students(plan):
    recs = []
    for i, arch in enumerate(plan["archs"]):
        ri = random.Random(f"{SEED}:{i}:profile")  # per-student streams: a student only changes if its family does
        family = plan["fam_of"][i]
        mix = BRANCH_MIX[family]
        branch = ri.choices(list(mix), list(mix.values()))[0]
        cgpa = round(min(9.8, max(5.5, ri.gauss(7.8, 0.85))), 2)
        backlogs = 0
        if ri.random() < (0.4 if cgpa < 6.5 else 0.06):
            backlogs = ri.choices([1, 2, 3], [.6, .3, .1])[0]
        if arch == "ineligible_strong":
            if ri.random() < .5:
                cgpa, backlogs = round(ri.uniform(5.5, 6.45), 2), ri.choice([0, 0, 1])
            else:
                cgpa, backlogs = round(max(6.5, min(9.5, ri.gauss(7.5, 0.8))), 2), ri.choice([1, 1, 2, 3])
        recs.append(dict(id=f"S{i + 1:03d}", branch=branch, cgpa=cgpa, active_backlogs=backlogs,
                         grad_year=ri.choices([2027, 2026, 2028], [.75, .2, .05])[0],
                         archetype=arch, family=family))

    # names: within each archetype, students sorted by CGPA are split into blocks of 6 and each block gets
    # the 6 name groups in random order -> group is unrelated to skills/archetype and CGPA is balanced
    nrng = random.Random(f"{SEED}:names")
    groups = list(NAME_POOLS)
    by_arch = defaultdict(list)
    for r in recs:
        by_arch[r["archetype"]].append(r)
    used = set()
    for arch in ARCH_COUNTS:
        members = sorted(by_arch[arch], key=lambda r: r["cgpa"])
        for i, r in enumerate(members):
            if i % len(groups) == 0:
                perm = nrng.sample(groups, len(groups))
            g = perm[i % len(groups)]
            while True:
                name = f"{nrng.choice(NAME_POOLS[g]['first'])} {nrng.choice(NAME_POOLS[g]['last'])}"
                if name not in used:
                    used.add(name)
                    break
            r["name"], r["name_group"] = name, g

    students, truths = [], []
    for r in recs:
        tr_ = random.Random(f"{SEED}:{r['id']}:text")
        lv, claimed = build_levels(tr_, r["archetype"], r["family"])
        text, surf, _ = make_resume(tr_, r, r["archetype"], lv, claimed, r["family"])
        students.append(dict(id=r["id"], name=r["name"], branch=r["branch"], cgpa=r["cgpa"],
                             active_backlogs=r["active_backlogs"], grad_year=r["grad_year"], resume_text=text))
        t = dict(id=r["id"], archetype=r["archetype"], name_group=r["name_group"], family=r["family"],
                 levels=lv, effective_levels=effective(lv), surfaces=surf)
        if claimed:
            t["claimed_skills"] = claimed
        truths.append(t)
    return students, truths


# ---------------------------------------------------------------- requirements

REQS = [
    dict(id="R01", split="dev", family="backend",
         text="We are hiring Junior Backend Engineers for our Ahmedabad office. The ideal candidate is comfortable writing server-side code in Python, has built or consumed REST APIs and can write SQL against a relational database such as PostgreSQL. Familiarity with Docker and Redis would be an added advantage. Candidates must hold a minimum CGPA of 7.0, must have no active backlogs, and should be from CSE, IT or ICT branches only.",
         must=["Python", "REST APIs", "SQL"], nice=["Docker", "Redis"], min_cgpa=7.0, branches=["CSE", "IT", "ICT"], max_backlogs=0,
         markers=dict(min_cgpa="minimum CGPA of 7.0", max_backlogs="no active backlogs", branches="CSE, IT or ICT branches only")),
    dict(id="R02", split="test", family="frontend",
         text="hey, need 2 frontend guys/girls asap!! react + js + html css must. typescript n figma if u know its a bonus. cgpa 6.5+ ok, 1 backlog is fine but not more than that. CS/IT/ICT/MSc IT only. fresher ok",
         must=["React", "JavaScript", "HTML/CSS"], nice=["TypeScript", "Figma"], min_cgpa=6.5, branches=["CSE", "IT", "ICT", "M.Sc IT"], max_backlogs=1,
         markers=dict(min_cgpa="cgpa 6.5+", max_backlogs="1 backlog is fine but not more than that", branches="CS/IT/ICT/MSc IT only")),
    dict(id="R03", split="test", family="fullstack",
         text="Full Stack Developer (MERN-ish)\n- Node.js + Express backend, React frontend\n- MongoDB for storage\n- REST APIs, login/auth experience and Docker are a plus\n- 6.5+ CGPA, backlog kuch nahi chahiye (no active backlogs)\n- CSE / IT / ICT / M.Sc IT",
         must=["Node.js", "React", "MongoDB"], nice=["REST APIs", "Authentication", "Docker"], min_cgpa=6.5, branches=["CSE", "IT", "ICT", "M.Sc IT"], max_backlogs=0,
         markers=dict(min_cgpa="6.5+ CGPA", max_backlogs="no active backlogs", branches="CSE / IT / ICT / M.Sc IT")),
    dict(id="R04", split="dev", family="data_analysis",
         text="Data analyst chahiye bhai, fresher chalega. SQL aur Excel strong hona chahiye, Power BI dashboards banana aana chahiye. Python (pandas) aaye toh aur accha. Koi bhi branch chalegi, CGPA 6 se upar hona chahiye. Backlog ka koi issue nahi.",
         must=["SQL", "Excel", "Power BI"], nice=["Python", "Pandas"], min_cgpa=6.0, branches=None, max_backlogs=None,
         markers=dict(min_cgpa="CGPA 6 se upar", max_backlogs="Backlog ka koi issue nahi", branches="Koi bhi branch chalegi")),
    dict(id="R05", split="test", family="ml",
         text="We r looking for ML engineer intern/fresher. Must know Python, machine learning basics and sckit-learn (sklearn). Deep learning with pytorch is a plus. 7 CGPA minimum plz and zero backlogs. Open to CSE, IT, ICT, ECE and MSc IT students.",
         must=["Python", "Machine Learning", "scikit-learn"], nice=["Deep Learning", "PyTorch"], min_cgpa=7.0, branches=["CSE", "IT", "ICT", "ECE", "M.Sc IT"], max_backlogs=0,
         markers=dict(min_cgpa="7 CGPA minimum", max_backlogs="zero backlogs", branches="CSE, IT, ICT, ECE and MSc IT")),
    dict(id="R06", split="test", family="data_engineering",
         text="Our analytics team needs someone to help move and prepare data at scale. They should be comfortable with SQL and with building ETL jobs, and have at least touched Apache Spark. Airflow or Kafka experience will be appreciated, AWS exposure even better. Preferably 7 CGPA or above. No pending backlogs please. Computer-science-related streams (CSE/IT/ICT/MSc IT) preferred.",
         must=["SQL", "ETL Pipelines", "Apache Spark"], nice=["Airflow", "Apache Kafka", "AWS"], min_cgpa=7.0, branches=["CSE", "IT", "ICT", "M.Sc IT"], max_backlogs=0,
         markers=dict(min_cgpa="7 CGPA or above", max_backlogs="No pending backlogs", branches="(CSE/IT/ICT/MSc IT)")),
    dict(id="R07", split="dev", family="devops_cloud",
         text="DevOps Trainee - Rajkot. Needs: Linux, Docker, CI/CD. Some AWS, K8s and Terraform are good to have. CGPA >= 6.5. Max 1 active backlog accepted. Branches: CSE, IT, ICT or ECE.",
         must=["Linux", "Docker", "CI/CD"], nice=["AWS", "Kubernetes", "Terraform"], min_cgpa=6.5, branches=["CSE", "IT", "ICT", "ECE"], max_backlogs=1,
         markers=dict(min_cgpa="CGPA >= 6.5", max_backlogs="Max 1 active backlog accepted", branches="CSE, IT, ICT or ECE")),
    dict(id="R08", split="test", family="qa_testing",
         text="QA engineer ke liye 8 students chahiye. Manual testing pakka aana chahiye, Selenium se automation scripts likh sake, aur Postman se API testing bhi. Python ya Java aata ho toh bonus. 6.0 CGPA cutoff hai, backlog allowed nahi hai. CSE/IT/ICT/ECE/M.Sc IT walon ko hi bulao.",
         must=["Manual Testing", "Selenium", "API Testing"], nice=["Python", "Java"], min_cgpa=6.0, branches=["CSE", "IT", "ICT", "ECE", "M.Sc IT"], max_backlogs=0,
         markers=dict(min_cgpa="6.0 CGPA cutoff", max_backlogs="backlog allowed nahi hai", branches="CSE/IT/ICT/ECE/M.Sc IT")),
    dict(id="R09", split="dev", family="mobile",
         text="Mobile app developer (fresher). React Native and JavaScript required, plus REST API integration. Kotlin/Android or Flutter experience is a bonus. Minimum 7 CGPA, no backlogs, only CSE/IT/ICT/MSc IT.",
         must=["React Native", "JavaScript", "REST APIs"], nice=["Android", "Kotlin", "Flutter"], min_cgpa=7.0, branches=["CSE", "IT", "ICT", "M.Sc IT"], max_backlogs=0,
         markers=dict(min_cgpa="Minimum 7 CGPA", max_backlogs="no backlogs", branches="only CSE/IT/ICT/MSc IT")),
    dict(id="R10", split="test", family="cybersecurity",
         text="Position: Security Analyst Trainee\nRequirements:\n * Working knowledge of network security concepts and Linux administration\n * Hands-on penetration testing (CTFs, labs or bug bounty count)\n * Cryptography basics and scripting in Python are desirable\nEligibility: CGPA 7 and above; no active backlogs; CSE, IT, ICT and ECE students only.",
         must=["Network Security", "Linux", "Penetration Testing"], nice=["Cryptography", "Python"], min_cgpa=7.0, branches=["CSE", "IT", "ICT", "ECE"], max_backlogs=0,
         markers=dict(min_cgpa="CGPA 7 and above", max_backlogs="no active backlogs", branches="CSE, IT, ICT and ECE students only")),
    dict(id="R11", split="test", family="embedded_iot",
         text="Embedded/IoT trainee needed. Strong in C is a must, Arduino or similar boards, and MQTT for device-to-cloud messaging. Raspberry Pi and C++ are nice to have. Core branches welcome: ECE, EE, CSE, Mechanical (mechatronics interest). CGPA 6.5 min; one backlog is okay.",
         must=["C", "Arduino", "MQTT"], nice=["Raspberry Pi", "C++"], min_cgpa=6.5, branches=["ECE", "EE", "CSE", "Mechanical"], max_backlogs=1,
         markers=dict(min_cgpa="CGPA 6.5 min", max_backlogs="one backlog is okay", branches="ECE, EE, CSE, Mechanical")),
    dict(id="R12", split="dev", family="business_analysis",
         text="We invite applications for the position of Associate Business Analyst. The candidate should be good at requirements gathering and documentation, work in an Agile/Scrum environment, and have strong stakeholder communication with non-technical clients. Knowledge of JIRA, SQL and process modelling would be considered a plus. Applicants from any branch with a CGPA of 7.5 or higher and no active backlogs may apply.",
         must=["Requirements Gathering", "Agile/Scrum", "Stakeholder Communication"], nice=["JIRA", "SQL", "Process Modeling"], min_cgpa=7.5, branches=None, max_backlogs=0,
         markers=dict(min_cgpa="CGPA of 7.5 or higher", max_backlogs="no active backlogs", branches="any branch")),
    dict(id="R13", split="test", family="backend",
         text="JAVA BACKEND DEVELOPER - Bengaluru. Must: Java, Spring Boot, SQL. Microservices, Kafka and Docker will give you an edge. 6.5+ CGPA, 0 backlogs, CSE/IT/ICT only. no exceptions!!",
         must=["Java", "Spring Boot", "SQL"], nice=["Microservices", "Apache Kafka", "Docker"], min_cgpa=6.5, branches=["CSE", "IT", "ICT"], max_backlogs=0,
         markers=dict(min_cgpa="6.5+ CGPA", max_backlogs="0 backlogs", branches="CSE/IT/ICT only")),
    dict(id="R14", split="test", family="ml",
         text="Looking for an NLP engineer trainee to work on text classification and chatbots. Need solid Python, natural language processing fundamentals and deep learning (PyTorch or TensorFlow either is fine). Top performers only - CGPA 7 minimum, no active backlogs. CSE, IT, ICT, MSc IT.",
         must=["Python", "NLP", "Deep Learning"], nice=["PyTorch", "TensorFlow"], min_cgpa=7.0, branches=["CSE", "IT", "ICT", "M.Sc IT"], max_backlogs=0,
         markers=dict(min_cgpa="CGPA 7 minimum", max_backlogs="no active backlogs", branches="CSE, IT, ICT, MSc IT")),
    dict(id="R15", split="test", family="fullstack",
         text="startup hiring web dev: Next.js and PostgreSQL must, typescript nice to have, docker knowledge is a plus. we dont care about cgpa or branch, just show us what u built. (backlogs also fine)",
         must=["Next.js", "PostgreSQL"], nice=["TypeScript", "Docker"], min_cgpa=None, branches=None, max_backlogs=None,
         markers=dict(min_cgpa="we dont care about cgpa", max_backlogs="backlogs also fine", branches="or branch")),
]


def relevance(req, student, eff):
    """Deterministic ground truth. Returns (eligible, relevance 0-3, extra_credit 0-1).

    not eligible -> 0 | 3: all must-haves effective level >= 2 | 2: all >= 1 | 1: at least half >= 1 | 0 otherwise.
    extra_credit = mean(nice-to-have levels) / 3 (tie-break only, never changes relevance).
    """
    ok = ((req["min_cgpa"] is None or student["cgpa"] >= req["min_cgpa"])
          and (req["branches"] is None or student["branch"] in req["branches"])
          and (req["max_backlogs"] is None or student["active_backlogs"] <= req["max_backlogs"]))
    lv = [eff.get(s, 0) for s in req["must"]]
    extra = round(sum(eff.get(s, 0) for s in req["nice"]) / (3 * len(req["nice"])), 3) if req["nice"] else 0.0
    if not ok:
        return False, 0, extra
    if all(v >= 2 for v in lv):
        rel = 3
    elif all(v >= 1 for v in lv):
        rel = 2
    elif sum(v >= 1 for v in lv) >= len(lv) / 2:
        rel = 1
    else:
        rel = 0
    return True, rel, extra


# ---------------------------------------------------------------- output


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def evaluate(students, truths):
    """{req_id: (eligible, qualified, qualified_from_hard_archetypes)}"""
    arch = {t["id"]: t["archetype"] for t in truths}
    out = {}
    for r in REQS:
        e = q = h = 0
        for s, t in zip(students, truths):
            el, rel, _ = relevance(r, s, t["effective_levels"])
            e += el
            if rel >= 2:
                q += 1
                h += arch[s["id"]] in HARD
        out[r["id"]] = (e, q, h)
    return out


def balance(plan):
    """Raise the quota of the family of any requirement with too few qualified / too few hard-archetype
    students by ~10% and regenerate (max MAX_ROUNDS). Never shrinks a quota to fix an upper-bound miss."""
    floors = {f: MIN_QUOTA for f in FAMILIES}
    log, fam_of_req = [], {r["id"]: r["family"] for r in REQS}
    for rnd in range(1, MAX_ROUNDS + 1):
        quotas = compute_quotas(floors)
        assign_families(plan, quotas)
        students, truths = generate_students(plan)
        res = evaluate(students, truths)
        low = [rid for rid, (_, q, h) in res.items() if q < Q_RANGE[0] or h < HARD_SHARE * q]
        high = [rid for rid, (_, q, _) in res.items() if q > Q_RANGE[1]]
        log.append((rnd, dict(quotas), res, low, high))
        if not low:
            return students, truths, log, True
        for fam in {fam_of_req[rid] for rid in low}:
            floors[fam] = max(quotas[fam] + 1, ceil(quotas[fam] * 1.1))
        if sum(floors.values()) > N_STUDENTS:
            break
    return students, truths, log, False


def write_log(log, converged):
    lines = ["# Balance log", "",
             f"Quota-based family assignment, {N_STUDENTS} students, minimum {MIN_QUOTA} per family. "
             f"A requirement is 'low' if qualified < {Q_RANGE[0]} or hard-archetype share < {HARD_SHARE:.0%}; "
             "the quota of its family is raised by ~10% for the next round. Upper bound "
             f"{Q_RANGE[1]} is reported, never fixed by shrinking quotas.", ""]
    for rnd, quotas, res, low, high in log:
        lines += [f"## Round {rnd}", "", "Quotas: " + ", ".join(f"{f}={q}" for f, q in quotas.items()), "",
                  "| req | family | eligible | qualified | hard | hard% | status |", "|---|---|---|---|---|---|---|"]
        for r in REQS:
            e, q, h = res[r["id"]]
            st = "LOW" if r["id"] in low else ("HIGH" if r["id"] in high else "ok")
            lines.append(f"| {r['id']} | {r['family']} | {e} | {q} | {h} | {h / max(1, q):.0%} | {st} |")
        lines.append("")
    lines.append(f"**{'Converged' if converged else 'NOT converged'} after {len(log)} round(s).**")
    (ROOT / "docs" / "balance_log.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    students, truths, log, converged = balance(make_plan())
    write_log(log, converged)
    print(f"balancing: {'converged' if converged else 'NOT CONVERGED'} after {len(log)} round(s)")
    if not converged:
        for rid, (e, q, h) in log[-1][2].items():
            print(f"  {rid} eligible={e} qualified={q} hard={h}")
        raise SystemExit("stopped: see docs/balance_log.md (data files not updated)")
    write_jsonl(DATA / "students.jsonl", students)
    write_jsonl(DATA / "students_truth.jsonl", truths)

    write_jsonl(DATA / "requirements.jsonl", [dict(id=r["id"], text=r["text"], split=r["split"]) for r in REQS])
    rt = {r["id"]: dict(role_family=r["family"], must_have=r["must"], nice_to_have=r["nice"], min_cgpa=r["min_cgpa"],
                        allowed_branches=r["branches"], max_backlogs=r["max_backlogs"], text_markers=r["markers"])
          for r in REQS}
    (DATA / "requirements_truth.json").write_text(json.dumps(rt, indent=2, ensure_ascii=False), encoding="utf-8")

    rows = []
    for r in REQS:
        for s, t in zip(students, truths):
            el, rel, extra = relevance(r, s, t["effective_levels"])
            rows.append(dict(req_id=r["id"], student_id=s["id"], eligible=int(el), relevance=rel,
                             qualified=int(rel >= 2), extra_credit=extra))
    with open(DATA / "qrels.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # spot-check sheet: 5 random pairs per relevance level, shuffled
    srng = random.Random(SEED + 1)
    picks = []
    for lvl in range(4):
        picks += srng.sample([x for x in rows if x["relevance"] == lvl], 5)
    srng.shuffle(picks)
    rtext = {r["id"]: r["text"] for r in REQS}
    stext = {s["id"]: s["resume_text"] for s in students}
    with open(DATA / "spotcheck.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["req_id", "student_id", "requirement_text", "resume_text", "eligible", "generated_label", "my_label"])
        for x in picks:
            w.writerow([x["req_id"], x["student_id"], rtext[x["req_id"]], stext[x["student_id"]],
                        x["eligible"], x["relevance"], ""])

    arch = {t["id"]: t["archetype"] for t in truths}
    print(f"students={len(students)} requirements={len(REQS)} qrels={len(rows)} spotcheck={len(picks)}")
    print("req   eligible qualified hard  hard%")
    for r in REQS:
        rr = [x for x in rows if x["req_id"] == r["id"]]
        q = [x for x in rr if x["qualified"]]
        h = sum(arch[x["student_id"]] in HARD for x in q)
        print(f"{r['id']}  {sum(x['eligible'] for x in rr):8d} {len(q):9d} {h:4d} {h / max(1, len(q)):6.0%}")


if __name__ == "__main__":
    main()


