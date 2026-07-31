"""Logs every query's token usage + cost-equivalent savings vs always using Tier 3, to SQLite."""
import sqlite3
import time

# Rough relative cost weights (Tier 3 = 1.0 baseline; Groq tiers are free but we
# still track "cost equivalent" so the savings metric means something if you ever
# swap in paid endpoints).
TIER_RATES = {1: 0.02, 2: 0.15, 3: 1.0}


def _ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS token_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT, tier INTEGER, model TEXT,
            tokens_in INTEGER, tokens_out INTEGER,
            cost_actual REAL, cost_baseline REAL, savings REAL,
            cache_hit INTEGER DEFAULT 0,
            timestamp REAL
        )
    """)
    conn.commit()


def log_query(sqlite_path: str, query: str, tier: int, model: str,
              tokens_in: int, tokens_out: int, cache_hit: bool = False):
    total_tokens = tokens_in + tokens_out
    cost_actual = total_tokens * TIER_RATES[tier]
    cost_baseline = total_tokens * TIER_RATES[3]
    savings = cost_baseline - cost_actual

    conn = sqlite3.connect(sqlite_path)
    _ensure_table(conn)
    conn.execute(
        "INSERT INTO token_log (query, tier, model, tokens_in, tokens_out, cost_actual, cost_baseline, savings, cache_hit, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (query, tier, model, tokens_in, tokens_out, cost_actual, cost_baseline, savings, int(cache_hit), time.time()),
    )
    conn.commit()
    conn.close()
    return {"savings": savings, "savings_pct": (savings / cost_baseline * 100) if cost_baseline else 0}


def get_metrics(sqlite_path: str) -> dict:
    conn = sqlite3.connect(sqlite_path)
    _ensure_table(conn)
    total = conn.execute("SELECT COUNT(*) FROM token_log").fetchone()[0]
    if total == 0:
        conn.close()
        return {"total_queries": 0, "cache_hit_rate": 0, "routing_distribution": {}, "total_tokens_saved": 0}

    cache_hits = conn.execute("SELECT COUNT(*) FROM token_log WHERE cache_hit = 1").fetchone()[0]
    tier_counts = dict(conn.execute("SELECT tier, COUNT(*) FROM token_log GROUP BY tier").fetchall())
    total_saved = conn.execute("SELECT SUM(savings) FROM token_log").fetchone()[0] or 0
    conn.close()

    routing_distribution = {f"tier{t}": round(c / total, 3) for t, c in tier_counts.items()}
    return {
        "total_queries": total,
        "cache_hit_rate": round(cache_hits / total, 3),
        "routing_distribution": routing_distribution,
        "total_tokens_saved": round(total_saved, 1),
    }
