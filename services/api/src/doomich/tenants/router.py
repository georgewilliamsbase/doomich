"""Информация о вузе для клиента и проверка обновлений приложения."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select

from doomich.common.timeutil import utc_offset_minutes
from doomich.db import get_db
from doomich.deps import CurrentUser, current_user
from doomich.models import AcademicTerm, AppRelease, Campus

router = APIRouter(prefix="/v1", tags=["tenant"])


class CampusOut(BaseModel):
    id: uuid.UUID
    name: str
    address: str | None
    lat: float | None
    lon: float | None


class TermOut(BaseModel):
    name: str
    starts_on: date
    ends_on: date
    first_week_odd: bool


class TenantOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    short_name: str | None
    timezone: str
    teacher_names: str
    features: dict[str, bool]
    bell_schedule: list[list[str]]
    campuses: list[CampusOut]
    terms: list[TermOut]
    support_contact: str | None = None
    utc_offset_minutes: int = 180


class ReleaseOut(BaseModel):
    version: str
    build: int
    url: str
    sha256: str
    signature: str | None
    force: bool
    notes: str | None


DEFAULT_FEATURES = {
    "voice": True, "documents": True, "schedule": True, "lectures": True, "navigation": False,
    "courses": False, "wake_word": False, "qr_login": True, "knowledge_base": True,
}


@router.get("/tenant", response_model=TenantOut)
async def tenant(user: CurrentUser = Depends(current_user)) -> TenantOut:
    t = user.tenant
    async with get_db().tenant_session(t.id) as s:
        campuses = (await s.scalars(select(Campus).where(Campus.tenant_id == t.id).order_by(Campus.name))).all()
        terms = (await s.scalars(select(AcademicTerm).where(AcademicTerm.tenant_id == t.id)
                                 .order_by(AcademicTerm.starts_on))).all()
    features = {**DEFAULT_FEATURES, **{k: bool(v) for k, v in (t.settings.get("features") or {}).items()}}
    return TenantOut(
        id=t.id, slug=t.slug, name=t.name, short_name=t.settings.get("short_name"), timezone=t.timezone,
        teacher_names=t.teacher_names_mode, features=features,
        bell_schedule=[list(x) for x in t.settings.get("bell_schedule", [])],
        campuses=[CampusOut(id=c.id, name=c.name, address=c.address, lat=c.lat, lon=c.lon) for c in campuses],
        terms=[TermOut(name=x.name, starts_on=x.starts_on, ends_on=x.ends_on, first_week_odd=x.first_week_odd)
               for x in terms],
        support_contact=t.settings.get("support_contact"),
        utc_offset_minutes=utc_offset_minutes(t.timezone),
    )


@router.get("/app/latest", response_model=ReleaseOut | None)
async def latest_release(
    app: str = Query(pattern="^(mobile|desktop)$"),
    platform: str = Query(max_length=32),
    channel: str = Query("stable", pattern="^(stable|beta)$"),
    build: int = Query(0, ge=0),
    lang: str = Query("ru", pattern="^(ru|en)$"),
) -> ReleaseOut | None:
    """Проверка обновлений для APK с сайта и ПК-версий. Без авторизации, без идентификаторов."""
    channels = ["stable"] if channel == "stable" else ["stable", "beta"]
    async with get_db().sys_session() as s:
        rel = await s.scalar(
            select(AppRelease).where(AppRelease.app == app, AppRelease.platform == platform,
                                     AppRelease.channel.in_(channels))
            .order_by(AppRelease.build.desc()).limit(1)
        )
    if rel is None or rel.build <= build:
        return None
    return ReleaseOut(version=rel.version, build=rel.build, url=rel.url, sha256=rel.sha256, signature=rel.signature,
                      force=build < rel.min_supported_build, notes=rel.notes_en if lang == "en" else rel.notes_ru)
