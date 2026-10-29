"""Paths, model names and flags. Everything lives on D:."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("HF_HOME", r"D:\ai-cache\hf")  # model downloads stay on D:
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
CHROMA_DIR = DATA / "chroma"
CACHE_DIR = ROOT / ".cache"
LLM_CACHE = CACHE_DIR / "llm_cache.jsonl"
STUDENTS_PATH = DATA / "students.jsonl"

MODEL = os.getenv("LLM_MODEL", "qwen3.5:4b-q4_K_M")
OPTIONS = {"temperature": 0, "num_ctx": 4096}
KEEP_ALIVE = "30m"

K_RETRIEVE = 20
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
COLLECTION = "students_bge_small"
CHUNK_TOKENS = 256
CHUNK_OVERLAP = 32
MAX_TOKENS = 512
CHUNK_IF_SHARE_ABOVE = 0.05

FAIRNESS_INSTRUCTION = True
BRANCHES = ["CSE", "IT", "ICT", "ECE", "EE", "Mechanical", "Civil", "M.Sc IT"]
