"""Общие фикстуры. Нужен PostgreSQL с расширением vector.

Адрес суперпользователя: DOOMICH_TEST_PG (по умолчанию локальный сокет /tmp, порт 5433).
Тесты создают отдельную БД на прогон и роли doomich_app/doomich_sys, если их нет.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from collections.abc import AsyncIterator
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import asyncpg
import httpx
import pytest

PG_ADMIN = os.environ.get("DOOMICH_TEST_PG", "postgresql://postgres@/postgres?host=/tmp&port=5433")
DB_NAME = f"doomich_test_{uuid.uuid4().hex[:8]}"


def _dsn(user: str, password: str, db: str) -> str:
    u = urlparse(PG_ADMIN)
    query = f"?{u.query}" if u.query else ""
    host = u.hostname or ""
    port = f":{u.port}" if u.port else ""
    return f"postgresql+asyncpg://{user}:{password}@{host}{port}/{db}{query}"


async def _prepare_db() -> None:
    conn = await asyncpg.connect(PG_ADMIN)
    try:
        for role, bypass in (("doomich_sys", "BYPASSRLS"), ("doomich_app", "NOBYPASSRLS")):
            exists = await conn.fetchval("SELECT 1 FROM pg_roles WHERE rolname = $1", role)
            if not exists:
                await conn.execute(f"CREATE ROLE {role} LOGIN {bypass} PASSWORD 'doomich'")
        await conn.execute(f'CREATE DATABASE "{DB_NAME}" OWNER doomich_sys')
    finally:
        await conn.close()
    conn = await asyncpg.connect(urlparse(PG_ADMIN)._replace(path=f"/{DB_NAME}").geturl())
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    finally:
        await conn.close()


async def _drop_db() -> None:
    conn = await asyncpg.connect(PG_ADMIN)
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{DB_NAME}" WITH (FORCE)')
    finally:
        await conn.close()


def _settings(tmp: Path, **over: Any):  # type: ignore[no-untyped-def]
    from doomich.config import Settings

    base = dict(
        env="test",
        database_url=_dsn("doomich_app", "doomich", DB_NAME),
        database_sys_url=_dsn("doomich_sys", "doomich", DB_NAME),
        db_null_pool=True,
        redis_url="memory://",
        celery_eager=True,
        argon2_time_cost=1,
        argon2_memory_kib=1024,
        argon2_parallelism=1,
        data_dir=tmp,
        llm_backend="mock",
        embed_backend="mock",
        rerank_backend="mock",
        asr_backend="mock",
        tts_backend="mock",
        nav_backend="mock",
        parser_backend="basic",
    )
    base.update(over)
    return Settings(**base)


@pytest.fixture(scope="session")
def data_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("data")


@pytest.fixture(scope="session", autouse=True)
def database(data_root: Path) -> Any:
    from doomich.config import override_settings

    asyncio.run(_prepare_db())
    st = _settings(data_root)
    override_settings(st)
    from alembic import command
    from alembic.config import Config

    root = Path(__file__).resolve().parents[1]
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    cfg.attributes["url"] = st.database_sys_url
    command.upgrade(cfg, "head")
    yield st
    asyncio.run(_drop_db())


@pytest.fixture(autouse=True)
def fresh_state(database: Any) -> Any:
    """Новые KV, ИИ-заглушки и кэши на каждый тест."""
    from doomich import bindings, deps
    from doomich.ai.registry import set_ai
    from doomich.config import override_settings
    from doomich.db import init_db
    from doomich.security.kv import MemoryKV, set_kv

    override_settings(database)
    init_db(database)
    set_kv(MemoryKV())
    set_ai(None)
    bindings.invalidate()
    deps._tenant_cache.clear()
    deps._key_cache.clear()
    yield


@pytest.fixture
def app(fresh_state: Any):  # type: ignore[no-untyped-def]
    from doomich.main import create_app

    return create_app()


@pytest.fixture
async def client(app: Any) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class Env:
    """Вуз с группой, семестром и кодами приглашения."""

    def __init__(self, tenant_id: uuid.UUID, slug: str, group_id: uuid.UUID, codes: list[str],
                 teacher_codes: list[str]) -> None:
        self.tenant_id = tenant_id
        self.slug = slug
        self.group_id = group_id
        self.codes = codes
        self.teacher_codes = teacher_codes


async def make_env(*, settings: dict[str, Any] | None = None, codes: int = 5) -> Env:
    from doomich.accounts import invites
    from doomich.db import get_db
    from doomich.models import AcademicTerm, StudyGroup, Tenant

    slug = f"t-{uuid.uuid4().hex[:8]}"
    async with get_db().sys_session() as s:
        tenant = Tenant(id=uuid.uuid4(), slug=slug, name=f"Тестовый вуз {slug}", timezone="Europe/Moscow",
                        settings=settings or {"teacher_names_mode": "store"})
        s.add(tenant)
        await s.flush()
        group = StudyGroup(id=uuid.uuid4(), tenant_id=tenant.id, code="ИВТ-21", subgroups=["1", "2"])
        s.add(group)
        today = date.today()
        s.add(AcademicTerm(id=uuid.uuid4(), tenant_id=tenant.id, name="Тест",
                           starts_on=today - timedelta(days=today.weekday() + 7),
                           ends_on=today + timedelta(days=90)))
        await s.flush()
        _, cs = await invites.create_batch(s, tenant_id=tenant.id, label="тест", count=codes, group_id=group.id,
                                           max_uses=1)
        _, ts = await invites.create_batch(s, tenant_id=tenant.id, label="преп", count=1, role="teacher", max_uses=5)
    return Env(tenant.id, slug, group.id, cs, ts)


@pytest.fixture
async def env() -> Env:
    return await make_env()


async def register(client: httpx.AsyncClient, code: str, login: str | None = None,
                   password: str = "Kosmos-Galaktika-42") -> dict[str, Any]:
    login = login or f"Енот{uuid.uuid4().hex[:6]}"
    r = await client.post("/v1/auth/register", json={"invite_code": code, "login": login, "password": password,
                                                     "platform": "android"})
    assert r.status_code == 201, r.text
    data = r.json()
    data["login"] = login
    data["password"] = password
    data["headers"] = {"Authorization": f"Bearer {data['tokens']['access_token']}"}
    return data


def parse_sse(body: str) -> list[tuple[str, dict[str, Any]]]:
    events = []
    for block in body.strip().split("\n\n"):
        event, data = None, None
        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data = json.loads(line[5:].strip())
        if event:
            events.append((event, data or {}))
    return events
