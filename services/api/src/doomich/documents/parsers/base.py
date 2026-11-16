"""Разбор документов в последовательность блоков.

Основной разборщик Docling (заголовки, таблицы, OCR). Если Docling не установлен
(например, в CI), работают лёгкие разборщики на pypdf, python-docx, openpyxl,
python-pptx. Они хуже с таблицами в PDF, но дают текст по страницам и листам.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol

BlockKind = Literal["heading", "text", "table", "list"]


@dataclass
class Block:
    kind: BlockKind
    text: str
    page: int | None = None
    sheet: str | None = None
    level: int = 0


@dataclass
class ParsedDocument:
    blocks: list[Block] = field(default_factory=list)
    pages: int | None = None
    title: str | None = None
    needs_ocr: bool = False


class Parser(Protocol):
    def parse(self, path: Path, kind: str) -> ParsedDocument: ...


class ParseError(Exception):
    def __init__(self, message: str, code: str = "parse_failed") -> None:
        super().__init__(message)
        self.code = code


MAGIC = {
    b"%PDF": "pdf",
}


def detect_kind(head: bytes, filename: str) -> str | None:
    """Определяет тип по содержимому, а не по расширению."""
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"PK\x03\x04"):
        name = filename.lower()
        if name.endswith(".docx"):
            return "docx"
        if name.endswith((".xlsx", ".xlsm")):
            return "xlsx"
        if name.endswith(".pptx"):
            return "pptx"
        return "zip"
    return None


def zip_kind(path: Path) -> str | None:
    import zipfile

    try:
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
    except zipfile.BadZipFile:
        return None
    if "word/document.xml" in names:
        return "docx"
    if "xl/workbook.xml" in names:
        return "xlsx"
    if "ppt/presentation.xml" in names:
        return "pptx"
    return None


MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
