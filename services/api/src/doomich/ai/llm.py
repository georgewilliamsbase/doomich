"""Клиент LLM.

Основной бэкенд: OpenAI-совместимый API (vLLM, llama.cpp server). Заглушка
MockLLM нужна для тестов и разработки без GPU: она умеет вызывать инструменты
расписания и документов и собирать ответ из их результатов.
"""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Protocol

import httpx

from doomich.common.errors import ServiceUnavailable


@dataclass
class TextDelta:
    text: str


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str


@dataclass
class Done:
    finish_reason: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    tool_calls: list[ToolCall] = field(default_factory=list)


LLMEvent = TextDelta | Done


class ChatLLM(Protocol):
    def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncIterator[LLMEvent]: ...

    async def complete(self, messages: list[dict[str, Any]], *, model: str | None = None,
                       max_tokens: int | None = None, temperature: float | None = None,
                       json_schema: dict[str, Any] | None = None) -> str: ...


class OpenAICompatLLM:
    def __init__(self, base_url: str, model: str, api_key: str, *, timeout: float = 120.0,
                 max_tokens: int = 1200, temperature: float = 0.4, enable_thinking: bool = False) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.enable_thinking = enable_thinking
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=5.0),
            headers={"Authorization": f"Bearer {api_key}"},
        )

    def _body(self, messages: list[dict[str, Any]], **kw: Any) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": kw.get("model") or self.model,
            "messages": messages,
            "max_tokens": kw.get("max_tokens") or self.max_tokens,
            "temperature": self.temperature if kw.get("temperature") is None else kw["temperature"],
            "chat_template_kwargs": {"enable_thinking": self.enable_thinking},
        }
        if kw.get("tools"):
            body["tools"] = kw["tools"]
            body["tool_choice"] = "auto"
        return body

    async def stream(self, messages: list[dict[str, Any]], *, tools: list[dict[str, Any]] | None = None,
                     model: str | None = None, max_tokens: int | None = None,
                     temperature: float | None = None) -> AsyncIterator[LLMEvent]:
        body = self._body(messages, tools=tools, model=model, max_tokens=max_tokens, temperature=temperature)
        body["stream"] = True
        body["stream_options"] = {"include_usage": True}
        calls: dict[int, dict[str, str]] = {}
        finish = "stop"
        usage = (0, 0)
        try:
            async with self._client.stream("POST", f"{self.base_url}/chat/completions", json=body) as resp:
                if resp.status_code >= 400:
                    detail = (await resp.aread())[:300].decode(errors="replace")
                    raise ServiceUnavailable(f"LLM {resp.status_code}: {detail}", code="llm_error")
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    if chunk.get("usage"):
                        usage = (chunk["usage"].get("prompt_tokens", 0), chunk["usage"].get("completion_tokens", 0))
                    for choice in chunk.get("choices", []):
                        delta = choice.get("delta") or {}
                        if delta.get("content"):
                            yield TextDelta(delta["content"])
                        for tc in delta.get("tool_calls") or []:
                            slot = calls.setdefault(tc.get("index", 0), {"id": "", "name": "", "arguments": ""})
                            if tc.get("id"):
                                slot["id"] = tc["id"]
                            fn = tc.get("function") or {}
                            if fn.get("name"):
                                slot["name"] += fn["name"]
                            if fn.get("arguments"):
                                slot["arguments"] += fn["arguments"]
                        if choice.get("finish_reason"):
                            finish = choice["finish_reason"]
        except httpx.HTTPError as e:
            raise ServiceUnavailable(f"LLM недоступна: {e}", code="llm_unavailable") from e
        tool_calls = [
            ToolCall(id=c["id"] or f"call_{i}", name=c["name"], arguments=c["arguments"] or "{}")
            for i, c in sorted(calls.items())
            if c["name"]
        ]
        yield Done(finish_reason="tool_calls" if tool_calls else finish, prompt_tokens=usage[0],
                   completion_tokens=usage[1], tool_calls=tool_calls)

    async def complete(self, messages: list[dict[str, Any]], *, model: str | None = None,
                       max_tokens: int | None = None, temperature: float | None = None,
                       json_schema: dict[str, Any] | None = None) -> str:
        body = self._body(messages, model=model, max_tokens=max_tokens, temperature=temperature)
        if json_schema is not None:
            body["response_format"] = {"type": "json_schema", "json_schema": {"name": "out", "schema": json_schema}}
        try:
            resp = await self._client.post(f"{self.base_url}/chat/completions", json=body)
        except httpx.HTTPError as e:
            raise ServiceUnavailable(f"LLM недоступна: {e}", code="llm_unavailable") from e
        if resp.status_code >= 400:
            raise ServiceUnavailable(f"LLM {resp.status_code}: {resp.text[:300]}", code="llm_error")
        return resp.json()["choices"][0]["message"].get("content") or ""

    async def health(self) -> bool:
        try:
            r = await self._client.get(f"{self.base_url}/models", timeout=3)
            return r.status_code == 200
        except httpx.HTTPError:
            return False


# --- Заглушка -----------------------------------------------------------------

SCHEDULE_WORDS = ("пар", "расписан", "занят", "что у меня", "где у меня", "лекци", "семинар", "lesson",
                  "schedule", "class", "экзамен", "зачёт")
NEXT_WORDS = ("следующ", "ближайш", "next", "сейчас")
DOC_WORDS = ("документ", "методичк", "файл", "pdf", "таблиц", "document", "по тексту", "в лекции", "конспект")
FRAGMENT_RE = re.compile(r"<<<FRAGMENT \[(\d+)\][^\n]*\n(.*?)\n>>>", re.S)
TODAY_RE = re.compile(r"(?:Сегодня|Today)[^:]*:\s*(\d{4}-\d{2}-\d{2})")


class MockLLM:
    """Детерминированная заглушка. Не умна, но проходит сценарии от начала до конца."""

    model = "mock-llm"

    def __init__(self, delay: float = 0.0) -> None:
        self.delay = delay

    @staticmethod
    def _today(messages: list[dict[str, Any]]) -> date:
        for m in messages:
            if m.get("role") == "system":
                found = TODAY_RE.search(str(m.get("content", "")))
                if found:
                    return date.fromisoformat(found.group(1))
        return date.today()

    def _plan(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None) -> ToolCall | None:
        last_user_idx = max((i for i, m in enumerate(messages) if m.get("role") == "user"), default=-1)
        if last_user_idx < 0 or any(m.get("role") == "tool" for m in messages[last_user_idx:]):
            return None
        names = {t["function"]["name"] for t in tools or []}
        text = str(messages[last_user_idx].get("content", "")).lower()
        today = self._today(messages)
        if "next_lesson" in names and any(w in text for w in NEXT_WORDS) and any(w in text for w in SCHEDULE_WORDS):
            return ToolCall(id=f"call_{uuid.uuid4().hex[:8]}", name="next_lesson", arguments="{}")
        if "get_schedule" in names and any(w in text for w in SCHEDULE_WORDS):
            if "завтра" in text or "tomorrow" in text:
                start = end = today + timedelta(days=1)
            elif "сегодня" in text or "today" in text:
                start = end = today
            else:
                start, end = today, today + timedelta(days=6)
            args = {"date_from": start.isoformat(), "date_to": end.isoformat()}
            return ToolCall(id=f"call_{uuid.uuid4().hex[:8]}", name="get_schedule", arguments=json.dumps(args))
        if "search_documents" in names and any(w in text for w in DOC_WORDS):
            args = {"query": text[:200]}
            return ToolCall(id=f"call_{uuid.uuid4().hex[:8]}", name="search_documents",
                            arguments=json.dumps(args, ensure_ascii=False))
        return None

    def _answer(self, messages: list[dict[str, Any]]) -> str:
        last_user_idx = max((i for i, m in enumerate(messages) if m.get("role") == "user"), default=0)
        question = str(messages[last_user_idx].get("content", "")) if messages else ""
        tool_outputs = [str(m.get("content", "")) for m in messages[last_user_idx:] if m.get("role") == "tool"]
        context = "\n".join(tool_outputs + [str(m.get("content", "")) for m in messages if m.get("role") == "system"])
        fragments = FRAGMENT_RE.findall(context)
        if fragments:
            num, body = fragments[0]
            body = re.sub(r"^\[[^\]\n]*\]\n", "", body.strip())  # строка с названием раздела
            sentence = re.split(r"(?<=[.!?])\s", body.strip(), maxsplit=1)[0]
            return f"По найденным фрагментам: {sentence} [{num}]"
        if tool_outputs:
            try:
                data = json.loads(tool_outputs[-1])
            except json.JSONDecodeError:
                data = {}
            lessons = data.get("lessons") if isinstance(data, dict) else None
            if lessons:
                parts = [f"{x.get('start', '')} {x.get('subject', '')}, ауд. {x.get('room') or 'не указана'}"
                         for x in lessons[:5]]
                return "Вот что в расписании: " + "; ".join(parts) + "."
            if isinstance(data, dict) and data.get("lesson"):
                x = data["lesson"]
                room = x.get("room") or "не указана"
                return f"Следующая пара: {x.get('subject')} в {x.get('start')}, аудитория {room}."
            if isinstance(data, dict) and data.get("not_found"):
                return "В документах ответа на этот вопрос нет."
            return "По расписанию занятий нет."
        if "Ответь только" in context and "фрагмент" in context:
            return "В документах ответа на этот вопрос нет."
        return f"Это ответ Думыча в тестовом режиме. Вы спросили: \"{question.strip()[:200]}\"."

    async def stream(self, messages: list[dict[str, Any]], *, tools: list[dict[str, Any]] | None = None,
                     model: str | None = None, max_tokens: int | None = None,
                     temperature: float | None = None) -> AsyncIterator[LLMEvent]:
        call = self._plan(messages, tools)
        if call:
            yield Done(finish_reason="tool_calls", tool_calls=[call])
            return
        answer = self._answer(messages)
        words = answer.split(" ")
        for i, w in enumerate(words):
            if self.delay:
                await asyncio.sleep(self.delay)
            yield TextDelta(w + ("" if i == len(words) - 1 else " "))
        yield Done(finish_reason="stop", prompt_tokens=sum(len(str(m.get("content", ""))) // 4 for m in messages),
                   completion_tokens=len(words))

    async def complete(self, messages: list[dict[str, Any]], *, model: str | None = None,
                       max_tokens: int | None = None, temperature: float | None = None,
                       json_schema: dict[str, Any] | None = None) -> str:
        if json_schema is not None:
            return json.dumps(_mock_from_schema(json_schema), ensure_ascii=False)
        text = "".join([e.text async for e in self.stream(messages) if isinstance(e, TextDelta)])
        return text

    async def health(self) -> bool:
        return True


def _mock_from_schema(schema: dict[str, Any]) -> Any:
    kind = schema.get("type")
    if kind == "object":
        return {k: _mock_from_schema(v) for k, v in (schema.get("properties") or {}).items()}
    if kind == "array":
        return [_mock_from_schema(schema.get("items") or {"type": "string"}) for _ in range(schema.get("minItems", 2))]
    if kind == "integer":
        return 0
    if kind == "number":
        return 0.0
    if kind == "boolean":
        return True
    if "enum" in schema:
        return schema["enum"][0]
    return "тест"
