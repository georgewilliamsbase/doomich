"""Токены доступа.

Access-токен: JWT (HS256) на 15 минут. Refresh-токен: случайная строка,
в БД лежит только её SHA-256. Админские токены отличаются полем typ.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import jwt

from doomich.common.errors import Unauthorized
from doomich.common.timeutil import utcnow
from doomich.config import settings

ALGO = "HS256"


@dataclass(frozen=True)
class AccessClaims:
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role: str
    session_id: uuid.UUID


@dataclass(frozen=True)
class AdminClaims:
    admin_id: uuid.UUID
    role: str
    tenant_id: uuid.UUID | None


def _encode(payload: dict[str, Any], ttl_sec: int) -> str:
    now = utcnow()
    payload = {**payload, "iat": int(now.timestamp()), "exp": int((now + timedelta(seconds=ttl_sec)).timestamp())}
    return jwt.encode(payload, settings().jwt_secret.get_secret_value(), algorithm=ALGO)


def _decode(token: str, typ: str) -> dict[str, Any]:
    try:
        data = jwt.decode(token, settings().jwt_secret.get_secret_value(), algorithms=[ALGO])
    except jwt.ExpiredSignatureError as e:
        raise Unauthorized("token expired", code="token_expired") from e
    except jwt.PyJWTError as e:
        raise Unauthorized("invalid token", code="token_invalid") from e
    if data.get("typ") != typ:
        raise Unauthorized("wrong token type", code="token_invalid")
    return data


def issue_access(claims: AccessClaims) -> str:
    return _encode(
        {
            "typ": "access",
            "sub": str(claims.user_id),
            "tid": str(claims.tenant_id),
            "role": claims.role,
            "sid": str(claims.session_id),
        },
        settings().access_token_ttl_sec,
    )


def read_access(token: str) -> AccessClaims:
    d = _decode(token, "access")
    try:
        return AccessClaims(
            user_id=uuid.UUID(d["sub"]),
            tenant_id=uuid.UUID(d["tid"]),
            role=str(d["role"]),
            session_id=uuid.UUID(d["sid"]),
        )
    except (KeyError, ValueError) as e:
        raise Unauthorized("invalid token", code="token_invalid") from e


def issue_admin(claims: AdminClaims) -> str:
    return _encode(
        {
            "typ": "admin",
            "sub": str(claims.admin_id),
            "role": claims.role,
            "tid": str(claims.tenant_id) if claims.tenant_id else None,
        },
        settings().admin_token_ttl_sec,
    )


def read_admin(token: str) -> AdminClaims:
    d = _decode(token, "admin")
    tid = d.get("tid")
    return AdminClaims(admin_id=uuid.UUID(d["sub"]), role=str(d["role"]), tenant_id=uuid.UUID(tid) if tid else None)


def issue_short(purpose: str, subject: str, ttl_sec: int, **extra: Any) -> str:
    """Короткоживущий токен для служебных целей (например, вход по QR)."""
    return _encode({"typ": purpose, "sub": subject, **extra}, ttl_sec)


def read_short(token: str, purpose: str) -> dict[str, Any]:
    return _decode(token, purpose)


def new_refresh_token() -> tuple[str, bytes]:
    token = secrets.token_urlsafe(32)
    return token, hash_refresh(token)


def hash_refresh(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()
