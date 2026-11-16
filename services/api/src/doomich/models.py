"""Таблицы Core API.

Схема создаётся миграциями Alembic (migrations/versions), а не create_all:
политики RLS и сгенерированные колонки там описаны явным SQL.
Здесь модели для работы с данными в коде. При изменении таблицы правим оба места,
тест test_schema_matches_models проверяет, что они не разъехались.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    Computed,
    ForeignKey,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from doomich.db import Base

EMBED_DIM = 1024


def uid() -> uuid.UUID:
    return uuid.uuid4()


# --- Вузы и кампусы ---------------------------------------------------------


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(Text)
    short_name: Mapped[str | None] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(Text, default="Europe/Moscow")
    default_locale: Mapped[str] = mapped_column(String(8), default="ru")
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Campus(Base):
    __tablename__ = "campuses"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None]
    lon: Mapped[float | None]
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class AcademicTerm(Base):
    __tablename__ = "academic_terms"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text)
    starts_on: Mapped[date]
    ends_on: Mapped[date]
    first_week_odd: Mapped[bool] = mapped_column(Boolean, default=True)
    holidays: Mapped[list[Any]] = mapped_column(JSONB, default=list)


# --- Расписание -------------------------------------------------------------


class StudyGroup(Base):
    __tablename__ = "study_groups"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(Text)
    faculty: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    subgroups: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    external_id: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Teacher(Base):
    __tablename__ = "teachers"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(Text)
    display_name: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text)


class Room(Base):
    __tablename__ = "rooms"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    campus_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("campuses.id", ondelete="SET NULL"))
    building: Mapped[str] = mapped_column(Text, default="")
    number: Mapped[str] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(Text)
    campus_room_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class ScheduleSource(Base):
    __tablename__ = "schedule_sources"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    require_review_on_spike: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[datetime | None]
    last_status: Mapped[str | None] = mapped_column(Text)
    last_error: Mapped[str | None] = mapped_column(Text)
    last_count: Mapped[int | None] = mapped_column(Integer)
    pending_snapshot: Mapped[list[Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("study_groups.id", ondelete="CASCADE"))
    subgroup: Mapped[str | None] = mapped_column(Text)
    subject: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text, default="other")
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime]
    room_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("rooms.id", ondelete="SET NULL"))
    room_text: Mapped[str | None] = mapped_column(Text)
    teacher_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teachers.id", ondelete="SET NULL"))
    source_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("schedule_sources.id", ondelete="SET NULL"))
    ext_key: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="scheduled")
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ScheduleChange(Base):
    __tablename__ = "schedule_changes"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("study_groups.id", ondelete="CASCADE"))
    ext_key: Mapped[str] = mapped_column(Text)
    change: Mapped[str] = mapped_column(Text)
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    lesson_date: Mapped[date]
    detected_at: Mapped[datetime] = mapped_column(server_default=func.now())


# --- Аккаунты ---------------------------------------------------------------


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    login: Mapped[str] = mapped_column(Text)
    login_norm: Mapped[str] = mapped_column(Text, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    recovery_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Text, default="student")
    group_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("study_groups.id", ondelete="SET NULL"))
    subgroup: Mapped[str | None] = mapped_column(Text)
    locale: Mapped[str] = mapped_column(String(8), default="ru")
    history_days: Mapped[int] = mapped_column(Integer, default=90)
    is_beta: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(Text, default="active")
    created_on: Mapped[date] = mapped_column(server_default=func.current_date())
    last_active_on: Mapped[date] = mapped_column(server_default=func.current_date())


class UserKey(Base):
    __tablename__ = "user_keys"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    kid: Mapped[str] = mapped_column(Text)
    wrapped: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    family_id: Mapped[uuid.UUID]
    token_hash: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    platform: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime]
    rotated_at: Mapped[datetime | None]
    revoked_at: Mapped[datetime | None]


class InviteBatch(Base):
    __tablename__ = "invite_batches"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text, default="register")
    role: Mapped[str] = mapped_column(Text, default="student")
    group_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("study_groups.id", ondelete="SET NULL"))
    is_beta: Mapped[bool] = mapped_column(Boolean, default=False)
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    expires_on: Mapped[date | None]
    code_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class InviteCode(Base):
    __tablename__ = "invite_codes"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invite_batches.id", ondelete="CASCADE"))
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    code_hash: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    code_enc: Mapped[bytes] = mapped_column(LargeBinary)
    uses: Mapped[int] = mapped_column(Integer, default=0)
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    expires_on: Mapped[date | None]
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


# --- Чаты -------------------------------------------------------------------


class Chat(Base):
    __tablename__ = "chats"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    title_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    document_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    lecture_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    course_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    summary_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(Text)
    content_enc: Mapped[bytes] = mapped_column(LargeBinary)
    sources_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    mode: Mapped[str] = mapped_column(Text, default="text")
    model_version: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    rating: Mapped[int] = mapped_column(SmallInteger)
    comment: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)
    model_version: Mapped[str | None] = mapped_column(Text)
    mode: Mapped[str | None] = mapped_column(Text)
    question: Mapped[str | None] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text)
    created_on: Mapped[date] = mapped_column(server_default=func.current_date())


# --- Документы --------------------------------------------------------------


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    scope: Mapped[str] = mapped_column(Text, default="personal")
    course_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    title_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    title: Mapped[str | None] = mapped_column(Text)
    mime: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    pages: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(Text, default="uploaded")
    error: Mapped[str | None] = mapped_column(Text)
    storage_key: Mapped[str | None] = mapped_column(Text)
    file_key_wrapped: Mapped[bytes | None] = mapped_column(LargeBinary)
    valid_as_of: Mapped[date | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    scope: Mapped[str] = mapped_column(Text)
    course_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    ord: Mapped[int] = mapped_column(Integer)
    page: Mapped[int | None] = mapped_column(Integer)
    sheet: Mapped[str | None] = mapped_column(Text)
    section: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBED_DIM))
    fts: Mapped[Any] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('russian', coalesce(section, '') || ' ' || body) || to_tsvector('english', body)",
            persisted=True,
        ),
        deferred=True,
    )
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


# --- Администрирование ------------------------------------------------------


class Admin(Base):
    __tablename__ = "admins"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    login: Mapped[str] = mapped_column(Text, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    totp_secret_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(Text)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_login_at: Mapped[datetime | None]


class AdminAudit(Base):
    __tablename__ = "admin_audit"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    admin_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(Text)
    object_type: Mapped[str | None] = mapped_column(Text)
    object_id: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ModelBinding(Base):
    __tablename__ = "model_bindings"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    campus_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("campuses.id", ondelete="CASCADE"))
    component: Mapped[str] = mapped_column(Text)
    model_ref: Mapped[str] = mapped_column(Text)
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    stage: Mapped[str] = mapped_column(Text, default="production")
    traffic_pct: Mapped[int] = mapped_column(Integer, default=100)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class AppRelease(Base):
    __tablename__ = "app_releases"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uid)
    app: Mapped[str] = mapped_column(Text)
    platform: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(Text, default="stable")
    version: Mapped[str] = mapped_column(Text)
    build: Mapped[int] = mapped_column(Integer)
    url: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(Text)
    signature: Mapped[str | None] = mapped_column(Text)
    min_supported_build: Mapped[int] = mapped_column(Integer, default=0)
    notes_ru: Mapped[str | None] = mapped_column(Text)
    notes_en: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UsageCounter(Base):
    __tablename__ = "usage_counters"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    period: Mapped[str] = mapped_column(Text, primary_key=True)
    metric: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[int] = mapped_column(BigInteger, default=0)
