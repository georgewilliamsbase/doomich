"""Гибридный поиск по фрагментам: векторы (pgvector) + полнотекст, слияние RRF, реранкер.

Поиск идёт под ролью приложения с контекстом пользователя, поэтому RLS
гарантирует, что в выдачу не попадут чужие фрагменты.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text

from doomich.ai.registry import get_ai
from doomich.db import get_db
from doomich.deps import CurrentUser, user_cipher_for

RRF_K = 60


@dataclass
class Hit:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    title: str
    page: int | None
    sheet: str | None
    section: str | None
    body: str
    scope: str
    meta: dict[str, Any] = field(default_factory=dict)
    rrf: float = 0.0
    score: float = 0.0


def vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{v:.6f}" for v in vec) + "]"


def _filters(scopes: list[str], document_ids: list[uuid.UUID] | None) -> tuple[str, dict[str, Any]]:
    sql = " AND c.scope = ANY(:scopes)"
    params: dict[str, Any] = {"scopes": scopes}
    if document_ids:
        sql += " AND c.document_id = ANY(:doc_ids)"
        params["doc_ids"] = document_ids
    return sql, params


COLUMNS = ("c.id, c.document_id, c.page, c.sheet, c.section, c.body, c.scope, c.meta, "
           "d.title, d.title_enc, d.user_id")


async def hybrid_search(
    user: CurrentUser,
    query: str,
    *,
    scopes: list[str],
    document_ids: list[uuid.UUID] | None = None,
    course_ids: list[uuid.UUID] | None = None,
    k: int = 6,
    candidates: int = 30,
    min_score: float | None = None,
) -> list[Hit]:
    ai = get_ai()
    qvec = (await ai.embedder.embed([query], kind="query"))[0]
    where, params = _filters(scopes, document_ids)
    hits: dict[uuid.UUID, Hit] = {}
    async with get_db().user_session(user.id, user.tenant_id, course_ids or ()) as s:
        await s.execute(text("select set_config('hnsw.ef_search', '100', true),"
                             " set_config('hnsw.iterative_scan', 'relaxed_order', true)"))
        vec_rows = (await s.execute(
            text(f"SELECT {COLUMNS} FROM chunks c JOIN documents d ON d.id = c.document_id "  # noqa: S608
                 f"WHERE c.embedding IS NOT NULL{where} "
                 "ORDER BY c.embedding <=> CAST(:q AS vector) LIMIT :n"),
            {**params, "q": vector_literal(qvec), "n": candidates},
        )).all()
        fts_rows = (await s.execute(
            text(f"SELECT {COLUMNS}, ts_rank_cd(c.fts, query) AS rank "  # noqa: S608
                 "FROM chunks c JOIN documents d ON d.id = c.document_id, "
                 "(SELECT websearch_to_tsquery('russian', :t) || websearch_to_tsquery('english', :t) AS query) q "
                 f"WHERE c.fts @@ query{where} ORDER BY rank DESC LIMIT :n"),
            {**params, "t": query, "n": candidates},
        )).all()
        cipher = await user_cipher_for(s, user.id)
        for ranked in (vec_rows, fts_rows):
            for rank, row in enumerate(ranked, start=1):
                hit = hits.get(row.id)
                if hit is None:
                    if row.title_enc is not None and row.user_id == user.id:
                        title = cipher.decrypt_str(row.title_enc, f"doc-title:{row.document_id}") or "документ"
                    else:
                        title = row.title or "документ"
                    hit = Hit(chunk_id=row.id, document_id=row.document_id, title=title, page=row.page,
                              sheet=row.sheet, section=row.section, body=row.body, scope=row.scope,
                              meta=dict(row.meta or {}))
                    hits[row.id] = hit
                hit.rrf += 1.0 / (RRF_K + rank)
    if not hits:
        return []
    pool = sorted(hits.values(), key=lambda h: h.rrf, reverse=True)[:20]
    docs = [f"{h.section}\n{h.body}" if h.section else h.body for h in pool]
    scores = await ai.reranker.rerank(query, docs)
    for h, sc in zip(pool, scores, strict=True):
        h.score = sc
    pool.sort(key=lambda h: (h.score, h.rrf), reverse=True)
    if min_score is not None:
        pool = [h for h in pool if h.score >= min_score]
    return pool[:k]
