"""Detects file type via extension + magic bytes and routes to the right loader."""
import os
import magic


def detect_file_type(file_path: str) -> str:
    """Returns one of: pdf_digital, pdf_scanned, image, email, text, table_csv"""
    ext = os.path.splitext(file_path)[1].lower()
    mime = magic.from_file(file_path, mime=True)

    if ext in (".png", ".jpg", ".jpeg", ".webp") or mime.startswith("image/"):
        return "image"
    if ext == ".eml":
        return "email"
    if ext in (".csv", ".tsv"):
        return "table_csv"
    if ext == ".txt" or mime == "text/plain":
        return "text"
    if ext == ".pdf" or mime == "application/pdf":
        return "pdf_unclassified"  # pdf_loader decides digital vs scanned
    raise ValueError(f"Unsupported file type: {file_path} (mime={mime})")
