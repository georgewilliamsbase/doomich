"""Админ-API (/admin/v1). Используется админ-панелью и ML-платформой (выкатка моделей)."""

from __future__ import annotations

import io
import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select, update

from doomich import bindings as bindings_mod
from doomich.accounts import invites
from doomich.accounts.service import normalize_login
from doomich.admin.auth import (
    CurrentAdmin,
    any_admin,
    audit,
    manager,
    new_totp_secret,
    provisioning_uri,
    superadmin,
    totp_for,
)
from doomich.admin.printing import invite_sheet
from doomich.ai.registry import get_ai
from doomich.common.errors import AppError, Conflict, NotFound, Unauthorized
from doomich.common.timeutil import day_bounds, tz, utcnow
from doomich.config import settings
from doomich.db import get_db
from doomich.deps import invalidate_tenant
from doomich.models import (
    AcademicTerm,
    Admin,
    AdminAudit,
    AppRelease,
    Campus,
    Document,
    Feedback,
    InviteBatch,
    InviteCode,
    Lesson,
    Message,
    ModelBinding,
    ScheduleSource,
    StudyGroup,
    Tenant,
    User,
)
from doomich.schedule import importers, sync
from doomich.schedule.adapters.base import available_kinds
from doomich.security import kv
from doomich.security.passwords import hash_secret, verify_secret
from doomich.security.tokens import AdminClaims, issue_admin, issue_short, read_short
from doomich.worker import dispatch

router = APIRouter(prefix="/admin/v1", tags=["admin"])


# --- Аутентификация -----------------------------------------------------------


class AdminLoginIn(BaseModel):
    login: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)
    totp: str | None = Field(default=None, min_length=6, max_length=8)


class AdminLoginOut(BaseModel):
    token: str | None = None
    totp_setup_required: bool = False
    setup_token: str | None = None
    otpauth_uri: str | None = None
    secret: str | None = None
    admin: dict[str, Any] | None = None


class TotpConfirmIn(BaseModel):
    setup_token: str
    code: str = Field(min_length=6, max_length=8)


def _admin_dict(a: Admin) -> dict[str, Any]:
    return {"id": str(a.id), "login": a.login, "role": a.role, "tenant_id": str(a.tenant_id) if a.tenant_id else None,
            "totp_enabled": a.totp_enabled, "disabled": a.disabled}


@router.post("/auth/login", response_model=AdminLoginOut)
async def admin_login(body: AdminLoginIn, request: Request) -> AdminLoginOut:
    await kv.hit(f"admin-login:{kv.anon(body.login.lower())}", 5, 300)
    async with get_db().sys_session() as s:
        admin = await s.scalar(select(Admin).where(Admin.login == body.login.lower()))
        if admin is None or admin.disabled or not verify_secret(admin.password_hash, body.password):
            raise Unauthorized("неверный логин или пароль", code="bad_credentials")
        totp = totp_for(admin)
        if admin.totp_enabled and totp is not None:
            if not body.totp or not totp.verify(body.totp, valid_window=1):
                raise Unauthorized("нужен код из приложения-аутентификатора", code="totp_required")
        elif settings().env in ("stage", "prod") or body.totp is not None:
            secret, enc = new_totp_secret()
            admin.totp_secret_enc = enc
            setup = issue_short("totp_setup", str(admin.id), 600)
            return AdminLoginOut(totp_setup_required=True, setup_token=setup,
                                 otpauth_uri=provisioning_uri(secret, admin.login), secret=secret)
        admin.last_login_at = utcnow()
        token = issue_admin(AdminClaims(admin_id=admin.id, role=admin.role, tenant_id=admin.tenant_id))
        return AdminLoginOut(token=token, admin=_admin_dict(admin))


@router.post("/auth/totp/confirm", response_model=AdminLoginOut)
async def totp_confirm(body: TotpConfirmIn) -> AdminLoginOut:
    data = read_short(body.setup_token, "totp_setup")
    async with get_db().sys_session() as s:
        admin = await s.get(Admin, uuid.UUID(data["sub"]))
        if admin is None or admin.disabled:
            raise Unauthorized()
        totp = totp_for(admin)
        if totp is None or not totp.verify(body.code, valid_window=1):
            raise Unauthorized("код не подошёл", code="totp_invalid")
        admin.totp_enabled = True
        admin.last_login_at = utcnow()
        token = issue_admin(AdminClaims(admin_id=admin.id, role=admin.role, tenant_id=admin.tenant_id))
        return AdminLoginOut(token=token, admin=_admin_dict(admin))


@router.get("/me")
async def admin_me(admin: CurrentAdmin = Depends(any_admin)) -> dict[str, Any]:
    return {"id": str(admin.id), "login": admin.login, "role": admin.role,
            "tenant_id": str(admin.tenant_id) if admin.tenant_id else None}


# --- Вузы, кампусы, семестры -------------------------------------------------


class TenantIn(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9-]{2,64}$")
    name: str = Field(min_length=2, max_length=300)
    short_name: str | None = Field(default=None, max_length=50)
    timezone: str = "Europe/Moscow"
    default_locale: Literal["ru", "en"] = "ru"
    settings: dict[str, Any] = Field(default_factory=dict)


class TenantPatch(BaseModel):
    name: str | None = Field(default=None, max_length=300)
    short_name: str | None = Field(default=None, max_length=50)
    timezone: str | None = None
    is_active: bool | None = None
    settings: dict[str, Any] | None = None


def _tenant_dict(t: Tenant) -> dict[str, Any]:
    return {"id": str(t.id), "slug": t.slug, "name": t.name, "short_name": t.short_name, "timezone": t.timezone,
            "default_locale": t.default_locale, "settings": t.settings, "is_active": t.is_active,
            "created_at": t.created_at}


@router.get("/tenants")
async def list_tenants(admin: CurrentAdmin = Depends(any_admin)) -> list[dict[str, Any]]:
    async with get_db().sys_session() as s:
        stmt = select(Tenant).order_by(Tenant.name)
        if not admin.is_super:
            stmt = stmt.where(Tenant.id == admin.tenant_id)
        return [_tenant_dict(t) for t in (await s.scalars(stmt)).all()]


@router.post("/tenants", status_code=201)
async def create_tenant(body: TenantIn, admin: CurrentAdmin = Depends(superadmin)) -> dict[str, Any]:
    tz(body.timezone)
    async with get_db().sys_session() as s:
        if await s.scalar(select(Tenant.id).where(Tenant.slug == body.slug)):
            raise Conflict("такой slug уже есть", code="slug_taken")
        t = Tenant(id=uuid.uuid4(), slug=body.slug, name=body.name, short_name=body.short_name,
                   timezone=body.timezone, default_locale=body.default_locale, settings=body.settings)
        s.add(t)
        await s.flush()
        await s.refresh(t)
        await audit(s, admin, "tenant.create", object_type="tenant", object_id=t.id, tenant_id=t.id)
        return _tenant_dict(t)


@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: uuid.UUID, admin: CurrentAdmin = Depends(any_admin)) -> dict[str, Any]:
    admin.check_tenant(tenant_id)
    async with get_db().sys_session() as s:
        t = await s.get(Tenant, tenant_id)
        if t is None:
            raise NotFound()
        return _tenant_dict(t)


@router.patch("/tenants/{tenant_id}")
async def patch_tenant(tenant_id: uuid.UUID, body: TenantPatch, admin: CurrentAdmin = Depends(manager)
                       ) -> dict[str, Any]:
    admin.check_tenant(tenant_id)
    async with get_db().sys_session() as s:
        t = await s.get(Tenant, tenant_id, with_for_update=True)
        if t is None:
            raise NotFound()
        if body.name is not None:
            t.name = body.name
        if body.short_name is not None:
            t.short_name = body.short_name
        if body.timezone is not None:
            tz(body.timezone)
            t.timezone = body.timezone
        if body.is_active is not None:
            if not admin.is_super:
                raise AppError("отключать вуз может только суперадмин", code="admin_role", status_code=403)
            t.is_active = body.is_active
        if body.settings is not None:
            merged = dict(t.settings or {})
            for k, v in body.settings.items():
                if v is None:
                    merged.pop(k, None)
                else:
                    merged[k] = v
            t.settings = merged
        await audit(s, admin, "tenant.update", object_type="tenant", object_id=t.id, tenant_id=t.id,
                    details={"fields": [k for k, v in body.model_dump().items() if v is not None]})
        await s.flush()
        await s.refresh(t)
        result = _tenant_dict(t)
    invalidate_tenant(tenant_id)
    return result


class CampusIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: str | None = Field(default=None, max_length=500)
    lat: float | None = None
    lon: float | None = None


@router.get("/tenants/{tenant_id}/campuses")
async def list_campuses(tenant_id: uuid.UUID, admin: CurrentAdmin = Depends(any_admin)) -> list[dict[str, Any]]:
    admin.check_tenant(tenant_id)
    async with get_db().sys_session() as s:
        rows = (await s.scalars(select(Campus).where(Campus.tenant_id == tenant_id).order_by(Campus.name))).all()
        return [{"id": str(c.id), "name": c.name, "address": c.address, "lat": c.lat, "lon": c.lon} for c in rows]


@router.post("/tenants/{tenant_id}/campuses", status_code=201)
async def create_campus(tenant_id: uuid.UUID, body: CampusIn, admin: CurrentAdmin = Depends(manager)
                        ) -> dict[str, Any]:
    admin.check_tenant(tenant_id)
    async with get_db().sys_session() as s:
        c = Campus(id=uuid.uuid4(), tenant_id=tenant_id, **body.model_dump())
        s.add(c)
        await audit(s, admin, "campus.create", object_type="campus", object_id=c.id, tenant_id=tenant_id)
        return {"id": str(c.id), **body.model_dump()}


@router.delete("/campuses/{campus_id}", status_code=204)
async def delete_campus(campus_id: uuid.UUID, admin: CurrentAdmin = Depends(manager)) -> None:
    async with get_db().sys_session() as s:
        c = await s.get(Campus, campus_id)
        if c is None:
            raise NotFound()
        admin.check_tenant(c.tenant_id)
        await s.delete(c)
        await audit(s, admin, "campus.delete", object_type="campus", object_id=campus_id, tenant_id=c.tenant_id)


class TermIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    starts_on: date
    ends_on: date
    first_week_odd: bool = True
    holidays: list[date] = Field(default_factory=list)


@router.get("/tenants/{tenant_id}/terms")
async def list_terms(tenant_id: uuid.UUID, admin: CurrentAdmin = Depends(any_admin)) -> list[dict[str, Any]]:
    admin.check_tenant(tenant_id)
    async with get_db().sys_session() as s:
        rows = (await s.scalars(select(AcademicTerm).where(AcademicTerm.tenant_id == tenant_id)
                                .order_by(AcademicTerm.starts_on))).all()
        return [{"id": str(t.id), "name": t.name, "starts_on": t.starts_on, "ends_on": t.ends_on,
                 "first_week_odd": t.first_week_odd, "holidays": t.holidays} for t in rows]


@router.post("/tenants/{tenant_id}/terms", status_code=201)
async def create_term(tenant_id: uuid.UUID, body: TermIn, admin: CurrentAdmin = Depends(manager)) -> dict[str, Any]:
    admin.check_tenant(tenant_id)
    if body.ends_on < body.starts_on:
        raise AppError("конец семестра раньше начала", code="bad_term")
    async with get_db().sys_session() as s:
        t = AcademicTerm(id=uuid.uuid4(), tenant_id=tenant_id, name=body.name, starts_on=body.starts_on,
                         ends_on=body.ends_on, first_week_odd=body.first_week_odd,
                         holidays=[d.isoformat() for d in body.holidays])
        s.add(t)
        await audit(s, admin, "term.create", object_type="term", object_id=t.id, tenant_id=tenant_id)
        return {"id": str(t.id), **body.model_dump(mode="json")}


@router.delete("/terms/{term_id}", status_code=204)
async def delete_term(term_id: uuid.UUID, admin: CurrentAdmin = Depends(manager)) -> None:
    async with get_db().sys_session() as s:
        t = await s.get(AcademicTerm, term_id)
        if t is None:
            raise NotFound()
        admin.check_tenant(t.tenant_id)
        await s.delete(t)
        await audit(s, admin, "term.delete", object_type="term", object_id=term_id, tenant_id=t.tenant_id)


# --- Группы ---------------------------------------------------------------------


class GroupIn(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str | None = Field(default=None, max_length=200)
    faculty: str | None = Field(default=None, max_length=200)
    year: int | None = Field(default=None, ge=1, le=7)
    subgroups: list[str] = Field(default_factory=list, max_length=10)
    is_active: bool = True


def _group_dict(g: StudyGroup) -> dict[str, Any]:
    return {"id": str(g.id), "code": g.code, "name": g.name, "faculty": g.faculty, "year": g.year,
            "subgroups": list(g.subgroups or []), "is_active": g.is_active}


@router.get("/tenants/{tenant_id}/groups")
async def list_groups(tenant_id: uuid.UUID, q: str | None = None, admin: CurrentAdmin = Depends(any_admin)
                      ) -> list[dict[str, Any]]:
    admin.check_tenant(tenant_id)
    async with get_db().sys_session() as s:
        stmt = select(StudyGroup).where(StudyGroup.tenant_id == tenant_id).order_by(StudyGroup.code)
        if q:
            stmt = stmt.where(StudyGroup.code.ilike(f"%{q}%"))
        return [_group_dict(g) for g in (await s.scalars(stmt.limit(1000))).all()]


@router.post("/tenants/{tenant_id}/groups", status_code=201)
async def create_group(tenant_id: uuid.UUID, body: GroupIn, admin: CurrentAdmin = Depends(any_admin)
                       ) -> dict[str, Any]:
    admin.check_tenant(tenant_id)
    async with get_db().sys_session() as s:
        code = body.code.strip().upper()
        if await s.scalar(select(StudyGroup.id).where(StudyGroup.tenant_id == tenant_id, StudyGroup.code == code)):
            raise Conflict("группа уже есть", code="group_exists")
        g = StudyGroup(id=uuid.uuid4(), tenant_id=tenant_id, **{**body.model_dump(), "code": code})
        s.add(g)
        await audit(s, admin, "group.create", object_type="group", object_id=g.id, tenant_id=tenant_id)
        return _group_dict(g)


@router.patch("/groups/{group_id}")
async def patch_group(group_id: uuid.UUID, body: GroupIn, admin: CurrentAdmin = Depends(any_admin)
                      ) -> dict[str, Any]:
    async with get_db().sys_session() as s:
        g = await s.get(StudyGroup, group_id)
        if g is None:
            raise NotFound()
        admin.check_tenant(g.tenant_id)
        for k, v in body.model_dump().items():
            setattr(g, k, v.strip().upper() if k == "code" else v)
        await audit(s, admin, "group.update", object_type="group", object_id=g.id, tenant_id=g.tenant_id)
        return _group_dict(g)


@router.delete("/groups/{group_id}", status_code=204)
async def delete_group(group_id: uuid.UUID, admin: CurrentAdmin = Depends(manager)) -> None:
    async with get_db().sys_session() as s:
        g = await s.get(StudyGroup, group_id)
        if g is None:
            raise NotFound()
        admin.check_tenant(g.tenant_id)
        await s.delete(g)
        await audit(s, admin, "group.delete", object_type="group", object_id=group_id, tenant_id=g.tenant_id)


# --- Коды приглашения -----------------------------------------------------------


class BatchIn(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    count: int = Field(ge=1, le=5000)
    role: Literal["student", "teacher", "staff"] = "student"
    kind: Literal["register", "role_upgrade"] = "register"
    group_id: uuid.UUID | None = None
    max_uses: int = Field(default=1, ge=1, le=10000)
    expires_on: date | None = None
    is_beta: bool = False


async def _batch_stats(s: Any, batch_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict[str, int]]:
    rows = (await s.execute(
        select(InviteCode.batch_id, func.count(), func.sum(InviteCode.uses),
               func.count().filter(InviteCode.revoked.is_(True)))
        .where(InviteCode.batch_id.in_(batch_ids)).group_by(InviteCode.batch_id)
    )).all()
    return {r[0]: {"codes": int(r[1]), "activations": int(r[2] or 0), "revoked": int(r[3] or 0)} for r in rows}


def _batch_dict(b: InviteBatch, stats: dict[str, int] | None = None) -> dict[str, Any]:
    return {"id": str(b.id), "tenant_id": str(b.tenant_id), "label": b.label, "kind": b.kind, "role": b.role,
            "group_id": str(b.group_id) if b.group_id else None, "max_uses": b.max_uses, "expires_on": b.expires_on,
            "is_beta": b.is_beta, "code_count": b.code_count, "created_at": b.created_at, "stats": stats or {}}


@router.post("/tenants/{tenant_id}/invite-batches", status_code=201)
async def create_batch(tenant_id: uuid.UUID, body: BatchIn, admin: CurrentAdmin = Depends(manager)
                       ) -> dict[str, Any]:
    admin.check_tenant(tenant_id)
    if body.role == "staff" and not admin.is_super:
        raise AppError("коды сотрудников выпускает суперадмин", code="admin_role", status_code=403)
    async with get_db().sys_session() as s:
        if body.group_id:
            g = await s.get(StudyGroup, body.group_id)
            if g is None or g.tenant_id != tenant_id:
                raise NotFound("группа не найдена")
        batch, codes = await invites.create_batch(
            s, tenant_id=tenant_id, label=body.label, count=body.count, role=body.role, kind=body.kind,
            group_id=body.group_id, max_uses=body.max_uses, expires_on=body.expires_on, is_beta=body.is_beta,
            created_by=admin.id,
        )
        await audit(s, admin, "invites.create", object_type="invite_batch", object_id=batch.id, tenant_id=tenant_id,
                    details={"count": body.count, "role": body.role, "kind": body.kind})
        await s.refresh(batch)
        return {"batch": _batch_dict(batch), "codes": codes}


@router.get("/tenants/{tenant_id}/invite-batches")
async def list_batches(tenant_id: uuid.UUID, admin: CurrentAdmin = Depends(any_admin)) -> list[dict[str, Any]]:
    admin.check_tenant(tenant_id)
    async with get_db().sys_session() as s:
        batches = (await s.scalars(select(InviteBatch).where(InviteBatch.tenant_id == tenant_id)
                                   .order_by(InviteBatch.created_at.desc()).limit(500))).all()
        stats = await _batch_stats(s, [b.id for b in batches]) if batches else {}
        return [_batch_dict(b, stats.get(b.id)) for b in batches]


@router.get("/invite-batches/{batch_id}")
async def get_batch(batch_id: uuid.UUID, admin: CurrentAdmin = Depends(manager)) -> dict[str, Any]:
    async with get_db().sys_session() as s:
        b = await s.get(InviteBatch, batch_id)
        if b is None:
            raise NotFound()
        admin.check_tenant(b.tenant_id)
        codes = (await s.scalars(select(InviteCode).where(InviteCode.batch_id == batch_id))).all()
        stats = await _batch_stats(s, [b.id])
        return {**_batch_dict(b, stats.get(b.id)),
                "codes": [{"id": str(c.id), "code": invites.reveal(c), "uses": c.uses, "revoked": c.revoked}
                          for c in codes]}


@router.get("/invite-batches/{batch_id}/print.pdf")
async def print_batch(batch_id: uuid.UUID, admin: CurrentAdmin = Depends(manager)) -> Response:
    async with get_db().sys_session() as s:
        b = await s.get(InviteBatch, batch_id)
        if b is None:
            raise NotFound()
        admin.check_tenant(b.tenant_id)
        tenant = await s.get(Tenant, b.tenant_id)
        assert tenant is not None
        codes = [invites.reveal(c) for c in (await s.scalars(
            select(InviteCode).where(InviteCode.batch_id == batch_id, InviteCode.revoked.is_(False))
            .order_by(InviteCode.id))).all()]
        await audit(s, admin, "invites.print", object_type="invite_batch", object_id=batch_id,
                    tenant_id=b.tenant_id)
    st = settings()
    site = (tenant.settings or {}).get("download_site", "doomich.ru")
    pdf = invite_sheet(codes, tenant_name=tenant.short_name or tenant.name, label=b.label, server=st.public_base_url,
                       site=site)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="invites-{batch_id}.pdf"'})


@router.post("/invite-batches/{batch_id}/revoke", status_code=204)
async def revoke_batch(batch_id: uuid.UUID, admin: CurrentAdmin = Depends(manager)) -> None:
    async with get_db().sys_session() as s:
        b = await s.get(InviteBatch, batch_id)
        if b is None:
            raise NotFound()
        admin.check_tenant(b.tenant_id)
        await s.execute(update(InviteCode).where(InviteCode.batch_id == batch_id).values(revoked=True))
        await audit(s, admin, "invites.revoke", object_type="invite_batch", object_id=batch_id, tenant_id=b.tenant_id)


# --- Расписание -------------------------------------------------------------------


class SourceIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    kind: str
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    require_review_on_spike: bool = True


def _source_dict(x: ScheduleSource) -> dict[str, Any]:
    return {"id": str(x.id), "name": x.name, "kind": x.kind, "config": x.config, "enabled": x.enabled,
            "require_review_on_spike": x.require_review_on_spike, "last_sync_at": x.last_sync_at,
            "last_status": x.last_status, "last_error": x.last_error, "last_count": x.last_count,
            "has_pending": x.pending_snapshot is not None}


@router.get("/schedule/adapters")
async def adapters(admin: CurrentAdmin = Depends(any_admin)) -> list[str]:
    return available_kinds()


@router.get("/tenants/{tenant_id}/schedule/sources")
async def list_sources(tenant_id: uuid.UUID, admin: CurrentAdmin = Depends(any_admin)) -> list[dict[str, Any]]:
    admin.check_tenant(tenant_id)
    async with get_db().sys_session() as s:
        rows = (await s.scalars(select(ScheduleSource).where(ScheduleSource.tenant_id == tenant_id)
                                .order_by(ScheduleSource.created_at))).all()
        return [_source_dict(x) for x in rows]


@router.post("/tenants/{tenant_id}/schedule/sources", status_code=201)
async def create_source(tenant_id: uuid.UUID, body: SourceIn, admin: CurrentAdmin = Depends(manager)
                        ) -> dict[str, Any]:
    admin.check_tenant(tenant_id)
    if body.kind not in available_kinds():
        raise AppError(f"неизвестный тип источника {body.kind}", code="bad_source_kind")
    async with get_db().sys_session() as s:
        x = ScheduleSource(id=uuid.uuid4(), tenant_id=tenant_id, **body.model_dump())
        s.add(x)
        await s.flush()
        await s.refresh(x)
        await audit(s, admin, "schedule.source.create", object_type="schedule_source", object_id=x.id,
                    tenant_id=tenant_id)
        return _source_dict(x)


@router.patch("/schedule/sources/{source_id}")
async def patch_source(source_id: uuid.UUID, body: SourceIn, admin: CurrentAdmin = Depends(manager)
                       ) -> dict[str, Any]:
    async with get_db().sys_session() as s:
        x = await s.get(ScheduleSource, source_id)
        if x is None:
            raise NotFound()
        admin.check_tenant(x.tenant_id)
        for k, v in body.model_dump().items():
            setattr(x, k, v)
        await audit(s, admin, "schedule.source.update", object_type="schedule_source", object_id=x.id,
                    tenant_id=x.tenant_id)
        return _source_dict(x)


@router.delete("/schedule/sources/{source_id}", status_code=204)
async def delete_source(source_id: uuid.UUID, admin: CurrentAdmin = Depends(manager)) -> None:
    async with get_db().sys_session() as s:
        x = await s.get(ScheduleSource, source_id)
        if x is None:
            raise NotFound()
        admin.check_tenant(x.tenant_id)
        await sync.delete_source_lessons(s, x.id, since=utcnow())
        await s.delete(x)
        await audit(s, admin, "schedule.source.delete", object_type="schedule_source", object_id=source_id,
                    tenant_id=x.tenant_id)


@router.post("/schedule/sources/{source_id}/sync")
async def sync_source(source_id: uuid.UUID, force: bool = False, admin: CurrentAdmin = Depends(any_admin)
                      ) -> dict[str, Any]:
    async with get_db().sys_session() as s:
        x = await s.get(ScheduleSource, source_id)
        if x is None:
            raise NotFound()
        admin.check_tenant(x.tenant_id)
        await audit(s, admin, "schedule.sync", object_type="schedule_source", object_id=source_id,
                    tenant_id=x.tenant_id, details={"force": force})
    result = await dispatch.schedule_sync(source_id, force=force)
    return result or {"status": "queued"}


@router.post("/tenants/{tenant_id}/schedule/import")
async def import_schedule(
    tenant_id: uuid.UUID,
    file: UploadFile = File(...),
    dry_run: bool = Form(True),
    group: str | None = Form(None),
    force: bool = Form(False),
    admin: CurrentAdmin = Depends(any_admin),
) -> dict[str, Any]:
    """Импорт из шаблона Excel/CSV или .ics. Сначала dry_run=true: отчёт с ошибками по строкам."""
    admin.check_tenant(tenant_id)
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise AppError("файл больше 20 МБ", code="file_too_large", status_code=413)
    name = (file.filename or "").lower()
    async with get_db().sys_session() as s:
        tenant = await s.get(Tenant, tenant_id)
        if tenant is None:
            raise NotFound()
        zone = tz(tenant.timezone)
        term = await sync.active_term(s, tenant_id)
        bells = [tuple(x) for x in (tenant.settings or {}).get("bell_schedule", [])] or None
        if name.endswith(".ics"):
            if not group:
                raise AppError("для .ics укажите группу", code="group_required")
            today = utcnow().date()
            window = (term.starts_on, term.ends_on) if term else (today - timedelta(days=7),
                                                                  today + timedelta(days=180))
            result = importers.parse_ics(data, group=group, tz=zone, window=window)
        else:
            result = importers.parse_template(data, name, tz=zone, term=term, bells=bells)
        report = result.report()
        if dry_run or (result.errors and not force):
            report["applied"] = False
            return report
        source = await sync.manual_source(s, tenant_id)
        applied = await sync.apply_records(s, tenant=tenant, source=source, records=result.records, force=True)
        await audit(s, admin, "schedule.import", object_type="schedule_source", object_id=source.id,
                    tenant_id=tenant_id, details={"lessons": len(result.records), "file": name[-60:]})
        report["applied"] = True
        report["sync"] = applied.as_dict()
        return report


@router.get("/schedule/template.xlsx")
async def schedule_template(admin: CurrentAdmin = Depends(any_admin)) -> Response:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Расписание"
    ws.append(["Группа", "Подгруппа", "День недели", "Неделя", "С", "По", "Дата", "Начало", "Конец", "Дисциплина",
               "Тип", "Аудитория", "Корпус", "Преподаватель", "Примечание"])
    ws.append(["ИВТ-21", "", "пн", "все", "", "", "", "08:30", "10:00", "Математический анализ", "лекция", "305",
               "Главный", "", ""])
    ws.append(["ИВТ-21", "1", "ср", "нечёт", "", "", "", "10:10", "11:40", "Программирование", "лаб", "214", "",
               "", ""])
    ws.append(["ИВТ-21", "", "", "", "", "", "20.01.2027", "09:00", "12:00", "Физика", "экзамен", "101", "", "",
               "консультация накануне"])
    buf = io.BytesIO()
    wb.save(buf)
    return Response(buf.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="doomich-schedule-template.xlsx"'})


class LessonIn(BaseModel):
    group_id: uuid.UUID
    subgroup: str | None = None
    subject: str = Field(min_length=1, max_length=300)
    kind: str = "other"
    starts_at: datetime
    ends_at: datetime
    room: str | None = Field(default=None, max_length=100)
    note: str | None = Field(default=None, max_length=500)
    status: Literal["scheduled", "cancelled"] = "scheduled"


def _lesson_dict(x: Lesson) -> dict[str, Any]:
    return {"id": str(x.id), "group_id": str(x.group_id), "subgroup": x.subgroup, "subject": x.subject,
            "kind": x.kind, "starts_at": x.starts_at, "ends_at": x.ends_at, "room": x.room_text, "note": x.note,
            "status": x.status, "source_id": str(x.source_id) if x.source_id else None}


@router.get("/tenants/{tenant_id}/lessons")
async def list_lessons(tenant_id: uuid.UUID, group_id: uuid.UUID, date_from: date = Query(alias="from"),
                       date_to: date = Query(alias="to"), admin: CurrentAdmin = Depends(any_admin)
                       ) -> list[dict[str, Any]]:
    admin.check_tenant(tenant_id)
    async with get_db().sys_session() as s:
        tenant = await s.get(Tenant, tenant_id)
        assert tenant is not None
        start, _ = day_bounds(date_from, tenant.timezone)
        _, end = day_bounds(date_to, tenant.timezone)
        rows = (await s.scalars(select(Lesson).where(Lesson.tenant_id == tenant_id, Lesson.group_id == group_id,
                                                     Lesson.starts_at >= start, Lesson.starts_at < end)
                                .order_by(Lesson.starts_at).limit(3000))).all()
        return [_lesson_dict(x) for x in rows]


@router.post("/tenants/{tenant_id}/lessons", status_code=201)
async def create_lesson(tenant_id: uuid.UUID, body: LessonIn, admin: CurrentAdmin = Depends(any_admin)
                        ) -> dict[str, Any]:
    admin.check_tenant(tenant_id)
    if body.ends_at <= body.starts_at:
        raise AppError("конец раньше начала", code="bad_time")
    async with get_db().sys_session() as s:
        source = await sync.manual_source(s, tenant_id)
        x = Lesson(id=uuid.uuid4(), tenant_id=tenant_id, group_id=body.group_id, subgroup=body.subgroup,
                   subject=body.subject, kind=body.kind, starts_at=body.starts_at, ends_at=body.ends_at,
                   room_text=body.room, note=body.note, status=body.status, source_id=source.id,
                   ext_key=f"manual-{uuid.uuid4().hex[:12]}")
        s.add(x)
        await audit(s, admin, "lesson.create", object_type="lesson", object_id=x.id, tenant_id=tenant_id)
        await s.flush()
        await s.refresh(x)
        return _lesson_dict(x)


@router.patch("/lessons/{lesson_id}")
async def patch_lesson(lesson_id: uuid.UUID, body: LessonIn, admin: CurrentAdmin = Depends(any_admin)
                       ) -> dict[str, Any]:
    from doomich.models import ScheduleChange
    from doomich.schedule.sync import _lesson_snapshot

    async with get_db().sys_session() as s:
        x = await s.get(Lesson, lesson_id)
        if x is None:
            raise NotFound()
        admin.check_tenant(x.tenant_id)
        before = _lesson_snapshot(x)
        x.subject, x.kind, x.starts_at, x.ends_at = body.subject, body.kind, body.starts_at, body.ends_at
        x.room_text, x.note, x.status, x.subgroup = body.room, body.note, body.status, body.subgroup
        x.updated_at = utcnow()
        if x.starts_at.date() >= utcnow().date():
            s.add(ScheduleChange(tenant_id=x.tenant_id, group_id=x.group_id, ext_key=x.ext_key,
                                 change="cancelled" if body.status == "cancelled" else "modified", before=before,
                                 after=_lesson_snapshot(x), lesson_date=x.starts_at.date()))
        await audit(s, admin, "lesson.update", object_type="lesson", object_id=x.id, tenant_id=x.tenant_id)
        return _lesson_dict(x)


@router.delete("/lessons/{lesson_id}", status_code=204)
async def delete_lesson(lesson_id: uuid.UUID, admin: CurrentAdmin = Depends(any_admin)) -> None:
    async with get_db().sys_session() as s:
        x = await s.get(Lesson, lesson_id)
        if x is None:
            raise NotFound()
        admin.check_tenant(x.tenant_id)
        await s.delete(x)
        await audit(s, admin, "lesson.delete", object_type="lesson", object_id=lesson_id, tenant_id=x.tenant_id)


# --- Пользователи (модерация) -----------------------------------------------------


class BlockIn(BaseModel):
    login: str = Field(min_length=1, max_length=64)
    blocked: bool = True


@router.post("/tenants/{tenant_id}/users/block")
async def block_user(tenant_id: uuid.UUID, body: BlockIn, admin: CurrentAdmin = Depends(manager)) -> dict[str, Any]:
    """Блокировка по псевдониму (регламент 7). Кто стоит за псевдонимом, администратор не знает."""
    admin.check_tenant(tenant_id)
    async with get_db().sys_session() as s:
        user = await s.scalar(select(User).where(User.login_norm == normalize_login(body.login),
                                                 User.tenant_id == tenant_id))
        if user is None:
            raise NotFound("пользователь не найден")
        user.status = "blocked" if body.blocked else "active"
        await audit(s, admin, "user.block" if body.blocked else "user.unblock", object_type="user",
                    object_id=user.id, tenant_id=tenant_id)
        return {"login": user.login, "status": user.status}


# --- Статистика, оценки, статус ---------------------------------------------------


@router.get("/tenants/{tenant_id}/stats")
async def tenant_stats(tenant_id: uuid.UUID, admin: CurrentAdmin = Depends(any_admin)) -> dict[str, Any]:
    """Только агрегаты: число пользователей, активность, документы, доля голосовых запросов, оценки."""
    admin.check_tenant(tenant_id)
    async with get_db().sys_session() as s:
        users = await s.scalar(select(func.count()).select_from(User).where(User.tenant_id == tenant_id)) or 0
        wau = await s.scalar(select(func.count()).select_from(User).where(
            User.tenant_id == tenant_id, User.last_active_on >= utcnow().date() - timedelta(days=7))) or 0
        dau = await s.scalar(select(func.count()).select_from(User).where(
            User.tenant_id == tenant_id, User.last_active_on >= utcnow().date())) or 0
        docs = await s.scalar(select(func.count()).select_from(Document).where(Document.tenant_id == tenant_id)) or 0
        users_with_docs = await s.scalar(select(func.count(func.distinct(Document.user_id))).where(
            Document.tenant_id == tenant_id, Document.scope == "personal")) or 0
        msg_rows = (await s.execute(
            select(Message.mode, func.count()).join(User, User.id == Message.user_id)
            .where(User.tenant_id == tenant_id, Message.role == "user",
                   Message.created_at >= utcnow() - timedelta(days=7)).group_by(Message.mode)
        )).all()
        fb_rows = (await s.execute(select(Feedback.rating, func.count()).where(
            Feedback.tenant_id == tenant_id, Feedback.created_on >= utcnow().date() - timedelta(days=30))
            .group_by(Feedback.rating))).all()
    by_mode = {m: int(c) for m, c in msg_rows}
    fb = {int(r): int(c) for r, c in fb_rows}
    total_fb = sum(fb.values())
    total_msgs = sum(by_mode.values())
    return {
        "users": users, "dau": dau, "wau": wau, "wau_share": round(wau / users, 3) if users else 0,
        "documents": docs, "users_with_documents_share": round(users_with_docs / users, 3) if users else 0,
        "messages_7d": by_mode, "voice_share_7d": round(by_mode.get("voice", 0) / total_msgs, 3) if total_msgs else 0,
        "feedback_30d": {"up": fb.get(1, 0), "down": fb.get(-1, 0),
                         "up_share": round(fb.get(1, 0) / total_fb, 3) if total_fb else None},
    }


@router.get("/tenants/{tenant_id}/feedback")
async def list_feedback(tenant_id: uuid.UUID, rating: int | None = None, limit: int = Query(100, le=1000),
                        admin: CurrentAdmin = Depends(manager)) -> list[dict[str, Any]]:
    admin.check_tenant(tenant_id)
    async with get_db().sys_session() as s:
        stmt = select(Feedback).where(Feedback.tenant_id == tenant_id).order_by(Feedback.created_on.desc())
        if rating is not None:
            stmt = stmt.where(Feedback.rating == rating)
        rows = (await s.scalars(stmt.limit(limit))).all()
        return [{"id": str(f.id), "rating": f.rating, "comment": f.comment, "category": f.category,
                 "model_version": f.model_version, "mode": f.mode, "question": f.question, "answer": f.answer,
                 "created_on": f.created_on} for f in rows]


@router.get("/status")
async def status(admin: CurrentAdmin = Depends(any_admin)) -> dict[str, Any]:
    st = settings()
    ai = get_ai()
    out: dict[str, Any] = {"env": st.env, "mock_components": st.mock_components(), "time": utcnow()}
    queues: dict[str, int | None] = {}
    if not st.redis_url.startswith("memory://"):
        try:
            import redis.asyncio as redis

            r = redis.from_url(st.celery_broker_url or st.redis_url)
            for q in ("documents", "lectures", "schedule", "maintenance"):
                queues[q] = int(await r.llen(q))
            await r.aclose()
        except Exception:
            queues = {"error": None}
    out["queues"] = queues
    health = getattr(ai.llm, "health", None)
    out["llm_ok"] = bool(await health()) if health else None
    async with get_db().sys_session() as s:
        doc_rows = (await s.execute(select(Document.status, func.count()).group_by(Document.status))).all()
        out["documents"] = {k: int(v) for k, v in doc_rows}
        stmt = select(ScheduleSource)
        if not admin.is_super:
            stmt = stmt.where(ScheduleSource.tenant_id == admin.tenant_id)
        out["schedule_sources"] = [
            {"id": str(x.id), "tenant_id": str(x.tenant_id), "name": x.name, "kind": x.kind,
             "last_status": x.last_status, "last_sync_at": x.last_sync_at, "last_error": x.last_error}
            for x in (await s.scalars(stmt)).all() if x.kind != "manual"
        ]
    backup_file = Path(st.data_dir) / "backup-status.json"
    if backup_file.exists():
        try:
            out["backup"] = json.loads(backup_file.read_text())
        except json.JSONDecodeError:
            out["backup"] = {"error": "bad status file"}
    out["grafana_url"] = (st.public_base_url.rstrip("/") + "/grafana/")
    return out


@router.get("/audit")
async def audit_log(tenant_id: uuid.UUID | None = None, limit: int = Query(200, le=2000),
                    admin: CurrentAdmin = Depends(manager)) -> list[dict[str, Any]]:
    scope = admin.scope_tenant(tenant_id)
    async with get_db().sys_session() as s:
        stmt = select(AdminAudit, Admin.login).outerjoin(Admin, Admin.id == AdminAudit.admin_id) \
            .order_by(AdminAudit.created_at.desc()).limit(limit)
        if scope is not None:
            stmt = stmt.where(AdminAudit.tenant_id == scope)
        rows = (await s.execute(stmt)).all()
        return [{"id": a.id, "admin": login, "action": a.action, "object_type": a.object_type,
                 "object_id": a.object_id, "tenant_id": str(a.tenant_id) if a.tenant_id else None,
                 "details": a.details, "created_at": a.created_at} for a, login in rows]


# --- Релизы приложений ----------------------------------------------------------


class ReleaseIn(BaseModel):
    app: Literal["mobile", "desktop"]
    platform: str = Field(max_length=32)
    channel: Literal["stable", "beta"] = "stable"
    version: str = Field(max_length=32)
    build: int = Field(ge=1)
    url: str = Field(max_length=500)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    signature: str | None = Field(default=None, max_length=500)
    min_supported_build: int = 0
    notes_ru: str | None = Field(default=None, max_length=4000)
    notes_en: str | None = Field(default=None, max_length=4000)


@router.get("/releases")
async def list_releases(admin: CurrentAdmin = Depends(any_admin)) -> list[dict[str, Any]]:
    async with get_db().sys_session() as s:
        rows = (await s.scalars(select(AppRelease).order_by(AppRelease.published_at.desc()).limit(200))).all()
        return [{"id": str(r.id), "app": r.app, "platform": r.platform, "channel": r.channel, "version": r.version,
                 "build": r.build, "url": r.url, "sha256": r.sha256, "min_supported_build": r.min_supported_build,
                 "published_at": r.published_at} for r in rows]


@router.post("/releases", status_code=201)
async def create_release(body: ReleaseIn, admin: CurrentAdmin = Depends(superadmin)) -> dict[str, Any]:
    async with get_db().sys_session() as s:
        r = AppRelease(id=uuid.uuid4(), **body.model_dump())
        s.add(r)
        await audit(s, admin, "release.create", object_type="release", object_id=r.id,
                    details={"app": body.app, "platform": body.platform, "version": body.version})
        return {"id": str(r.id)}


# --- Привязки моделей (ML-платформа) ------------------------------------------------


class BindingIn(BaseModel):
    tenant_id: uuid.UUID | None = None
    campus_id: uuid.UUID | None = None
    component: Literal["llm_adapter", "asr_profile", "tts_voice", "kws_model", "vpr_index", "embed_model"]
    model_ref: str = Field(min_length=1, max_length=300)
    stage: Literal["canary", "production"] = "production"
    traffic_pct: int = Field(default=100, ge=0, le=100)
    params: dict[str, Any] = Field(default_factory=dict)


def _binding_dict(b: ModelBinding) -> dict[str, Any]:
    return {"id": str(b.id), "tenant_id": str(b.tenant_id) if b.tenant_id else None,
            "campus_id": str(b.campus_id) if b.campus_id else None, "component": b.component,
            "model_ref": b.model_ref, "stage": b.stage, "traffic_pct": b.traffic_pct, "params": b.params,
            "updated_at": b.updated_at}


@router.get("/bindings")
async def list_bindings(tenant_id: uuid.UUID | None = None, admin: CurrentAdmin = Depends(any_admin)
                        ) -> list[dict[str, Any]]:
    scope = admin.scope_tenant(tenant_id)
    async with get_db().sys_session() as s:
        stmt = select(ModelBinding).order_by(ModelBinding.component)
        if scope is not None:
            stmt = stmt.where((ModelBinding.tenant_id == scope) | ModelBinding.tenant_id.is_(None))
        return [_binding_dict(b) for b in (await s.scalars(stmt)).all()]


@router.put("/bindings")
async def put_binding(body: BindingIn, admin: CurrentAdmin = Depends(superadmin)) -> dict[str, Any]:
    """Создаёт или заменяет привязку для (компонент, вуз, кампус, стадия)."""
    async with get_db().sys_session() as s:
        stmt = select(ModelBinding).where(
            ModelBinding.component == body.component, ModelBinding.stage == body.stage,
            ModelBinding.tenant_id.is_(None) if body.tenant_id is None else ModelBinding.tenant_id == body.tenant_id,
            ModelBinding.campus_id.is_(None) if body.campus_id is None else ModelBinding.campus_id == body.campus_id,
        )
        b = await s.scalar(stmt)
        if b is None:
            b = ModelBinding(id=uuid.uuid4(), **body.model_dump())
            s.add(b)
        else:
            b.model_ref, b.traffic_pct, b.params, b.updated_at = body.model_ref, body.traffic_pct, body.params, utcnow()
        await audit(s, admin, "binding.put", object_type="binding", object_id=b.id, tenant_id=body.tenant_id,
                    details={"component": body.component, "model_ref": body.model_ref, "stage": body.stage})
        await s.flush()
        await s.refresh(b)
        result = _binding_dict(b)
    bindings_mod.invalidate()
    return result


@router.delete("/bindings/{binding_id}", status_code=204)
async def delete_binding(binding_id: uuid.UUID, admin: CurrentAdmin = Depends(superadmin)) -> None:
    async with get_db().sys_session() as s:
        await s.execute(delete(ModelBinding).where(ModelBinding.id == binding_id))
        await audit(s, admin, "binding.delete", object_type="binding", object_id=binding_id)
    bindings_mod.invalidate()


# --- Администраторы -----------------------------------------------------------------


class AdminIn(BaseModel):
    login: str = Field(pattern=r"^[a-z0-9._-]{3,64}$")
    password: str = Field(min_length=12, max_length=128)
    role: Literal["superadmin", "tenant_admin", "operator"]
    tenant_id: uuid.UUID | None = None


class AdminPatch(BaseModel):
    disabled: bool | None = None
    role: Literal["superadmin", "tenant_admin", "operator"] | None = None
    reset_totp: bool = False
    password: str | None = Field(default=None, min_length=12, max_length=128)


@router.get("/admins")
async def list_admins(admin: CurrentAdmin = Depends(superadmin)) -> list[dict[str, Any]]:
    async with get_db().sys_session() as s:
        return [_admin_dict(a) for a in (await s.scalars(select(Admin).order_by(Admin.login))).all()]


@router.post("/admins", status_code=201)
async def create_admin(body: AdminIn, admin: CurrentAdmin = Depends(superadmin)) -> dict[str, Any]:
    if body.role != "superadmin" and body.tenant_id is None:
        raise AppError("администратору вуза нужен tenant_id", code="tenant_required")
    async with get_db().sys_session() as s:
        if await s.scalar(select(Admin.id).where(Admin.login == body.login)):
            raise Conflict("логин занят", code="login_taken")
        a = Admin(id=uuid.uuid4(), login=body.login, password_hash=hash_secret(body.password), role=body.role,
                  tenant_id=body.tenant_id if body.role != "superadmin" else None)
        s.add(a)
        await audit(s, admin, "admin.create", object_type="admin", object_id=a.id, tenant_id=a.tenant_id)
        return _admin_dict(a)


@router.patch("/admins/{admin_id}")
async def patch_admin(admin_id: uuid.UUID, body: AdminPatch, admin: CurrentAdmin = Depends(superadmin)
                      ) -> dict[str, Any]:
    async with get_db().sys_session() as s:
        a = await s.get(Admin, admin_id)
        if a is None:
            raise NotFound()
        if body.disabled is not None:
            a.disabled = body.disabled
        if body.role is not None:
            a.role = body.role
        if body.reset_totp:
            a.totp_enabled, a.totp_secret_enc = False, None
        if body.password:
            a.password_hash = hash_secret(body.password)
        await audit(s, admin, "admin.update", object_type="admin", object_id=a.id,
                    details={"disabled": body.disabled, "role": body.role, "reset_totp": body.reset_totp})
        return _admin_dict(a)

