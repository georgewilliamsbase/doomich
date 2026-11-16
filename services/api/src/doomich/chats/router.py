"""Чаты и сообщения. Ответ ассистента идёт потоком (Server-Sent Events).

События потока:
  meta     {chat_id, user_message_id, assistant_message_id}
  tool     {name, status}
  delta    {text}
  sources  {items: [...]}
  done     {message_id, model_version, finish_reason}
  error    {code, message}
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import insert, select

from doomich import bindings
from doomich.ai.registry import get_ai
from doomich.chats import service
from doomich.chats.schemas import (
    ChatCreate,
    ChatOut,
    ChatPatch,
    FeedbackIn,
    IncognitoIn,
    MessageIn,
    MessageOut,
)
from doomich.common.errors import AppError, Conflict, NotFound
from doomich.common.timeutil import local_now
from doomich.config import settings
from doomich.db import get_db
from doomich.deps import CurrentUser, current_user, user_cipher_for
from doomich.models import Document, Feedback, Message, StudyGroup
from doomich.observability.metrics import FEEDBACK
from doomich.orchestrator.engine import HistoryItem, TurnResult, run_turn
from doomich.orchestrator.prompts import PROMPT_VERSION, detect_lang
from doomich.orchestrator.tools import ClientContext, ToolContext
from doomich.security import kv

router = APIRouter(prefix="/v1", tags=["chats"])
log = logging.getLogger(__name__)
_background: set[asyncio.Task[Any]] = set()


def sse(event: str, data: dict[str, Any]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n".encode()


async def check_rate(user: CurrentUser) -> None:
    st = settings()
    await kv.hit(f"msg:{user.id}", st.messages_per_minute, 60)
    await kv.hit(f"msg:{user.id}", st.messages_per_day, 86400)


async def _group_code(user: CurrentUser, group_id: uuid.UUID | None) -> str | None:
    if group_id is None:
        return None
    async with get_db().tenant_session(user.tenant_id) as s:
        return await s.scalar(select(StudyGroup.code).where(StudyGroup.id == group_id))


async def make_context(user: CurrentUser, body: MessageIn, *, document_ids: list[uuid.UUID],
                       lecture_id: uuid.UUID | None = None, course_id: uuid.UUID | None = None) -> ToolContext:
    c = body.context
    client = ClientContext(group_id=c.group_id, subgroup=c.subgroup, teacher_key=c.teacher_key,
                           campus_id=c.campus_id, location_node_id=c.location_node_id)
    ctx = ToolContext(user=user, client=client, now=local_now(user.tenant.timezone), lang=detect_lang(body.text),
                      document_ids=document_ids, lecture_id=lecture_id, course_id=course_id)
    ctx.group_code = await _group_code(user, ctx.group_id)
    return ctx


async def model_version_for(user: CurrentUser) -> tuple[str, str]:
    base = get_ai().llm_model
    model = await bindings.llm_model_for(user.tenant_id, user.id, base)
    return model, f"{model}+{PROMPT_VERSION}"


def stream_turn(
    ctx: ToolContext,
    *,
    question: str,
    history: list[HistoryItem],
    mode: str,
    model: str,
    model_version: str,
    meta: dict[str, Any],
    persist: Callable[[TurnResult], Awaitable[None]] | None,
) -> StreamingResponse:
    tenant_prompt = ctx.user.tenant.settings.get("assistant_prompt")

    async def gen() -> AsyncIterator[bytes]:
        result = TurnResult(model_version=model_version)
        saved = asyncio.Event()

        async def save() -> None:
            if saved.is_set() or persist is None:
                return
            saved.set()
            try:
                await persist(result)
            except Exception:
                log.exception("не удалось сохранить ответ")

        try:
            yield sse("meta", meta)
            async for ev in run_turn(ctx, question=question, history=history, mode=mode, model=model,
                                     tenant_prompt=tenant_prompt, result=result):
                yield sse(ev["type"], ev)
            await save()
            yield sse("sources", {"items": result.sources})
            yield sse("done", {"message_id": meta.get("assistant_message_id"), "model_version": model_version,
                               "finish_reason": result.finish_reason})
        except asyncio.CancelledError:
            # Клиент закрыл соединение: сохраняем то, что успели сгенерировать
            task = asyncio.ensure_future(save())
            _background.add(task)
            task.add_done_callback(_background.discard)
            raise
        except AppError as e:
            await save()
            yield sse("error", e.to_dict()["error"])
        except Exception:
            log.exception("ошибка генерации ответа")
            await save()
            yield sse("error", {"code": "internal", "message": "внутренняя ошибка"})

    return StreamingResponse(
        gen(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def persister(user: CurrentUser, chat_id: uuid.UUID, assistant_id: uuid.UUID,
              mode: str) -> Callable[[TurnResult], Awaitable[None]]:
    async def persist(result: TurnResult) -> None:
        if not result.text:
            return
        async with get_db().user_session(user.id, user.tenant_id) as s:
            cipher = await user_cipher_for(s, user.id)
            chat = await service.get_chat(s, chat_id)
            await service.add_message(s, cipher, chat=chat, user_id=user.id, role="assistant", content=result.text,
                                      mode=mode, sources=result.sources, model_version=result.model_version,
                                      msg_id=assistant_id)

    return persist


async def _docs_exist(user: CurrentUser, ids: list[uuid.UUID]) -> list[uuid.UUID]:
    if not ids:
        return []
    async with get_db().user_session(user.id, user.tenant_id) as s:
        found = (await s.scalars(select(Document.id).where(Document.id.in_(ids)))).all()
    missing = set(ids) - set(found)
    if missing:
        raise NotFound("документ не найден", code="document_not_found")
    return list(ids)


@router.get("/chats", response_model=list[ChatOut])
async def list_chats(user: CurrentUser = Depends(current_user), limit: int = Query(50, ge=1, le=200),
                     before: datetime | None = None) -> list[ChatOut]:
    async with get_db().user_session(user.id, user.tenant_id) as s:
        cipher = await user_cipher_for(s, user.id)
        chats = await service.list_chats(s, limit=limit, before=before)
        return [service.chat_out(c, cipher, user.history_days) for c in chats]


@router.post("/chats", response_model=ChatOut, status_code=201)
async def create_chat(body: ChatCreate, user: CurrentUser = Depends(current_user)) -> ChatOut:
    if user.history_days == 0:
        raise Conflict("история отключена, используйте режим инкогнито", code="history_disabled")
    await _docs_exist(user, body.document_ids)
    async with get_db().user_session(user.id, user.tenant_id) as s:
        cipher = await user_cipher_for(s, user.id)
        chat = await service.create_chat(s, cipher, user_id=user.id, tenant_id=user.tenant_id, title=body.title,
                                         document_ids=body.document_ids, lecture_id=body.lecture_id,
                                         course_id=body.course_id)
        return service.chat_out(chat, cipher, user.history_days)


@router.patch("/chats/{chat_id}", response_model=ChatOut)
async def rename_chat(chat_id: uuid.UUID, body: ChatPatch, user: CurrentUser = Depends(current_user)) -> ChatOut:
    async with get_db().user_session(user.id, user.tenant_id) as s:
        cipher = await user_cipher_for(s, user.id)
        chat = await service.get_chat(s, chat_id)
        await service.rename_chat(s, cipher, chat, body.title)
        return service.chat_out(chat, cipher, user.history_days)


@router.delete("/chats/{chat_id}", status_code=204)
async def delete_chat(chat_id: uuid.UUID, user: CurrentUser = Depends(current_user)) -> None:
    async with get_db().user_session(user.id, user.tenant_id) as s:
        await service.delete_chat(s, chat_id)


@router.post("/chats/incognito/messages", response_class=StreamingResponse)
async def incognito(body: IncognitoIn, user: CurrentUser = Depends(current_user)) -> StreamingResponse:
    """Инкогнито: на сервере ничего не сохраняется, историю присылает клиент."""
    await check_rate(user)
    doc_ids = await _docs_exist(user, body.document_ids or [])
    ctx = await make_context(user, body, document_ids=doc_ids)
    model, version = await model_version_for(user)
    hist = [HistoryItem(h.role, h.content) for h in body.history]
    return stream_turn(ctx, question=body.text, history=hist, mode=body.mode, model=model, model_version=version,
                       meta={"chat_id": None, "incognito": True}, persist=None)


@router.get("/chats/{chat_id}/messages", response_model=list[MessageOut])
async def get_messages(chat_id: uuid.UUID, user: CurrentUser = Depends(current_user),
                       limit: int = Query(50, ge=1, le=200), before: datetime | None = None) -> list[MessageOut]:
    async with get_db().user_session(user.id, user.tenant_id) as s:
        cipher = await user_cipher_for(s, user.id)
        await service.get_chat(s, chat_id)
        msgs = await service.list_messages(s, chat_id, limit=limit, before=before)
        return [service.message_out(m, cipher) for m in msgs]


@router.post("/chats/{chat_id}/messages", response_class=StreamingResponse)
async def post_message(chat_id: uuid.UUID, body: MessageIn,
                       user: CurrentUser = Depends(current_user)) -> StreamingResponse:
    await check_rate(user)
    if body.document_ids:
        await _docs_exist(user, body.document_ids)
    async with get_db().user_session(user.id, user.tenant_id) as s:
        cipher = await user_cipher_for(s, user.id)
        chat = await service.get_chat(s, chat_id)
        hist = await service.history(s, cipher, chat.id)
        user_msg = await service.add_message(s, cipher, chat=chat, user_id=user.id, role="user",
                                             content=body.text, mode=body.mode)
        doc_ids = body.document_ids if body.document_ids is not None else list(chat.document_ids or [])
        lecture_id, course_id = chat.lecture_id, chat.course_id
    ctx = await make_context(user, body, document_ids=doc_ids, lecture_id=lecture_id, course_id=course_id)
    model, version = await model_version_for(user)
    assistant_id = uuid.uuid4()
    meta = {"chat_id": str(chat_id), "user_message_id": str(user_msg.id), "assistant_message_id": str(assistant_id)}
    return stream_turn(ctx, question=body.text, history=hist, mode=body.mode, model=model, model_version=version,
                       meta=meta, persist=persister(user, chat_id, assistant_id, body.mode))


@router.post("/chats/{chat_id}/retry", response_class=StreamingResponse)
async def retry(chat_id: uuid.UUID, user: CurrentUser = Depends(current_user)) -> StreamingResponse:
    await check_rate(user)
    async with get_db().user_session(user.id, user.tenant_id) as s:
        cipher = await user_cipher_for(s, user.id)
        chat = await service.get_chat(s, chat_id)
        last_user_id = await service.delete_last_assistant(s, chat.id)
        if last_user_id is None:
            raise AppError("нечего повторять", code="nothing_to_retry")
        msg = await s.get(Message, uuid.UUID(last_user_id))
        assert msg is not None
        question = cipher.decrypt_str(msg.content_enc, f"msg:{msg.id}") or ""
        hist = [h for h in await service.history(s, cipher, chat.id)][:-1]
        mode = msg.mode
        doc_ids = list(chat.document_ids or [])
        lecture_id, course_id = chat.lecture_id, chat.course_id
    body = MessageIn(text=question, mode=mode)
    ctx = await make_context(user, body, document_ids=doc_ids, lecture_id=lecture_id, course_id=course_id)
    model, version = await model_version_for(user)
    assistant_id = uuid.uuid4()
    meta = {"chat_id": str(chat_id), "user_message_id": last_user_id, "assistant_message_id": str(assistant_id)}
    return stream_turn(ctx, question=question, history=hist, mode=mode, model=model, model_version=version,
                       meta=meta, persist=persister(user, chat_id, assistant_id, mode))


@router.post("/feedback", status_code=204)
async def feedback(body: FeedbackIn, user: CurrentUser = Depends(current_user)) -> None:
    """Оценка без привязки к пользователю: сохраняется только вуз, дата и сама оценка."""
    await kv.hit(f"feedback:{user.id}", 60, 3600)
    model_version = body.model_version
    if body.message_id:
        async with get_db().user_session(user.id, user.tenant_id) as s:
            mv = await s.scalar(select(Message.model_version).where(Message.id == body.message_id))
            model_version = mv or model_version
    # Вставка без RETURNING: у роли приложения нет права читать таблицу оценок
    async with get_db().tenant_session(user.tenant_id) as s:
        await s.execute(insert(Feedback).values(
            id=uuid.uuid4(), tenant_id=user.tenant_id, rating=body.rating, comment=body.comment,
            category=body.category, model_version=model_version, mode=body.mode,
            question=body.question if body.share_content else None,
            answer=body.answer if body.share_content else None,
        ))
    FEEDBACK.labels(rating="up" if body.rating > 0 else "down").inc()
