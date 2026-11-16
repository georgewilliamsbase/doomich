"""Хранилище ключ-значение: Valkey в работе, словарь в памяти для тестов.

Используется для лимитов частоты, коротких сессий (вход по QR) и кэшей.
IP-адреса в ключах лимитов хэшируются и живут только до конца окна.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from typing import Protocol

from doomich.common.errors import TooManyRequests


class KV(Protocol):
    async def incr_window(self, key: str, window_sec: int) -> int: ...
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl_sec: int) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def close(self) -> None: ...


class MemoryKV:
    def __init__(self) -> None:
        self._data: dict[str, tuple[str, float]] = {}
        self._lock = asyncio.Lock()

    def _alive(self, key: str) -> tuple[str, float] | None:
        item = self._data.get(key)
        if item and item[1] < time.monotonic():
            self._data.pop(key, None)
            return None
        return item

    async def incr_window(self, key: str, window_sec: int) -> int:
        async with self._lock:
            item = self._alive(key)
            if item is None:
                self._data[key] = ("1", time.monotonic() + window_sec)
                return 1
            value = int(item[0]) + 1
            self._data[key] = (str(value), item[1])
            return value

    async def get(self, key: str) -> str | None:
        item = self._alive(key)
        return item[0] if item else None

    async def set(self, key: str, value: str, ttl_sec: int) -> None:
        self._data[key] = (value, time.monotonic() + ttl_sec)

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def close(self) -> None:
        self._data.clear()


class RedisKV:
    def __init__(self, url: str) -> None:
        import redis.asyncio as redis

        self._r = redis.from_url(url, decode_responses=True)

    async def incr_window(self, key: str, window_sec: int) -> int:
        pipe = self._r.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_sec, nx=True)
        value, _ = await pipe.execute()
        return int(value)

    async def get(self, key: str) -> str | None:
        value = await self._r.get(key)
        return value.decode() if isinstance(value, bytes) else value

    async def set(self, key: str, value: str, ttl_sec: int) -> None:
        await self._r.set(key, value, ex=ttl_sec)

    async def delete(self, key: str) -> None:
        await self._r.delete(key)

    async def close(self) -> None:
        await self._r.aclose()


def make_kv(url: str) -> KV:
    if url.startswith("memory://"):
        return MemoryKV()
    return RedisKV(url)


_kv: dict[str, KV] = {}


def get_kv() -> KV:
    if "default" not in _kv:
        from doomich.config import settings

        _kv["default"] = make_kv(settings().redis_url)
    return _kv["default"]


def set_kv(kv: KV) -> None:
    _kv["default"] = kv


def anon(value: str) -> str:
    """Короткий необратимый отпечаток для ключей лимитов (IP не хранится)."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


async def hit(key: str, limit: int, window_sec: int) -> None:
    count = await get_kv().incr_window(f"rl:{key}:{window_sec}", window_sec)
    if count > limit:
        raise TooManyRequests("слишком много запросов", retry_after=window_sec)
