"""Изоляция данных: чужие чаты, документы и фрагменты недоступны ни через API, ни напрямую из БД."""

from __future__ import annotations

import io
import uuid

from sqlalchemy import func, select, text

from tests.conftest import make_env, register
from tests.test_documents import make_docx


async def test_users_do_not_see_each_other(client, env):
    alice = await register(client, env.codes[0])
    bob = await register(client, env.codes[1])
    chat = (await client.post("/v1/chats", json={"title": "мой секретный чат"}, headers=alice["headers"])).json()
    files = {"file": ("конспект.docx", io.BytesIO(make_docx("Секретная формула Алисы: E = mc^2")),
                      "application/octet-stream")}
    doc = (await client.post("/v1/documents", files=files, headers=alice["headers"])).json()
    assert doc["status"] == "ready", doc

    assert (await client.get(f"/v1/chats/{chat['id']}/messages", headers=bob["headers"])).status_code == 404
    assert (await client.get(f"/v1/documents/{doc['id']}", headers=bob["headers"])).status_code == 404
    assert (await client.request("DELETE", f"/v1/chats/{chat['id']}", headers=bob["headers"])).status_code == 404
    assert (await client.get("/v1/chats", headers=bob["headers"])).json() == []

    # Прямой запрос под ролью приложения с контекстом Боба
    from doomich.db import get_db

    bob_id = uuid.UUID(bob["user"]["id"])
    async with get_db().user_session(bob_id, env.tenant_id) as s:
        assert await s.scalar(text("select count(*) from chats")) == 0
        assert await s.scalar(text("select count(*) from documents")) == 0
        assert await s.scalar(text("select count(*) from chunks")) == 0
        assert await s.scalar(text("select count(*) from messages")) == 0
    # Без контекста пользователя роль приложения не видит ничего личного
    async with get_db().tenant_session(env.tenant_id) as s:
        assert await s.scalar(text("select count(*) from chunks")) == 0
        assert await s.scalar(text("select count(*) from users")) == 0


async def test_app_role_cannot_read_secrets(client, env):
    import pytest
    from sqlalchemy.exc import DBAPIError

    alice = await register(client, env.codes[0])
    from doomich.db import get_db

    with pytest.raises(DBAPIError):
        async with get_db().user_session(uuid.UUID(alice["user"]["id"]), env.tenant_id) as s:
            await s.execute(text("select password_hash from users"))
    with pytest.raises(DBAPIError):
        async with get_db().user_session(uuid.UUID(alice["user"]["id"]), env.tenant_id) as s:
            await s.execute(text("update users set role = 'teacher'"))
    with pytest.raises(DBAPIError):
        async with get_db().user_session(uuid.UUID(alice["user"]["id"]), env.tenant_id) as s:
            await s.execute(text("select count(*) from sessions"))


async def test_tenants_are_isolated(client, env):
    from doomich.db import get_db
    from doomich.models import StudyGroup

    other = await make_env()
    student = await register(client, env.codes[0])
    groups = (await client.get("/v1/groups", headers=student["headers"])).json()
    assert {g["id"] for g in groups} == {str(env.group_id)}
    # Группа другого вуза не подставляется
    r = await client.patch("/v1/me", json={"group_id": str(other.group_id)}, headers=student["headers"])
    assert r.status_code == 404
    async with get_db().tenant_session(env.tenant_id) as s:
        assert await s.scalar(select(func.count()).select_from(StudyGroup)) == 1
