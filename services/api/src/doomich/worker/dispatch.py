"""Постановка фоновых задач.

В тестах и на ноутбуке без Celery (DOOMICH_CELERY_EAGER=true) задача выполняется
сразу в текущем цикле событий, иначе уходит в очередь Valkey.
"""

from __future__ import annotations

import uuid

from doomich.config import settings


async def document_uploaded(doc_id: uuid.UUID) -> None:
    if settings().celery_eager:
        from doomich.documents.pipeline import process_document

        await process_document(doc_id)
        return
    from doomich.worker.tasks import process_document_task

    process_document_task.delay(str(doc_id))


async def schedule_sync(source_id: uuid.UUID, force: bool = False) -> dict | None:
    if settings().celery_eager:
        from doomich.schedule.service import run_source_sync

        return await run_source_sync(source_id, force=force)
    from doomich.worker.tasks import sync_schedule_source_task

    sync_schedule_source_task.delay(str(source_id), force)
    return None


async def lecture_uploaded(lecture_id: uuid.UUID) -> None:
    if settings().celery_eager:
        from doomich.lectures.pipeline import process_lecture

        await process_lecture(lecture_id)
        return
    from doomich.worker.tasks import process_lecture_task

    process_lecture_task.delay(str(lecture_id))


async def generic(task_name: str, *args: str) -> None:
    """Любая задача по имени (например, обработка эталонного фото кампуса)."""
    if settings().celery_eager:
        from doomich.worker import tasks

        fn = getattr(tasks, f"_{task_name}")
        await fn(*args)
        return
    from doomich.worker.app import celery_app

    celery_app.send_task(f"doomich.{task_name}", args=list(args))
