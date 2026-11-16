"""Подключение к PostgreSQL.

Два движка:
- app: роль без BYPASSRLS. Каждая транзакция получает app.user_id и
  app.tenant_id, политики RLS режут всё чужое.
- sys: роль с BYPASSRLS для воркеров, админ-API, регистрации и входа.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Any

from sqlalchemy import MetaData, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from sqlalchemy.types import Date, DateTime

from doomich.config import Settings

NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)
    type_annotation_map = {  # noqa: RUF012
        uuid.UUID: UUID(as_uuid=True),
        dict[str, Any]: JSONB,
        datetime: DateTime(timezone=True),
        date: Date,
    }


def _engine(url: str, settings: Settings) -> AsyncEngine:
    kwargs: dict[str, Any] = {"pool_pre_ping": True}
    if settings.db_null_pool:
        kwargs["poolclass"] = NullPool
    else:
        kwargs["pool_size"] = settings.db_pool_size
        kwargs["max_overflow"] = settings.db_pool_size
    return create_async_engine(url, **kwargs)


class Database:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.app_engine = _engine(settings.database_url, settings)
        self.sys_engine = _engine(settings.database_sys_url, settings)
        self._app = async_sessionmaker(self.app_engine, expire_on_commit=False)
        self._sys = async_sessionmaker(self.sys_engine, expire_on_commit=False)

    async def dispose(self) -> None:
        await self.app_engine.dispose()
        await self.sys_engine.dispose()

    @asynccontextmanager
    async def user_session(
        self, user_id: uuid.UUID, tenant_id: uuid.UUID, course_ids: Sequence[uuid.UUID] = ()
    ) -> AsyncIterator[AsyncSession]:
        async with self._app() as session, session.begin():
            await set_context(session, user_id=user_id, tenant_id=tenant_id, course_ids=course_ids)
            yield session

    @asynccontextmanager
    async def tenant_session(self, tenant_id: uuid.UUID) -> AsyncIterator[AsyncSession]:
        """Сессия под ролью app только с контекстом вуза (без пользователя)."""
        async with self._app() as session, session.begin():
            await set_context(session, user_id=None, tenant_id=tenant_id)
            yield session

    @asynccontextmanager
    async def sys_session(self) -> AsyncIterator[AsyncSession]:
        async with self._sys() as session, session.begin():
            yield session


async def set_context(
    session: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    tenant_id: uuid.UUID | None,
    course_ids: Sequence[uuid.UUID] = (),
) -> None:
    await session.execute(
        text(
            "select set_config('app.user_id', :u, true),"
            " set_config('app.tenant_id', :t, true),"
            " set_config('app.course_ids', :c, true)"
        ),
        {
            "u": str(user_id) if user_id else "",
            "t": str(tenant_id) if tenant_id else "",
            "c": ",".join(str(c) for c in course_ids),
        },
    )


_db: dict[str, Database] = {}


def init_db(settings: Settings) -> Database:
    db = Database(settings)
    _db["default"] = db
    return db


def get_db() -> Database:
    if "default" not in _db:
        from doomich.config import settings

        return init_db(settings())
    return _db["default"]


async def close_db() -> None:
    db = _db.pop("default", None)
    if db is not None:
        await db.dispose()
