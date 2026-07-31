"""Tracks ingested documents by content hash to prevent duplicate indexing.

Registry lives in the same SQLite DB used for table data, in a
`document_registry` table: document_id, filename, file_hash, chunk_count, ingested_at.
"""
import hashlib
import sqlite3
import time
from loguru import logger


def compute_file_hash(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS document_registry (
            document_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            chunk_count INTEGER,
            ingested_at REAL
        )
    """)
    conn.commit()


def find_by_hash(sqlite_path: str, file_hash: str) -> dict | None:
    conn = sqlite3.connect(sqlite_path)
    _ensure_table(conn)
    row = conn.execute(
        "SELECT document_id, filename, chunk_count FROM document_registry WHERE file_hash = ?",
        (file_hash,),
    ).fetchone()
    conn.close()
    if row:
        return {"document_id": row[0], "filename": row[1], "chunk_count": row[2]}
    return None


def find_by_filename(sqlite_path: str, filename: str) -> dict | None:
    conn = sqlite3.connect(sqlite_path)
    _ensure_table(conn)
    row = conn.execute(
        "SELECT document_id, file_hash, chunk_count FROM document_registry WHERE filename = ?",
        (filename,),
    ).fetchone()
    conn.close()
    if row:
        return {"document_id": row[0], "file_hash": row[1], "chunk_count": row[2]}
    return None


def register_document(sqlite_path: str, document_id: str, filename: str, file_hash: str, chunk_count: int):
    conn = sqlite3.connect(sqlite_path)
    _ensure_table(conn)
    conn.execute(
        "INSERT OR REPLACE INTO document_registry (document_id, filename, file_hash, chunk_count, ingested_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (document_id, filename, file_hash, chunk_count, time.time()),
    )
    conn.commit()
    conn.close()
    logger.info(f"Registered document {document_id} ({filename}, {chunk_count} chunks)")


def clear_document(vector_store, sqlite_path: str, document_id: str):
    """Removes old chunks from ChromaDB and old per-document tables from SQLite
    before a document is re-ingested with fresh content."""
    vector_store.collection.delete(where={"document_id": document_id})

    conn = sqlite3.connect(sqlite_path)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
        (f"doc_{document_id}_%",),
    ).fetchall()
    for (table_name,) in rows:
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.commit()
    conn.close()
    logger.info(f"Cleared old chunks + tables for document {document_id}")
