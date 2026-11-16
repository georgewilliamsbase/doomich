"""Запросы к расписанию для API и инструментов ассистента."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from doomich.common.timeutil import day_bounds, tz
from doomich.db import get_db
from doomich.models import Lesson, Room, ScheduleSource, StudyGroup, Teacher, Tenant
from doomich.schedule import sync
from doomich.schedule.adapters.base import AdapterContext, get_adapter
from doomich.schedule.records import LessonRecord

KIND_RU = {"lecture": "лекция", "practice": "практика", "lab": "лабораторная", "exam": "экзамен",
           "credit": "зачёт", "consultation": "консультация", "other": "занятие"}


@dataclass
class LessonView:
    id: uuid.UUID
    group_id: uuid.UUID
    subgroup: str | None
    subject: str
    kind: str
    starts_at: datetime
    ends_at: datetime
    room: str | None
    room_id: uuid.UUID | None
    campus_room_id: uuid.UUID | None
    teacher: str | None
    teacher_key: str | None
    note: str | None
    status: str

    def brief(self, zone: str) -> dict[str, Any]:
        local = self.starts_at.astimezone(tz(zone))
        end = self.ends_at.astimezone(tz(zone))
        d: dict[str, Any] = {
            "date": local.date().isoformat(), "start": local.strftime("%H:%M"), "end": end.strftime("%H:%M"),
            "subject": self.subject, "kind": KIND_RU.get(self.kind, self.kind), "room": self.room,
        }
        if self.teacher:
            d["teacher"] = self.teacher
        if self.subgroup:
            d["subgroup"] = self.subgroup
        if self.status != "scheduled":
            d["status"] = "отменено" if self.status == "cancelled" else self.status
        if self.note:
            d["note"] = self.note[:200]
        return d


async def lessons(
    s: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    start: datetime,
    end: datetime,
    group_id: uuid.UUID | None = None,
    subgroup: str | None = None,
    teacher_key: str | None = None,
    subject_like: str | None = None,
    kinds: list[str] | None = None,
    limit: int = 500,
) -> list[LessonView]:
    stmt = (
        select(Lesson, Teacher.display_name, Teacher.key, Room.campus_room_id)
        .outerjoin(Teacher, Teacher.id == Lesson.teacher_id)
        .outerjoin(Room, Room.id == Lesson.room_id)
        .where(Lesson.tenant_id == tenant_id, Lesson.starts_at >= start, Lesson.starts_at < end)
        .order_by(Lesson.starts_at)
        .limit(limit)
    )
    if group_id is not None:
        stmt = stmt.where(Lesson.group_id == group_id)
        if subgroup:
            stmt = stmt.where(or_(Lesson.subgroup.is_(None), Lesson.subgroup == subgroup))
    if teacher_key is not None:
        stmt = stmt.where(Teacher.key == teacher_key)
    if subject_like:
        for word in subject_like.split()[:4]:
            stmt = stmt.where(Lesson.subject.ilike(f"%{word[:6]}%"))
    if kinds:
        stmt = stmt.where(Lesson.kind.in_(kinds))
    rows = (await s.execute(stmt)).all()
    return [
        LessonView(id=lesson.id, group_id=lesson.group_id, subgroup=lesson.subgroup, subject=lesson.subject,
                   kind=lesson.kind, starts_at=lesson.starts_at, ends_at=lesson.ends_at, room=lesson.room_text,
                   room_id=lesson.room_id, campus_room_id=campus_room_id, teacher=name, teacher_key=key,
                   note=lesson.note, status=lesson.status)
        for lesson, name, key, campus_room_id in rows
    ]


async def day_range(s: AsyncSession, tenant_id: uuid.UUID, zone: str, d_from: date, d_to: date,
                    **kw: Any) -> list[LessonView]:
    start, _ = day_bounds(d_from, zone)
    _, end = day_bounds(d_to, zone)
    return await lessons(s, tenant_id=tenant_id, start=start, end=end, **kw)


async def now_next(s: AsyncSession, tenant_id: uuid.UUID, now: datetime, **kw: Any) -> tuple[
        LessonView | None, LessonView | None]:
    items = await lessons(s, tenant_id=tenant_id, start=now - timedelta(hours=4), end=now + timedelta(days=14),
                          limit=200, **kw)
    items = [x for x in items if x.status != "cancelled"]
    current = next((x for x in items if x.starts_at <= now < x.ends_at), None)
    upcoming = next((x for x in items if x.starts_at > now), None)
    return current, upcoming


async def search_groups(s: AsyncSession, tenant_id: uuid.UUID, q: str | None, limit: int = 50) -> list[StudyGroup]:
    stmt = select(StudyGroup).where(StudyGroup.tenant_id == tenant_id, StudyGroup.is_active.is_(True))
    if q:
        stmt = stmt.where(or_(StudyGroup.code.ilike(f"%{q}%"), StudyGroup.name.ilike(f"%{q}%")))
    return list((await s.scalars(stmt.order_by(StudyGroup.code).limit(limit))).all())


async def run_source_sync(source_id: uuid.UUID, *, force: bool = False) -> dict[str, Any]:
    """Синхронизация одного источника (вызывается из Celery и из админки)."""
    from doomich.common.timeutil import utcnow
    from doomich.observability.metrics import SCHEDULE_SYNC

    async with get_db().sys_session() as s:
        source = await s.get(ScheduleSource, source_id, with_for_update=True)
        if source is None:
            raise ValueError("источник не найден")
        tenant = await s.get(Tenant, source.tenant_id)
        assert tenant is not None
        term = await sync.active_term(s, tenant.id)
        zone = tz(tenant.timezone)
        today = utcnow().astimezone(zone).date()
        window = (term.starts_on, term.ends_on) if term else (today - timedelta(days=7), today + timedelta(days=120))
        bells = [tuple(x) for x in (tenant.settings or {}).get("bell_schedule", [])] or None
        ctx = AdapterContext(tz=zone, term=term, window=window, bells=bells)
        source.last_sync_at = utcnow()
        try:
            records: list[LessonRecord]
            if force and source.pending_snapshot:
                records = [LessonRecord.from_json(x) for x in source.pending_snapshot]
            else:
                adapter = get_adapter(source.kind, dict(source.config or {}), ctx)
                records = await adapter.fetch()
            report = await sync.apply_records(s, tenant=tenant, source=source, records=records, force=force)
        except Exception as e:
            source.last_status = "error"
            source.last_error = f"{type(e).__name__}: {e}"[:1000]
            SCHEDULE_SYNC.labels(status="error").inc()
            return {"status": "error", "error": source.last_error}
        if report.needs_review:
            source.last_status = "needs_review"
            source.last_error = report.review_reason
            source.pending_snapshot = [r.to_json() for r in records][:20000]
            SCHEDULE_SYNC.labels(status="needs_review").inc()
        else:
            source.last_status = "ok"
            source.last_error = None
            source.last_count = len(records)
            source.pending_snapshot = None
            SCHEDULE_SYNC.labels(status="ok").inc()
        return {"status": source.last_status, **report.as_dict()}
