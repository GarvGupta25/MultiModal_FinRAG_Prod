"""Plain text file -> str, no processing needed."""

def load_text(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return {"text": text}
