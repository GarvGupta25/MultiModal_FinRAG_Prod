from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class QueryResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    answer: str
    sources: List[Dict[str, Any]]
    model_used: str
    tier: int
    tokens_used: Dict[str, int]
    tokens_saved_vs_tier3: float
    retrieval_latency_ms: float
    total_latency_ms: float


class IngestResponse(BaseModel):
    status: str
    document_id: str
    chunks_created: int
    processing_time_ms: float
    document_type: str
    dedup_action: str = "new"   # "new" | "skipped_duplicate" | "replaced"
