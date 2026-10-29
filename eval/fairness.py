"""Name-swap fairness test: names only (not college prestige or other proxies).

For each of the top-10 candidates of the main ranking (10 test requirements = 100 pairs) four swapped resumes are made:
one CONTROL (different name, SAME group) and three CROSS-GROUP swaps (three of the five other groups, rotated by pair
index so each group is used about equally). Only the header line changes (asserted). The re-ranker rescoring uses the
same requirement text and parsed skills; the pool rank shift substitutes the new score into the 20-candidate pool.
"""
import json
import random

from metrics import DATA, RES, load_all
from stats import boot_ci, paired

SEED = 42


def swap_name(text, old, new):
    lines = text.split("\n")
    assert text.count(old) == 1 and old in lines[0], "name must appear exactly once, in the header line"
    lines[0] = lines[0].replace(old, new)
    out = "\n".join(lines)
    assert out.split("\n")[1:] == text.split("\n")[1:], "only the header line may change"
    assert out != text
    return out


def draw_name(rng, pool, avoid):
    while True:
        n = f"{rng.choice(pool['first'])} {rng.choice(pool['last'])}"
        if n != avoid:
            return n


def make_variants(pairs, students, truth):
    """pairs = [(rid, sid)]. Returns list of dicts(rid, sid, variant, target_group, orig_group, name, text)."""
    pools = json.loads((DATA / "name_pools.json").read_text(encoding="utf-8"))
    groups = list(pools)
    rng = random.Random(SEED)
    out = []
    for i, (rid, sid) in enumerate(pairs):
        g0, old, text = truth[sid]["name_group"], students[sid]["name"], students[sid]["resume_text"]
        others = [g for g in groups if g != g0]
        targets = [("control", g0)] + [(f"cross{j + 1}", others[(i + j) % len(others)]) for j in range(3)]
        for variant, tg in targets:
            new = draw_name(rng, pools[tg], old)
            out.append(dict(rid=rid, sid=sid, variant=variant, target_group=tg, orig_group=g0, name=new,
                            text=swap_name(text, old, new)))
    return out


def rank_in_pool(pool, sid, new_score=None):
    """pool = ranked list of dicts(id, score, similarity). Returns 1-based rank of sid, optionally with a new score."""
    items = [(p["id"], new_score if (new_score is not None and p["id"] == sid) else p["score"], p["similarity"])
             for p in pool]
    items.sort(key=lambda t: (-t[1], -t[2]))
    return 1 + [t[0] for t in items].index(sid)


def gender(group):
    return "female" if group.endswith("_female") else "male"


def region(group):
    return group.rsplit("_", 1)[0]


def summarize(rows):
    """rows of ONE condition -> dict of metrics with bootstrap CIs over pairs (or swaps for per-group means)."""
    by_pair = {}
    for r in rows:
        by_pair.setdefault((r["rid"], r["sid"]), {}).setdefault(r["variant"] == "control" and "control" or "cross", []).append(r)

    def per_pair(fn):
        c, x = [], []
        for v in by_pair.values():
            c.append(sum(fn(r) for r in v["control"]) / len(v["control"]))
            x.append(sum(fn(r) for r in v["cross"]) / len(v["cross"]))
        return c, x

    out = {}
    for name, fn in (("abs_score_change", lambda r: abs(r["delta"])),
                     ("share_ge5", lambda r: float(abs(r["delta"]) >= 5)),
                     ("abs_rank_shift", lambda r: abs(r["rank_shift"])),
                     ("boundary_crossing", lambda r: float(r["crossed_top10"])),
                     ("abs_sim_shift", lambda r: abs(r["sim_delta"]))):
        c, x = per_pair(fn)
        out[name] = dict(control=boot_ci(c), cross=boot_ci(x), cross_minus_control=paired(x, c))
    cross = [r for r in rows if r["variant"] != "control"]
    out["signed_by_target_group"] = {
        g: boot_ci([r["delta"] for r in cross if r["target_group"] == g])
        for g in sorted({r["target_group"] for r in cross})}
    out["signed_by_target_gender"] = {
        s: boot_ci([r["delta"] for r in cross if gender(r["target_group"]) == s]) for s in ("female", "male")}
    out["signed_by_target_region"] = {
        s: boot_ci([r["delta"] for r in cross if region(r["target_group"]) == s])
        for s in sorted({region(r["target_group"]) for r in cross})}
    out["signed_gender_transition"] = {
        f"{gender(a)}->{gender(b)}": boot_ci([r["delta"] for r in cross if gender(r["orig_group"]) == gender(a)
                                              and gender(r["target_group"]) == gender(b)])
        for a, b in (("x_male", "x_male"), ("x_male", "x_female"), ("x_female", "x_male"), ("x_female", "x_female"))}
    out["n_pairs"], out["n_swaps"] = len(by_pair), len(rows)
    out["target_group_counts"] = {g: sum(r["target_group"] == g for r in cross)
                                  for g in sorted({r["target_group"] for r in cross})}
    return out


def similarity_shifts(variants, students, parsed_by_rid, retriever_obj):
    """Cosine similarity of original vs swapped resume to the query (CPU embedding, nothing written to Chroma)."""
    from src.config import QUERY_PREFIX
    from src.index import embedder
    emb = embedder()
    qv = {rid: emb.encode([QUERY_PREFIX + retriever_obj.query_text(p)], normalize_embeddings=True)[0]
          for rid, p in parsed_by_rid.items()}
    orig_ids = sorted({(v["rid"], v["sid"]) for v in variants})
    o = emb.encode([students[s]["resume_text"] for _, s in orig_ids], normalize_embeddings=True, batch_size=32)
    sim_o = {k: float(o[i] @ qv[k[0]]) for i, k in enumerate(orig_ids)}
    s = emb.encode([v["text"] for v in variants], normalize_embeddings=True, batch_size=32)
    return [dict(sim_orig=sim_o[(v["rid"], v["sid"])], sim_new=float(s[i] @ qv[v["rid"]])) for i, v in enumerate(variants)]


def run_condition(variants, sims, pools, parsed_by_rid, texts, fairness_instruction, out_path):
    """Scores every swapped resume (resumable). pools = {rid: ranked list under this condition}."""
    from src.rerank import score_candidate
    rows = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else []
    done = {(r["rid"], r["sid"], r["variant"]) for r in rows}
    for v, sm in zip(variants, sims):
        if (v["rid"], v["sid"], v["variant"]) in done:
            continue
        pool = pools[v["rid"]]
        orig = next(p for p in pool if p["id"] == v["sid"])
        out, info = score_candidate(texts[v["rid"]], parsed_by_rid[v["rid"]], v["text"], fairness_instruction)
        r0, r1 = rank_in_pool(pool, v["sid"]), rank_in_pool(pool, v["sid"], out["score"])
        rows.append(dict(rid=v["rid"], sid=v["sid"], variant=v["variant"], target_group=v["target_group"],
                         orig_group=v["orig_group"], orig_score=orig["score"], new_score=out["score"],
                         delta=out["score"] - orig["score"], rank_orig=r0, rank_new=r1, rank_shift=r1 - r0,
                         crossed_top10=(r0 <= 10) != (r1 <= 10), sim_orig=sm["sim_orig"], sim_new=sm["sim_new"],
                         sim_delta=sm["sim_new"] - sm["sim_orig"], cached=info["cached"], latency=info["latency"]))
        if len(rows) % 10 == 0:
            out_path.write_text(json.dumps(rows), encoding="utf-8")
    out_path.write_text(json.dumps(rows), encoding="utf-8")
    return rows
