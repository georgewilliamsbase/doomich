from __future__ import annotations

from datetime import date, datetime, timedelta

from doomich.common.timeutil import tz
from tests.conftest import parse_sse, register


async def _add_lessons(env, day: date) -> None:
    from doomich.db import get_db
    from doomich.models import Tenant
    from doomich.schedule.records import LessonRecord
    from doomich.schedule.sync import apply_records, manual_source

    zone = tz("Europe/Moscow")
    async with get_db().sys_session() as s:
        tenant = await s.get(Tenant, env.tenant_id)
        src = await manual_source(s, env.tenant_id)
        await apply_records(s, tenant=tenant, source=src, force=True, records=[
            LessonRecord(group="ИВТ-21", subject="Математический анализ", kind="lecture", room="305",
                         starts_at=datetime(day.year, day.month, day.day, 8, 30, tzinfo=zone),
                         ends_at=datetime(day.year, day.month, day.day, 10, 0, tzinfo=zone)),
            LessonRecord(group="ИВТ-21", subject="Физика", kind="lab", room="112", subgroup="1",
                         starts_at=datetime(day.year, day.month, day.day, 10, 10, tzinfo=zone),
                         ends_at=datetime(day.year, day.month, day.day, 11, 40, tzinfo=zone)),
        ])


async def test_chat_stream_and_history(client, env):
    user = await register(client, env.codes[0])
    h = user["headers"]
    r = await client.post("/v1/chats", json={}, headers=h)
    assert r.status_code == 201
    chat_id = r.json()["id"]

    r = await client.post(f"/v1/chats/{chat_id}/messages", json={"text": "Объясни производную простыми словами"},
                          headers=h)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(r.text)
    kinds = [e for e, _ in events]
    assert kinds[0] == "meta" and kinds[-1] == "done"
    text = "".join(d["text"] for e, d in events if e == "delta")
    assert "производную" in text

    r = await client.get(f"/v1/chats/{chat_id}/messages", headers=h)
    msgs = r.json()
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert msgs[1]["content"] == text.strip()
    assert msgs[1]["model_version"].startswith("mock-llm")

    chats = (await client.get("/v1/chats", headers=h)).json()
    assert chats[0]["title"].startswith("Объясни производную")

    # Сообщения в БД зашифрованы
    from doomich.db import get_db
    from doomich.models import Message

    async with get_db().sys_session() as s:
        row = await s.get(Message, msgs[0]["id"])
        assert "производную".encode() not in row.content_enc

    r = await client.post(f"/v1/chats/{chat_id}/retry", headers=h)
    assert parse_sse(r.text)[-1][0] == "done"
    assert len((await client.get(f"/v1/chats/{chat_id}/messages", headers=h)).json()) == 2


async def test_schedule_question_uses_tool(client, env):
    tomorrow = date.today() + timedelta(days=1)
    await _add_lessons(env, tomorrow)
    user = await register(client, env.codes[0])
    chat = (await client.post("/v1/chats", json={}, headers=user["headers"])).json()
    r = await client.post(f"/v1/chats/{chat['id']}/messages", json={"text": "Какие пары у меня завтра?"},
                          headers=user["headers"])
    events = parse_sse(r.text)
    tools = [d for e, d in events if e == "tool"]
    assert {"name": "get_schedule", "status": "done", "type": "tool"} in tools
    text = "".join(d["text"] for e, d in events if e == "delta")
    assert "Математический анализ" in text and "305" in text


async def test_next_lesson_with_device_group(client, env):
    await _add_lessons(env, date.today() + timedelta(days=1))
    teacher = await register(client, env.teacher_codes[0])  # у преподавателя нет группы на сервере
    r = await client.post("/v1/chats/incognito/messages",
                          json={"text": "Какая следующая пара?", "context": {"group_id": str(env.group_id)}},
                          headers=teacher["headers"])
    events = parse_sse(r.text)
    assert any(e == "tool" and d["name"] == "next_lesson" for e, d in events)
    text = "".join(d["text"] for e, d in events if e == "delta")
    assert "Математический анализ" in text
    # Инкогнито ничего не сохраняет
    assert (await client.get("/v1/chats", headers=teacher["headers"])).json() == []


async def test_history_disabled(client, env):
    user = await register(client, env.codes[0])
    await client.patch("/v1/me", json={"history_days": 0}, headers=user["headers"])
    r = await client.post("/v1/chats", json={}, headers=user["headers"])
    assert r.json()["error"]["code"] == "history_disabled"


async def test_feedback_is_anonymous(client, env):
    from sqlalchemy import select

    from doomich.db import get_db
    from doomich.models import Feedback

    user = await register(client, env.codes[0])
    r = await client.post("/v1/feedback", json={"rating": -1, "comment": "неверно", "share_content": False,
                                                "question": "секрет", "answer": "ответ"}, headers=user["headers"])
    assert r.status_code == 204
    async with get_db().sys_session() as s:
        fb = (await s.scalars(select(Feedback).where(Feedback.tenant_id == env.tenant_id))).all()
    assert len(fb) == 1 and fb[0].question is None and fb[0].comment == "неверно"
    assert not hasattr(fb[0], "user_id")


async def test_message_rate_limit(client, env, database):
    user = await register(client, env.codes[0])
    chat = (await client.post("/v1/chats", json={}, headers=user["headers"])).json()
    codes = []
    for _ in range(database.messages_per_minute + 1):
        r = await client.post(f"/v1/chats/{chat['id']}/messages", json={"text": "привет"}, headers=user["headers"])
        codes.append(r.status_code)
    assert codes[-1] == 429
