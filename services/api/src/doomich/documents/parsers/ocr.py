"""OCR сканов без Docling: страницы PDF рендерятся pypdfium2, текст распознаёт Tesseract (rus+eng)."""

from __future__ import annotations

from pathlib import Path

from doomich.documents.parsers.base import Block, ParsedDocument


def available() -> bool:
    try:
        import pypdfium2  # noqa: F401
        import pytesseract  # noqa: F401
    except ImportError:
        return False
    return True


def ocr_pdf(path: Path, max_pages: int = 300, dpi: int = 200) -> ParsedDocument:
    import pypdfium2 as pdfium
    import pytesseract

    pdf = pdfium.PdfDocument(str(path))
    doc = ParsedDocument(pages=len(pdf))
    scale = dpi / 72
    for i in range(min(len(pdf), max_pages)):
        image = pdf[i].render(scale=scale).to_pil()
        text = pytesseract.image_to_string(image, lang="rus+eng")
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        if text:
            doc.blocks.append(Block("text", text, page=i + 1))
    return doc
