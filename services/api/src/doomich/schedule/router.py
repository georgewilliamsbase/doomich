from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy import select

from doomich.common.errors import AppError, NotFound
from doomich.common.timeutil import local_now
from doomich.db import get_db
from doomich.deps import CurrentUser, current_user
from doomich.models import ScheduleChange, StudyGroup, Teacher
from doomich.schedule import service

router = APIRouter(prefix="/v1", tags=["schedule"])


class GroupOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str | None = None
    faculty: str | None = None
    year: int | None = None
    subgroups: list[str] = []


class LessonOut(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    subgroup: str | None
    subject: str
    kind: str
    starts_at: datetime
    ends_at: datetime
    room: str | None
    campus_room_id: uuid.UUID | None = None
    teacher: str | None
    teacher_key: str | None
    note: str | None
    status: str


class ScheduleOut(BaseModel):
    group: GroupOut | None
    date_from: date
    date_to: date
    lessons: list[LessonOut]
    version: str
    generated_at: datetime


class NowNextOut(BaseModel):
    current: LessonOut | None
    next: LessonOut | None


class ChangeOut(BaseModel):
    id: int
    group_id: uuid.UUID
    change: str
    before: dict | None
    after: dict | None
    lesson_date: date
    detected_at: datetime


class TeacherOut(BaseModel):
    key: str
    name: str


def _lesson(v: service.LessonView) -> LessonOut:
    return LessonOut(id=v.id, group_id=v.group_id, subgroup=v.subgroup, subject=v.subject, kind=v.kind,
                     starts_at=v.starts_at, ends_at=v.ends_at, room=v.room, campus_room_id=v.campus_room_id,
                     teacher=v.teacher, teacher_key=v.teacher_key, note=v.note, status=v.status)


@router.get("/groups", response_model=list[GroupOut])
async def groups(q: str | None = Query(None, max_length=50), limit: int = Query(50, ge=1, le=500),
                 user: CurrentUser = Depends(current_user)) -> list[GroupOut]:
    async with get_db().tenant_session(user.tenant_id) as s:
        rows = await service.search_groups(s, user.tenant_id, q, limit)
    return [GroupOut(id=g.id, code=g.code, name=g.name, faculty=g.faculty, year=g.year,
                     subgroups=list(g.subgroups or [])) for g in rows]


@router.get("/teachers", response_model=list[TeacherOut])
async def teachers(q: str = Query(min_length=2, max_length=50), user: CurrentUser = Depends(current_user)
                   ) -> list[TeacherOut]:
    """Поиск преподавателя по имени работает только если вуз разрешил хранить ФИО."""
    if user.tenant.teacher_names_mode != "store":
        return []
    async with get_db().tenant_session(user.tenant_id) as s:
        rows = (await s.scalars(
            select(Teacher).where(Teacher.tenant_id == user.tenant_id, Teacher.display_name.ilike(f"%{q}%"))
            .order_by(Teacher.display_name).limit(30)
        )).all()
    return [TeacherOut(key=t.key, name=t.display_name or "") for t in rows]


@router.get("/schedule", response_model=ScheduleOut)
async def schedule(
    response: Response,
    group_id: uuid.UUID | None = None,
    subgroup: str | None = Query(None, max_length=16),
    teacher_key: str | None = Query(None, max_length=64),
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    user: CurrentUser = Depends(current_user),
) -> ScheduleOut:
    if teacher_key is None:
        group_id = group_id or user.group_id
        if group_id is None:
            raise AppError("группа не выбрана", code="group_required")
        if subgroup is None and group_id == user.group_id:
            subgroup = user.subgroup
    today = local_now(user.tenant.timezone).date()
    d_from = date_from or today - timedelta(days=today.weekday())
    d_to = date_to or d_from + timedelta(days=13)
    if (d_to - d_from).days > 120:
        raise AppError("слишком большой период", code="range_too_large")
    async with get_db().tenant_session(user.tenant_id) as s:
        group = await s.get(StudyGroup, group_id) if group_id else None
        if group_id and group is None:
            raise NotFound("группа не найдена", code="group_not_found")
        items = await service.day_range(s, user.tenant_id, user.tenant.timezone, d_from, d_to,
                                        group_id=group_id if teacher_key is None else None,
                                        subgroup=subgroup, teacher_key=teacher_key, limit=2000)
    lessons = [_lesson(v) for v in items]
    version = hashlib.sha1(  # noqa: S324
        "".join(f"{x.id}{x.starts_at}{x.room}{x.status}{x.subject}" for x in lessons).encode()
    ).hexdigest()[:16]
    response.headers["ETag"] = f'"{version}"'
    return ScheduleOut(
        group=GroupOut(id=group.id, code=group.code, name=group.name, faculty=group.faculty, year=group.year,
                       subgroups=list(group.subgroups or [])) if group else None,
        date_from=d_from, date_to=d_to, lessons=lessons, version=version,
        generated_at=local_now(user.tenant.timezone),
    )


@router.get("/schedule/now", response_model=NowNextOut)
async def now_next(group_id: uuid.UUID | None = None, subgroup: str | None = None,
                   teacher_key: str | None = None, user: CurrentUser = Depends(current_user)) -> NowNextOut:
    gid = group_id or user.group_id
    if teacher_key is None and gid is None:
        raise AppError("группа не выбрана", code="group_required")
    async with get_db().tenant_session(user.tenant_id) as s:
        current, upcoming = await service.now_next(
            s, user.tenant_id, local_now(user.tenant.timezone),
            group_id=gid if teacher_key is None else None,
            subgroup=subgroup or (user.subgroup if gid == user.group_id else None), teacher_key=teacher_key)
    return NowNextOut(current=_lesson(current) if current else None, next=_lesson(upcoming) if upcoming else None)


@router.get("/schedule/changes", response_model=list[ChangeOut])
async def changes(since: datetime, group_id: uuid.UUID | None = None,
                  user: CurrentUser = Depends(current_user)) -> list[ChangeOut]:
    gid = group_id or user.group_id
    if gid is None:
        return []
    async with get_db().tenant_session(user.tenant_id) as s:
        rows = (await s.scalars(
            select(ScheduleChange).where(ScheduleChange.group_id == gid, ScheduleChange.detected_at > since)
            .order_by(ScheduleChange.detected_at).limit(200)
        )).all()
    return [ChangeOut(id=r.id, group_id=r.group_id, change=r.change, before=r.before, after=r.after,
                      lesson_date=r.lesson_date, detected_at=r.detected_at) for r in rows]
