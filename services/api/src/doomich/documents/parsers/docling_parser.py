"""Разбор через Docling (MIT). Ставится extra-зависимостью: uv sync --extra docling."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from doomich.documents.parsers.base import Block, ParsedDocument, ParseError


def available() -> bool:
    try:
        import docling  # noqa: F401
    except ImportError:
        return False
    return True


class DoclingParser:
    def __init__(self, ocr: bool = False) -> None:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption

        opts = PdfPipelineOptions()
        opts.do_ocr = ocr
        opts.do_table_structure = True
        if ocr:
            try:
                from docling.datamodel.pipeline_options import TesseractCliOcrOptions

                opts.ocr_options = TesseractCliOcrOptions(lang=["rus", "eng"])
            except ImportError:
                pass
        self._conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})

    def parse(self, path: Path, kind: str) -> ParsedDocument:
        try:
            result = self._conv.convert(str(path))
        except Exception as e:
            raise ParseError(f"Docling: {e}") from e
        ddoc = result.document
        out = ParsedDocument()
        max_page = 0
        for item, level in ddoc.iterate_items():
            page = _page(item)
            max_page = max(max_page, page or 0)
            label = str(getattr(item, "label", "")).lower()
            if "table" in label and hasattr(item, "export_to_markdown"):
                try:
                    md = item.export_to_markdown(doc=ddoc)
                except TypeError:
                    md = item.export_to_markdown()
                if md.strip():
                    out.blocks.append(Block("table", md.strip(), page=page))
                continue
            text = (getattr(item, "text", "") or "").strip()
            if not text:
                continue
            if "section_header" in label or "title" in label:
                out.blocks.append(Block("heading", text, page=page, level=max(1, int(level or 1))))
            elif "list" in label:
                out.blocks.append(Block("list", "- " + text, page=page))
            elif "page_header" in label or "page_footer" in label:
                continue
            else:
                out.blocks.append(Block("text", text, page=page))
        out.pages = max_page or None
        return out


def _page(item: Any) -> int | None:
    prov = getattr(item, "prov", None) or []
    if prov:
        return int(getattr(prov[0], "page_no", 0) or 0) or None
    return None
