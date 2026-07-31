# Architecture

This document describes the implemented MultiModal FinRAG Prod architecture. It focuses on what is present in the repository and avoids deployment or benchmark claims that are not represented by code.

## Ingestion

`api/main.py` exposes `POST /ingest` for document upload. Uploaded files are written to `data/raw`, hashed, checked for duplicates, routed by type, extracted, chunked, embedded, and persisted.

`ingestion/file_router.py` detects common file types using extension and MIME information. The active API branch handles PDFs, images, emails, and text files. CSV/TSV detection exists in the router, but CSV/TSV ingestion is not wired into the current API branch.

## Chunking

Chunking is split by content type:

- `chunking/text_chunker.py` handles extracted text.
- `chunking/table_chunker.py` handles table rows extracted from PDFs.
- `chunking/email_chunker.py` handles email content.

The chunkers output strings that become vector-store documents.

## Embeddings

`embeddings/embedder.py` provides query and document embeddings. `api/main.py` uses `embed_texts` during ingestion and `embed_query` during question answering.

## Vector Store

`embeddings/vector_store.py` wraps a persistent ChromaDB collection named `finrag`. The API stores chunk IDs, chunk texts, embeddings, and metadata containing source filename, document ID, and chunk index.

## SQL Retrieval

`database/sqlite_manager.py` stores extracted tables and document metadata. `retrieval/sql_retriever.py` lists available SQLite tables, asks a Groq-hosted model for a single `SELECT` statement, and executes it when valid.

The SQL path is opportunistic: if no table is available, the model returns `NONE`, or the SQL execution fails, the normal retrieval pipeline continues.

## Hybrid Retrieval

`retrieval/hybrid_search.py` combines:

- dense semantic retrieval from ChromaDB;
- BM25 keyword retrieval over current vector-store documents;
- Reciprocal Rank Fusion to merge both ranked lists.

## BM25

`retrieval/bm25_search.py` rebuilds an in-memory BM25 index from ChromaDB documents when the vector-store count changes. This is straightforward and useful for modest corpora, but a larger deployment should persist or incrementally update the keyword index.

## Reranker

`retrieval/reranker.py` loads `BAAI/bge-reranker-base` through Sentence Transformers' `CrossEncoder`. It scores `(query, candidate_text)` pairs and returns the top ranked candidates.

## MMR

`retrieval/mmr.py` embeds reranked candidate texts and applies Maximum Marginal Relevance. This keeps selected context relevant while reducing redundant chunks.

## Router

`routing/complexity_classifier.py` is a rule-based classifier. It assigns a query to Tier 1, Tier 2, or Tier 3 based on keywords, word count, and whether an image reference is detected.

`routing/llm_router.py` maps tiers to generation models:

- Tier 1: Groq `llama-3.1-8b-instant`
- Tier 2: `GROQ_TIER2_MODEL`, defaulting to `llama-3.3-70b-versatile`
- Tier 3: Gemini, with Groq Tier 2 fallback on failure

## Generation

`generation/prompt_builder.py` builds the prompt from retrieved context. `generation/groq_client.py` and `generation/gemini_client.py` wrap the external model APIs and return answer text plus token metadata.

## Cache

`cache/semantic_cache.py` uses Redis to store query embeddings and response payloads. Cache lookup is cosine-similarity based. Redis failures are intentionally non-fatal, so caching behaves as an optimization rather than a required service.

## Monitoring

`monitoring/prometheus_metrics.py` defines counters, gauges, and histograms. `monitoring/middleware.py` integrates metrics collection with FastAPI requests. The API exposes both JSON and Prometheus-format metrics.

Grafana dashboard JSON files are stored under `monitoring/grafana_dashboards/`.

## API

The API endpoints are implemented in `api/main.py`:

- `GET /health`
- `GET /dashboard`
- `GET /metrics`
- `GET /metrics/prometheus`
- `POST /ingest`
- `POST /query`

Request and response schemas live in `api/schemas.py`.

## Frontend

`ui/app.py` provides a Gradio interface with tabs for document upload, chat, dashboard, metrics, and health. The API also serves a simple HTML dashboard at `/dashboard`.

## Orchestration and Experiment Assets

The repository includes:

- Airflow DAG definitions under `orchestration/airflow_dags/`;
- DVC pipeline metadata in `dvc.yaml`;
- MLflow logging helper in `experiments/mlflow_logging.py`;
- Grafana dashboard definitions under `monitoring/grafana_dashboards/`.

These are useful production-readiness assets, but this repository does not currently include Docker Compose or a complete multi-service deployment file.
