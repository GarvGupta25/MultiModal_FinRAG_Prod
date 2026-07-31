"""Defines Prometheus metrics exposed at GET /metrics/prometheus."""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

total_queries = Counter("finrag_total_queries", "Total queries processed")
cache_hits = Counter("finrag_cache_hits", "Total semantic cache hits")
queries_per_tier = Counter("finrag_queries_per_tier", "Queries routed per LLM tier", ["tier"])
query_latency_seconds = Histogram("finrag_query_latency_seconds", "End-to-end query latency")
retrieval_latency_seconds = Histogram("finrag_retrieval_latency_seconds", "Retrieval-only latency")
tokens_saved_gauge = Gauge("finrag_tokens_saved_total", "Cumulative token-cost savings vs always-Tier-3")
active_connections = Gauge("finrag_active_connections", "In-flight HTTP requests")
documents_ingested = Counter("finrag_documents_ingested_total", "Total documents ingested")


def render_metrics():
    return generate_latest(), CONTENT_TYPE_LATEST
