"""Инструменты расписания для ассистента."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field

from doomich.db import get_db
from doomich.orchestrator.tools import Tool, ToolContext, registry
from doomich.schedule import service

MAX_DAYS = 31


class GetScheduleArgs(BaseModel):
    date_from: date = Field(description="Первая дата периода, YYYY-MM-DD")
    date_to: date = Field(description="Последняя дата периода, YYYY-MM-DD, не дальше 31 дня от первой")


class NextLessonArgs(BaseModel):
    pass


class FindLessonsArgs(BaseModel):
    query: str = Field(description="Часть названия дисциплины, например \"матанализ\" или \"физика\"",
                       min_length=2, max_length=100)
    kind: Literal["exam", "credit", "lecture", "practice", "lab", "consultation", "any"] = Field(
        default="any", description="Тип занятия: exam (экзамен), credit (зачёт) и т. д.")


def _no_group(ctx: ToolContext) -> str:
    return json.dumps({
        "error": "группа не выбрана",
        "hint": "Попроси пользователя выбрать группу в разделе Расписание или назвать её.",
    }, ensure_ascii=False)


def _filters(ctx: ToolContext) -> dict[str, object]:
    if ctx.client.teacher_key:
        return {"teacher_key": ctx.client.teacher_key}
    return {"group_id": ctx.group_id, "subgroup": ctx.subgroup}


def _ready(ctx: ToolContext) -> bool:
    return bool(ctx.client.teacher_key or ctx.group_id)


async def get_schedule(ctx: ToolContext, args: GetScheduleArgs) -> str:
    if not _ready(ctx):
        return _no_group(ctx)
    d_from, d_to = args.date_from, args.date_to
    if d_to < d_from:
        d_from, d_to = d_to, d_from
    d_to = min(d_to, d_from + timedelta(days=MAX_DAYS))
    zone = ctx.user.tenant.timezone
    async with get_db().tenant_session(ctx.user.tenant_id) as s:
        items = await service.day_range(s, ctx.user.tenant_id, zone, d_from, d_to, limit=80, **_filters(ctx))
    return json.dumps({
        "period": [d_from.isoformat(), d_to.isoformat()],
        "lessons": [x.brief(zone) for x in items],
        "count": len(items),
    }, ensure_ascii=False)


async def next_lesson(ctx: ToolContext, args: NextLessonArgs) -> str:
    if not _ready(ctx):
        return _no_group(ctx)
    zone = ctx.user.tenant.timezone
    async with get_db().tenant_session(ctx.user.tenant_id) as s:
        current, upcoming = await service.now_next(s, ctx.user.tenant_id, ctx.now, **_filters(ctx))
    out: dict[str, object] = {"now": ctx.now.strftime("%Y-%m-%d %H:%M")}
    if current:
        out["current"] = current.brief(zone)
    if upcoming:
        out["lesson"] = upcoming.brief(zone)
        if upcoming.campus_room_id:
            out["navigation_available"] = True
    if not current and not upcoming:
        out["lesson"] = None
        out["note"] = "в ближайшие две недели занятий нет"
    return json.dumps(out, ensure_ascii=False)


async def find_lessons(ctx: ToolContext, args: FindLessonsArgs) -> str:
    if not _ready(ctx):
        return _no_group(ctx)
    zone = ctx.user.tenant.timezone
    today = ctx.now.date()
    kinds = None if args.kind == "any" else [args.kind]
    async with get_db().tenant_session(ctx.user.tenant_id) as s:
        items = await service.day_range(s, ctx.user.tenant_id, zone, today - timedelta(days=7),
                                        today + timedelta(days=150), subject_like=args.query, kinds=kinds,
                                        limit=30, **_filters(ctx))
    return json.dumps({"query": args.query, "lessons": [x.brief(zone) for x in items]}, ensure_ascii=False)


registry.register(Tool(
    name="get_schedule",
    description="Расписание занятий пользователя за период. Используй для вопросов о парах на день или неделю.",
    args_model=GetScheduleArgs, fn=get_schedule,
))
registry.register(Tool(
    name="next_lesson",
    description="Текущая и следующая пара пользователя: что, когда и в какой аудитории.",
    args_model=NextLessonArgs, fn=next_lesson,
))
registry.register(Tool(
    name="find_lessons",
    description="Поиск занятий по названию дисциплины и типу, например когда экзамен по физике.",
    args_model=FindLessonsArgs, fn=find_lessons,
))
