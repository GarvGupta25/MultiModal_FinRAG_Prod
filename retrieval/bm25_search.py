"""BM25 keyword search over all chunks currently in the vector store.
Rebuilds the BM25 index from ChromaDB's stored documents (fine at this corpus size;
for very large corpora you'd persist the index separately)."""
from rank_bm25 import BM25Okapi
from loguru import logger

_bm25_cache = {"index": None, "ids": None, "texts": None, "count": 0}


def _tokenize(text: str) -> list:
    return text.lower().split()


def _build_index(vector_store):
    all_data = vector_store.collection.get()
    ids = all_data["ids"]
    texts = all_data["documents"]
    tokenized = [_tokenize(t) for t in texts]
    index = BM25Okapi(tokenized)
    _bm25_cache.update({"index": index, "ids": ids, "texts": texts, "count": len(ids)})
    logger.info(f"Rebuilt BM25 index over {len(ids)} chunks")


def bm25_search(vector_store, query: str, top_k: int = 20) -> list:
    current_count = vector_store.collection.count()
    if _bm25_cache["index"] is None or _bm25_cache["count"] != current_count:
        _build_index(vector_store)

    if _bm25_cache["count"] == 0:
        return []

    scores = _bm25_cache["index"].get_scores(_tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [
        {"id": _bm25_cache["ids"][i], "text": _bm25_cache["texts"][i], "score": float(scores[i])}
        for i in ranked if scores[i] > 0
    ]
