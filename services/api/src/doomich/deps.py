"""Общие зависимости FastAPI: текущий пользователь, вуз, ключ шифрования."""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from fastapi import Depends, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from doomich.common.errors import Forbidden, Unauthorized
from doomich.common.timeutil import today_utc, utcnow
from doomich.db import get_db
from doomich.models import Session, Tenant, User, UserKey
from doomich.security import crypto
from doomich.security.tokens import read_access


@dataclass(frozen=True)
class TenantInfo:
    id: uuid.UUID
    slug: str
    name: str
    timezone: str
    default_locale: str
    settings: dict[str, Any] = field(default_factory=dict)
    short_name: str | None = None

    def feature(self, name: str, default: bool = True) -> bool:
        return bool(self.settings.get("features", {}).get(name, default))

    @property
    def teacher_names_mode(self) -> str:
        return str(self.settings.get("teacher_names_mode", "hide"))


@dataclass(frozen=True)
class CurrentUser:
    id: uuid.UUID
    tenant: TenantInfo
    role: str
    session_id: uuid.UUID
    login: str
    locale: str
    group_id: uuid.UUID | None
    subgroup: str | None
    history_days: int
    is_beta: bool

    @property
    def tenant_id(self) -> uuid.UUID:
        return self.tenant.id


_tenant_cache: dict[uuid.UUID, tuple[float, TenantInfo]] = {}
TENANT_TTL = 60.0


def tenant_from_row(t: Tenant) -> TenantInfo:
    return TenantInfo(id=t.id, slug=t.slug, name=t.name, timezone=t.timezone,
                      default_locale=t.default_locale, settings=dict(t.settings or {}), short_name=t.short_name)


async def load_tenant(tenant_id: uuid.UUID) -> TenantInfo:
    now = time.monotonic()
    cached = _tenant_cache.get(tenant_id)
    if cached and cached[0] > now:
        return cached[1]
    async with get_db().sys_session() as s:
        t = await s.get(Tenant, tenant_id)
        if t is None or not t.is_active:
            raise Forbidden("вуз отключён", code="tenant_inactive")
        info = tenant_from_row(t)
    _tenant_cache[tenant_id] = (now + TENANT_TTL, info)
    return info


def invalidate_tenant(tenant_id: uuid.UUID) -> None:
    _tenant_cache.pop(tenant_id, None)


def bearer(request: Request) -> str:
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    raise Unauthorized("нужен токен доступа", code="token_missing")


async def authenticate(token: str) -> CurrentUser:
    claims = read_access(token)
    async with get_db().sys_session() as s:
        row = (
            await s.execute(
                select(
                    User.id, User.tenant_id, User.role, User.login, User.locale, User.group_id, User.subgroup,
                    User.history_days, User.is_beta, User.status, User.last_active_on, Session.revoked_at,
                    Session.expires_at,
                )
                .join(Session, Session.user_id == User.id)
                .where(User.id == claims.user_id, Session.id == claims.session_id)
            )
        ).first()
        if row is None or row.revoked_at is not None or row.expires_at < utcnow():
            raise Unauthorized("сессия завершена", code="session_revoked")
        if row.status != "active":
            raise Forbidden("аккаунт заблокирован", code="account_blocked")
        if row.last_active_on != today_utc():
            await s.execute(update(User).where(User.id == row.id).values(last_active_on=today_utc()))
    tenant = await load_tenant(row.tenant_id)
    return CurrentUser(
        id=row.id, tenant=tenant, role=row.role, session_id=claims.session_id, login=row.login,
        locale=row.locale, group_id=row.group_id, subgroup=row.subgroup, history_days=row.history_days,
        is_beta=row.is_beta,
    )


async def current_user(request: Request) -> CurrentUser:
    user = await authenticate(bearer(request))
    request.state.user_id = user.id
    return user


def require_role(*roles: str):
    async def checker(user: CurrentUser = Depends(current_user)) -> CurrentUser:
        if user.role not in roles:
            raise Forbidden("недостаточно прав", code="role_required")
        return user

    return checker


async def user_db(user: CurrentUser = Depends(current_user)) -> AsyncIterator[AsyncSession]:
    async with get_db().user_session(user.id, user.tenant_id) as s:
        yield s


# Кэш расшифрованных ключей пользователей: экономит запрос к БД на каждое сообщение.
_key_cache: dict[uuid.UUID, tuple[float, bytes]] = {}
KEY_TTL = 300.0


async def user_cipher_for(session: AsyncSession, user_id: uuid.UUID) -> crypto.UserCipher:
    now = time.monotonic()
    cached = _key_cache.get(user_id)
    if cached and cached[0] > now:
        return crypto.UserCipher(cached[1])
    row = await session.get(UserKey, user_id)
    if row is None:
        raise Unauthorized("нет ключа пользователя", code="key_missing")
    key = crypto.unwrap_user_key(user_id, row.kid, row.wrapped)
    _key_cache[user_id] = (now + KEY_TTL, key)
    if len(_key_cache) > 10000:
        for k in list(_key_cache)[:1000]:
            _key_cache.pop(k, None)
    return crypto.UserCipher(key)


def forget_user_key(user_id: uuid.UUID) -> None:
    _key_cache.pop(user_id, None)
