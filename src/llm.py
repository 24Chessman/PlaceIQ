"""Ollama chat with JSON-schema output and a disk cache keyed by hash(model, messages, schema, options)."""
import hashlib
import json
import time

import ollama

from .config import CACHE_DIR, KEEP_ALIVE, LLM_CACHE, MODEL, OPTIONS

_cache = None
_client = None


def _load():
    global _cache
    if _cache is None:
        _cache = {}
        if LLM_CACHE.exists():
            for line in LLM_CACHE.read_text(encoding="utf-8").splitlines():
                e = json.loads(line)
                _cache[e["key"]] = e
    return _cache


def client():
    global _client
    if _client is None:
        _client = ollama.Client(timeout=300)
    return _client


def _bounded(schema, max_items=8):
    out = json.loads(json.dumps(schema))
    for prop in out.get("properties", {}).values():
        if prop.get("type") == "array":
            prop["maxItems"] = max_items
    return out


def warm_up():
    """Load the model into memory (not cached on purpose). Returns seconds taken."""
    t0 = time.perf_counter()
    client().chat(model=MODEL, messages=[{"role": "user", "content": "Reply with OK."}], think=False,
                  options=OPTIONS, keep_alive=KEEP_ALIVE)
    return time.perf_counter() - t0


def chat_json(messages, schema, options=None):
    """Returns (parsed_json, info) where info = {latency, cached, eval_count}. latency is the original one on cache hits."""
    options = options or OPTIONS
    cache = _load()
    key = hashlib.sha256(json.dumps(dict(model=MODEL, messages=messages, schema=schema, options=options),
                                    sort_keys=True).encode()).hexdigest()
    if key in cache:
        e = cache[key]
        return e["result"], dict(latency=e["latency"], cached=True, eval_count=e.get("eval_count", 0))
    t0 = time.perf_counter()
    r = client().chat(model=MODEL, messages=messages, format=schema, think=False, options=options,
                      keep_alive=KEEP_ALIVE)
    fallback = False
    try:
        result = json.loads(r.message.content)
    except json.JSONDecodeError:
        # Added after the freeze tag (bug fix, see docs/RESULTS.md): an unbounded array in the schema can make the
        # model loop until the context is full. Retry once with every array capped, store under the ORIGINAL key.
        fallback = True
        r = client().chat(model=MODEL, messages=messages, format=_bounded(schema), think=False,
                          options={**options, "num_predict": 700}, keep_alive=KEEP_ALIVE)
        result = json.loads(r.message.content)
    latency = time.perf_counter() - t0
    entry = dict(key=key, latency=latency, eval_count=r.eval_count or 0, result=result, fallback=fallback)
    CACHE_DIR.mkdir(exist_ok=True)
    with open(LLM_CACHE, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    cache[key] = entry
    return result, dict(latency=latency, cached=False, eval_count=entry["eval_count"], fallback=fallback)
