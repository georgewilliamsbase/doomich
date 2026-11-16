from __future__ import annotations

import io
from datetime import date, datetime, timedelta

from sqlalchemy import select

from doomich.common.timeutil import tz
from doomich.schedule.importers import parse_ics, parse_rows, read_csv
from doomich.schedule.records import LessonRecord, Term, expand_weekly, parse_weeks
from tests.conftest import register

ZONE = tz("Europe/Moscow")


def test_week_parity_expansion():
    term = Term(starts_on=date(2027, 2, 8), ends_on=date(2027, 3, 7), first_week_odd=True,
                holidays={date(2027, 2, 23)})
    odd_mondays = expand_weekly(term, 0, parse_weeks("нечёт"), None, None)
    assert odd_mondays == [date(2027, 2, 8), date(2027, 2, 22)]
    even_tuesdays = expand_weekly(term, 1, parse_weeks("чёт"), None, None)
    assert even_tuesdays == [date(2027, 2, 16), date(2027, 3, 2)]
    all_tue = expand_weekly(term, 1, parse_weeks("все"), None, None)
    assert date(2027, 2, 23) not in all_tue  # праздник
    assert expand_weekly(term, 2, parse_weeks("1,3"), None, None) == [date(2027, 2, 10), date(2027, 2, 24)]


def test_template_rows_and_errors():
    term = Term(starts_on=date(2027, 2, 8), ends_on=date(2027, 2, 21))
    rows = [
        ["Группа", "Подгруппа", "День недели", "Неделя", "Дата", "Начало", "Конец", "Дисциплина", "Тип", "Аудитория"],
        ["ИВТ-21", "", "пн", "все", "", "08:30", "10:00", "Матанализ", "лекция", "305"],
        ["ИВТ-21", "1", "", "", "20.02.2027", "10:10", "11:40", "Физика", "лаб", "112"],
        ["ИВТ-21", "", "пн", "", "", "25:00", "26:00", "Ошибка", "", ""],
        ["", "", "вт", "", "", "08:30", "10:00", "Без группы", "", ""],
    ]
    res = parse_rows(rows, tz=ZONE, term=term)
    assert res.rows_total == 4 and res.rows_ok == 2
    assert len(res.records) == 3  # два понедельника и одна разовая пара
    assert {e.row for e in res.errors} == {4, 5}
    assert res.errors[0].column == "start"
    lab = next(r for r in res.records if r.subject == "Физика")
    assert lab.kind == "lab" and lab.subgroup == "1" and lab.starts_at.hour == 10


def test_csv_cp1251_semicolon():
    text = "Группа;Дата;Начало;Конец;Дисциплина\nИВТ-21;01.03.2027;9:00;10:30;История\n"
    rows = read_csv(text.encode("cp1251"))
    res = parse_rows(rows, tz=ZONE, term=None)
    assert res.records[0].subject == "История"


def test_ics_rrule_and_exdate():
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nUID:1\nSUMMARY:Лекция: Алгебра\nLOCATION:201\n"
        "DTSTART;TZID=Europe/Moscow:20270208T083000\nDTEND;TZID=Europe/Moscow:20270208T100000\n"
        "RRULE:FREQ=WEEKLY;COUNT=4\nEXDATE;TZID=Europe/Moscow:20270215T083000\nEND:VEVENT\nEND:VCALENDAR\n"
    ).encode()
    res = parse_ics(ics, group="ИВТ-21", tz=ZONE, window=(date(2027, 2, 1), date(2027, 6, 30)))
    assert [r.starts_at.date() for r in res.records] == [date(2027, 2, 8), date(2027, 2, 22), date(2027, 3, 1)]
    assert res.records[0].kind == "lecture" and res.records[0].subject == "Алгебра"


def _rec(day: date, hour: int, subject: str, room: str = "305") -> LessonRecord:
    return LessonRecord(group="ИВТ-21", subject=subject, room=room,
                        starts_at=datetime(day.year, day.month, day.day, hour, 0, tzinfo=ZONE),
                        ends_at=datetime(day.year, day.month, day.day, hour + 1, 30, tzinfo=ZONE))


async def test_sync_diff_and_changes(env):
    from doomich.db import get_db
    from doomich.models import Lesson, ScheduleChange, ScheduleSource, Tenant
    from doomich.schedule.sync import apply_records

    d1 = date.today() + timedelta(days=2)
    d2 = date.today() + timedelta(days=3)
    async with get_db().sys_session() as s:
        tenant = await s.get(Tenant, env.tenant_id)
        src = ScheduleSource(tenant_id=env.tenant_id, name="тест", kind="json_api", config={})
        s.add(src)
        await s.flush()
        first = [_rec(d1, 9, "Алгебра"), _rec(d1, 11, "Физика"), _rec(d2, 9, "История")]
        rep = await apply_records(s, tenant=tenant, source=src, records=first)
        assert rep.added == 3 and rep.changes_logged == 0

        second = [_rec(d1, 9, "Алгебра", room="404"), _rec(d2, 13, "Физика"), _rec(d2, 9, "История")]
        rep = await apply_records(s, tenant=tenant, source=src, records=second)
        assert rep.modified == 1 and rep.added == 1 and rep.removed == 1
        changes = (await s.scalars(select(ScheduleChange).where(ScheduleChange.tenant_id == env.tenant_id))).all()
        kinds = sorted(c.change for c in changes)
        assert kinds == ["moved", "room_changed"]
        room_change = next(c for c in changes if c.change == "room_changed")
        assert room_change.before["room"] == "305" and room_change.after["room"] == "404"
        count = len((await s.scalars(select(Lesson).where(Lesson.source_id == src.id))).all())
        assert count == 3


async def test_spike_requires_review(env):
    from doomich.db import get_db
    from doomich.models import ScheduleSource, Tenant
    from doomich.schedule.sync import apply_records

    base = date.today() + timedelta(days=1)
    async with get_db().sys_session() as s:
        tenant = await s.get(Tenant, env.tenant_id)
        src = ScheduleSource(tenant_id=env.tenant_id, name="сайт", kind="html_table", config={})
        s.add(src)
        await s.flush()
        many = [_rec(base + timedelta(days=i // 3), 8 + 2 * (i % 3), f"Предмет {i}") for i in range(30)]
        await apply_records(s, tenant=tenant, source=src, records=many)
        rep = await apply_records(s, tenant=tenant, source=src, records=many[:5])
        assert rep.needs_review and "раза" in rep.review_reason


async def test_schedule_api(client, env):
    from doomich.db import get_db
    from doomich.models import Tenant
    from doomich.schedule.sync import apply_records, manual_source

    today = date.today()
    async with get_db().sys_session() as s:
        tenant = await s.get(Tenant, env.tenant_id)
        src = await manual_source(s, env.tenant_id)
        rec = _rec(today + timedelta(days=1), 9, "Алгебра")
        rec.teacher = "Иванова Мария Петровна"
        await apply_records(s, tenant=tenant, source=src, records=[rec, _rec(today + timedelta(days=1), 12, "Химия")],
                            force=True)
    user = await register(client, env.codes[0])
    h = user["headers"]
    r = await client.get("/v1/schedule", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["group"]["code"] == "ИВТ-21" and len(body["lessons"]) == 2
    assert body["lessons"][0]["teacher"] == "Иванова Мария Петровна"
    assert r.headers["etag"].strip('"') == body["version"]
    assert body["utc_offset_minutes"] == 180
    nn = (await client.get("/v1/schedule/now", headers=h)).json()
    assert nn["next"]["subject"] == "Алгебра"
    teachers = (await client.get("/v1/teachers", params={"q": "иванов"}, headers=h)).json()
    assert teachers[0]["name"].startswith("Иванова")
    r = await client.get("/v1/schedule", params={"teacher_key": teachers[0]["key"]}, headers=h)
    assert [x["subject"] for x in r.json()["lessons"]] == ["Алгебра"]


async def test_teacher_names_hidden_mode(client):
    from doomich.db import get_db
    from doomich.models import Teacher, Tenant
    from doomich.schedule.sync import apply_records, manual_source, teacher_key
    from tests.conftest import make_env

    env = await make_env(settings={"teacher_names_mode": "hide"})
    async with get_db().sys_session() as s:
        tenant = await s.get(Tenant, env.tenant_id)
        src = await manual_source(s, env.tenant_id)
        rec = _rec(date.today() + timedelta(days=1), 9, "Алгебра")
        rec.teacher = "Сидоров П. П."
        await apply_records(s, tenant=tenant, source=src, records=[rec], force=True)
        t = (await s.scalars(select(Teacher).where(Teacher.tenant_id == env.tenant_id))).one()
        assert t.display_name is None
        assert t.key == teacher_key(env.slug, "сидоров п п")
    user = await register(client, env.codes[0])
    lessons = (await client.get("/v1/schedule", headers=user["headers"])).json()["lessons"]
    assert lessons[0]["teacher"] is None
    # Преподаватель вычисляет ключ на устройстве из своего имени и видит своё расписание
    r = await client.get("/v1/schedule", params={"teacher_key": teacher_key(env.slug, "Сидоров П.П.")},
                         headers=user["headers"])
    assert len(r.json()["lessons"]) == 1


async def test_admin_style_xlsx_import(env):
    from openpyxl import Workbook

    from doomich.schedule.importers import parse_template

    wb = Workbook()
    ws = wb.active
    ws.append(["Группа", "День недели", "Неделя", "Начало", "Конец", "Дисциплина", "Аудитория"])
    ws.append(["ИВТ-21", "пт", "все", "13:00", "14:30", "Английский", "101"])
    buf = io.BytesIO()
    wb.save(buf)
    term = Term(starts_on=date(2027, 2, 8), ends_on=date(2027, 2, 28))
    res = parse_template(buf.getvalue(), "s.xlsx", tz=ZONE, term=term)
    assert len(res.records) == 3 and not res.errors
