"""Профили распознавания для вузов.

Профиль готовит ML-платформа (dml asr build-profile): словарь терминов вуза,
таблица исправлений частых ошибок и, если есть, путь к дообученной модели.
Файл: <profiles_dir>/<slug вуза>.json
"""

from __future__ import annotations

import difflib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

WORD = re.compile(r"[\wё-]+", re.IGNORECASE)


@dataclass
class Profile:
    tenant: str
    version: str = ""
    hotwords: list[str] = field(default_factory=list)
    corrections: dict[str, str] = field(default_factory=dict)
    model: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> Profile:
        d = json.loads(path.read_text(encoding="utf-8"))
        return cls(tenant=d.get("tenant", path.stem), version=str(d.get("version", "")),
                   hotwords=list(d.get("hotwords", [])), corrections=dict(d.get("corrections", {})),
                   model=dict(d.get("model", {})))


def correct(text: str, hotwords: list[str], corrections: dict[str, str], cutoff: float = 0.84) -> str:
    """Подправляет распознанный текст под термины вуза.

    Сначала точные замены фраз (без учёта регистра), потом нечёткое совпадение
    отдельных слов и пар слов с терминами из словаря.
    """
    out = text
    for wrong, right in sorted(corrections.items(), key=lambda x: -len(x[0])):
        out = re.sub(rf"(?<![\wё]){re.escape(wrong)}(?![\wё])", right, out, flags=re.IGNORECASE)
    if not hotwords:
        return out
    terms = {h.lower(): h for h in hotwords if len(h) >= 4}
    single = [t for t in terms if " " not in t]
    multi = [t for t in terms if " " in t]
    words = WORD.findall(out)
    replaced: dict[str, str] = {}

    def best(candidate: str, pool: list[str]) -> str | None:
        match = difflib.get_close_matches(candidate, pool, n=1, cutoff=cutoff)
        if match and abs(len(match[0]) - len(candidate)) <= 3:
            return match[0]
        return None

    for i, w in enumerate(words):
        low = w.lower()
        if len(low) >= 4 and low not in terms:
            hit = best(low, single)
            if hit:
                replaced[w] = terms[hit]
        if i + 1 < len(words) and min(len(w), len(words[i + 1])) >= 3:
            pair = f"{w} {words[i + 1]}"
            # Слово, разорванное распознавателем на два: "мат анализ" -> "матанализ"
            hit = best((w + words[i + 1]).lower(), single) or best(pair.lower(), multi)
            if hit and pair.lower() not in terms:
                replaced[pair] = terms[hit]
    for wrong, right in sorted(replaced.items(), key=lambda x: -len(x[0])):
        out = re.sub(rf"(?<![\wё]){re.escape(wrong)}(?![\wё])", right, out)
    return out


class ProfileStore:
    def __init__(self, root: Path, ttl: float = 60.0) -> None:
        self.root = root
        self.ttl = ttl
        self._cache: dict[str, tuple[float, Profile | None]] = {}

    def get(self, tenant: str | None) -> Profile | None:
        if not tenant or not re.fullmatch(r"[a-z0-9-]{1,64}", tenant):
            return None
        now = time.monotonic()
        hit = self._cache.get(tenant)
        if hit and hit[0] > now:
            return hit[1]
        path = self.root / f"{tenant}.json"
        profile = Profile.load(path) if path.exists() else None
        self._cache[tenant] = (now + self.ttl, profile)
        return profile
