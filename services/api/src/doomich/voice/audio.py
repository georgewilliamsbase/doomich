"""Декодирование входящего аудио: PCM16 или пакеты Opus (libopus через ctypes)."""

from __future__ import annotations

import ctypes
import ctypes.util
import struct

import numpy as np


class AudioError(Exception):
    pass


class OpusDecoder:
    """Минимальная обёртка над libopus: только декодирование моно-пакетов."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        path = ctypes.util.find_library("opus")
        if not path:
            raise AudioError("libopus не найдена, установите пакет libopus0")
        self._lib = ctypes.CDLL(path)
        self._lib.opus_decoder_create.restype = ctypes.c_void_p
        self._lib.opus_decoder_create.argtypes = [ctypes.c_int32, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        self._lib.opus_decode.restype = ctypes.c_int
        self._lib.opus_decode.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int32,
                                          ctypes.POINTER(ctypes.c_int16), ctypes.c_int, ctypes.c_int]
        self._lib.opus_decoder_destroy.argtypes = [ctypes.c_void_p]
        err = ctypes.c_int()
        self._dec = self._lib.opus_decoder_create(sample_rate, channels, ctypes.byref(err))
        if err.value != 0 or not self._dec:
            raise AudioError(f"opus_decoder_create: {err.value}")
        self.sample_rate = sample_rate
        self._max = sample_rate * 120 // 1000  # максимум 120 мс в пакете
        self._out = (ctypes.c_int16 * self._max)()

    def decode(self, packet: bytes) -> bytes:
        n = self._lib.opus_decode(self._dec, packet, len(packet), self._out, self._max, 0)
        if n < 0:
            raise AudioError(f"opus_decode: {n}")
        return bytes(memoryview(self._out).cast("B")[: n * 2])

    def close(self) -> None:
        if getattr(self, "_dec", None):
            self._lib.opus_decoder_destroy(self._dec)
            self._dec = None

    def __del__(self) -> None:
        self.close()


def split_opus_frames(payload: bytes) -> list[bytes]:
    """Кадр WebSocket содержит несколько пакетов Opus с 2-байтовым префиксом длины (big-endian)."""
    packets: list[bytes] = []
    i = 0
    while i + 2 <= len(payload):
        (size,) = struct.unpack(">H", payload[i : i + 2])
        i += 2
        if size == 0 or i + size > len(payload):
            raise AudioError("битый кадр Opus")
        packets.append(payload[i : i + size])
        i += size
    return packets


def resample_pcm16(pcm: bytes, src_rate: int, dst_rate: int = 16000) -> bytes:
    if src_rate == dst_rate or not pcm:
        return pcm
    samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32)
    duration = len(samples) / src_rate
    n_out = int(duration * dst_rate)
    if n_out <= 1:
        return b""
    x_old = np.linspace(0, duration, num=len(samples), endpoint=False)
    x_new = np.linspace(0, duration, num=n_out, endpoint=False)
    out = np.interp(x_new, x_old, samples)
    return np.clip(out, -32768, 32767).astype("<i2").tobytes()


def rms(pcm: bytes) -> float:
    if len(pcm) < 2:
        return 0.0
    s = np.frombuffer(pcm[: len(pcm) // 2 * 2], dtype="<i2").astype(np.float32)
    return float(np.sqrt(np.mean(s * s)))
