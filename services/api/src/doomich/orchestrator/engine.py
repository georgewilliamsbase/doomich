"""Оркестратор диалога.

Один ход: системный промпт, сжатая история, при необходимости предварительный
поиск по документам, затем до MAX_TOOL_ROUNDS раундов "модель -> инструменты".
Текст ответа уходит наружу потоком, в конце собираются ссылки на источники.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from doomich.ai.llm import Done, TextDelta
from doomich.ai.registry import get_ai
from doomich.observability.metrics import FIRST_TOKEN, LLM_TOKENS, TOOL_CALLS
from doomich.orchestrator import prompts
from doomich.orchestrator.tools import ToolContext, registry

MAX_TOOL_ROUNDS = 3
CHARS_PER_TOKEN = 3.5
CITE_RE = re.compile(r"\[(\d{1,2})\]")


@dataclass
class HistoryItem:
    role: str  # user | assistant
    content: str


@dataclass
class TurnResult:
    text: str = ""
    sources: list[dict[str, Any]] = field(default_factory=list)
    model_version: str = ""
    finish_reason: str = "stop"
    tools_used: list[str] = field(default_factory=list)


def estimate_tokens(text: str) -> int:
    return int(len(text) / CHARS_PER_TOKEN) + 1


def trim_history(history: list[HistoryItem], budget_tokens: int) -> list[HistoryItem]:
    """Оставляем последние сообщения, которые помещаются в бюджет."""
    kept: list[HistoryItem] = []
    used = 0
    for item in reversed(history):
        cost = estimate_tokens(item.content)
        if used + cost > budget_tokens and kept:
            break
        content = item.content if cost <= budget_tokens else item.content[: int(budget_tokens * CHARS_PER_TOKEN)]
        kept.append(HistoryItem(item.role, content))
        used += cost
    kept.reverse()
    # История не должна начинаться с ответа ассистента
    while kept and kept[0].role != "user":
        kept.pop(0)
    return kept


def source_title(title: str, page: int | None, sheet: str | None, meta: dict[str, Any]) -> str:
    where = ""
    if page:
        where = f", стр. {page}"
    elif sheet:
        where = f", лист {sheet}"
    elif meta.get("start") is not None:
        sec = int(meta["start"])
        where = f", {sec // 60:02d}:{sec % 60:02d}"
    return f"\"{title}\"{where}"


async def rewrite_query(question: str, history: list[HistoryItem], model: str) -> str:
    """Переформулировка вопроса с учётом диалога для поиска по документам."""
    if not history:
        return question
    convo = "\n".join(f"{h.role}: {h.content[:500]}" for h in history[-4:])
    try:
        out = await get_ai().llm.complete(
            [
                {"role": "system", "content": prompts.REWRITE_RU},
                {"role": "user", "content": f"Диалог:\n{convo}\n\nПоследний вопрос: {question}"},
            ],
            model=model, max_tokens=80, temperature=0.0,
        )
    except Exception:
        return question
    out = out.strip().strip('"')
    if not out or len(out) > 400 or out.startswith("Это ответ Думыча"):
        return question
    return out


async def run_turn(
    ctx: ToolContext,
    *,
    question: str,
    history: list[HistoryItem],
    mode: str,
    model: str,
    tenant_prompt: str | None = None,
    result: TurnResult,
) -> AsyncIterator[dict[str, Any]]:
    """Генератор событий: tool, delta. Итог пишется в result."""
    from doomich.config import settings

    st = settings()
    lang = ctx.lang
    docs_only = bool(ctx.document_ids or ctx.lecture_id)
    tools = registry.specs(ctx)
    available = {t["function"]["name"] for t in tools}
    extra_tools = [line for name, line in (prompts.EXTRA_TOOLS_EN if lang == "en" else prompts.EXTRA_TOOLS_RU)
                   if name in available]
    system = prompts.build_system_prompt(
        lang=lang, tenant_name=ctx.user.tenant.name, now=ctx.now, tz_name=ctx.user.tenant.timezone,
        role=ctx.user.role, group_code=ctx.group_code, mode=mode, docs_only=docs_only, extra_tools=extra_tools,
        tenant_prompt=tenant_prompt,
    )
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    budget = max(1000, st.llm_context_tokens - st.llm_max_tokens - estimate_tokens(system) - 3000)
    for h in trim_history(history, budget):
        messages.append({"role": h.role, "content": h.content})

    if docs_only:
        query = await rewrite_query(question, history, model)
        yield {"type": "tool", "name": "search_documents", "status": "start"}
        found, status = await registry.call(ctx, "search_documents", json.dumps({"query": query}, ensure_ascii=False))
        TOOL_CALLS.labels(tool="search_documents", status=status).inc()
        result.tools_used.append("search_documents")
        yield {"type": "tool", "name": "search_documents", "status": "done" if status == "ok" else status}
        messages[0]["content"] += "\n\n" + found

    messages.append({"role": "user", "content": question})
    started = time.monotonic()
    first_token_seen = False
    parts: list[str] = []
    finish = "stop"
    for round_no in range(MAX_TOOL_ROUNDS + 1):
        allow_tools = tools if round_no < MAX_TOOL_ROUNDS else None
        calls = []
        async for ev in get_ai().llm.stream(messages, tools=allow_tools, model=model):
            if isinstance(ev, TextDelta):
                if not first_token_seen:
                    first_token_seen = True
                    FIRST_TOKEN.labels(mode=mode).observe(time.monotonic() - started)
                parts.append(ev.text)
                yield {"type": "delta", "text": ev.text}
            elif isinstance(ev, Done):
                finish = ev.finish_reason
                calls = ev.tool_calls
                LLM_TOKENS.labels(kind="prompt").inc(ev.prompt_tokens)
                LLM_TOKENS.labels(kind="completion").inc(ev.completion_tokens)
        if not calls:
            break
        messages.append({
            "role": "assistant",
            "content": "".join(parts) or None,
            "tool_calls": [
                {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": c.arguments}}
                for c in calls
            ],
        })
        for c in calls:
            yield {"type": "tool", "name": c.name, "status": "start"}
            output, status = await registry.call(ctx, c.name, c.arguments)
            TOOL_CALLS.labels(tool=c.name, status=status).inc()
            result.tools_used.append(c.name)
            messages.append({"role": "tool", "tool_call_id": c.id, "content": output})
            yield {"type": "tool", "name": c.name, "status": "done" if status == "ok" else status}

    text = "".join(parts).strip()
    result.text = text
    result.finish_reason = finish
    result.sources = collect_sources(ctx, text, docs_only)


def collect_sources(ctx: ToolContext, text: str, docs_only: bool) -> list[dict[str, Any]]:
    cited = {int(n) for n in CITE_RE.findall(text)}
    out: list[dict[str, Any]] = []
    for f in ctx.fragments:
        is_cited = f.n in cited
        if not is_cited and not (docs_only and not cited and f.n <= 3):
            continue
        out.append({
            "n": f.n, "chunk_id": str(f.chunk_id), "document_id": str(f.document_id), "title": f.title,
            "page": f.page, "sheet": f.sheet, "snippet": f.text[:300], "cited": is_cited,
            "start": f.meta.get("start"),
        })
    return out
