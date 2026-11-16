"""HTTP API синтеза речи.

POST /v1/synthesize {text, lang, voice, speed, format, tenant} -> аудио (wav или ogg_opus)
POST /v1/normalize  {text, lang, tenant} -> текст после нормализации (для отладки и оценки)
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from doomich_tts.backends.impl import Audio, MockSynthesizer, Synthesizer, resample
from doomich_tts.encode import OpusEncoder, opus_available, wav_bytes
from doomich_tts.normalize.en import normalize_en
from doomich_tts.normalize.ru import normalize_ru
from doomich_tts.stress import StressDict, strip_marks

log = logging.getLogger("doomich_tts")
LATENCY = Histogram("tts_synthesis_seconds", "Время синтеза фразы", ["backend"],
                    buckets=(0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1, 2, 5))
CACHE_HITS = Counter("tts_cache_total", "Обращения к кэшу фраз", ["result"])


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TTS_", extra="ignore")
    backend: Literal["mock", "openai_speech", "kokoro", "chatterbox"] = "mock"
    url: str = "http://tts-model:8000/v1"
    model: str = "qwen3-tts"
    voice: str = "default"
    stress_style: Literal["plus", "acute", "none"] = "none"
    kokoro_model: str = "/models/tts/kokoro-v1.0.onnx"
    kokoro_voices: str = "/models/tts/voices-v1.0.bin"
    device: str = "cuda"
    dicts_dir: Path = Path("/models/tts/dicts")
    cache_dir: Path = Path("/var/cache/doomich-tts")
    cache_max_files: int = 5000
    max_chars: int = 600
    opus_rate: int = 24000


@lru_cache
def settings() -> Settings:
    return Settings()


_lock = threading.Lock()
_engine: dict[str, Synthesizer] = {}


def engine() -> Synthesizer:
    st = settings()
    with _lock:
        if "e" not in _engine:
            if st.backend == "openai_speech":
                from doomich_tts.backends.impl import OpenAISpeechSynthesizer

                _engine["e"] = OpenAISpeechSynthesizer(st.url, st.model, st.voice, st.stress_style)
            elif st.backend == "kokoro":
                from doomich_tts.backends.impl import KokoroSynthesizer

                _engine["e"] = KokoroSynthesizer(st.kokoro_model, st.kokoro_voices, st.voice)
            elif st.backend == "chatterbox":
                from doomich_tts.backends.impl import ChatterboxSynthesizer

                _engine["e"] = ChatterboxSynthesizer(st.device)
            else:
                _engine["e"] = MockSynthesizer()
        return _engine["e"]


class SynthIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    lang: Literal["ru", "en"] = "ru"
    voice: str | None = Field(default=None, max_length=100)
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    format: Literal["wav", "ogg_opus"] = "wav"
    tenant: str | None = Field(default=None, max_length=64)


class NormalizeIn(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    lang: Literal["ru", "en"] = "ru"
    tenant: str | None = None


def prepare(text: str, lang: str, tenant: str | None, stress: StressDict, style: str) -> str:
    out = normalize_ru(text) if lang == "ru" else normalize_en(text)
    if lang == "ru":
        out = stress.apply(out, tenant, style)
    return out if style != "none" else strip_marks(out)


class PhraseCache:
    """Кэш частых фраз ("Минутку", "Не расслышал" и т. п.) на диске."""

    def __init__(self, root: Path, max_files: int) -> None:
        self.root = root
        self.max_files = max_files
        self.enabled = True
        try:
            root.mkdir(parents=True, exist_ok=True)
        except OSError:
            self.enabled = False

    def key(self, *parts: Any) -> str:
        return hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()

    def get(self, key: str) -> bytes | None:
        if not self.enabled:
            return None
        path = self.root / key
        if path.exists():
            path.touch()
            return path.read_bytes()
        return None

    def put(self, key: str, data: bytes) -> None:
        if not self.enabled:
            return
        (self.root / key).write_bytes(data)
        files = sorted(self.root.iterdir(), key=lambda p: p.stat().st_mtime)
        for old in files[: max(0, len(files) - self.max_files)]:
            old.unlink(missing_ok=True)


def create_app() -> FastAPI:
    st = settings()
    app = FastAPI(title="Doomich TTS", version="1.0.0")
    stress = StressDict(st.dicts_dir if st.dicts_dir.exists() else None)
    cache = PhraseCache(st.cache_dir, st.cache_max_files)

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "backend": st.backend, "opus": opus_available()}

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> PlainTextResponse:
        return PlainTextResponse(generate_latest().decode(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/v1/voices")
    def voices() -> list[str]:
        return engine().voices()

    @app.post("/v1/normalize")
    def normalize(body: NormalizeIn) -> dict[str, str]:
        return {"text": prepare(body.text, body.lang, body.tenant, stress, "plus")}

    @app.post("/v1/synthesize")
    def synthesize(body: SynthIn) -> Response:
        eng = engine()
        text = prepare(body.text, body.lang, body.tenant, stress, eng.stress_style)[: st.max_chars]
        if not text.strip():
            raise HTTPException(400, "пустой текст после нормализации")
        key = cache.key(eng.name, st.model, body.voice, body.speed, body.format, text) if len(text) <= 80 else None
        if key:
            hit = cache.get(key)
            if hit is not None:
                CACHE_HITS.labels(result="hit").inc()
                return Response(hit, media_type=_mime(body.format), headers=_headers(body.format, None, hit))
            CACHE_HITS.labels(result="miss").inc()
        started = time.monotonic()
        try:
            audio: Audio = eng.synthesize(text, lang=body.lang, voice=body.voice, speed=body.speed)
        except Exception as e:
            log.exception("ошибка синтеза")
            raise HTTPException(500, "ошибка синтеза") from e
        LATENCY.labels(backend=eng.name).observe(time.monotonic() - started)
        fmt = body.format if (body.format == "wav" or opus_available()) else "wav"
        if fmt == "ogg_opus":
            audio = resample(audio, st.opus_rate)
            data = OpusEncoder(st.opus_rate).encode_ogg(audio.samples)
        else:
            data = wav_bytes(audio.samples, audio.sample_rate)
        if key:
            cache.put(key, data)
        return Response(data, media_type=_mime(fmt), headers=_headers(fmt, audio.duration, data))

    return app


def _mime(fmt: str) -> str:
    return "audio/ogg" if fmt == "ogg_opus" else "audio/wav"


def _headers(fmt: str, duration: float | None, data: bytes) -> dict[str, str]:
    if duration is None and fmt == "wav":
        import io
        import wave

        with wave.open(io.BytesIO(data)) as w:
            duration = w.getnframes() / w.getframerate()
    return {"X-Audio-Format": fmt, "X-Audio-Duration": f"{duration or 0:.2f}"}
