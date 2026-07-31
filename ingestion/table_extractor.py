"""Persists tables extracted by pdf_loader into SQLite (one table per source table)."""
import sqlite3
import pandas as pd
from loguru import logger


def store_tables(tables: list, document_id: str, sqlite_path: str) -> list:
    """tables: list of {'page', 'table_index', 'rows'} from pdf_loader.
    Returns list of created SQLite table names."""
    conn = sqlite3.connect(sqlite_path)
    created = []

    for t in tables:
        rows = t["rows"]
        if not rows or len(rows) < 2:
            continue

        raw_header = [
            str(c).strip().replace(" ", "_").replace(".", "")
            for c in rows[0]
        ]

        header = []
        seen = {}

        for i, col in enumerate(raw_header):
            if not col or col.lower() == "none":
                col = f"col_{i}"

            if col in seen:
                seen[col] += 1
                col = f"{col}_{seen[col]}"
            else:
                seen[col] = 0

            header.append(col)

        df = pd.DataFrame(rows[1:], columns=header)

        table_name = f"doc_{document_id}_p{t['page']}_t{t['table_index']}".replace("-", "_")

        df.to_sql(table_name, conn, if_exists="replace", index=False)
        created.append(table_name)

    conn.close()
    logger.info(f"Stored {len(created)} tables for document {document_id}")
    return created