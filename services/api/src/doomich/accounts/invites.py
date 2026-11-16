"""Коды приглашения.

Вид кода: XXXX-XXXX из алфавита без похожих символов (около 40 бит).
В БД хранится HMAC кода для поиска и сам код, зашифрованный системным ключом,
чтобы администратор мог перепечатать лист с QR.
"""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from doomich.common.errors import AppError
from doomich.common.timeutil import today_utc
from doomich.models import InviteBatch, InviteCode
from doomich.security import crypto

ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"  # без 0/O, 1/I/L
PURPOSE = "invite"


def generate_code() -> str:
    raw = "".join(secrets.choice(ALPHABET) for _ in range(8))
    return f"{raw[:4]}-{raw[4:]}"


# Пользователи с русской раскладкой часто вводят похожие кириллические буквы
LOOKALIKES = str.maketrans("АВЕКМНРСТУХ", "ABEKMHPCTYX")


def normalize_code(code: str) -> str:
    code = code.strip().upper().replace(" ", "").replace("-", "").translate(LOOKALIKES)
    if len(code) == 8:
        return f"{code[:4]}-{code[4:]}"
    return code


def code_hash(code: str) -> bytes:
    return crypto.hmac_lookup(PURPOSE, normalize_code(code))


@dataclass
class InviteInfo:
    code: InviteCode
    batch: InviteBatch


async def find_valid(session: AsyncSession, code: str, *, lock: bool = False,
                     kind: str = "register") -> InviteInfo:
    stmt = (
        select(InviteCode, InviteBatch)
        .join(InviteBatch, InviteBatch.id == InviteCode.batch_id)
        .where(InviteCode.code_hash == code_hash(code))
    )
    if lock:
        stmt = stmt.with_for_update(of=InviteCode)
    row = (await session.execute(stmt)).first()
    if row is None:
        raise AppError("код приглашения не найден", code="invite_invalid", status_code=404)
    inv, batch = row
    if batch.kind != kind:
        raise AppError("код другого типа", code="invite_wrong_kind")
    if inv.revoked:
        raise AppError("код отозван", code="invite_revoked")
    if inv.expires_on and inv.expires_on < today_utc():
        raise AppError("срок кода истёк", code="invite_expired")
    if inv.uses >= inv.max_uses:
        raise AppError("код уже использован", code="invite_used_up")
    return InviteInfo(code=inv, batch=batch)


async def create_batch(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    label: str,
    count: int,
    role: str = "student",
    kind: str = "register",
    group_id: uuid.UUID | None = None,
    max_uses: int = 1,
    expires_on: date | None = None,
    is_beta: bool = False,
    created_by: uuid.UUID | None = None,
) -> tuple[InviteBatch, list[str]]:
    if not 1 <= count <= 5000:
        raise AppError("в пачке от 1 до 5000 кодов", code="invite_batch_size")
    batch = InviteBatch(
        id=uuid.uuid4(), tenant_id=tenant_id, label=label, kind=kind, role=role, group_id=group_id,
        max_uses=max_uses, expires_on=expires_on, is_beta=is_beta, code_count=count, created_by=created_by,
    )
    session.add(batch)
    # Без relationship() порядок вставок не гарантирован: сначала пачка, потом коды
    await session.flush()
    codes: list[str] = []
    seen: set[str] = set()
    while len(codes) < count:
        c = generate_code()
        if c in seen:
            continue
        seen.add(c)
        codes.append(c)
        session.add(
            InviteCode(
                id=uuid.uuid4(), batch_id=batch.id, tenant_id=tenant_id, code_hash=code_hash(c),
                code_enc=crypto.seal_system(PURPOSE, c.encode()), max_uses=max_uses, expires_on=expires_on,
            )
        )
    await session.flush()
    return batch, codes


def reveal(code: InviteCode) -> str:
    return crypto.open_system(PURPOSE, code.code_enc).decode()
