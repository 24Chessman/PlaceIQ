"""Student loading. Only the resume and the structured fields; never the truth files."""
import json

from .config import STUDENTS_PATH


def load_students():
    with open(STUDENTS_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def resume_texts():
    return {s["id"]: s["resume_text"] for s in load_students()}
