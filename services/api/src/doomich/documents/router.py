from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, UploadFile

from doomich.db import get_db
from doomich.deps import CurrentUser, current_user, user_cipher_for
from doomich.documents import service
from doomich.documents.service import ChunkOut, DocumentOut
from doomich.security import kv
from doomich.worker import dispatch

router = APIRouter(prefix="/v1", tags=["documents"])


@router.post("/documents", response_model=DocumentOut, status_code=201)
async def upload(file: UploadFile = File(...), user: CurrentUser = Depends(current_user)) -> DocumentOut:
    await kv.hit(f"upload:{user.id}", 30, 3600)
    async with get_db().user_session(user.id, user.tenant_id) as s:
        doc = await service.create_personal(s, user, src=file.file, filename=file.filename or "document")
        cipher = await user_cipher_for(s, user.id)
        result = service.out(doc, cipher)
    await dispatch.document_uploaded(doc.id)
    if result.status == "uploaded":
        async with get_db().user_session(user.id, user.tenant_id) as s:
            fresh = await service.get_document(s, doc.id)
            result = service.out(fresh, cipher)
    return result


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(user: CurrentUser = Depends(current_user)) -> list[DocumentOut]:
    async with get_db().user_session(user.id, user.tenant_id) as s:
        cipher = await user_cipher_for(s, user.id)
        return [service.out(d, cipher) for d in await service.list_documents(s, user)]


@router.get("/documents/{doc_id}", response_model=DocumentOut)
async def get_document(doc_id: uuid.UUID, user: CurrentUser = Depends(current_user)) -> DocumentOut:
    async with get_db().user_session(user.id, user.tenant_id) as s:
        doc = await service.get_document(s, doc_id)
        cipher = await user_cipher_for(s, user.id) if doc.user_id == user.id else None
        return service.out(doc, cipher)


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(doc_id: uuid.UUID, user: CurrentUser = Depends(current_user)) -> None:
    async with get_db().user_session(user.id, user.tenant_id) as s:
        await service.delete_document(s, user, doc_id)


@router.get("/documents/{doc_id}/chunks/{chunk_id}", response_model=ChunkOut)
async def chunk(doc_id: uuid.UUID, chunk_id: uuid.UUID, user: CurrentUser = Depends(current_user)) -> ChunkOut:
    async with get_db().user_session(user.id, user.tenant_id) as s:
        return await service.chunk_view(s, user, doc_id, chunk_id)
