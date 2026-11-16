"""Клиенты сервисов ASR и TTS.

Сервисы живут отдельно (services/asr, services/tts). Здесь только HTTP-клиенты
и встроенные заглушки, чтобы Core API можно было тестировать без них.
"""

from __future__ import annotations

import io
import math
import struct
import wave
from dataclasses import dataclass, field
from typing import Protocol

import httpx

from doomich.common.errors import ServiceUnavailable


@dataclass
class Transcript:
    text: str
    lang: str
    segments: list[dict[str, float | str]] = field(default_factory=list)


@dataclass
class SpeechAudio:
    data: bytes
    format: str  # "wav" | "ogg_opus"
    duration_sec: float


class ASR(Protocol):
    async def transcribe(self, pcm16: bytes, *, sample_rate: int = 16000, lang: str = "auto",
                         hotwords: list[str] | None = None, timestamps: bool = False,
                         tenant: str | None = None) -> Transcript: ...


class TTS(Protocol):
    async def synthesize(self, text: str, *, lang: str = "ru", voice: str | None = None,
                         speed: float = 1.0, fmt: str = "wav", tenant: str | None = None) -> SpeechAudio: ...


class HttpASR:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=5.0))

    async def transcribe(self, pcm16: bytes, *, sample_rate: int = 16000, lang: str = "auto",
                         hotwords: list[str] | None = None, timestamps: bool = False,
                         tenant: str | None = None) -> Transcript:
        params: dict[str, str] = {"lang": lang, "sample_rate": str(sample_rate), "timestamps": str(timestamps).lower()}
        if tenant:
            params["tenant"] = tenant
        if hotwords:
            params["hotwords"] = ",".join(hotwords[:200])
        try:
            resp = await self._client.post(
                f"{self.base_url}/v1/transcribe", params=params, content=pcm16,
                headers={"Content-Type": "audio/l16"},
            )
        except httpx.HTTPError as e:
            raise ServiceUnavailable(f"ASR недоступен: {e}", code="asr_unavailable") from e
        if resp.status_code >= 400:
            raise ServiceUnavailable(f"ASR {resp.status_code}: {resp.text[:200]}", code="asr_error")
        d = resp.json()
        return Transcript(text=d.get("text", ""), lang=d.get("lang", lang), segments=d.get("segments", []))


class HttpTTS:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=5.0))

    async def synthesize(self, text: str, *, lang: str = "ru", voice: str | None = None,
                         speed: float = 1.0, fmt: str = "wav", tenant: str | None = None) -> SpeechAudio:
        body = {"text": text, "lang": lang, "voice": voice, "speed": speed, "format": fmt, "tenant": tenant}
        try:
            resp = await self._client.post(f"{self.base_url}/v1/synthesize", json=body)
        except httpx.HTTPError as e:
            raise ServiceUnavailable(f"TTS недоступен: {e}", code="tts_unavailable") from e
        if resp.status_code >= 400:
            raise ServiceUnavailable(f"TTS {resp.status_code}: {resp.text[:200]}", code="tts_error")
        duration = float(resp.headers.get("X-Audio-Duration", "0") or 0)
        return SpeechAudio(data=resp.content, format=resp.headers.get("X-Audio-Format", fmt), duration_sec=duration)


class MockASR:
    """Возвращает предсказуемый текст. Тишина распознаётся как пустая строка."""

    def __init__(self, text: str = "что у меня завтра") -> None:
        self.text = text

    async def transcribe(self, pcm16: bytes, *, sample_rate: int = 16000, lang: str = "auto",
                         hotwords: list[str] | None = None, timestamps: bool = False,
                         tenant: str | None = None) -> Transcript:
        n = len(pcm16) // 2
        if n == 0:
            return Transcript(text="", lang="ru")
        samples = struct.unpack(f"<{n}h", pcm16[: n * 2])
        rms = math.sqrt(sum(s * s for s in samples[:: max(1, n // 4000)]) / max(1, len(samples[:: max(1, n // 4000)])))
        if rms < 100:
            return Transcript(text="", lang="ru")
        duration = n / sample_rate
        segs: list[dict[str, float | str]] = [{"start": 0.0, "end": round(duration, 2), "text": self.text}]
        return Transcript(text=self.text, lang="ru" if lang == "auto" else lang, segments=segs if timestamps else [])


class MockTTS:
    """Тон 440 Гц, длительность пропорциональна длине текста."""

    async def synthesize(self, text: str, *, lang: str = "ru", voice: str | None = None,
                         speed: float = 1.0, fmt: str = "wav", tenant: str | None = None) -> SpeechAudio:
        rate = 16000
        seconds = min(10.0, max(0.3, len(text) / 15.0 / max(speed, 0.5)))
        n = int(rate * seconds)
        frames = b"".join(
            struct.pack("<h", int(3000 * math.sin(2 * math.pi * 440 * i / rate))) for i in range(0, n)
        )
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(frames)
        return SpeechAudio(data=buf.getvalue(), format="wav", duration_sec=seconds)
