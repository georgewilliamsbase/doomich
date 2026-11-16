"""Применение расписания к БД: сравнение версий, журнал изменений, защита от сбоев источника.

Замена идёт в пределах источника и диапазона дат, который покрывают новые данные.
Прошлые занятия вне диапазона не трогаем. Изменения в будущих занятиях пишутся
в schedule_changes, по ним клиенты показывают уведомления (R1.1).
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from doomich.common.timeutil import today_utc, utcnow
from doomich.models import (
    AcademicTerm,
    Lesson,
    Room,
    ScheduleChange,
    ScheduleSource,
    StudyGroup,
    Teacher,
    Tenant,
)
from doomich.schedule.records import LessonRecord, Term, norm_group

SPIKE_LOW = 0.7
SPIKE_HIGH = 1.5
SPIKE_MIN_BASE = 20
COMPARE_FIELDS = ("subject", "kind", "room_text", "teacher_id", "ends_at", "status", "note")


@dataclass
class SyncReport:
    added: int = 0
    removed: int = 0
    modified: int = 0
    unchanged: int = 0
    groups_created: list[str] = field(default_factory=list)
    changes_logged: int = 0
    needs_review: bool = False
    review_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def teacher_key(tenant_slug: str, name: str) -> str:
    """Ключ преподавателя. Тот же ключ клиент считает на устройстве из имени,
    которое ввёл сам преподаватель, поэтому при режиме hide имена на сервере не нужны."""
    normalized = " ".join(name.lower().replace("ё", "е").replace(".", " ").split())
    return hashlib.sha256(f"{tenant_slug}:{normalized}".encode()).hexdigest()[:24]


async def active_term(s: AsyncSession, tenant_id: uuid.UUID, on: date | None = None) -> Term | None:
    on = on or today_utc()
    rows = (await s.scalars(
        select(AcademicTerm).where(AcademicTerm.tenant_id == tenant_id).order_by(AcademicTerm.starts_on)
    )).all()
    chosen = next((t for t in rows if t.starts_on <= on <= t.ends_on), None)
    if chosen is None:
        future = [t for t in rows if t.starts_on > on]
        chosen = future[0] if future else (rows[-1] if rows else None)
    if chosen is None:
        return None
    holidays = set()
    for h in chosen.holidays or []:
        try:
            holidays.add(date.fromisoformat(str(h)))
        except ValueError:
            continue
    return Term(starts_on=chosen.starts_on, ends_on=chosen.ends_on, first_week_odd=chosen.first_week_odd,
                holidays=holidays)


async def manual_source(s: AsyncSession, tenant_id: uuid.UUID) -> ScheduleSource:
    src = await s.scalar(
        select(ScheduleSource).where(ScheduleSource.tenant_id == tenant_id, ScheduleSource.kind == "manual")
    )
    if src is None:
        src = ScheduleSource(id=uuid.uuid4(), tenant_id=tenant_id, name="Ручной импорт", kind="manual",
                             config={}, enabled=False, require_review_on_spike=False)
        s.add(src)
        await s.flush()
    return src


def _lesson_snapshot(lesson: Lesson) -> dict[str, Any]:
    return {
        "subject": lesson.subject, "kind": lesson.kind, "starts_at": lesson.starts_at.isoformat(),
        "ends_at": lesson.ends_at.isoformat(), "room": lesson.room_text, "status": lesson.status,
        "subgroup": lesson.subgroup,
    }


async def apply_records(
    s: AsyncSession,
    *,
    tenant: Tenant,
    source: ScheduleSource,
    records: list[LessonRecord],
    force: bool = False,
    create_groups: bool = True,
) -> SyncReport:
    report = SyncReport()
    if not records:
        report.needs_review = True
        report.review_reason = "источник вернул пустое расписание"
        return report

    store_teachers = (tenant.settings or {}).get("teacher_names_mode", "hide")
    span_from = min(r.starts_at for r in records)
    span_to = max(r.starts_at for r in records) + timedelta(minutes=1)

    groups = {norm_group(g.code): g for g in (await s.scalars(
        select(StudyGroup).where(StudyGroup.tenant_id == tenant.id))).all()}
    for code in sorted({norm_group(r.group) for r in records}):
        if code not in groups:
            if not create_groups:
                continue
            g = StudyGroup(id=uuid.uuid4(), tenant_id=tenant.id, code=code, subgroups=[])
            s.add(g)
            groups[code] = g
            report.groups_created.append(code)
    await s.flush()

    existing = list((await s.scalars(
        select(Lesson).where(Lesson.tenant_id == tenant.id, Lesson.source_id == source.id,
                             Lesson.starts_at >= span_from, Lesson.starts_at < span_to)
    )).all())

    # База для сравнения объёма: последняя успешная синхронизация, иначе то, что уже лежит в диапазоне
    base = source.last_count if source.last_count else len(existing)
    if not force and source.require_review_on_spike and base >= SPIKE_MIN_BASE:
        ratio = len(records) / base
        if ratio < SPIKE_LOW or ratio > SPIKE_HIGH:
            report.needs_review = True
            report.review_reason = f"объём расписания изменился в {ratio:.2f} раза ({base} -> {len(records)})"
            return report

    rooms: dict[tuple[str, str], uuid.UUID] = {
        (r.building, r.number): r.id
        for r in (await s.scalars(select(Room).where(Room.tenant_id == tenant.id))).all()
    }
    teachers: dict[str, uuid.UUID] = {
        t.key: t.id for t in (await s.scalars(select(Teacher).where(Teacher.tenant_id == tenant.id))).all()
    }

    desired: dict[tuple[uuid.UUID, str], tuple[LessonRecord, dict[str, Any]]] = {}
    for rec in records:
        group = groups.get(norm_group(rec.group))
        if group is None:
            continue
        salt = ""
        key = (group.id, rec.ext_key())
        n = 1
        while key in desired:
            n += 1
            salt = f"#{n}"
            key = (group.id, rec.ext_key(salt))
        room_id = None
        if rec.room:
            rkey = ((rec.building or "").strip(), rec.room.strip())
            room_id = rooms.get(rkey)
            if room_id is None:
                room_id = uuid.uuid4()
                s.add(Room(id=room_id, tenant_id=tenant.id, building=rkey[0], number=rkey[1]))
                rooms[rkey] = room_id
        teacher_id = None
        if rec.teacher:
            tkey = teacher_key(tenant.slug, rec.teacher)
            teacher_id = teachers.get(tkey)
            if teacher_id is None:
                teacher_id = uuid.uuid4()
                s.add(Teacher(id=teacher_id, tenant_id=tenant.id, key=tkey,
                              display_name=rec.teacher if store_teachers == "store" else None))
                teachers[tkey] = teacher_id
        room_text = rec.room if not rec.building else f"{rec.room} ({rec.building})"
        values: dict[str, Any] = {
            "subject": rec.subject, "kind": rec.kind, "starts_at": rec.starts_at, "ends_at": rec.ends_at,
            "subgroup": rec.subgroup, "room_id": room_id, "room_text": room_text, "teacher_id": teacher_id,
            "note": rec.note, "status": rec.status,
        }
        desired[key] = (rec, values)
    await s.flush()

    today = today_utc()
    track_changes = len(existing) > 0
    now = utcnow()
    by_key = {(lesson.group_id, lesson.ext_key): lesson for lesson in existing}
    removed: list[Lesson] = []
    for key, lesson in by_key.items():
        if key not in desired:
            removed.append(lesson)
    added_keys = [k for k in desired if k not in by_key]

    changes: list[ScheduleChange] = []
    for key, (_rec, values) in desired.items():
        found = by_key.get(key)
        if found is None:
            continue
        lesson = found
        diff = {f for f in COMPARE_FIELDS if _norm(getattr(lesson, f)) != _norm(values.get(f))}
        if not diff:
            report.unchanged += 1
            continue
        before = _lesson_snapshot(lesson)
        for f, v in values.items():
            setattr(lesson, f, v)
        lesson.updated_at = now
        report.modified += 1
        if track_changes and lesson.starts_at.date() >= today:
            change = "cancelled" if values["status"] == "cancelled" and before["status"] != "cancelled" else (
                "room_changed" if diff == {"room_text"} else "modified")
            changes.append(ScheduleChange(tenant_id=tenant.id, group_id=lesson.group_id, ext_key=lesson.ext_key,
                                          change=change, before=before, after=_lesson_snapshot(lesson),
                                          lesson_date=lesson.starts_at.date()))

    # Перенос: удалённое и добавленное занятие с той же дисциплиной в пределах недели
    added_records = {k: desired[k] for k in added_keys}
    moved_pairs: list[tuple[Lesson, tuple[uuid.UUID, str]]] = []
    for lesson in removed:
        for k, (_r, values) in added_records.items():
            if k[0] == lesson.group_id and values["subject"] == lesson.subject and \
                    abs((values["starts_at"] - lesson.starts_at).days) <= 7:
                moved_pairs.append((lesson, k))
                added_records.pop(k)
                break
    moved_removed = {lesson.id for lesson, _ in moved_pairs}

    for lesson in removed:
        if track_changes and lesson.starts_at.date() >= today and lesson.id not in moved_removed:
            changes.append(ScheduleChange(tenant_id=tenant.id, group_id=lesson.group_id, ext_key=lesson.ext_key,
                                          change="removed", before=_lesson_snapshot(lesson), after=None,
                                          lesson_date=lesson.starts_at.date()))
    if removed:
        await s.execute(delete(Lesson).where(Lesson.id.in_([x.id for x in removed])))
        report.removed = len(removed)

    for key in added_keys:
        _rec, values = desired[key]
        lesson = Lesson(id=uuid.uuid4(), tenant_id=tenant.id, group_id=key[0], ext_key=key[1],
                        source_id=source.id, **values)
        s.add(lesson)
        report.added += 1
        if track_changes and values["starts_at"].date() >= today:
            moved_from = next((old for old, k in moved_pairs if k == key), None)
            if moved_from is not None:
                changes.append(ScheduleChange(
                    tenant_id=tenant.id, group_id=key[0], ext_key=key[1], change="moved",
                    before=_lesson_snapshot(moved_from), after={**_snap_values(values)},
                    lesson_date=values["starts_at"].date()))
            elif key in added_records:
                changes.append(ScheduleChange(
                    tenant_id=tenant.id, group_id=key[0], ext_key=key[1], change="added", before=None,
                    after=_snap_values(values), lesson_date=values["starts_at"].date()))
    for ch in changes:
        s.add(ch)
    report.changes_logged = len(changes)
    source.last_count = len(records)
    await s.flush()
    return report


def _snap_values(v: dict[str, Any]) -> dict[str, Any]:
    return {
        "subject": v["subject"], "kind": v["kind"], "starts_at": v["starts_at"].isoformat(),
        "ends_at": v["ends_at"].isoformat(), "room": v["room_text"], "status": v["status"],
        "subgroup": v["subgroup"],
    }


def _norm(v: Any) -> Any:
    if isinstance(v, datetime):
        return v.timestamp()
    return v


async def delete_source_lessons(s: AsyncSession, source_id: uuid.UUID, since: datetime | None = None) -> int:
    cond = [Lesson.source_id == source_id]
    if since:
        cond.append(Lesson.starts_at >= since)
    res = await s.execute(delete(Lesson).where(and_(*cond)))
    return int(res.rowcount or 0)  # type: ignore[attr-defined]
