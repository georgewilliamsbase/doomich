"""Эмбеддинги и реранкер.

Qwen3-Embedding ждёт инструкцию перед запросом и не ждёт её перед документом,
поэтому у embed есть параметр kind. Заглушка HashEmbedder строит вектор из
хэшей слов и их окончаний: лексически похожие тексты получают близкие векторы,
этого хватает для тестов гибридного поиска.
"""

from __future__ import annotations

import hashlib
import itertools
import math
import re
from typing import Literal, Protocol

import httpx

from doomich.common.errors import ServiceUnavailable

Kind = Literal["query", "document"]

QUERY_INSTRUCTION = "Instruct: Given a question, retrieve passages from study materials that answer it\nQuery: "


class Embedder(Protocol):
    dim: int

    async def embed(self, texts: list[str], kind: Kind = "document") -> list[list[float]]: ...


class Reranker(Protocol):
    async def rerank(self, query: str, documents: list[str]) -> list[float]: ...


class OpenAICompatEmbedder:
    def __init__(self, base_url: str, model: str, dim: int, *, batch: int = 32) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dim = dim
        self.batch = batch
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=5.0))

    async def embed(self, texts: list[str], kind: Kind = "document") -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), self.batch):
            part = texts[i : i + self.batch]
            if kind == "query":
                part = [QUERY_INSTRUCTION + t for t in part]
            try:
                resp = await self._client.post(
                    f"{self.base_url}/embeddings",
                    json={"model": self.model, "input": part, "dimensions": self.dim},
                )
            except httpx.HTTPError as e:
                raise ServiceUnavailable(f"эмбеддинги недоступны: {e}", code="embeddings_unavailable") from e
            if resp.status_code >= 400:
                raise ServiceUnavailable(f"эмбеддинги {resp.status_code}: {resp.text[:200]}", code="embeddings_error")
            data = sorted(resp.json()["data"], key=lambda d: d["index"])
            out.extend(_normalize(d["embedding"][: self.dim]) for d in data)
        return out


class OpenAICompatReranker:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0))

    async def rerank(self, query: str, documents: list[str]) -> list[float]:
        if not documents:
            return []
        try:
            resp = await self._client.post(
                f"{self.base_url}/rerank",
                json={"model": self.model, "query": query, "documents": documents},
            )
        except httpx.HTTPError as e:
            raise ServiceUnavailable(f"реранкер недоступен: {e}", code="reranker_unavailable") from e
        if resp.status_code >= 400:
            raise ServiceUnavailable(f"реранкер {resp.status_code}", code="reranker_error")
        scores = [0.0] * len(documents)
        for item in resp.json().get("results", []):
            scores[item["index"]] = float(item.get("relevance_score", item.get("score", 0.0)))
        return scores


WORD_RE = re.compile(r"[\wё]+", re.I)


def tokens(text: str) -> list[str]:
    return [w.lower().replace("ё", "е") for w in WORD_RE.findall(text)]


def stem(word: str) -> str:
    """Грубое усечение окончаний, достаточно для заглушки."""
    return word[:6] if len(word) > 6 else word


class HashEmbedder:
    def __init__(self, dim: int = 1024) -> None:
        self.dim = dim

    def _vec(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        words = [stem(w) for w in tokens(text)]
        feats = words + [f"{a}_{b}" for a, b in itertools.pairwise(words)]
        for f in feats:
            h = hashlib.blake2b(f.encode(), digest_size=8).digest()
            idx = int.from_bytes(h[:4], "little") % self.dim
            sign = 1.0 if h[4] & 1 else -1.0
            vec[idx] += sign
        if not feats:
            vec[0] = 1.0
        return _normalize(vec)

    async def embed(self, texts: list[str], kind: Kind = "document") -> list[list[float]]:
        return [self._vec(t) for t in texts]


class LexicalReranker:
    async def rerank(self, query: str, documents: list[str]) -> list[float]:
        q = {stem(w) for w in tokens(query) if len(w) > 2}
        scores = []
        for d in documents:
            dw = {stem(w) for w in tokens(d)}
            scores.append(len(q & dw) / (len(q) or 1))
        return scores


class NoReranker:
    async def rerank(self, query: str, documents: list[str]) -> list[float]:
        return [1.0 - i * 1e-3 for i in range(len(documents))]


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]
