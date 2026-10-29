# LLM test results: qwen3.5:4b-q4_K_M

Script: `scripts/test_llm.py` (raw output: `scripts/test_llm_summary.json`). Ollama, weights on D:\ai-cache\ollama.
Settings: format=JSON schema, think=False, temperature 0, num_ctx 4096, 6 tasks x 3 repeats = 18 calls. GPU: RTX 4050 Laptop 6 GB.

| Check | Result | Verdict |
|---|---|---|
| Valid JSON | 18/18 (100%) | PASS |
| Schema compliance | 18/18 (100%) | PASS |
| Scoring latency (warm) | avg 2.9 s (2.3-3.5 s) | PASS (< 8 s) |
| Parsing latency (warm) | avg 1.75 s | PASS |
| Cold first call | 118.5 s (model load from D:) | one-off |
| Avg over all 18 calls | 8.8 s (2.4 s excluding cold load) | n/a |
| Throughput | ~45 tok/s avg (44-50 warm) | |
| Peak VRAM | 4493 MiB total (baseline 755, so ~3.7 GB for the model) | fits 6 GB |
| CPU spill (`ollama ps`) | 100% GPU, context 4096, 3.1 GB | none |
| Ordering | strong 95 > paraphrased 85 > keyword-stuffed 10 | PASS |
| Repeat variance | spread 0 points on all 3 resumes (> 10 would fail) | PASS |

## Examples
Parse ("python n sql ... pune/remote ok. docker is a plus"):
`{"title":"Data Analyst","must_have_skills":["Python","SQL"],"nice_to_have_skills":["Docker"],"min_experience_years":2,"location":"Pune/Remote"}`
(Note: "2-3 yrs" became 2, taking the lower bound.)

Score (paraphrased resume): `score 85`, matched Python, SQL; missing Docker; reasoning cites pandas/numpy as Python and PostgreSQL/MySQL joins as SQL.

## Decision
No rule triggered (JSON 100%, warm scoring latency < 8 s, ordering correct). Qwen3:4b was not pulled.
**Recommended: `qwen3.5:4b-q4_K_M`** (written to `.env` as `LLM_MODEL`).

Caveats: tiny sample (3 resumes, 1 job); temperature 0 explains the zero variance; keep the model warm (`keep_alive`) because the cold load took ~2 min.
