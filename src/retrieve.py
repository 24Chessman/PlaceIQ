"""Dense retrieval with metadata filters built from the parsed eligibility (or an override for ablations)."""
from .config import COLLECTION, K_RETRIEVE, QUERY_PREFIX
from .index import build_index, chroma_client, embedder


def filters_from_parsed(parsed):
    return dict(min_cgpa=parsed.get("min_cgpa"), max_backlogs=parsed.get("max_backlogs"),
                allowed_branches=list(parsed.get("allowed_branches") or []))


def build_where(f):
    conds = []
    if f.get("min_cgpa") is not None:
        conds.append({"cgpa": {"$gte": float(f["min_cgpa"])}})
    if f.get("max_backlogs") is not None:
        conds.append({"active_backlogs": {"$lte": int(f["max_backlogs"])}})
    if f.get("allowed_branches"):
        conds.append({"branch": {"$in": list(f["allowed_branches"])}})
    if not conds:
        return None
    return conds[0] if len(conds) == 1 else {"$and": conds}


class Retriever:
    def __init__(self):
        self.info = build_index()  # no-op when the stored index matches the resumes
        self.col = chroma_client().get_collection(COLLECTION)
        self.chunked = self.info.get("mode") == "chunked"

    def query_text(self, parsed):
        q = (parsed.get("semantic_query") or "").strip()
        if not q:
            q = f"{parsed.get('role_title', '')}. " + ", ".join(parsed.get("must_have_skills", []))
        return q

    def retrieve(self, parsed, k=K_RETRIEVE, filters_override=None):
        """Returns (hits, filters_used); hits = [{id, similarity}] best first."""
        filters = filters_override if filters_override is not None else filters_from_parsed(parsed)
        where = build_where(filters)
        qv = embedder().encode([QUERY_PREFIX + self.query_text(parsed)], normalize_embeddings=True)[0].tolist()
        total, n = self.col.count(), k * (8 if self.chunked else 1)
        while True:
            res = self.col.query(query_embeddings=[qv], n_results=min(n, total), where=where,
                                 include=["metadatas", "distances"])
            best = {}
            for md, dist in zip(res["metadatas"][0], res["distances"][0]):
                sid = md["student_id"]
                best[sid] = max(best.get(sid, -1.0), 1.0 - dist)
            if len(best) >= k or len(res["ids"][0]) < min(n, total) or n >= total:
                break
            n *= 2
        hits = sorted(({"id": s, "similarity": v} for s, v in best.items()), key=lambda h: -h["similarity"])[:k]
        return hits, filters
