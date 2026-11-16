"""Интерфейс распознавателя и общие типы."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Result:
    text: str
    lang: str
    segments: list[Segment] = field(default_factory=list)


class Recognizer(Protocol):
    name: str

    def transcribe(self, audio: np.ndarray, *, sample_rate: int, lang: str, timestamps: bool,
                   prompt: str | None = None) -> Result: ...


def pcm16_to_float(pcm: bytes) -> np.ndarray:
    data = np.frombuffer(pcm[: len(pcm) // 2 * 2], dtype="<i2")
    return (data.astype(np.float32) / 32768.0).copy()


def wav_to_float(data: bytes) -> tuple[np.ndarray, int]:
    import io
    import wave

    with wave.open(io.BytesIO(data)) as w:
        if w.getsampwidth() != 2:
            raise ValueError("нужен WAV 16 бит")
        rate = w.getframerate()
        channels = w.getnchannels()
        frames = w.readframes(w.getnframes())
    audio = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    return audio, rate


def resample(audio: np.ndarray, src: int, dst: int = 16000) -> np.ndarray:
    if src == dst or len(audio) == 0:
        return audio
    duration = len(audio) / src
    n = int(duration * dst)
    x_old = np.linspace(0, duration, num=len(audio), endpoint=False)
    x_new = np.linspace(0, duration, num=n, endpoint=False)
    return np.interp(x_new, x_old, audio).astype(np.float32)


def split_on_silence(audio: np.ndarray, sr: int, max_sec: float = 25.0, frame_ms: int = 30) -> list[tuple[int, int]]:
    """Режет длинную запись на куски до max_sec по самым тихим местам (энергетический VAD).

    Модели вроде GigaAM лучше всего работают на фразах до 25-30 секунд.
    """
    n = len(audio)
    if n <= max_sec * sr:
        return [(0, n)]
    frame = int(sr * frame_ms / 1000)
    energy = np.array([float(np.mean(audio[i : i + frame] ** 2)) for i in range(0, n - frame, frame)])
    pieces: list[tuple[int, int]] = []
    start = 0
    limit = int(max_sec * sr)
    while n - start > limit:
        lo = start + limit // 2
        hi = start + limit
        f_lo, f_hi = lo // frame, min(hi // frame, len(energy) - 1)
        if f_hi <= f_lo:
            cut = hi
        else:
            cut = (f_lo + int(np.argmin(energy[f_lo:f_hi]))) * frame
        pieces.append((start, cut))
        start = cut
    pieces.append((start, n))
    return pieces
