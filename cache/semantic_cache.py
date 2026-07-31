"""Redis-backed semantic cache. Embeds each query, checks stored embeddings for
cosine similarity > threshold, returns the cached response on a hit.

Fails soft: if Redis isn't running, cache checks/stores are skipped silently
rather than crashing the request -- caching is an optimization, not a dependency.
"""
import os
import json
import hashlib
import numpy as np
from loguru import logger

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        import redis
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        _redis_client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
    return _redis_client


def _cosine(a, b) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def check_cache(query_embedding: list, threshold: float = 0.92) -> dict | None:
    try:
        r = _get_redis()
        r.ping()
    except Exception:
        return None  # Redis not available -- treat as cache miss, don't fail the request

    keys = r.keys("semcache:emb:*")
    if not keys:
        return None

    best_id, best_score = None, 0.0
    for k in keys:
        cached_emb = json.loads(r.get(k))
        score = _cosine(query_embedding, cached_emb)
        if score > best_score:
            best_score, best_id = score, k.split("semcache:emb:")[1]

    if best_id and best_score >= threshold:
        payload = r.get(f"semcache:payload:{best_id}")
        if payload:
            logger.info(f"Semantic cache HIT (score={best_score:.3f})")
            return json.loads(payload)
    return None


def store_cache(query: str, query_embedding: list, response_payload: dict):
    try:
        r = _get_redis()
        r.ping()
    except Exception:
        return  # skip silently if Redis isn't up

    cache_id = hashlib.sha256(query.encode()).hexdigest()[:16]
    r.set(f"semcache:emb:{cache_id}", json.dumps(query_embedding))
    r.set(f"semcache:payload:{cache_id}", json.dumps(response_payload))


def cache_size() -> int:
    try:
        r = _get_redis()
        r.ping()
        return len(r.keys("semcache:payload:*"))
    except Exception:
        return 0
