"""Адаптеры источников расписания.

Адаптер получает конфиг источника (JSON из таблицы schedule_sources) и возвращает
список LessonRecord. Адаптер под конкретный вуз пишется одним классом:

    from doomich.schedule.adapters.base import ScheduleAdapter, register

    @register("my_university")
    class MyUniversityAdapter(ScheduleAdapter):
        async def fetch(self) -> list[LessonRecord]:
            ...

Сторонний пакет может зарегистрировать адаптер через entry point
группы "doomich.schedule_adapters".
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from datetime import date
from importlib.metadata import entry_points
from typing import Any, ClassVar
from zoneinfo import ZoneInfo

import httpx

from doomich.schedule.records import LessonRecord, Term

USER_AGENT = "DoomichScheduleSync/1.0"


@dataclass
class AdapterContext:
    tz: ZoneInfo
    term: Term | None
    window: tuple[date, date]
    bells: list[tuple[str, str]] | None = None


class AdapterError(Exception):
    pass


class ScheduleAdapter:
    kind: ClassVar[str] = ""

    def __init__(self, config: dict[str, Any], ctx: AdapterContext) -> None:
        self.config = config
        self.ctx = ctx

    async def fetch(self) -> list[LessonRecord]:
        raise NotImplementedError

    async def http_get(self, url: str, **kw: Any) -> httpx.Response:
        timeout = float(self.config.get("timeout_sec", 30))
        headers = {"User-Agent": USER_AGENT, **(self.config.get("headers") or {})}
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
            try:
                resp = await client.get(url, **kw)
            except httpx.HTTPError as e:
                raise AdapterError(f"не удалось загрузить {url}: {e}") from e
        if resp.status_code >= 400:
            raise AdapterError(f"{url}: HTTP {resp.status_code}")
        return resp


_REGISTRY: dict[str, type[ScheduleAdapter]] = {}


def register(kind: str):
    def deco(cls: type[ScheduleAdapter]) -> type[ScheduleAdapter]:
        cls.kind = kind
        _REGISTRY[kind] = cls
        return cls

    return deco


def _load_entry_points() -> None:
    try:
        for ep in entry_points(group="doomich.schedule_adapters"):
            if ep.name not in _REGISTRY:
                _REGISTRY[ep.name] = ep.load()
    except Exception:  # noqa: S110 - битый плагин не должен ломать встроенные адаптеры
        pass


def get_adapter(kind: str, config: dict[str, Any], ctx: AdapterContext) -> ScheduleAdapter:
    from doomich.schedule.adapters import builtin  # noqa: F401  регистрирует встроенные

    if kind == "python":
        # Адаптер, указанный путём "package.module:ClassName"
        module_name, _, cls_name = str(config.get("class", "")).partition(":")
        if not module_name or not cls_name:
            raise AdapterError("для kind=python нужен config.class вида module:Class")
        cls = getattr(importlib.import_module(module_name), cls_name)
        return cls(config, ctx)
    _load_entry_points()
    if kind not in _REGISTRY:
        raise AdapterError(f"неизвестный тип источника: {kind}")
    return _REGISTRY[kind](config, ctx)


def available_kinds() -> list[str]:
    from doomich.schedule.adapters import builtin  # noqa: F401

    _load_entry_points()
    return sorted([*_REGISTRY, "python"])
