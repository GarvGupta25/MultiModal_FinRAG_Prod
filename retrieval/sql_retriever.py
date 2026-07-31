"""Text-to-SQL: given a natural-language query about tables, generates + runs SQL via Groq."""
from database.sqlite_manager import list_tables, get_table_schema, run_sql
from generation.groq_client import generate


def sql_retrieve(sqlite_path: str, query: str, document_id: str = None) -> dict | None:
    tables = list_tables(sqlite_path, document_id)
    if not tables:
        return None

    schema_desc = []
    for t in tables:
        cols = get_table_schema(sqlite_path, t)
        schema_desc.append(f"Table {t}: columns = {cols}")
    schema_text = "\n".join(schema_desc)

    prompt = f"""Given these SQLite tables:
{schema_text}

Write ONE valid SQLite SELECT query (no explanation, just SQL, no markdown fences) to answer:
"{query}"

If the question can't be answered from these tables, respond with exactly: NONE"""

    result = generate(prompt, model="llama-3.1-8b-instant", max_tokens=200)
    sql = result["answer"].strip().strip("`").replace("sql\n", "")

    if sql.upper().startswith("NONE") or not sql.upper().startswith("SELECT"):
        return None

    try:
        rows = run_sql(sqlite_path, sql)
        return {"sql": sql, "rows": rows}
    except Exception:
        return None
