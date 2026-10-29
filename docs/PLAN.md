# CONTEXT

I'm building a college placement matching prototype for a course project (final evaluation 19 Nov 2026, but I want the prototype and paper done quickly). I'm working alone with Claude.

Pipeline: a company requirement (free text) goes to a local LLM (Ollama), which parses it into a semantic query plus hard eligibility filters (CGPA, branch, backlogs). The query is embedded (bge-small-en-v1.5) and the top-20 students are retrieved from ChromaDB with those filters applied. The LLM then scores and explains each candidate in JSON, and the top-10 are shown as a ranked list.
Baselines: keyword ATS, BM25, dense-only.
Data: fully synthetic (about 300 students, about 15 free-text requirements).
Stack: Python, ChromaDB, sentence-transformers, Ollama, Streamlit with a polished custom UI.
Machine: Windows laptop, about 6GB VRAM.

HARD RULE: ALL downloads, caches, models, venvs and project files must be on the D drive. Keep the C drive clean.
