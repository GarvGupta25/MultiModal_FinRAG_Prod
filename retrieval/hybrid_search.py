"""Merges semantic search + BM25 results via Reciprocal Rank Fusion (RRF)."""
from retrieval.semantic_search import semantic_search
from retrieval.bm25_search import bm25_search


def _rrf_merge(rank_lists: list, k: int = 60) -> dict:
    """rank_lists: list of ordered-by-rank lists of chunk ids. Returns {id: rrf_score}."""
    scores = {}
    for ranked_ids in rank_lists:
        for rank, cid in enumerate(ranked_ids):
            scores[cid] = scores.get(cid, 0) + 1.0 / (k + rank + 1)
    return scores


def hybrid_search(vector_store, query: str, top_k: int = 20) -> list:
    semantic_hits = semantic_search(vector_store, query, top_k=top_k)
    keyword_hits = bm25_search(vector_store, query, top_k=top_k)

    by_id = {h["id"]: h for h in semantic_hits}
    for h in keyword_hits:
        by_id.setdefault(h["id"], h)

    semantic_ids = [h["id"] for h in semantic_hits]
    keyword_ids = [h["id"] for h in keyword_hits]
    rrf_scores = _rrf_merge([semantic_ids, keyword_ids])

    merged = sorted(by_id.values(), key=lambda h: rrf_scores.get(h["id"], 0), reverse=True)
    for h in merged:
        h["rrf_score"] = rrf_scores.get(h["id"], 0)
    return merged[:top_k]
