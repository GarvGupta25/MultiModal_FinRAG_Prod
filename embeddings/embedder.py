"""Wraps BAAI/bge-base-en-v1.5 for local, free embeddings."""
import os
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_TORCH", "1")

from loguru import logger

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("BAAI/bge-base-en-v1.5")
        logger.info("Loaded embedding model: BAAI/bge-base-en-v1.5")
    return _model


def embed_texts(texts: list) -> list:
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str) -> list:
    # BGE recommends a query instruction prefix for retrieval
    prefixed = f"Represent this sentence for searching relevant passages: {query}"
    return embed_texts([prefixed])[0]
