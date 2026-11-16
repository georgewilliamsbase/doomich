"""Хранение чатов. Сообщения и названия шифруются ключом пользователя."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from doomich.chats.schemas import ChatOut, MessageOut, Source
from doomich.common.errors import NotFound
from doomich.models import Chat, Message
from doomich.orchestrator.engine import HistoryItem
from doomich.security.crypto import UserCipher

TITLE_LEN = 60


def title_from_text(text: str) -> str:
    line = " ".join(text.strip().split())
    return line if len(line) <= TITLE_LEN else line[: TITLE_LEN - 3].rstrip() + "..."


def chat_out(chat: Chat, cipher: UserCipher, history_days: int) -> ChatOut:
    expires = chat.updated_at + timedelta(days=history_days) if history_days else None
    return ChatOut(
        id=chat.id, title=cipher.decrypt_str(chat.title_enc, f"chat-title:{chat.id}"),
        document_ids=list(chat.document_ids or []), lecture_id=chat.lecture_id, course_id=chat.course_id,
        created_at=chat.created_at, updated_at=chat.updated_at, expires_at=expires,
    )


async def create_chat(s: AsyncSession, cipher: UserCipher, *, user_id: uuid.UUID, tenant_id: uuid.UUID,
                      title: str | None, document_ids: list[uuid.UUID], lecture_id: uuid.UUID | None = None,
                      course_id: uuid.UUID | None = None) -> Chat:
    chat_id = uuid.uuid4()
    chat = Chat(
        id=chat_id, user_id=user_id, tenant_id=tenant_id, document_ids=document_ids, lecture_id=lecture_id,
        course_id=course_id,
        title_enc=cipher.encrypt(title, f"chat-title:{chat_id}") if title else None,
    )
    s.add(chat)
    await s.flush()
    await s.refresh(chat)
    return chat


async def get_chat(s: AsyncSession, chat_id: uuid.UUID) -> Chat:
    chat = await s.get(Chat, chat_id)
    if chat is None:  # RLS прячет чужие чаты, поэтому "нет" и "чужой" выглядят одинаково
        raise NotFound("чат не найден", code="chat_not_found")
    return chat


async def list_chats(s: AsyncSession, *, limit: int = 50, before: datetime | None = None) -> list[Chat]:
    stmt = select(Chat).order_by(Chat.updated_at.desc()).limit(limit)
    if before:
        stmt = stmt.where(Chat.updated_at < before)
    return list((await s.scalars(stmt)).all())


async def rename_chat(s: AsyncSession, cipher: UserCipher, chat: Chat, title: str) -> Chat:
    chat.title_enc = cipher.encrypt(title, f"chat-title:{chat.id}")
    await s.flush()
    return chat


async def delete_chat(s: AsyncSession, chat_id: uuid.UUID) -> None:
    res = await s.execute(delete(Chat).where(Chat.id == chat_id))
    if res.rowcount == 0:  # type: ignore[attr-defined]
        raise NotFound("чат не найден", code="chat_not_found")


async def add_message(s: AsyncSession, cipher: UserCipher, *, chat: Chat, user_id: uuid.UUID, role: str,
                      content: str, mode: str, sources: list[dict[str, Any]] | None = None,
                      model_version: str | None = None, msg_id: uuid.UUID | None = None) -> Message:
    msg_id = msg_id or uuid.uuid4()
    msg = Message(
        id=msg_id, chat_id=chat.id, user_id=user_id, role=role,
        content_enc=cipher.encrypt(content, f"msg:{msg_id}"),
        sources_enc=cipher.encrypt(json.dumps(sources, ensure_ascii=False), f"msg-src:{msg_id}") if sources else None,
        mode=mode, model_version=model_version,
    )
    s.add(msg)
    values: dict[str, Any] = {"updated_at": func.now()}
    if chat.title_enc is None and role == "user":
        values["title_enc"] = cipher.encrypt(title_from_text(content), f"chat-title:{chat.id}")
    await s.execute(update(Chat).where(Chat.id == chat.id).values(**values))
    await s.flush()
    await s.refresh(msg)
    return msg


def message_out(msg: Message, cipher: UserCipher) -> MessageOut:
    sources: list[Source] = []
    if msg.sources_enc:
        raw = cipher.decrypt_str(msg.sources_enc, f"msg-src:{msg.id}") or "[]"
        sources = [Source.model_validate(x) for x in json.loads(raw)]
    return MessageOut(
        id=msg.id, role=msg.role,
        content=cipher.decrypt_str(msg.content_enc, f"msg:{msg.id}") or "",
        mode=msg.mode, sources=sources, model_version=msg.model_version, created_at=msg.created_at,
    )


async def list_messages(s: AsyncSession, chat_id: uuid.UUID, *, limit: int = 50,
                        before: datetime | None = None) -> list[Message]:
    stmt = select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.desc()).limit(limit)
    if before:
        stmt = stmt.where(Message.created_at < before)
    rows = list((await s.scalars(stmt)).all())
    rows.reverse()
    return rows


async def history(s: AsyncSession, cipher: UserCipher, chat_id: uuid.UUID, limit: int = 30) -> list[HistoryItem]:
    msgs = await list_messages(s, chat_id, limit=limit)
    return [HistoryItem(m.role, cipher.decrypt_str(m.content_enc, f"msg:{m.id}") or "") for m in msgs]


async def delete_last_assistant(s: AsyncSession, chat_id: uuid.UUID) -> str | None:
    """Для "повторить": убираем последний ответ и возвращаем вопрос перед ним."""
    msgs = await list_messages(s, chat_id, limit=2)
    if not msgs:
        return None
    if msgs[-1].role == "assistant":
        await s.execute(delete(Message).where(Message.id == msgs[-1].id))
        msgs = msgs[:-1]
    return str(msgs[-1].id) if msgs and msgs[-1].role == "user" else None


async def purge_expired(s: AsyncSession) -> int:
    """Удаляет сообщения старше срока хранения пользователя (под sys-ролью).

    history_days = 0 означает "не хранить": удаляется всё.
    """
    res = await s.execute(text(
        "DELETE FROM messages m USING users u "
        "WHERE m.user_id = u.id AND m.created_at < now() - make_interval(days => u.history_days)"
    ))
    await s.execute(text(
        "DELETE FROM chats c USING users u "
        "WHERE c.user_id = u.id AND c.updated_at < now() - make_interval(days => u.history_days) "
        "AND NOT EXISTS (SELECT 1 FROM messages m WHERE m.chat_id = c.id)"
    ))
    return int(res.rowcount or 0)  # type: ignore[attr-defined]
