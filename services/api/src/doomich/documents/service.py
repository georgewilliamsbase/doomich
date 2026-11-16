"""Загрузка, список и удаление документов пользователя."""

from __future__ import annotations

import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from doomich.common.errors import AppError, NotFound, PayloadTooLarge
from doomich.config import settings
from doomich.deps import CurrentUser, user_cipher_for
from doomich.documents.parsers.base import MIME, detect_kind, zip_kind
from doomich.models import Chunk, Document
from doomich.security.crypto import UserCipher
from doomich.storage.files import get_storage

ALLOWED = {"pdf", "docx", "xlsx", "pptx"}


class DocumentOut(BaseModel):
    id: uuid.UUID
    title: str
    kind: str
    scope: str
    size_bytes: int
    pages: int | None
    status: str
    error: str | None
    created_at: datetime


class ChunkOut(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    title: str
    page: int | None
    sheet: str | None
    section: str | None
    text: str
    prev_text: str | None = None
    next_text: str | None = None
    meta: dict = {}


def title_of(doc: Document, cipher: UserCipher | None) -> str:
    if doc.title_enc is not None and cipher is not None:
        return cipher.decrypt_str(doc.title_enc, f"doc-title:{doc.id}") or "документ"
    return doc.title or "документ"


def out(doc: Document, cipher: UserCipher | None) -> DocumentOut:
    return DocumentOut(id=doc.id, title=title_of(doc, cipher), kind=doc.kind, scope=doc.scope,
                       size_bytes=doc.size_bytes, pages=doc.pages, status=doc.status, error=doc.error,
                       created_at=doc.created_at)


def spool_upload(src: BinaryIO, limit_bytes: int) -> tuple[Path, int, bytes]:
    """Копирует загрузку во временный файл с проверкой размера. Возвращает путь, размер, первые байты."""
    fd, name = tempfile.mkstemp(prefix="dm-up-", dir=get_storage().tmp_dir())
    path = Path(name)
    size = 0
    head = b""
    with open(fd, "wb") as dst:
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            if not head:
                head = chunk[:16]
            size += len(chunk)
            if size > limit_bytes:
                dst.close()
                path.unlink(missing_ok=True)
                raise PayloadTooLarge(f"файл больше {limit_bytes // (1024 * 1024)} МБ", code="file_too_large")
            dst.write(chunk)
    return path, size, head


def resolve_kind(path: Path, head: bytes, filename: str) -> str:
    kind = detect_kind(head, filename)
    if kind == "zip" or (kind in ("docx", "xlsx", "pptx")):
        kind = zip_kind(path) or kind
    if kind not in ALLOWED:
        raise AppError("поддерживаются PDF, DOCX, XLSX и PPTX", code="unsupported_type", status_code=415)
    return kind


async def create_personal(
    s: AsyncSession, user: CurrentUser, *, src: BinaryIO, filename: str, scope: str = "personal",
) -> Document:
    st = settings()
    count = await s.scalar(select(func.count()).select_from(Document).where(Document.user_id == user.id,
                                                                            Document.scope == "personal"))
    if scope == "personal" and (count or 0) >= st.max_documents_per_user:
        raise AppError(f"можно хранить не больше {st.max_documents_per_user} документов", code="documents_limit")
    path, size, head = spool_upload(src, st.max_document_mb * 1024 * 1024)
    try:
        kind = resolve_kind(path, head, filename)
        cipher = await user_cipher_for(s, user.id)
        doc_id = uuid.uuid4()
        file_key, wrapped = cipher.file_key()
        key = f"{user.tenant_id}/{user.id}/{doc_id}.bin"
        with path.open("rb") as f:
            get_storage().put_encrypted(key, f, file_key, str(doc_id))
        title = Path(filename).name[:200] or f"документ.{kind}"
        doc = Document(
            id=doc_id, tenant_id=user.tenant_id, user_id=user.id, scope=scope,
            title_enc=cipher.encrypt(title, f"doc-title:{doc_id}"), mime=MIME[kind], kind=kind, size_bytes=size,
            status="uploaded", storage_key=key, file_key_wrapped=wrapped,
        )
        s.add(doc)
        await s.flush()
        await s.refresh(doc)
        return doc
    finally:
        path.unlink(missing_ok=True)


async def list_documents(s: AsyncSession, user: CurrentUser) -> list[Document]:
    rows = await s.scalars(
        select(Document).where(Document.user_id == user.id, Document.scope == "personal")
        .order_by(Document.created_at.desc())
    )
    return list(rows.all())


async def get_document(s: AsyncSession, doc_id: uuid.UUID) -> Document:
    doc = await s.get(Document, doc_id)
    if doc is None:
        raise NotFound("документ не найден", code="document_not_found")
    return doc


async def delete_document(s: AsyncSession, user: CurrentUser, doc_id: uuid.UUID) -> None:
    doc = await get_document(s, doc_id)
    if doc.user_id != user.id:
        raise NotFound("документ не найден", code="document_not_found")
    key = doc.storage_key
    await s.execute(delete(Document).where(Document.id == doc_id))
    if key:
        get_storage().delete(key)


async def chunk_view(s: AsyncSession, user: CurrentUser, doc_id: uuid.UUID, chunk_id: uuid.UUID) -> ChunkOut:
    doc = await get_document(s, doc_id)
    chunk = await s.get(Chunk, chunk_id)
    if chunk is None or chunk.document_id != doc.id:
        raise NotFound("фрагмент не найден", code="chunk_not_found")
    neighbours = {
        c.ord: c.body for c in (await s.scalars(
            select(Chunk).where(Chunk.document_id == doc.id, Chunk.ord.in_([chunk.ord - 1, chunk.ord + 1]))
        )).all()
    }
    cipher = await user_cipher_for(s, user.id) if doc.user_id == user.id else None
    return ChunkOut(chunk_id=chunk.id, document_id=doc.id, title=title_of(doc, cipher), page=chunk.page,
                    sheet=chunk.sheet, section=chunk.section, text=chunk.body,
                    prev_text=neighbours.get(chunk.ord - 1), next_text=neighbours.get(chunk.ord + 1),
                    meta=dict(chunk.meta or {}))


def copy_stream(src: BinaryIO, dst: BinaryIO) -> None:
    shutil.copyfileobj(src, dst, 1024 * 1024)
