"""BGE cross-encoder reranker -- re-scores hybrid_search candidates against the query."""
import os
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_TORCH", "1")

from loguru import logger

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder
        _model = CrossEncoder("BAAI/bge-reranker-base")
        logger.info("Loaded reranker: BAAI/bge-reranker-base")
    return _model


def rerank(query: str, candidates: list, top_k: int = 5) -> list:
    if not candidates:
        return []
    model = _get_model()
    pairs = [(query, c["text"]) for c in candidates]
    scores = model.predict(pairs)
    for c, s in zip(candidates, scores):
        c["rerank_score"] = float(s)
    ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
    return ranked[:top_k]
