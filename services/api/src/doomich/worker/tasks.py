"""Фоновые задачи. Каждая задача запускает асинхронный код в своём цикле событий
и своём подключении к БД (без пула), чтобы не тащить соединения между циклами."""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any, TypeVar

from sqlalchemy import delete, select, text, update

from doomich.worker.app import celery_app

log = logging.getLogger(__name__)
T = TypeVar("T")


def run(fn: Callable[..., Awaitable[T]], *args: Any) -> T:
    from doomich.config import settings
    from doomich.db import close_db, init_db

    async def wrapper() -> T:
        s = settings().model_copy(update={"db_null_pool": True})
        init_db(s)
        try:
            return await fn(*args)
        finally:
            await close_db()

    return asyncio.run(wrapper())


# --- Документы --------------------------------------------------------------


async def _process_document(doc_id: str) -> str:
    from doomich.documents.pipeline import process_document

    return await process_document(uuid.UUID(doc_id))


@celery_app.task(name="doomich.process_document", bind=True, max_retries=3, default_retry_delay=60)
def process_document_task(self: Any, doc_id: str) -> str:
    return run(_process_document, doc_id)


async def _retry_stuck() -> int:
    """Документы, застрявшие в обработке дольше 30 минут (воркер упал), ставим заново."""
    from doomich.common.timeutil import utcnow
    from doomich.db import get_db
    from doomich.models import Document

    async with get_db().sys_session() as s:
        ids = (await s.scalars(
            select(Document.id).where(Document.status.in_(["uploaded", "scanning", "parsing", "indexing"]),
                                      Document.updated_at < utcnow() - timedelta(minutes=30))
        )).all()
        if ids:
            await s.execute(update(Document).where(Document.id.in_(ids)).values(status="uploaded",
                                                                                 updated_at=utcnow()))
    for doc_id in ids:
        process_document_task.delay(str(doc_id))
    return len(ids)


@celery_app.task(name="doomich.retry_stuck")
def retry_stuck_task() -> int:
    return run(_retry_stuck)


# --- Расписание -------------------------------------------------------------


async def _sync_source(source_id: str, force: bool = False) -> dict[str, Any]:
    from doomich.schedule.service import run_source_sync

    return await run_source_sync(uuid.UUID(source_id), force=force)


@celery_app.task(name="doomich.sync_schedule_source")
def sync_schedule_source_task(source_id: str, force: bool = False) -> dict[str, Any]:
    return run(_sync_source, source_id, force)


async def _sync_all() -> int:
    from doomich.db import get_db
    from doomich.models import ScheduleSource

    async with get_db().sys_session() as s:
        ids = (await s.scalars(
            select(ScheduleSource.id).where(ScheduleSource.enabled.is_(True), ScheduleSource.kind != "manual")
        )).all()
    for sid in ids:
        sync_schedule_source_task.delay(str(sid))
    return len(ids)


@celery_app.task(name="doomich.sync_all_schedules")
def sync_all_task() -> int:
    return run(_sync_all)


# --- Очистка ----------------------------------------------------------------


async def _purge_history() -> int:
    from doomich.chats.service import purge_expired
    from doomich.db import get_db

    async with get_db().sys_session() as s:
        return await purge_expired(s)


@celery_app.task(name="doomich.purge_history")
def purge_history_task() -> int:
    return run(_purge_history)


async def _purge_inactive() -> int:
    """Документы аккаунтов без активности 12 месяцев удаляются (в приложении заранее предупреждаем)."""
    from doomich.db import get_db
    from doomich.models import Document, User
    from doomich.storage.files import get_storage

    async with get_db().sys_session() as s:
        rows = (await s.execute(
            select(Document.id, Document.storage_key).join(User, User.id == Document.user_id)
            .where(User.last_active_on < text("current_date - interval '365 days'"))
        )).all()
        if rows:
            await s.execute(delete(Document).where(Document.id.in_([r.id for r in rows])))
    storage = get_storage()
    for r in rows:
        if r.storage_key:
            storage.delete(r.storage_key)
    return len(rows)


@celery_app.task(name="doomich.purge_inactive")
def purge_inactive_task() -> int:
    return run(_purge_inactive)


async def _purge_sessions() -> int:
    from doomich.db import get_db

    async with get_db().sys_session() as s:
        res = await s.execute(text(
            "DELETE FROM sessions WHERE expires_at < now() - interval '1 day' "
            "OR revoked_at < now() - interval '30 days'"
        ))
        return int(res.rowcount or 0)  # type: ignore[attr-defined]


@celery_app.task(name="doomich.purge_sessions")
def purge_sessions_task() -> int:
    return run(_purge_sessions)


# --- Лекции (R1.1) и кампус (R2) подключаются ниже ---------------------------


async def _process_lecture(lecture_id: str) -> str:
    from doomich.lectures.pipeline import process_lecture

    return await process_lecture(uuid.UUID(lecture_id))


@celery_app.task(name="doomich.process_lecture", bind=True, max_retries=2, default_retry_delay=120)
def process_lecture_task(self: Any, lecture_id: str) -> str:
    return run(_process_lecture, lecture_id)


async def _process_ref_photo(photo_id: str) -> str:
    from doomich.campus.photos import process_ref_photo

    return await process_ref_photo(uuid.UUID(photo_id))


@celery_app.task(name="doomich.process_ref_photo")
def process_ref_photo_task(photo_id: str) -> str:
    return run(_process_ref_photo, photo_id)
