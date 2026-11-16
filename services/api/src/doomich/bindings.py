"""Привязки моделей к вузам и кампусам.

Привязку выставляет ML-платформа (dml deploy) через админ-API. Компоненты:
llm_adapter (имя адаптера LoRA в vLLM), asr_profile, tts_voice, kws_model,
vpr_index (индекс фото кампуса). У компонента может быть канареечная версия
на долю пользователей: выбор стабилен для пользователя (по хэшу id).
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select

from doomich.db import get_db
from doomich.models import ModelBinding


@dataclass(frozen=True)
class Binding:
    component: str
    model_ref: str
    stage: str
    params: dict[str, Any] = field(default_factory=dict)


_cache: dict[tuple[str, uuid.UUID | None, uuid.UUID | None], tuple[float, list[ModelBinding]]] = {}
TTL = 60.0


async def _load(component: str, tenant_id: uuid.UUID | None, campus_id: uuid.UUID | None) -> list[ModelBinding]:
    key = (component, tenant_id, campus_id)
    now = time.monotonic()
    hit = _cache.get(key)
    if hit and hit[0] > now:
        return hit[1]
    async with get_db().sys_session() as s:
        rows = list(
            (await s.scalars(
                select(ModelBinding).where(
                    ModelBinding.component == component,
                    ModelBinding.tenant_id.is_(None) if tenant_id is None else ModelBinding.tenant_id == tenant_id,
                    ModelBinding.campus_id.is_(None) if campus_id is None else ModelBinding.campus_id == campus_id,
                )
            )).all()
        )
    _cache[key] = (now + TTL, rows)
    return rows


def _bucket(subject: str) -> int:
    return int(hashlib.sha256(subject.encode()).hexdigest()[:8], 16) % 100


async def resolve(component: str, tenant_id: uuid.UUID | None, *, campus_id: uuid.UUID | None = None,
                  subject: str | None = None) -> Binding | None:
    """Самая конкретная привязка: кампус, затем вуз, затем общая."""
    scopes: list[tuple[uuid.UUID | None, uuid.UUID | None]] = []
    if campus_id is not None:
        scopes.append((tenant_id, campus_id))
    if tenant_id is not None:
        scopes.append((tenant_id, None))
    scopes.append((None, None))
    for t, c in scopes:
        rows = await _load(component, t, c)
        if not rows:
            continue
        prod = next((r for r in rows if r.stage == "production"), None)
        canary = next((r for r in rows if r.stage == "canary"), None)
        chosen = prod
        if canary is not None and subject is not None and _bucket(subject) < canary.traffic_pct:
            chosen = canary
        chosen = chosen or canary
        if chosen is not None:
            return Binding(component=component, model_ref=chosen.model_ref, stage=chosen.stage,
                           params=dict(chosen.params or {}))
    return None


def invalidate() -> None:
    _cache.clear()


async def llm_model_for(tenant_id: uuid.UUID, user_id: uuid.UUID, default: str) -> str:
    b = await resolve("llm_adapter", tenant_id, subject=str(user_id))
    return b.model_ref if b else default
