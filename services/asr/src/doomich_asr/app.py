"""HTTP API сервиса распознавания.

POST /v1/transcribe?lang=ru|en|auto&sample_rate=16000&timestamps=false&hotwords=a,b&tenant=slug
  тело: PCM16 (Content-Type: audio/l16) или WAV (audio/wav)
Аудио обрабатывается в памяти, на диск не пишется (кроме бэкенда gigaam, см. impl.py).
"""

from __future__ import annotations

import logging
import threading
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic_settings import BaseSettings, SettingsConfigDict

from doomich_asr.backends.base import Recognizer, Result, pcm16_to_float, resample, wav_to_float
from doomich_asr.backends.impl import MockRecognizer
from doomich_asr.profiles import ProfileStore, correct

log = logging.getLogger("doomich_asr")

SECONDS = Histogram("asr_audio_seconds", "Длительность распознанного аудио", buckets=(1, 2, 5, 10, 30, 60, 300))
RTF = Histogram("asr_rtf", "Отношение времени обработки к длительности", ["backend"],
                buckets=(0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2))
REQUESTS = Counter("asr_requests_total", "Запросы распознавания", ["lang", "status"])


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ASR_", extra="ignore")
    ru_backend: Literal["sherpa", "gigaam", "faster_whisper", "mock"] = "mock"
    ru_model: str = "/models/asr/gigaam-v3-rnnt"
    ru_kind: str = "nemo_transducer"
    en_backend: Literal["sherpa", "faster_whisper", "mock"] = "mock"
    en_model: str = "large-v3-turbo"
    device: str = "cuda"
    threads: int = 4
    profiles_dir: Path = Path("/models/asr/profiles")
    max_seconds: int = 120
    tmp_dir: str = "/dev/shm"


@lru_cache
def settings() -> Settings:
    return Settings()


_lock = threading.Lock()
_models: dict[str, Recognizer] = {}


def build(backend: str, model: str, lang: str, kind: str = "nemo_transducer") -> Recognizer:
    st = settings()
    if backend == "mock":
        return MockRecognizer()
    if backend == "sherpa":
        from doomich_asr.backends.impl import SherpaRecognizer

        return SherpaRecognizer(model, kind=kind if lang == "ru" else "whisper", device=st.device,
                                threads=st.threads, lang=lang)
    if backend == "gigaam":
        from doomich_asr.backends.impl import GigaAMRecognizer

        return GigaAMRecognizer(model, device=st.device, tmp_dir=st.tmp_dir)
    if backend == "faster_whisper":
        from doomich_asr.backends.impl import WhisperRecognizer

        return WhisperRecognizer(model, device=st.device)
    raise ValueError(f"неизвестный бэкенд {backend}")


def recognizer(lang: str, override: dict[str, Any] | None = None) -> Recognizer:
    """Модель по языку. Профиль вуза может подставить дообученную модель."""
    st = settings()
    if override:
        key = f"{lang}:{override.get('backend')}:{override.get('model_dir')}"
        args = (override.get("backend", "sherpa"), override["model_dir"], lang, override.get("kind", st.ru_kind))
    elif lang == "en":
        key, args = "en", (st.en_backend, st.en_model, "en", st.ru_kind)
    else:
        key, args = "ru", (st.ru_backend, st.ru_model, "ru", st.ru_kind)
    with _lock:
        if key not in _models:
            log.info("загружаю модель %s", key)
            _models[key] = build(*args)
            # Держим не больше 4 дообученных моделей вузов одновременно
            extra = [k for k in _models if k not in ("ru", "en")]
            if len(extra) > 4:
                _models.pop(extra[0], None)
        return _models[key]


def detect_lang(audio: Any) -> str:
    st = settings()
    if st.en_backend == "faster_whisper":
        rec = recognizer("en")
        detect = getattr(rec, "detect", None)
        if detect is not None:
            return "en" if detect(audio) == "en" else "ru"
    return "ru"


def create_app() -> FastAPI:
    app = FastAPI(title="Doomich ASR", version="1.0.0")
    profiles = ProfileStore(settings().profiles_dir)

    @app.get("/health")
    def health() -> dict[str, Any]:
        st = settings()
        return {"status": "ok", "ru": st.ru_backend, "en": st.en_backend, "loaded": sorted(_models)}

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> PlainTextResponse:
        return PlainTextResponse(generate_latest().decode(), media_type=CONTENT_TYPE_LATEST)

    @app.post("/v1/transcribe")
    async def transcribe(
        request: Request,
        lang: Literal["ru", "en", "auto"] = "auto",
        sample_rate: int = Query(16000, ge=8000, le=48000),
        timestamps: bool = False,
        hotwords: str | None = Query(None, max_length=8000),
        tenant: str | None = Query(None, max_length=64),
    ) -> dict[str, Any]:
        st = settings()
        body = await request.body()
        ctype = request.headers.get("content-type", "audio/l16")
        try:
            if "wav" in ctype or body[:4] == b"RIFF":
                audio, sr = wav_to_float(body)
            else:
                audio, sr = pcm16_to_float(body), sample_rate
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        audio = resample(audio, sr, 16000)
        duration = len(audio) / 16000
        if duration > st.max_seconds:
            raise HTTPException(413, f"не больше {st.max_seconds} с за запрос")
        profile = profiles.get(tenant)
        terms = [h for h in (hotwords or "").split(",") if h] + (profile.hotwords if profile else [])
        if lang == "auto":
            lang = detect_lang(audio) if duration > 0.5 else "ru"  # type: ignore[assignment]
        override = (profile.model.get(lang) if profile else None) or None
        rec = recognizer(lang, override)
        started = time.monotonic()
        try:
            result: Result = rec.transcribe(audio, sample_rate=16000, lang=lang, timestamps=timestamps,
                                            prompt=", ".join(terms[:50]) if terms and lang == "en" else None)
        except Exception as e:
            REQUESTS.labels(lang=lang, status="error").inc()
            log.exception("ошибка распознавания")
            raise HTTPException(500, "ошибка распознавания") from e
        elapsed = time.monotonic() - started
        text = correct(result.text, terms, profile.corrections if profile else {})
        SECONDS.observe(duration)
        if duration > 0:
            RTF.labels(backend=rec.name).observe(elapsed / duration)
        REQUESTS.labels(lang=lang, status="ok").inc()
        segments = [{"start": s.start, "end": s.end,
                     "text": correct(s.text, terms, profile.corrections if profile else {})} for s in result.segments]
        return {"text": text, "lang": result.lang or lang, "segments": segments, "duration": round(duration, 2),
                "rtf": round(elapsed / duration, 3) if duration else 0, "profile": profile.version if profile else None}

    return app
