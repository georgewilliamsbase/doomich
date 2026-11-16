from __future__ import annotations

import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Locale = Literal["ru", "en"]
Platform = Literal["android", "ios", "windows", "linux", "macos", "web", "other"]


class InviteCheckIn(BaseModel):
    code: str = Field(min_length=8, max_length=16)


class TenantBrief(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    short_name: str | None = None
    timezone: str


class GroupBrief(BaseModel):
    id: uuid.UUID
    code: str
    name: str | None = None


class InviteCheckOut(BaseModel):
    tenant: TenantBrief
    role: str
    group: GroupBrief | None = None


class LoginCheckOut(BaseModel):
    valid: bool
    available: bool
    problems: list[str] = []
    warnings: list[str] = []


class RegisterIn(BaseModel):
    invite_code: str = Field(min_length=8, max_length=16)
    login: str = Field(min_length=3, max_length=24)
    password: str = Field(min_length=10, max_length=128)
    locale: Locale = "ru"
    platform: Platform | None = None


class LoginIn(BaseModel):
    login: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)
    platform: Platform | None = None


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=200)


class Tokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105
    expires_in: int
    refresh_expires_in: int


class MeOut(BaseModel):
    id: uuid.UUID
    login: str
    role: str
    tenant: TenantBrief
    group: GroupBrief | None = None
    subgroup: str | None = None
    locale: str
    history_days: int
    is_beta: bool
    created_on: date
    features: dict[str, bool] = {}


class AuthOut(BaseModel):
    tokens: Tokens
    user: MeOut


class RegisterOut(AuthOut):
    recovery_code: str


class RecoverIn(BaseModel):
    login: str = Field(min_length=1, max_length=64)
    recovery_code: str = Field(min_length=20, max_length=40)
    new_password: str = Field(min_length=10, max_length=128)
    platform: Platform | None = None


class RecoverOut(AuthOut):
    recovery_code: str


class MePatch(BaseModel):
    locale: Locale | None = None
    group_id: uuid.UUID | None = None
    clear_group: bool = False
    subgroup: str | None = Field(default=None, max_length=16)
    history_days: Literal[0, 7, 30, 90] | None = None


class PasswordChangeIn(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


class PasswordIn(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class RecoveryCodeOut(BaseModel):
    recovery_code: str


class RoleUpgradeIn(BaseModel):
    code: str = Field(min_length=8, max_length=16)


class SessionOut(BaseModel):
    id: uuid.UUID
    platform: str | None
    created_on: date
    current: bool


class QrStartOut(BaseModel):
    token: str
    expires_in: int


class QrApproveIn(BaseModel):
    token: str = Field(min_length=10, max_length=400)


class QrPollIn(BaseModel):
    token: str = Field(min_length=10, max_length=400)
