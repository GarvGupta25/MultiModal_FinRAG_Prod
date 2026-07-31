"""Serializes table rows into text chunks, one chunk per row, for embedding + retrieval.
The raw structured data still lives in SQLite (see table_extractor.py); these text
chunks let the row show up in normal semantic search with a pointer back to the SQL table.
"""

def chunk_table(rows: list, table_name: str) -> list:
    if not rows or len(rows) < 2:
        return []
    header = rows[0]
    chunks = []
    for row in rows[1:]:
        pairs = [f"{h}: {v}" for h, v in zip(header, row)]
        text = f"[table: {table_name}] " + "; ".join(pairs)
        chunks.append(text)
    return chunks
