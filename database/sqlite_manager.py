"""Lists available SQLite tables and their schemas, for Text-to-SQL context building."""
import sqlite3


def list_tables(sqlite_path: str, document_id: str = None) -> list:
    conn = sqlite3.connect(sqlite_path)
    pattern = f"doc_{document_id}_%" if document_id else "doc_%"
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (pattern,)
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_table_schema(sqlite_path: str, table_name: str) -> list:
    conn = sqlite3.connect(sqlite_path)
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    conn.close()
    return [r[1] for r in rows]  # column names


def run_sql(sqlite_path: str, query: str) -> list:
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.execute(query)
    columns = [d[0] for d in cursor.description] if cursor.description else []
    rows = cursor.fetchall()
    conn.close()
    return [dict(zip(columns, row)) for row in rows]
