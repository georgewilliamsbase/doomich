"""Аутентификация администраторов: пароль + TOTP, отдельные токены, журнал действий.

Админ-API доступно только через VPN (это обеспечивает nginx), здесь вторая линия защиты.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import pyotp
from fastapi import Depends, Request
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from doomich.common.errors import Forbidden, Unauthorized
from doomich.db import get_db
from doomich.models import Admin, AdminAudit
from doomich.security import crypto
from doomich.security.tokens import AdminClaims, read_admin

TOTP_PURPOSE = "admin-totp"
ISSUER = "Doomich Admin"


@dataclass(frozen=True)
class CurrentAdmin:
    id: uuid.UUID
    login: str
    role: str
    tenant_id: uuid.UUID | None

    @property
    def is_super(self) -> bool:
        return self.role == "superadmin"

    def check_tenant(self, tenant_id: uuid.UUID | None) -> None:
        if self.is_super:
            return
        if tenant_id is None or tenant_id != self.tenant_id:
            raise Forbidden("нет доступа к этому вузу", code="tenant_forbidden")

    def scope_tenant(self, requested: uuid.UUID | None) -> uuid.UUID | None:
        """Вуз, в рамках которого выполняется запрос."""
        if self.is_super:
            return requested
        return self.tenant_id


def totp_for(admin: Admin) -> pyotp.TOTP | None:
    if admin.totp_secret_enc is None:
        return None
    secret = crypto.open_system(TOTP_PURPOSE, admin.totp_secret_enc).decode()
    return pyotp.TOTP(secret)


def new_totp_secret() -> tuple[str, bytes]:
    secret = pyotp.random_base32()
    return secret, crypto.seal_system(TOTP_PURPOSE, secret.encode())


def provisioning_uri(secret: str, login: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=login, issuer_name=ISSUER)


async def current_admin(request: Request) -> CurrentAdmin:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise Unauthorized("нужен токен администратора", code="token_missing")
    claims: AdminClaims = read_admin(header[7:].strip())
    async with get_db().sys_session() as s:
        admin = await s.get(Admin, claims.admin_id)
        if admin is None or admin.disabled:
            raise Unauthorized("учётная запись отключена", code="admin_disabled")
        return CurrentAdmin(id=admin.id, login=admin.login, role=admin.role, tenant_id=admin.tenant_id)


def require(*roles: str):
    async def checker(admin: CurrentAdmin = Depends(current_admin)) -> CurrentAdmin:
        if admin.role not in roles:
            raise Forbidden("недостаточно прав", code="admin_role")
        return admin

    return checker


any_admin = require("superadmin", "tenant_admin", "operator")
manager = require("superadmin", "tenant_admin")
superadmin = require("superadmin")


async def audit(s: AsyncSession, admin: CurrentAdmin, action: str, *, object_type: str | None = None,
                object_id: Any = None, tenant_id: uuid.UUID | None = None, details: dict[str, Any] | None = None
                ) -> None:
    await s.execute(insert(AdminAudit).values(
        admin_id=admin.id, tenant_id=tenant_id or admin.tenant_id, action=action, object_type=object_type,
        object_id=str(object_id) if object_id is not None else None, details=details or {},
    ))
