"""Инструменты ассистента.

Белый список: модель может вызвать только зарегистрированные здесь функции,
аргументы проверяются pydantic-схемой. Модули (расписание, документы, кампус)
регистрируют свои инструменты при импорте.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ValidationError

from doomich.deps import CurrentUser


@dataclass
class Fragment:
    """Фрагмент документа, попавший в контекст ответа. Номер нужен для ссылок [n]."""

    n: int
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    title: str
    page: int | None
    sheet: str | None
    text: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClientContext:
    """Контекст с устройства. Не сохраняется на сервере."""

    group_id: uuid.UUID | None = None
    subgroup: str | None = None
    teacher_key: str | None = None
    campus_id: uuid.UUID | None = None
    location_node_id: uuid.UUID | None = None


@dataclass
class ToolContext:
    user: CurrentUser
    client: ClientContext
    now: datetime
    lang: str
    group_code: str | None = None
    document_ids: list[uuid.UUID] = field(default_factory=list)
    lecture_id: uuid.UUID | None = None
    course_id: uuid.UUID | None = None
    fragments: list[Fragment] = field(default_factory=list)
    attachments: list[dict[str, Any]] = field(default_factory=list)

    def add_fragment(self, **kw: Any) -> Fragment:
        frag = Fragment(n=len(self.fragments) + 1, **kw)
        self.fragments.append(frag)
        return frag

    @property
    def group_id(self) -> uuid.UUID | None:
        return self.client.group_id or self.user.group_id

    @property
    def subgroup(self) -> str | None:
        return self.client.subgroup if self.client.group_id else self.user.subgroup


ToolFn = Callable[[ToolContext, Any], Awaitable[str]]


@dataclass
class Tool:
    name: str
    description: str
    args_model: type[BaseModel]
    fn: ToolFn
    available: Callable[[ToolContext], bool] = lambda ctx: True

    def spec(self) -> dict[str, Any]:
        schema = self.args_model.model_json_schema()
        schema.pop("title", None)
        for prop in schema.get("properties", {}).values():
            prop.pop("title", None)
        return {"type": "function", "function": {"name": self.name, "description": self.description,
                                                 "parameters": schema}}


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def specs(self, ctx: ToolContext) -> list[dict[str, Any]]:
        return [t.spec() for t in self._tools.values() if t.available(ctx)]

    def names(self) -> list[str]:
        return list(self._tools)

    async def call(self, ctx: ToolContext, name: str, arguments: str) -> tuple[str, str]:
        """Возвращает (результат для модели, статус)."""
        tool = self._tools.get(name)
        if tool is None or not tool.available(ctx):
            return json.dumps({"error": f"инструмент {name} недоступен"}, ensure_ascii=False), "unknown"
        try:
            args = tool.args_model.model_validate_json(arguments or "{}")
        except ValidationError as e:
            errors = [{"field": ".".join(str(p) for p in err["loc"]), "msg": err["msg"]} for err in e.errors()]
            return json.dumps({"error": "неверные аргументы", "details": errors}, ensure_ascii=False), "invalid"
        try:
            return await tool.fn(ctx, args), "ok"
        except Exception as e:
            return json.dumps({"error": f"инструмент не сработал: {type(e).__name__}"}, ensure_ascii=False), "error"


registry = ToolRegistry()
