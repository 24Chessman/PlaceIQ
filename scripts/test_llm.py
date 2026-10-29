"""Smoke-test a local Ollama model: JSON validity, schema compliance, latency, ordering, stability.

Usage (from venv): python scripts/test_llm.py [model]
"""
import json
import statistics as st
import subprocess
import sys
import threading
import time

import ollama
from jsonschema import ValidationError, validate

MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3.5:4b-q4_K_M"
REPEATS = 3
OPTIONS = {"temperature": 0, "num_ctx": 4096}

PARSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "must_have_skills": {"type": "array", "items": {"type": "string"}},
        "nice_to_have_skills": {"type": "array", "items": {"type": "string"}},
        "min_experience_years": {"type": "number"},
        "location": {"type": "string"},
    },
    "required": ["title", "must_have_skills", "nice_to_have_skills", "min_experience_years", "location"],
    "additionalProperties": False,
}
SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "matched_skills": {"type": "array", "items": {"type": "string"}},
        "missing_skills": {"type": "array", "items": {"type": "string"}},
        "reasoning": {"type": "string"},
    },
    "required": ["score", "matched_skills", "missing_skills", "reasoning"],
    "additionalProperties": False,
}

REQUIREMENTS = [
    "we need smone who knows python n sql, atleast 2-3 yrs, pune/remote ok. docker is a plus. data analyst role",
    "Looking 4 backend dev!! java springboot REQUIRED, microservices exp, kafka nice to have, 5+ years, Bangalore only",
    "fresher ok. frontend - react, js, css. figma bonus. mumbai office, no exp needed",
]
PARSE_PROMPT = (
    "Extract the job requirement into JSON. Use empty list if none, 0 for no experience, "
    "'unspecified' if no location. Requirement:\n"
)

JOB = {
    "title": "Data Analyst",
    "must_have_skills": ["Python", "SQL"],
    "nice_to_have_skills": ["Docker"],
    "min_experience_years": 2,
    "location": "Pune",
}
RESUMES = {
    "strong": (
        "Rohan M. Data Analyst, 3 years at a Pune fintech. Built ETL pipelines in Python (pandas) and wrote "
        "complex SQL (window functions, CTEs) on PostgreSQL. Containerised reporting jobs with Docker. B.E. Computer Science."
    ),
    "paraphrased": (
        "Anita S. 3 years analysing business data in Pune. Wrote scripts with pandas and numpy to clean and "
        "model datasets, and queried relational databases (PostgreSQL, MySQL) daily using joins and aggregations "
        "to produce dashboards for management. B.Sc. Statistics."
    ),
    "keyword_stuffed": (
        "Vikram. Skills: Python SQL Docker Python SQL Docker Python SQL Docker Kubernetes AWS Python SQL. "
        "Fresher, no work experience. Interests: gaming, cricket. Location: Delhi."
    ),
}
SCORE_PROMPT = (
    "You are a recruiter. Score the resume against the job from 0 to 100 on genuine fit "
    "(demonstrated skills, experience, location), not on keyword repetition. Equivalent skills described "
    "in other words count as matched.\nJOB:\n{job}\nRESUME:\n{resume}"
)

TASKS = [(f"parse_{i + 1}", PARSE_SCHEMA, PARSE_PROMPT + r) for i, r in enumerate(REQUIREMENTS)] + [
    (f"score_{name}", SCORE_SCHEMA, SCORE_PROMPT.format(job=json.dumps(JOB), resume=text))
    for name, text in RESUMES.items()
]


def vram_used_mib() -> int:
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        capture_output=True, text=True,
    ).stdout
    return int(out.split()[0])


peak = {"vram": 0, "stop": False}


def sample_vram():
    while not peak["stop"]:
        peak["vram"] = max(peak["vram"], vram_used_mib())
        time.sleep(0.5)


def main():
    client = ollama.Client()
    baseline = vram_used_mib()
    threading.Thread(target=sample_vram, daemon=True).start()
    rows = []
    for name, schema, prompt in TASKS:
        for rep in range(REPEATS):
            t0 = time.perf_counter()
            r = client.chat(
                model=MODEL, messages=[{"role": "user", "content": prompt}],
                format=schema, think=False, options=OPTIONS,
            )
            latency = time.perf_counter() - t0
            raw = r.message.content
            valid_json = schema_ok = False
            parsed = None
            try:
                parsed = json.loads(raw)
                valid_json = True
                validate(parsed, schema)
                schema_ok = True
            except (json.JSONDecodeError, ValidationError):
                pass
            tps = r.eval_count / (r.eval_duration / 1e9) if r.eval_duration else 0
            rows.append(dict(task=name, rep=rep, latency=latency, json=valid_json, schema=schema_ok,
                             tps=tps, out=parsed if valid_json else raw))
            print(f"{name} #{rep + 1}: {latency:.1f}s json={valid_json} schema={schema_ok} {tps:.0f} tok/s", flush=True)
    ps = subprocess.run(["ollama", "ps"], capture_output=True, text=True).stdout
    peak["stop"] = True

    n = len(rows)
    score_rows = [x for x in rows if x["task"].startswith("score_")]
    spread, means = {}, {}
    for name in RESUMES:
        s = [x["out"]["score"] for x in score_rows if x["task"] == f"score_{name}" and x["schema"]]
        spread[name] = (max(s) - min(s)) if s else None
        means[name] = st.mean(s) if s else None

    summary = {
        "model": MODEL,
        "calls": n,
        "valid_json_rate": sum(x["json"] for x in rows) / n,
        "schema_rate": sum(x["schema"] for x in rows) / n,
        "avg_latency_s": st.mean(x["latency"] for x in rows),
        "avg_parse_latency_s": st.mean(x["latency"] for x in rows if x["task"].startswith("parse_")),
        "avg_score_latency_s": st.mean(x["latency"] for x in score_rows),
        "avg_tok_per_s": st.mean(x["tps"] for x in rows),
        "vram_baseline_mib": baseline,
        "vram_peak_mib": peak["vram"],
        "ollama_ps": ps.strip(),
        "mean_scores": means,
        "score_spread_across_repeats": spread,
        "paraphrased_beats_stuffed": (
            None if None in (means["paraphrased"], means["keyword_stuffed"])
            else means["paraphrased"] > means["keyword_stuffed"]
        ),
        "strong_beats_stuffed": (
            None if None in (means["strong"], means["keyword_stuffed"])
            else means["strong"] > means["keyword_stuffed"]
        ),
        "examples": {t: next(x["out"] for x in rows if x["task"] == t) for t in ("parse_1", "score_paraphrased")},
    }
    print(json.dumps(summary, indent=2, default=str))
    with open("scripts/test_llm_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)


if __name__ == "__main__":
    main()
