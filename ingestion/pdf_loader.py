"""Digital PDF -> text + tables via pdfplumber.
Also decides digital vs scanned: if extracted text is near-empty, flags for OCR.
"""
import pdfplumber
from loguru import logger


def is_scanned(file_path: str, min_chars_per_page: int = 20) -> bool:
    with pdfplumber.open(file_path) as pdf:
        sample_pages = pdf.pages[: min(3, len(pdf.pages))]
        total_chars = sum(len((p.extract_text() or "")) for p in sample_pages)
    avg = total_chars / max(1, len(sample_pages))
    return avg < min_chars_per_page


def load_digital_pdf(file_path: str) -> dict:
    """Returns {'text': str, 'tables': [pd.DataFrame-like dicts], 'pages': int}"""
    full_text = []
    tables = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            full_text.append(f"[page {i+1}]\n{text}")
            for t_idx, table in enumerate(page.extract_tables()):
                tables.append({"page": i + 1, "table_index": t_idx, "rows": table})
        page_count = len(pdf.pages)
    logger.info(f"Loaded digital PDF: {file_path} ({page_count} pages, {len(tables)} tables)")
    return {"text": "\n\n".join(full_text), "tables": tables, "pages": page_count}
