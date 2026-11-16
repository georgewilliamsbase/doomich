"""Бэкенды синтеза. Выбор модели делается по итогам бенчмарка Спринта 0.

- mock: тон, длина пропорциональна тексту (тесты, разработка);
- openai_speech: любой сервер с OpenAI-совместимым /v1/audio/speech (например, vLLM-Omni
  с Qwen3-TTS или свой сервер для ESpeech-TTS). Так модель меняется без правок кода;
- kokoro: Kokoro-82M через kokoro-onnx (Apache-2.0), работает и на CPU;
- chatterbox: Chatterbox Multilingual (MIT) на PyTorch.
"""

from __future__ import annotations

import io
import math
import wave
from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass
class Audio:
    samples: np.ndarray  # float32 моно
    sample_rate: int

    @property
    def duration(self) -> float:
        return len(self.samples) / self.sample_rate


class Synthesizer(Protocol):
    name: str
    stress_style: str  # plus | acute | none

    def synthesize(self, text: str, *, lang: str, voice: str | None, speed: float) -> Audio: ...

    def voices(self) -> list[str]: ...


class MockSynthesizer:
    name = "mock"
    stress_style = "none"

    def synthesize(self, text: str, *, lang: str, voice: str | None, speed: float) -> Audio:
        rate = 24000
        seconds = min(15.0, max(0.25, len(text) / 14.0 / max(speed, 0.5)))
        t = np.arange(int(rate * seconds)) / rate
        freq = 440.0 if lang == "ru" else 520.0
        samples = (0.2 * np.sin(2 * math.pi * freq * t)).astype(np.float32)
        fade = min(len(samples), rate // 50)
        samples[:fade] *= np.linspace(0, 1, fade)
        samples[-fade:] *= np.linspace(1, 0, fade)
        return Audio(samples, rate)

    def voices(self) -> list[str]:
        return ["mock"]


def decode_wav(data: bytes) -> Audio:
    with wave.open(io.BytesIO(data)) as w:
        rate = w.getframerate()
        frames = w.readframes(w.getnframes())
        width = w.getsampwidth()
        channels = w.getnchannels()
    if width != 2:
        raise ValueError("ожидается WAV 16 бит")
    s = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
    if channels > 1:
        s = s.reshape(-1, channels).mean(axis=1)
    return Audio(s, rate)


class OpenAISpeechSynthesizer:
    name = "openai_speech"

    def __init__(self, base_url: str, model: str, default_voice: str, stress_style: str = "none",
                 api_key: str = "not-needed") -> None:
        import httpx

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.default_voice = default_voice
        self.stress_style = stress_style
        self._client = httpx.Client(timeout=httpx.Timeout(60.0, connect=5.0),
                                    headers={"Authorization": f"Bearer {api_key}"})

    def synthesize(self, text: str, *, lang: str, voice: str | None, speed: float) -> Audio:
        resp = self._client.post(f"{self.base_url}/audio/speech", json={
            "model": self.model, "input": text, "voice": voice or self.default_voice, "speed": speed,
            "response_format": "wav",
        })
        resp.raise_for_status()
        return decode_wav(resp.content)

    def voices(self) -> list[str]:
        return [self.default_voice]


class KokoroSynthesizer:
    name = "kokoro"
    stress_style = "none"

    def __init__(self, model_path: str, voices_path: str, default_voice: str = "af_heart") -> None:
        from kokoro_onnx import Kokoro

        self.k = Kokoro(model_path, voices_path)
        self.default_voice = default_voice

    def synthesize(self, text: str, *, lang: str, voice: str | None, speed: float) -> Audio:
        samples, rate = self.k.create(text, voice=voice or self.default_voice, speed=speed,
                                      lang="ru" if lang == "ru" else "en-us")
        return Audio(np.asarray(samples, dtype=np.float32), int(rate))

    def voices(self) -> list[str]:
        try:
            return sorted(self.k.get_voices())
        except AttributeError:
            return [self.default_voice]


class ChatterboxSynthesizer:
    name = "chatterbox"
    stress_style = "none"

    def __init__(self, device: str = "cuda", voice_prompts: dict[str, str] | None = None) -> None:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        self.model = ChatterboxMultilingualTTS.from_pretrained(device=device)
        self.prompts = voice_prompts or {}

    def synthesize(self, text: str, *, lang: str, voice: str | None, speed: float) -> Audio:
        prompt = self.prompts.get(voice or "", None)
        wav = self.model.generate(text, language_id=lang, audio_prompt_path=prompt)
        samples = wav.squeeze().detach().cpu().numpy().astype(np.float32)
        return Audio(samples, int(self.model.sr))

    def voices(self) -> list[str]:
        return ["default", *self.prompts]


def change_speed(audio: Audio, speed: float) -> Audio:
    """Грубое изменение темпа для бэкендов без параметра скорости (через передискретизацию)."""
    if abs(speed - 1.0) < 0.05:
        return audio
    n = int(len(audio.samples) / speed)
    x = np.linspace(0, len(audio.samples) - 1, n)
    return Audio(np.interp(x, np.arange(len(audio.samples)), audio.samples).astype(np.float32), audio.sample_rate)


def resample(audio: Audio, rate: int) -> Audio:
    if audio.sample_rate == rate:
        return audio
    n = int(audio.duration * rate)
    x_new = np.linspace(0, audio.duration, n, endpoint=False)
    x_old = np.linspace(0, audio.duration, len(audio.samples), endpoint=False)
    return Audio(np.interp(x_new, x_old, audio.samples).astype(np.float32), rate)
