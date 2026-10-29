"""requirement text -> parse -> filtered dense retrieval -> LLM re-rank -> ranked list."""
import time

from .config import FAIRNESS_INSTRUCTION, K_RETRIEVE
from .data import resume_texts
from .parser import parse_requirement
from .rerank import score_candidate
from .retrieve import Retriever

_retriever = None
_resumes = None


def retriever():
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def run(requirement_text, k=K_RETRIEVE, filters_override=None, fairness_instruction=FAIRNESS_INSTRUCTION,
        resume_override=None, parsed_override=None):
    """resume_override: {student_id: text} replaces the resumes shown to the re-ranker (name-swap tests).
    Returns dict(parsed, filters, ranked, timing); ranked = [{id, score, similarity, matched, missing,
    explanation, latency, cached}] sorted by score, ties by dense similarity."""
    global _resumes
    if _resumes is None:
        _resumes = resume_texts()
    t0 = time.perf_counter()
    if parsed_override is None:
        parsed, pinfo = parse_requirement(requirement_text)
    else:
        parsed, pinfo = parsed_override, dict(latency=0.0, cached=True)
    t1 = time.perf_counter()
    hits, filters = retriever().retrieve(parsed, k=k, filters_override=filters_override)
    t2 = time.perf_counter()
    ranked, lat = [], []
    for h in hits:
        text = (resume_override or {}).get(h["id"], _resumes[h["id"]])
        out, info = score_candidate(requirement_text, parsed, text, fairness_instruction)
        lat.append(info["latency"])
        ranked.append(dict(id=h["id"], score=out["score"], similarity=h["similarity"], matched=out["matched_skills"],
                           missing=out["missing_skills"], explanation=out["explanation"], latency=info["latency"],
                           cached=info["cached"]))
    t3 = time.perf_counter()
    ranked.sort(key=lambda r: (-r["score"], -r["similarity"]))
    timing = dict(parse_s=pinfo["latency"], retrieve_s=t2 - t1, rerank_s=sum(lat),
                  rerank_per_candidate_s=(sum(lat) / len(lat)) if lat else 0.0, wall_s=t3 - t0,
                  parse_cached=pinfo["cached"], n_candidates=len(hits))
    return dict(parsed=parsed, filters=filters, ranked=ranked, timing=timing)
