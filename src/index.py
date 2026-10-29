"""Persistent ChromaDB index of resume embeddings (cosine, normalised bge-small, CPU).

Whole resumes are embedded unless more than CHUNK_IF_SHARE_ABOVE of them exceed 512 tokens; then each resume is
split into ~256-token chunks and a student scores by the max similarity of its chunks. Only resume_text is embedded.
"""
import hashlib
import sys

import chromadb
from chromadb.config import Settings

from .config import (CHROMA_DIR, CHUNK_IF_SHARE_ABOVE, CHUNK_OVERLAP, CHUNK_TOKENS, COLLECTION, EMBED_MODEL,
                     MAX_TOKENS)
from .data import load_students

_model = None


def embedder():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBED_MODEL, device="cpu")
    return _model


def chroma_client():
    return chromadb.PersistentClient(path=str(CHROMA_DIR), settings=Settings(anonymized_telemetry=False))


def token_stats(students):
    tok = embedder().tokenizer
    lens = [len(tok(s["resume_text"], add_special_tokens=True)["input_ids"]) for s in students]
    over = sum(n > MAX_TOKENS for n in lens)
    return dict(n=len(lens), over_512=over, share_over_512=over / len(lens), max_tokens=max(lens),
                mean_tokens=sum(lens) / len(lens))


def chunk(text):
    tok = embedder().tokenizer
    ids = tok(text, add_special_tokens=False)["input_ids"]
    step = CHUNK_TOKENS - CHUNK_OVERLAP
    out = [tok.decode(ids[i:i + CHUNK_TOKENS]) for i in range(0, max(1, len(ids) - CHUNK_OVERLAP), step)]
    return out or [text]


def build_index(force=False, verbose=True):
    """Builds (or reuses) the collection; returns its metadata (mode, token stats, hash)."""
    students = load_students()
    stats = token_stats(students)
    mode = "chunked" if stats["share_over_512"] > CHUNK_IF_SHARE_ABOVE else "whole"
    digest = hashlib.sha256((mode + EMBED_MODEL + "".join(s["resume_text"] for s in students)).encode()).hexdigest()[:16]
    client = chroma_client()
    existing = [c.name for c in client.list_collections()]
    if COLLECTION in existing and not force:
        col = client.get_collection(COLLECTION)
        if (col.metadata or {}).get("hash") == digest:
            return dict(col.metadata)
    if COLLECTION in existing:
        client.delete_collection(COLLECTION)
    meta = {"hnsw:space": "cosine", "hash": digest, "mode": mode,
            "share_over_512": round(stats["share_over_512"], 4), "max_tokens": stats["max_tokens"]}
    col = client.create_collection(COLLECTION, metadata=meta)
    ids, docs, metas = [], [], []
    for s in students:
        parts = chunk(s["resume_text"]) if mode == "chunked" else [s["resume_text"]]
        for j, part in enumerate(parts):
            ids.append(f"{s['id']}#{j}")
            docs.append(part)
            metas.append(dict(student_id=s["id"], branch=s["branch"], cgpa=float(s["cgpa"]),
                              active_backlogs=int(s["active_backlogs"]), grad_year=int(s["grad_year"])))
    emb = embedder().encode(docs, batch_size=32, normalize_embeddings=True, show_progress_bar=verbose)
    for i in range(0, len(ids), 500):
        col.add(ids=ids[i:i + 500], documents=docs[i:i + 500], metadatas=metas[i:i + 500],
                embeddings=emb[i:i + 500].tolist())
    return dict(meta, chunks=len(ids), **{k: stats[k] for k in ("n", "over_512", "mean_tokens")})


if __name__ == "__main__":
    info = build_index(force="--force" in sys.argv)
    print(info)
