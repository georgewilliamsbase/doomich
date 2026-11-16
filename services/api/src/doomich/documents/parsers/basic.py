"""Лёгкие разборщики без моделей. Используются, когда Docling недоступен."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any

from doomich.documents.parsers.base import Block, ParsedDocument, ParseError

MAX_SHEET_ROWS = 5000


def _clean(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _heading_level(line: str) -> int:
    """Грубая эвристика заголовков в PDF: "1.2 Название", "Глава 3", короткая строка капсом."""
    s = line.strip()
    if len(s) > 120 or len(s) < 3:
        return 0
    if re.match(r"^(глава|раздел|часть|chapter|section)\s+\d+", s, re.I):
        return 1
    m = re.match(r"^(\d+(?:\.\d+){0,3})\.?\s+[A-ZА-ЯЁ]", s)
    if m and not s.endswith((".", ",", ";")):
        return min(3, m.group(1).count(".") + 1)
    if s.isupper() and len(s.split()) <= 10 and re.search(r"[A-ZА-ЯЁ]", s):
        return 1
    return 0


def parse_pdf(path: Path) -> ParsedDocument:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as e:
                raise ParseError("PDF защищён паролем", "pdf_encrypted") from e
        pages = reader.pages
    except PdfReadError as e:
        raise ParseError(f"повреждённый PDF: {e}", "pdf_broken") from e
    doc = ParsedDocument(pages=len(pages))
    empty_pages = 0
    for i, page in enumerate(pages, start=1):
        try:
            text = _clean(page.extract_text() or "")
        except Exception:
            text = ""
        if len(text) < 20:
            empty_pages += 1
            continue
        para: list[str] = []
        for line in text.split("\n"):
            level = _heading_level(line)
            if level:
                if para:
                    doc.blocks.append(Block("text", "\n".join(para), page=i))
                    para = []
                doc.blocks.append(Block("heading", line.strip(), page=i, level=level))
            elif line.strip():
                para.append(line.strip())
            elif para:
                doc.blocks.append(Block("text", "\n".join(para), page=i))
                para = []
        if para:
            doc.blocks.append(Block("text", "\n".join(para), page=i))
    meta: dict[str, object] = dict(reader.metadata or {})
    doc.title = str(meta.get("/Title") or "") or None
    doc.needs_ocr = bool(pages) and empty_pages / len(pages) > 0.5
    return doc


def _table_md(rows: list[list[Any]]) -> str:
    rows = [[("" if c is None else str(c)).replace("|", "/").replace("\n", " ").strip() for c in r] for r in rows]
    rows = [r for r in rows if any(r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    head = "| " + " | ".join(rows[0]) + " |"
    sep = "| " + " | ".join("---" for _ in range(width)) + " |"
    body = ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join([head, sep, *body])


def parse_docx(path: Path) -> ParsedDocument:
    import docx
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    try:
        d = docx.Document(str(path))
    except (zipfile.BadZipFile, KeyError, ValueError) as e:
        raise ParseError(f"повреждённый DOCX: {e}", "docx_broken") from e
    doc = ParsedDocument()
    # Номер страницы в DOCX неизвестен без вёрстки; используем условные "страницы" по разрывам
    page = 1
    body = d.element.body
    for child in body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            p = Paragraph(child, d)
            if 'w:br w:type="page"' in child.xml or "lastRenderedPageBreak" in child.xml:
                page += 1
            text = _clean(p.text)
            if not text:
                continue
            style = (p.style.name if p.style is not None else "") or ""
            if style.lower().startswith(("heading", "заголовок", "title")):
                digits = re.findall(r"\d", style)
                doc.blocks.append(Block("heading", text, page=page, level=int(digits[0]) if digits else 1))
            elif style.lower().startswith(("list", "список")):
                doc.blocks.append(Block("list", "- " + text, page=page))
            else:
                doc.blocks.append(Block("text", text, page=page))
        elif tag == "tbl":
            t = Table(child, d)
            rows = [[cell.text for cell in row.cells] for row in t.rows]
            md = _table_md(rows)
            if md:
                doc.blocks.append(Block("table", md, page=page))
    doc.pages = page
    core = d.core_properties
    doc.title = core.title or None
    return doc


def parse_xlsx(path: Path) -> ParsedDocument:
    from openpyxl import load_workbook

    try:
        wb = load_workbook(str(path), read_only=True, data_only=True)
    except (zipfile.BadZipFile, KeyError, ValueError) as e:
        raise ParseError(f"повреждённый XLSX: {e}", "xlsx_broken") from e
    doc = ParsedDocument(pages=len(wb.worksheets))
    for ws in wb.worksheets:
        rows: list[list[Any]] = []
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i >= MAX_SHEET_ROWS:
                break
            if any(c is not None and str(c).strip() for c in row):
                rows.append(list(row))
        if not rows:
            continue
        doc.blocks.append(Block("heading", f"Лист {ws.title}", sheet=ws.title, level=1))
        # Большие таблицы режем по 40 строк, повторяя заголовок, чтобы фрагмент был понятен сам по себе
        header, data = rows[0], rows[1:]
        for start in range(0, max(1, len(data)), 40):
            part = [header, *data[start : start + 40]]
            md = _table_md(part)
            if md:
                doc.blocks.append(Block("table", md, sheet=ws.title))
    return doc


def parse_pptx(path: Path) -> ParsedDocument:
    from pptx import Presentation

    try:
        prs = Presentation(str(path))
    except (zipfile.BadZipFile, KeyError, ValueError) as e:
        raise ParseError(f"повреждённый PPTX: {e}", "pptx_broken") from e
    doc = ParsedDocument(pages=len(prs.slides))
    for i, slide in enumerate(prs.slides, start=1):
        title = slide.shapes.title.text.strip() if slide.shapes.title is not None and slide.shapes.title.text else ""
        if title:
            doc.blocks.append(Block("heading", title, page=i, level=2))
        texts: list[str] = []
        for shape in slide.shapes:
            if shape == slide.shapes.title:
                continue
            if shape.has_text_frame:
                t = _clean(shape.text_frame.text)
                if t:
                    texts.append(t)
            if getattr(shape, "has_table", False) and shape.has_table:
                rows = [[c.text for c in r.cells] for r in shape.table.rows]
                md = _table_md(rows)
                if md:
                    doc.blocks.append(Block("table", md, page=i))
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
            notes = _clean(slide.notes_slide.notes_text_frame.text)
            if notes:
                texts.append("Заметки: " + notes)
        if texts:
            doc.blocks.append(Block("text", "\n".join(texts), page=i))
    return doc


class BasicParser:
    def parse(self, path: Path, kind: str) -> ParsedDocument:
        if kind == "pdf":
            return parse_pdf(path)
        if kind == "docx":
            return parse_docx(path)
        if kind == "xlsx":
            return parse_xlsx(path)
        if kind == "pptx":
            return parse_pptx(path)
        raise ParseError(f"неподдерживаемый тип {kind}", "unsupported_type")
