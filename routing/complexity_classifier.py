"""Rule-based query complexity classifier -> tier 1 / 2 / 3. No model call, instant."""

TIER1_KEYWORDS = ["what is", "who is", "when", "define", "how much", "what was", "which"]
TIER2_KEYWORDS = ["compare", "analyze", "explain", "why", "how did", "what are the reasons", "difference between"]
TIER3_KEYWORDS = ["summarize", "what trends", "across all documents", "synthesize", "overall", "in general"]


def classify_query(query: str, has_image_ref: bool = False) -> int:
    q = query.lower()
    word_count = len(query.split())

    if has_image_ref or any(k in q for k in TIER3_KEYWORDS) or word_count > 40:
        return 3
    if any(k in q for k in TIER2_KEYWORDS) or 15 <= word_count <= 40:
        return 2
    if any(k in q for k in TIER1_KEYWORDS) or word_count < 15:
        return 1
    return 2  # default to medium if nothing matches clearly
