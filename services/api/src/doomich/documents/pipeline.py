"""Фоновая обработка документа: антивирус, разбор, нарезка, эмбеддинги, индекс.

Статусы документа: uploaded -> scanning -> parsing -> indexing -> ready | failed.
Расшифрованная копия файла живёт только во временном каталоге на время обработки.
"""

from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path

from sqlalchemy import delete, update

from doomich.ai.registry import get_ai
from doomich.config import settings
from doomich.db import get_db
from doomich.documents import antivirus
from doomich.documents.chunking import ChunkDraft, chunk_document
from doomich.documents.parsers.base import ParsedDocument, ParseError, Parser
from doomich.documents.parsers.basic import BasicParser
from doomich.models import Chunk, Document, UserKey
from doomich.observability.logs import log_event
from doomich.observability.metrics import DOC_SECONDS, DOCS_PROCESSED
from doomich.security import crypto
from doomich.storage.files import get_storage

log = logging.getLogger(__name__)
_parser: dict[str, Parser] = {}


def get_parser() -> Parser:
    st = settings()
    if "p" not in _parser:
        parser: Parser = BasicParser()
        if st.parser_backend in ("auto", "docling"):
            from doomich.documents.parsers import docling_parser

            if docling_parser.available():
                parser = docling_parser.DoclingParser(ocr=st.ocr_enabled)
            elif st.parser_backend == "docling":
                raise RuntimeError("DOOMICH_PARSER_BACKEND=docling, но docling не установлен")
        _parser["p"] = parser
    return _parser["p"]


async def _set_status(doc_id: uuid.UUID, status: str, **extra: object) -> None:
    async with get_db().sys_session() as s:
        await s.execute(update(Document).where(Document.id == doc_id).values(status=status, **extra))


async def file_key_for(doc: Document) -> bytes:
    """Ключ файла: у личных документов он зашифрован ключом пользователя, у общих системным."""
    assert doc.file_key_wrapped is not None
    if doc.user_id is None:
        return crypto.open_system(f"doc-file:{doc.id}", doc.file_key_wrapped)
    async with get_db().sys_session() as s:
        row = await s.get(UserKey, doc.user_id)
        if row is None:
            raise ParseError("нет ключа пользователя", "key_missing")
        key = crypto.unwrap_user_key(doc.user_id, row.kid, row.wrapped)
    return crypto.UserCipher(key).open_file_key(doc.file_key_wrapped)


async def index_drafts(doc: Document, drafts: list[ChunkDraft]) -> int:
    ai = get_ai()
    texts = [f"{d.section}\n{d.body}" if d.section else d.body for d in drafts]
    vectors: list[list[float]] = []
    for i in range(0, len(texts), 64):
        vectors.extend(await ai.embedder.embed(texts[i : i + 64], kind="document"))
    async with get_db().sys_session() as s:
        await s.execute(delete(Chunk).where(Chunk.document_id == doc.id))
        for d, vec in zip(drafts, vectors, strict=True):
            s.add(Chunk(
                id=uuid.uuid4(), document_id=doc.id, tenant_id=doc.tenant_id, user_id=doc.user_id, scope=doc.scope,
                course_id=doc.course_id, ord=d.ord, page=d.page, sheet=d.sheet, section=d.section, body=d.body,
                tokens=d.tokens, embedding=vec, meta=d.meta,
            ))
    return len(drafts)


async def process_document(doc_id: uuid.UUID) -> str:
    st = settings()
    started = time.monotonic()
    async with get_db().sys_session() as s:
        doc = await s.get(Document, doc_id)
    if doc is None:
        return "missing"
    if doc.status == "ready":
        return "ready"
    storage = get_storage()
    tmp: Path | None = None
    try:
        file_key = await file_key_for(doc)
        assert doc.storage_key is not None
        tmp = storage.decrypt_to_temp(doc.storage_key, file_key, str(doc.id), suffix=f".{doc.kind}")
        if st.clamd_host:
            await _set_status(doc.id, "scanning")
            try:
                await antivirus.scan_file(tmp, st.clamd_host, st.clamd_port)
            except antivirus.VirusFound as e:
                raise ParseError(f"файл заражён: {e.signature}", "virus_found") from e
        elif st.is_prod_like:
            raise ParseError("антивирус не настроен", "antivirus_unavailable")
        await _set_status(doc.id, "parsing")
        parsed: ParsedDocument = get_parser().parse(tmp, doc.kind)
        if parsed.needs_ocr and doc.kind == "pdf":
            from doomich.documents.parsers import ocr

            if st.ocr_enabled and ocr.available():
                parsed = ocr.ocr_pdf(tmp, max_pages=st.max_document_pages)
            elif not parsed.blocks:
                raise ParseError("похоже на скан без текста, OCR пока не включён", "needs_ocr")
        if parsed.pages and parsed.pages > st.max_document_pages:
            raise ParseError(f"больше {st.max_document_pages} страниц", "too_many_pages")
        drafts = chunk_document(parsed)
        if not drafts:
            raise ParseError("в документе не найден текст", "empty_document")
        await _set_status(doc.id, "indexing", pages=parsed.pages)
        count = await index_drafts(doc, drafts)
        await _set_status(doc.id, "ready", error=None)
        DOCS_PROCESSED.labels(status="ready", kind=doc.kind).inc()
        DOC_SECONDS.observe(time.monotonic() - started)
        log_event(log, "документ обработан", kind=doc.kind, chunks=count, seconds=round(time.monotonic() - started, 1))
        return "ready"
    except ParseError as e:
        await _set_status(doc.id, "failed", error=e.code)
        DOCS_PROCESSED.labels(status="failed", kind=doc.kind).inc()
        log_event(log, "документ не обработан", logging.WARNING, kind=doc.kind, reason=e.code)
        return "failed"
    except Exception:
        await _set_status(doc.id, "failed", error="internal")
        DOCS_PROCESSED.labels(status="failed", kind=doc.kind).inc()
        log.exception("ошибка обработки документа")
        return "failed"
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
