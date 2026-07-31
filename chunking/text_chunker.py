"""Splits text using a simple recursive character splitter (token-approximated by chars*4)."""
from chunking.chunking_config import CHUNK_CONFIG


def _recursive_split(text: str, chunk_size_chars: int, overlap_chars: int) -> list:
    separators = ["\n\n", "\n", ". ", " ", ""]

    def split(text, seps):
        if len(text) <= chunk_size_chars or not seps:
            return [text]
        sep = seps[0]
        parts = text.split(sep) if sep else list(text)
        chunks, current = [], ""
        for part in parts:
            piece = part + sep
            if len(current) + len(piece) <= chunk_size_chars:
                current += piece
            else:
                if current:
                    chunks.append(current)
                current = piece
        if current:
            chunks.append(current)
        # recurse on any still-oversized chunk
        result = []
        for c in chunks:
            if len(c) > chunk_size_chars:
                result.extend(split(c, seps[1:]))
            else:
                result.append(c)
        return result

    raw_chunks = split(text, separators)

    # apply overlap
    overlapped = []
    for i, c in enumerate(raw_chunks):
        if i == 0:
            overlapped.append(c)
        else:
            prev_tail = raw_chunks[i - 1][-overlap_chars:] if overlap_chars else ""
            overlapped.append(prev_tail + c)
    return [c.strip() for c in overlapped if c.strip()]


def chunk_text(text: str, doc_type: str = "text") -> list:
    cfg = CHUNK_CONFIG.get(doc_type, CHUNK_CONFIG["text"])
    chunk_size_chars = cfg["chunk_size"] * 4   # rough tokens->chars
    overlap_chars = cfg["overlap"] * 4
    return _recursive_split(text, chunk_size_chars, overlap_chars)
