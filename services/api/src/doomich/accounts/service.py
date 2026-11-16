"""Аккаунты без персональных данных: регистрация, вход, сессии, восстановление."""

from __future__ import annotations

import json
import re
import secrets
import unicodedata
import uuid
from datetime import timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from doomich.accounts import invites
from doomich.accounts.schemas import GroupBrief, MeOut, TenantBrief, Tokens
from doomich.common.errors import AppError, Conflict, Unauthorized, ValidationFailed
from doomich.common.timeutil import utcnow
from doomich.config import settings
from doomich.db import get_db
from doomich.deps import forget_user_key, load_tenant
from doomich.models import Document, StudyGroup, Tenant, User, UserKey
from doomich.models import Session as DbSession
from doomich.observability.metrics import REGISTRATIONS
from doomich.security import crypto, kv
from doomich.security.passwords import (
    dummy_verify,
    generate_recovery_code,
    hash_secret,
    needs_rehash,
    normalize_recovery_code,
    password_problems,
    verify_secret,
)
from doomich.security.tokens import AccessClaims, hash_refresh, issue_access, new_refresh_token
from doomich.storage.files import get_storage

LOGIN_RE = re.compile(r"^[0-9A-Za-zА-Яа-яЁё][0-9A-Za-zА-Яа-яЁё_.\-]{2,23}$")
# Две части с заглавных кириллических букв подряд: ИванПетров, Иван_Петров, Petrov.Ivan
NAME_LIKE = re.compile(r"^[А-ЯЁ][а-яё]{1,}[_.\- ]?[А-ЯЁ][а-яё]{2,}", re.U)
NAME_LIKE_LAT = re.compile(r"^[A-Z][a-z]{1,}[_.\- ]?[A-Z][a-z]{2,}$")
COMMON_FIRST_NAMES = {
    "александр", "алексей", "андрей", "анна", "анастасия", "дмитрий", "екатерина", "елена", "иван",
    "мария", "михаил", "наталья", "ольга", "сергей", "татьяна", "юлия", "артём", "артем", "дарья",
    "максим", "никита", "полина", "софия", "кирилл", "виктория", "егор", "алина", "илья", "ксения",
}


def normalize_login(login: str) -> str:
    return unicodedata.normalize("NFKC", login).strip().lower().replace("ё", "е")


def login_problems(login: str) -> list[str]:
    login = unicodedata.normalize("NFKC", login).strip()
    if not LOGIN_RE.match(login):
        return ["invalid_format"]
    return []


def login_warnings(login: str) -> list[str]:
    login = unicodedata.normalize("NFKC", login).strip()
    low = normalize_login(login)
    if NAME_LIKE.match(login) or NAME_LIKE_LAT.match(login):
        return ["looks_like_name"]
    if any(low.startswith(n) and len(low) > len(n) + 2 for n in COMMON_FIRST_NAMES):
        return ["looks_like_name"]
    if re.search(r"\d{10,}", low):
        return ["looks_like_phone"]
    if "@" in login:
        return ["looks_like_email"]
    return []


async def login_available(login: str) -> bool:
    async with get_db().sys_session() as s:
        found = await s.scalar(select(User.id).where(User.login_norm == normalize_login(login)))
    return found is None


async def _open_session(s: AsyncSession, user: User, platform: str | None,
                        family_id: uuid.UUID | None = None) -> Tokens:
    st = settings()
    refresh, refresh_hash = new_refresh_token()
    sess = DbSession(
        id=uuid.uuid4(), user_id=user.id, family_id=family_id or uuid.uuid4(), token_hash=refresh_hash,
        platform=platform, expires_at=utcnow() + timedelta(days=st.refresh_token_ttl_days),
    )
    s.add(sess)
    await s.flush()
    access = issue_access(AccessClaims(user_id=user.id, tenant_id=user.tenant_id, role=user.role,
                                       session_id=sess.id))
    return Tokens(access_token=access, refresh_token=refresh, expires_in=st.access_token_ttl_sec,
                  refresh_expires_in=st.refresh_token_ttl_days * 86400)


async def me_out(s: AsyncSession, user: User) -> MeOut:
    tenant = await s.get(Tenant, user.tenant_id)
    assert tenant is not None
    group = await s.get(StudyGroup, user.group_id) if user.group_id else None
    info = await load_tenant(user.tenant_id)
    features = {k: bool(v) for k, v in (info.settings.get("features") or {}).items()}
    return MeOut(
        id=user.id, login=user.login, role=user.role,
        tenant=TenantBrief(id=tenant.id, slug=tenant.slug, name=tenant.name, short_name=tenant.short_name,
                           timezone=tenant.timezone),
        group=GroupBrief(id=group.id, code=group.code, name=group.name) if group else None,
        subgroup=user.subgroup, locale=user.locale, history_days=user.history_days, is_beta=user.is_beta,
        created_on=user.created_on, features=features,
    )


async def register(*, invite_code: str, login: str, password: str, locale: str,
                   platform: str | None) -> tuple[Tokens, MeOut, str]:
    login = unicodedata.normalize("NFKC", login).strip()
    problems = login_problems(login)
    if problems:
        raise ValidationFailed("псевдоним не подходит", code="login_invalid", details={"problems": problems})
    pw_problems = password_problems(password, login)
    if pw_problems:
        raise ValidationFailed("пароль слишком простой", code="password_weak", details={"problems": pw_problems})
    recovery = generate_recovery_code()
    async with get_db().sys_session() as s:
        info = await invites.find_valid(s, invite_code, lock=True)
        exists = await s.scalar(select(User.id).where(User.login_norm == normalize_login(login)))
        if exists:
            raise Conflict("псевдоним занят", code="login_taken")
        user = User(
            id=uuid.uuid4(), tenant_id=info.batch.tenant_id, login=login, login_norm=normalize_login(login),
            password_hash=hash_secret(password), recovery_hash=hash_secret(normalize_recovery_code(recovery)),
            role=info.batch.role, group_id=info.batch.group_id, locale=locale, is_beta=info.batch.is_beta,
        )
        s.add(user)
        await s.flush()
        kid, wrapped = crypto.wrap_user_key(user.id, crypto.new_data_key())
        s.add(UserKey(user_id=user.id, kid=kid, wrapped=wrapped))
        info.code.uses += 1
        tokens = await _open_session(s, user, platform)
        await s.flush()
        await s.refresh(user)
        me = await me_out(s, user)
    REGISTRATIONS.labels(role=user.role).inc()
    return tokens, me, recovery


async def login(*, login: str, password: str, platform: str | None, client_key: str) -> tuple[Tokens, MeOut]:
    st = settings()
    norm = normalize_login(login)
    await kv.hit(f"login:{kv.anon(norm)}", st.login_attempts_per_minute, 60)
    await kv.hit(f"login:{kv.anon(norm)}", st.login_attempts_per_hour, 3600)
    await kv.hit(f"login-client:{kv.anon(client_key)}", st.login_attempts_per_hour * 3, 3600)
    async with get_db().sys_session() as s:
        user = await s.scalar(select(User).where(User.login_norm == norm))
        if user is None:
            dummy_verify(password)
            raise Unauthorized("неверный псевдоним или пароль", code="bad_credentials")
        if not verify_secret(user.password_hash, password):
            raise Unauthorized("неверный псевдоним или пароль", code="bad_credentials")
        if user.status != "active":
            raise AppError("аккаунт заблокирован", code="account_blocked", status_code=403)
        if needs_rehash(user.password_hash):
            user.password_hash = hash_secret(password)
        tokens = await _open_session(s, user, platform)
        me = await me_out(s, user)
    return tokens, me


async def refresh(refresh_token: str) -> Tokens:
    st = settings()
    reused = False
    async with get_db().sys_session() as s:
        sess = await s.scalar(
            select(DbSession).where(DbSession.token_hash == hash_refresh(refresh_token)).with_for_update()
        )
        if sess is None:
            raise Unauthorized("сессия недействительна", code="refresh_invalid")
        if sess.rotated_at is not None and sess.revoked_at is None:
            if (utcnow() - sess.rotated_at).total_seconds() <= st.refresh_reuse_grace_sec:
                # Два параллельных обновления с одного устройства: второе просим повторить с новым токеном
                raise Conflict("токен уже обновлён", code="refresh_in_progress")
            # Повторное использование старого токена: возможно, его украли. Отзываем всю цепочку.
            # Исключение бросаем после выхода из транзакции, иначе отзыв откатится.
            await s.execute(
                update(DbSession).where(DbSession.family_id == sess.family_id, DbSession.revoked_at.is_(None))
                .values(revoked_at=utcnow())
            )
            reused = True
        else:
            if sess.revoked_at is not None or sess.expires_at < utcnow():
                raise Unauthorized("сессия недействительна", code="refresh_invalid")
            user = await s.get(User, sess.user_id)
            if user is None or user.status != "active":
                raise Unauthorized("аккаунт недоступен", code="refresh_invalid")
            # Старая запись остаётся (rotated_at), чтобы поймать повторное использование.
            # Выданный по ней access-токен доживает свои 15 минут.
            sess.rotated_at = utcnow()
            return await _open_session(s, user, sess.platform, family_id=sess.family_id)
    assert reused
    raise Unauthorized("повторное использование токена", code="refresh_reused")


async def logout(refresh_token: str) -> None:
    async with get_db().sys_session() as s:
        sess = await s.scalar(select(DbSession).where(DbSession.token_hash == hash_refresh(refresh_token)))
        if sess is not None:
            await s.execute(
                update(DbSession).where(DbSession.family_id == sess.family_id, DbSession.revoked_at.is_(None))
                .values(revoked_at=utcnow())
            )


async def logout_session(session_id: uuid.UUID) -> None:
    async with get_db().sys_session() as s:
        sess = await s.get(DbSession, session_id)
        if sess is not None:
            await s.execute(
                update(DbSession).where(DbSession.family_id == sess.family_id, DbSession.revoked_at.is_(None))
                .values(revoked_at=utcnow())
            )


async def recover(*, login: str, recovery_code: str, new_password: str, platform: str | None,
                  client_key: str) -> tuple[Tokens, MeOut, str]:
    norm = normalize_login(login)
    await kv.hit(f"recover:{kv.anon(norm)}", 5, 3600)
    await kv.hit(f"recover-client:{kv.anon(client_key)}", 20, 3600)
    pw_problems = password_problems(new_password, login)
    if pw_problems:
        raise ValidationFailed("пароль слишком простой", code="password_weak", details={"problems": pw_problems})
    async with get_db().sys_session() as s:
        user = await s.scalar(select(User).where(User.login_norm == norm).with_for_update())
        code = normalize_recovery_code(recovery_code)
        if user is None:
            dummy_verify(code)
            raise Unauthorized("неверный псевдоним или код", code="bad_recovery")
        if not verify_secret(user.recovery_hash, code):
            raise Unauthorized("неверный псевдоним или код", code="bad_recovery")
        new_code = generate_recovery_code()
        user.password_hash = hash_secret(new_password)
        user.recovery_hash = hash_secret(normalize_recovery_code(new_code))
        await s.execute(
            update(DbSession).where(DbSession.user_id == user.id, DbSession.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )
        tokens = await _open_session(s, user, platform)
        me = await me_out(s, user)
    return tokens, me, new_code


async def change_password(user_id: uuid.UUID, old: str, new: str, keep_session: uuid.UUID) -> None:
    async with get_db().sys_session() as s:
        user = await s.get(User, user_id, with_for_update=True)
        if user is None or not verify_secret(user.password_hash, old):
            raise Unauthorized("неверный пароль", code="bad_credentials")
        problems = password_problems(new, user.login)
        if problems:
            raise ValidationFailed("пароль слишком простой", code="password_weak", details={"problems": problems})
        user.password_hash = hash_secret(new)
        keep = await s.get(DbSession, keep_session)
        stmt = update(DbSession).where(DbSession.user_id == user_id, DbSession.revoked_at.is_(None))
        if keep is not None:
            stmt = stmt.where(DbSession.family_id != keep.family_id)
        await s.execute(stmt.values(revoked_at=utcnow()))


async def new_recovery_code(user_id: uuid.UUID, password: str) -> str:
    async with get_db().sys_session() as s:
        user = await s.get(User, user_id, with_for_update=True)
        if user is None or not verify_secret(user.password_hash, password):
            raise Unauthorized("неверный пароль", code="bad_credentials")
        code = generate_recovery_code()
        user.recovery_hash = hash_secret(normalize_recovery_code(code))
    return code


async def delete_account(user_id: uuid.UUID, password: str | None, *, verify: bool = True) -> None:
    """Удаляет аккаунт сразу: строки в БД (каскадом), ключ пользователя и файлы."""
    async with get_db().sys_session() as s:
        user = await s.get(User, user_id, with_for_update=True)
        if user is None:
            return
        if verify and (password is None or not verify_secret(user.password_hash, password)):
            raise Unauthorized("неверный пароль", code="bad_credentials")
        tenant_id = user.tenant_id
        keys = (await s.scalars(select(Document.storage_key).where(Document.user_id == user_id))).all()
        await s.execute(delete(User).where(User.id == user_id))
    storage = get_storage()
    for key in keys:
        if key:
            storage.delete(key)
    storage.delete_prefix(f"{tenant_id}/{user_id}")
    forget_user_key(user_id)


async def list_sessions(user_id: uuid.UUID) -> list[DbSession]:
    async with get_db().sys_session() as s:
        rows = (
            await s.scalars(
                select(DbSession).where(DbSession.user_id == user_id, DbSession.revoked_at.is_(None),
                                        DbSession.expires_at > utcnow())
                .order_by(DbSession.created_at.desc())
            )
        ).all()
    return list(rows)


async def role_upgrade(user_id: uuid.UUID, code: str) -> str:
    """Подтверждение роли преподавателя кодом кафедры (R2.0). Документы не собираем."""
    async with get_db().sys_session() as s:
        info = await invites.find_valid(s, code, lock=True, kind="role_upgrade")
        user = await s.get(User, user_id, with_for_update=True)
        if user is None:
            raise Unauthorized("нет пользователя")
        if info.batch.tenant_id != user.tenant_id:
            raise AppError("код другого вуза", code="invite_invalid", status_code=404)
        user.role = info.batch.role
        info.code.uses += 1
        # Старые access-токены содержат прежнюю роль, поэтому сессии надо перевыпустить
        return user.role


# --- Вход на ПК по QR (R2.0) --------------------------------------------------

QR_TTL = 120


async def qr_start() -> str:
    token = secrets.token_urlsafe(24)
    await kv.get_kv().set(f"qr:{token}", json.dumps({"status": "pending"}), QR_TTL)
    return token


async def qr_approve(token: str, user_id: uuid.UUID) -> None:
    store = kv.get_kv()
    raw = await store.get(f"qr:{token}")
    if raw is None:
        raise AppError("код входа устарел", code="qr_expired", status_code=410)
    await store.set(f"qr:{token}", json.dumps({"status": "approved", "user_id": str(user_id)}), QR_TTL)


async def qr_poll(token: str) -> tuple[Tokens, MeOut] | None:
    store = kv.get_kv()
    raw = await store.get(f"qr:{token}")
    if raw is None:
        raise AppError("код входа устарел", code="qr_expired", status_code=410)
    data = json.loads(raw)
    if data.get("status") != "approved":
        return None
    await store.delete(f"qr:{token}")
    async with get_db().sys_session() as s:
        user = await s.get(User, uuid.UUID(data["user_id"]))
        if user is None or user.status != "active":
            raise Unauthorized("аккаунт недоступен")
        tokens = await _open_session(s, user, "desktop-qr")
        me = await me_out(s, user)
    return tokens, me
