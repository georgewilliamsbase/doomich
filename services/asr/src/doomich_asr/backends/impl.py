"""Реализации распознавателей.

- sherpa: sherpa-onnx с ONNX-экспортом GigaAM-v3 (или T-one, Whisper). Аудио передаётся
  массивом, на диск ничего не пишется. Основной вариант для продакшена.
- gigaam: оригинальная модель GigaAM на PyTorch. Пакет читает аудио из файла, поэтому
  запись кладётся в /dev/shm (оперативная память) и сразу удаляется.
- faster_whisper: Whisper large-v3-turbo для английского.
- mock: для тестов и разработки без моделей.
"""

from __future__ import annotations

import os
import tempfile
import wave
from pathlib import Path

import numpy as np

from doomich_asr.backends.base import Result, Segment, split_on_silence


class MockRecognizer:
    name = "mock"

    def __init__(self, text: str = "что у меня завтра") -> None:
        self.text = text

    def transcribe(self, audio: np.ndarray, *, sample_rate: int, lang: str, timestamps: bool,
                   prompt: str | None = None) -> Result:
        if len(audio) == 0 or float(np.sqrt(np.mean(audio**2))) < 0.004:
            return Result(text="", lang=lang if lang != "auto" else "ru")
        duration = len(audio) / sample_rate
        segs = [Segment(0.0, round(duration, 2), self.text)] if timestamps else []
        return Result(text=self.text, lang=lang if lang != "auto" else "ru", segments=segs)


class SherpaRecognizer:
    """config: model_dir с encoder/decoder/joiner (RNNT) или model.onnx (CTC) и tokens.txt."""

    name = "sherpa"

    def __init__(self, model_dir: str, kind: str = "nemo_transducer", device: str = "cpu", threads: int = 4,
                 lang: str = "ru") -> None:
        import sherpa_onnx

        d = Path(model_dir)
        provider = "cuda" if device.startswith("cuda") else "cpu"
        if kind == "nemo_ctc":
            self.rec = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
                model=str(d / "model.onnx"), tokens=str(d / "tokens.txt"), num_threads=threads, provider=provider)
        elif kind == "whisper":
            self.rec = sherpa_onnx.OfflineRecognizer.from_whisper(
                encoder=str(d / "encoder.onnx"), decoder=str(d / "decoder.onnx"), tokens=str(d / "tokens.txt"),
                language=lang, num_threads=threads, provider=provider)
        else:
            self.rec = sherpa_onnx.OfflineRecognizer.from_transducer(
                encoder=str(d / "encoder.onnx"), decoder=str(d / "decoder.onnx"), joiner=str(d / "joiner.onnx"),
                tokens=str(d / "tokens.txt"), num_threads=threads, provider=provider, model_type="nemo_transducer")
        self.lang = lang

    def _one(self, audio: np.ndarray, sr: int) -> str:
        stream = self.rec.create_stream()
        stream.accept_waveform(sr, audio)
        self.rec.decode_stream(stream)
        return str(stream.result.text).strip()

    def transcribe(self, audio: np.ndarray, *, sample_rate: int, lang: str, timestamps: bool,
                   prompt: str | None = None) -> Result:
        segments: list[Segment] = []
        texts: list[str] = []
        for a, b in split_on_silence(audio, sample_rate):
            text = self._one(audio[a:b], sample_rate)
            if text:
                texts.append(text)
                segments.append(Segment(round(a / sample_rate, 2), round(b / sample_rate, 2), text))
        return Result(text=" ".join(texts), lang=self.lang, segments=segments if timestamps else [])


class GigaAMRecognizer:
    name = "gigaam"

    def __init__(self, model_name: str = "v3_e2e_rnnt", device: str = "cuda", tmp_dir: str = "/dev/shm") -> None:
        import gigaam

        self.model = gigaam.load_model(model_name, device=device)
        self.tmp_dir = tmp_dir if os.path.isdir(tmp_dir) else None

    def _one(self, audio: np.ndarray, sr: int) -> str:
        fd, path = tempfile.mkstemp(suffix=".wav", dir=self.tmp_dir)
        try:
            with os.fdopen(fd, "wb") as f, wave.open(f, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(sr)
                w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
            return str(self.model.transcribe(path)).strip()
        finally:
            Path(path).unlink(missing_ok=True)

    def transcribe(self, audio: np.ndarray, *, sample_rate: int, lang: str, timestamps: bool,
                   prompt: str | None = None) -> Result:
        segments: list[Segment] = []
        texts: list[str] = []
        for a, b in split_on_silence(audio, sample_rate):
            text = self._one(audio[a:b], sample_rate)
            if text:
                texts.append(text)
                segments.append(Segment(round(a / sample_rate, 2), round(b / sample_rate, 2), text))
        return Result(text=" ".join(texts), lang="ru", segments=segments if timestamps else [])


class WhisperRecognizer:
    name = "faster_whisper"

    def __init__(self, model: str = "large-v3-turbo", device: str = "cuda", compute_type: str = "float16") -> None:
        from faster_whisper import WhisperModel

        self.model = WhisperModel(model, device="cuda" if device.startswith("cuda") else "cpu",
                                  compute_type=compute_type if device.startswith("cuda") else "int8")

    def detect(self, audio: np.ndarray) -> str:
        _, info = self.model.transcribe(audio[: 16000 * 10], beam_size=1, without_timestamps=True)
        return str(info.language)

    def transcribe(self, audio: np.ndarray, *, sample_rate: int, lang: str, timestamps: bool,
                   prompt: str | None = None) -> Result:
        language = None if lang == "auto" else lang
        segs, info = self.model.transcribe(audio, language=language, beam_size=5, vad_filter=True,
                                           initial_prompt=prompt, without_timestamps=not timestamps)
        out = [Segment(round(s.start, 2), round(s.end, 2), s.text.strip()) for s in segs]
        return Result(text=" ".join(s.text for s in out).strip(), lang=str(info.language),
                      segments=out if timestamps else [])
