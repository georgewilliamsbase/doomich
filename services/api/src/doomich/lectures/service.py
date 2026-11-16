"""Лекции (R1.1). Здесь пока только то, что нужно чату с лекцией."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession


async def lecture_document_id(s: AsyncSession, lecture_id: uuid.UUID) -> uuid.UUID | None:
    """Документ с расшифровкой лекции (scope=lecture). Таблица лекций появится в R1.1."""
    return None
