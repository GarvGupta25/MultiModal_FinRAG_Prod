"""Scanned PDF -> images (pdf2image) -> text (PaddleOCR)."""
from pdf2image import convert_from_path
from loguru import logger

_ocr_engine = None


def _get_ocr():
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR
        _ocr_engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    return _ocr_engine


def load_scanned_pdf(file_path: str, dpi: int = 200) -> dict:
    ocr = _get_ocr()
    images = convert_from_path(file_path, dpi=dpi)
    full_text = []
    for i, img in enumerate(images):
        import numpy as np
        result = ocr.ocr(np.array(img), cls=True)
        page_lines = []
        for line in (result[0] or []):
            page_lines.append(line[1][0])
        full_text.append(f"[page {i+1}]\n" + "\n".join(page_lines))
    logger.info(f"OCR'd scanned PDF: {file_path} ({len(images)} pages)")
    return {"text": "\n\n".join(full_text), "tables": [], "pages": len(images)}
