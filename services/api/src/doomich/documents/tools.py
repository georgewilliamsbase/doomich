"""Инструмент search_documents для ассистента."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from doomich.documents.search import hybrid_search
from doomich.orchestrator import prompts
from doomich.orchestrator.engine import source_title
from doomich.orchestrator.tools import Tool, ToolContext, registry


class SearchDocumentsArgs(BaseModel):
    query: str = Field(min_length=2, max_length=500, description="Поисковый запрос по документам пользователя")


async def search_documents(ctx: ToolContext, args: SearchDocumentsArgs) -> str:
    doc_ids = list(ctx.document_ids)
    if ctx.lecture_id is not None:
        from doomich.db import get_db
        from doomich.lectures.service import lecture_document_id

        async with get_db().user_session(ctx.user.id, ctx.user.tenant_id) as s:
            lecture_doc = await lecture_document_id(s, ctx.lecture_id)
        if lecture_doc:
            doc_ids.append(lecture_doc)
    from doomich.config import settings

    hits = await hybrid_search(ctx.user, args.query, scopes=["personal", "lecture"], document_ids=doc_ids or None,
                               k=6, min_score=settings().rag_min_score)
    if not hits:
        return json.dumps({"not_found": True, "note": "в документах ничего не найдено"}, ensure_ascii=False)
    blocks = []
    for h in hits:
        frag = ctx.add_fragment(chunk_id=h.chunk_id, document_id=h.document_id, title=h.title, page=h.page,
                                sheet=h.sheet, text=h.body, meta=h.meta)
        header = source_title(h.title, h.page, h.sheet, h.meta)
        body = f"[{h.section}]\n{h.body}" if h.section else h.body
        blocks.append((frag.n, header, body))
    return prompts.fragments_block(blocks, ctx.lang)


registry.register(Tool(
    name="search_documents",
    description="Поиск по документам и конспектам пользователя (PDF, DOCX, XLSX, PPTX, лекции). "
                "Возвращает фрагменты с номерами для ссылок [n].",
    args_model=SearchDocumentsArgs,
    fn=search_documents,
))
