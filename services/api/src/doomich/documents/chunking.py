"""Нарезка документа на фрагменты по структуре.

Фрагмент собирается из блоков под одним заголовком, пока не наберётся
TARGET_CHARS. Таблица не режется посередине строки. В начало фрагмента
добавляется путь заголовков (section), чтобы он был понятен вне контекста.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from doomich.documents.parsers.base import ParsedDocument

TARGET_CHARS = 1400
MAX_CHARS = 2400
OVERLAP_CHARS = 200


@dataclass
class ChunkDraft:
    ord: int
    body: str
    page: int | None
    sheet: str | None
    section: str | None
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def tokens(self) -> int:
        return int(len(self.body) / 3.5) + 1


def _split_long(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    rest = text
    while len(rest) > limit:
        cut = max(rest.rfind("\n", 0, limit), rest.rfind(". ", 0, limit))
        if cut < limit // 2:
            cut = rest.rfind(" ", 0, limit)
        if cut <= 0:
            cut = limit
        parts.append(rest[: cut + 1].strip())
        rest = rest[cut + 1 :]
    if rest.strip():
        parts.append(rest.strip())
    return parts


def _split_table(md: str, limit: int) -> list[str]:
    lines = md.split("\n")
    if len(md) <= limit or len(lines) < 4:
        return [md]
    head = lines[:2]
    out: list[str] = []
    cur: list[str] = []
    size = 0
    for line in lines[2:]:
        if size + len(line) > limit and cur:
            out.append("\n".join(head + cur))
            cur, size = [], 0
        cur.append(line)
        size += len(line) + 1
    if cur:
        out.append("\n".join(head + cur))
    return out


def chunk_document(doc: ParsedDocument) -> list[ChunkDraft]:
    drafts: list[ChunkDraft] = []
    path: list[tuple[int, str]] = []
    buf: list[str] = []
    buf_page: int | None = None
    buf_sheet: str | None = None
    size = 0

    def section() -> str | None:
        return " / ".join(t for _, t in path) or None

    def flush(carry: bool = True) -> None:
        nonlocal buf, size, buf_page, buf_sheet
        text = "\n\n".join(buf).strip()
        if text:
            drafts.append(ChunkDraft(ord=len(drafts), body=text, page=buf_page, sheet=buf_sheet, section=section()))
        tail = text[-OVERLAP_CHARS:] if carry and text and len(text) > OVERLAP_CHARS else ""
        buf = [tail] if tail and not text.startswith("|") else []
        size = len(tail)
        buf_page, buf_sheet = None, None

    for block in doc.blocks:
        if block.kind == "heading":
            flush(carry=False)
            while path and path[-1][0] >= block.level:
                path.pop()
            path.append((block.level, block.text[:150]))
            continue
        pieces = _split_table(block.text, MAX_CHARS) if block.kind == "table" else _split_long(block.text, MAX_CHARS)
        for piece in pieces:
            if block.kind == "table" and buf:
                flush(carry=False)
            if size + len(piece) > TARGET_CHARS and buf:
                flush()
            if buf_page is None:
                buf_page = block.page
            if buf_sheet is None:
                buf_sheet = block.sheet
            buf.append(piece)
            size += len(piece)
            if block.kind == "table":
                flush(carry=False)
    flush(carry=False)
    # Пустые хвосты от перекрытия не нужны
    return [d for d in drafts if len(d.body.strip()) > 20 or d.body.startswith("|")]
