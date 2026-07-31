"""FastAPI app -- Stage 1: POST /ingest, POST /query, GET /health."""
import os

# Must be set before any transformers/sentence_transformers import anywhere in
# this process. Colab preinstalls TensorFlow, and transformers' TF import path
# frequently breaks on protobuf version conflicts. We only ever use PyTorch here.
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

import time
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, Response
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

from ingestion.file_router import detect_file_type
from ingestion.pdf_loader import load_digital_pdf, is_scanned
from ingestion.ocr_loader import load_scanned_pdf
from ingestion.image_loader import describe_image
from ingestion.email_loader import load_eml
from ingestion.text_loader import load_text
from ingestion.table_extractor import store_tables
from ingestion.dedup import compute_file_hash, find_by_hash, find_by_filename, register_document, clear_document
from chunking.text_chunker import chunk_text
from chunking.table_chunker import chunk_table
from chunking.email_chunker import chunk_email
from embeddings.embedder import embed_texts
from embeddings.vector_store import VectorStore
from retrieval.semantic_search import semantic_search
from retrieval.hybrid_search import hybrid_search
from retrieval.reranker import rerank
from retrieval.mmr import mmr_filter
from retrieval.sql_retriever import sql_retrieve
from embeddings.embedder import embed_query
from generation.prompt_builder import build_prompt
from routing.llm_router import route_and_generate
from routing.token_tracker import log_query, get_metrics
from cache.semantic_cache import check_cache, store_cache, cache_size
from monitoring.prometheus_metrics import (
    total_queries, cache_hits, queries_per_tier, query_latency_seconds,
    retrieval_latency_seconds, tokens_saved_gauge, documents_ingested, render_metrics,
)
from monitoring.middleware import MetricsMiddleware
from ui.dashboard import DASHBOARD_HTML

from api.schemas import QueryRequest, QueryResponse, IngestResponse

CHROMA_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./data/chromadb")
SQLITE_PATH = os.environ.get("SQLITE_PATH", "./data/tables.db")
UPLOAD_DIR = "./data/raw"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="FinRAG API - Stage 1-3")
app.add_middleware(MetricsMiddleware)
vector_store = VectorStore(persist_dir=CHROMA_DIR)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML


@app.get("/metrics/prometheus")
def metrics_prometheus():
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)


@app.get("/health")
def health():
    return {"status": "healthy", "chromadb": "ok", "documents_indexed": vector_store.count()}


@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    start = time.time()

    # Save to a temp path first so we can hash it before deciding on a document_id
    tmp_path = os.path.join(UPLOAD_DIR, f"_tmp_{uuid.uuid4().hex[:8]}_{file.filename}")
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    file_hash = compute_file_hash(tmp_path)

    # Case 1: exact same file already ingested -> skip, no duplicate chunks
    existing_by_hash = find_by_hash(SQLITE_PATH, file_hash)
    if existing_by_hash:
        os.remove(tmp_path)
        elapsed_ms = (time.time() - start) * 1000
        logger.info(f"Skipped duplicate ingest of {file.filename} (matches document {existing_by_hash['document_id']})")
        return IngestResponse(
            status="success", document_id=existing_by_hash["document_id"],
            chunks_created=existing_by_hash["chunk_count"], processing_time_ms=elapsed_ms,
            document_type="unchanged", dedup_action="skipped_duplicate",
        )

    # Case 2: same filename, different content -> reuse document_id, clear old chunks first
    existing_by_name = find_by_filename(SQLITE_PATH, file.filename)
    dedup_action = "new"
    if existing_by_name:
        document_id = existing_by_name["document_id"]
        clear_document(vector_store, SQLITE_PATH, document_id)
        dedup_action = "replaced"
    else:
        document_id = str(uuid.uuid4())[:8]

    save_path = os.path.join(UPLOAD_DIR, f"{document_id}_{file.filename}")
    shutil.move(tmp_path, save_path)

    file_type = detect_file_type(save_path)
    all_chunks = []

    if file_type == "pdf_unclassified":
        if is_scanned(save_path):
            file_type = "pdf_scanned"
            doc = load_scanned_pdf(save_path)
            all_chunks = chunk_text(doc["text"], doc_type="scanned")
        else:
            file_type = "pdf_digital"
            doc = load_digital_pdf(save_path)
            all_chunks = chunk_text(doc["text"], doc_type="text")
            if doc["tables"]:
                table_names = store_tables(doc["tables"], document_id, SQLITE_PATH)
                for t in doc["tables"]:
                    all_chunks.extend(chunk_table(t["rows"], f"doc_{document_id}"))
    elif file_type == "image":
        description = describe_image(save_path)
        all_chunks = chunk_text(description, doc_type="text")
    elif file_type == "email":
        doc = load_eml(save_path)
        all_chunks = chunk_email(doc)
    elif file_type == "text":
        doc = load_text(save_path)
        all_chunks = chunk_text(doc["text"], doc_type="text")
    else:
        raise ValueError(f"Unhandled file_type: {file_type}")

    if all_chunks:
        embeddings = embed_texts(all_chunks)
        ids = [f"{document_id}_{i}" for i in range(len(all_chunks))]
        metadatas = [{"source": file.filename, "document_id": document_id, "chunk_index": i}
                     for i in range(len(all_chunks))]
        vector_store.add(ids=ids, texts=all_chunks, embeddings=embeddings, metadatas=metadatas)

    register_document(SQLITE_PATH, document_id, file.filename, file_hash, len(all_chunks))
    documents_ingested.inc()

    elapsed_ms = (time.time() - start) * 1000
    logger.info(f"Ingested {file.filename} as {file_type}: {len(all_chunks)} chunks in {elapsed_ms:.0f}ms ({dedup_action})")
    return IngestResponse(
        status="success", document_id=document_id, chunks_created=len(all_chunks),
        processing_time_ms=elapsed_ms, document_type=file_type, dedup_action=dedup_action,
    )


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    start = time.time()
    total_queries.inc()

    q_emb = embed_query(req.query)

    cached = check_cache(q_emb, threshold=0.92)
    if cached:
        cache_hits.inc()
        queries_per_tier.labels(tier=str(cached["tier"])).inc()
        log_query(SQLITE_PATH, req.query, tier=cached["tier"], model=cached["model_used"],
                  tokens_in=0, tokens_out=0, cache_hit=True)
        elapsed_ms = (time.time() - start) * 1000
        query_latency_seconds.observe(elapsed_ms / 1000)
        cached["total_latency_ms"] = elapsed_ms
        cached["tokens_saved_vs_tier3"] = 0.0  # no generation happened, nothing to compute savings on
        return QueryResponse(**cached)

    # Table/aggregation-style questions get a shot at Text-to-SQL first
    sql_result = sql_retrieve(SQLITE_PATH, req.query)

    retrieval_start = time.time()
    candidates = hybrid_search(vector_store, req.query, top_k=20)
    reranked = rerank(req.query, candidates, top_k=req.top_k * 2)
    hits = mmr_filter(q_emb, reranked, top_k=req.top_k, lambda_param=0.5)
    retrieval_latency_ms = (time.time() - retrieval_start) * 1000
    retrieval_latency_seconds.observe(retrieval_latency_ms / 1000)

    prompt = build_prompt(req.query, hits)
    if sql_result:
        prompt += f"\n\n[SQL query run: {sql_result['sql']}]\n[SQL result rows: {sql_result['rows']}]"

    has_image_ref = any("image" in (h.get("metadata") or {}).get("source", "").lower() for h in hits)
    result = route_and_generate(req.query, prompt, has_image_ref=has_image_ref)
    queries_per_tier.labels(tier=str(result["tier"])).inc()

    savings = log_query(
        SQLITE_PATH, req.query, tier=result["tier"], model=result["model"],
        tokens_in=result["tokens_in"], tokens_out=result["tokens_out"],
    )
    tokens_saved_gauge.set(get_metrics(SQLITE_PATH)["total_tokens_saved"])

    elapsed_ms = (time.time() - start) * 1000
    query_latency_seconds.observe(elapsed_ms / 1000)

    response_payload = {
        "answer": result["answer"],
        "sources": [{"source": (h.get("metadata") or {}).get("source", "sql"), "score": h.get("rerank_score", h.get("score")), "text": h["text"][:200]} for h in hits],
        "model_used": result["model"],
        "tier": result["tier"],
        "tokens_used": {"input": result["tokens_in"], "output": result["tokens_out"]},
        "tokens_saved_vs_tier3": round(savings["savings"], 1),
        "retrieval_latency_ms": retrieval_latency_ms,
        "total_latency_ms": elapsed_ms,
    }

    store_cache(req.query, q_emb, response_payload)
    return QueryResponse(**response_payload)


@app.get("/metrics")
def metrics():
    m = get_metrics(SQLITE_PATH)
    m["documents_indexed"] = vector_store.count()
    m["semantic_cache_size"] = cache_size()
    return m
