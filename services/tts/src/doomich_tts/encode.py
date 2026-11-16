"""Упаковка звука: WAV и Ogg/Opus (libopus через ctypes, свой минимальный мультиплексор Ogg).

Ogg/Opus в 8-10 раз легче WAV и играется на Android (ExoPlayer) и в libmpv на ПК.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import io
import random
import struct
import wave

import numpy as np

OPUS_APPLICATION_VOIP = 2048
OPUS_SET_BITRATE = 4002


def to_pcm16(audio: np.ndarray) -> bytes:
    return (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2").tobytes()


def wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(to_pcm16(audio))
    return buf.getvalue()


def _crc_table() -> list[int]:
    table = []
    for i in range(256):
        r = i << 24
        for _ in range(8):
            r = ((r << 1) ^ 0x04C11DB7) if r & 0x80000000 else (r << 1)
        table.append(r & 0xFFFFFFFF)
    return table


CRC = _crc_table()


def ogg_crc(data: bytes) -> int:
    crc = 0
    for b in data:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ CRC[((crc >> 24) & 0xFF) ^ b]
    return crc


def ogg_page(serial: int, seq: int, granule: int, packets: list[bytes], header_type: int) -> bytes:
    lacing = b""
    for p in packets:
        n = len(p)
        lacing += b"\xff" * (n // 255) + bytes([n % 255])
    head = struct.pack("<4sBBqIIIB", b"OggS", 0, header_type, granule, serial, seq, 0, len(lacing))
    page = head + lacing + b"".join(packets)
    crc = ogg_crc(page)
    return page[:22] + struct.pack("<I", crc) + page[26:]


class OpusEncoder:
    def __init__(self, sample_rate: int = 24000, bitrate: int = 24000) -> None:
        path = ctypes.util.find_library("opus")
        if not path:
            raise RuntimeError("libopus не найдена")
        lib = ctypes.CDLL(path)
        lib.opus_encoder_create.restype = ctypes.c_void_p
        lib.opus_encoder_create.argtypes = [ctypes.c_int32, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        lib.opus_encode.restype = ctypes.c_int32
        lib.opus_encode.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int16), ctypes.c_int, ctypes.c_char_p,
                                    ctypes.c_int32]
        lib.opus_encoder_ctl.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int32]
        lib.opus_encoder_destroy.argtypes = [ctypes.c_void_p]
        if sample_rate not in (8000, 12000, 16000, 24000, 48000):
            raise ValueError("Opus поддерживает 8, 12, 16, 24 и 48 кГц")
        err = ctypes.c_int()
        self._enc = lib.opus_encoder_create(sample_rate, 1, OPUS_APPLICATION_VOIP, ctypes.byref(err))
        if err.value != 0:
            raise RuntimeError(f"opus_encoder_create: {err.value}")
        lib.opus_encoder_ctl(self._enc, OPUS_SET_BITRATE, bitrate)
        self._lib = lib
        self.sample_rate = sample_rate
        self.frame = sample_rate // 50  # 20 мс

    def encode_ogg(self, audio: np.ndarray) -> bytes:
        pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        pad = (-len(pcm)) % self.frame
        if pad:
            pcm = np.concatenate([pcm, np.zeros(pad, dtype=np.int16)])
        serial = random.randint(1, 2**31 - 1)
        pre_skip = 312
        head = b"OpusHead" + struct.pack("<BBHIhB", 1, 1, pre_skip, self.sample_rate, 0, 0)
        tags = b"OpusTags" + struct.pack("<I", 7) + b"doomich" + struct.pack("<I", 0)
        out = [ogg_page(serial, 0, 0, [head], 0x02), ogg_page(serial, 1, 0, [tags], 0x00)]
        buf = ctypes.create_string_buffer(4000)
        seq = 2
        granule = 0
        packets: list[bytes] = []
        total = len(pcm) // self.frame
        for i in range(total):
            chunk = np.ascontiguousarray(pcm[i * self.frame : (i + 1) * self.frame])
            n = self._lib.opus_encode(self._enc, chunk.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), self.frame,
                                      buf, 4000)
            if n < 0:
                raise RuntimeError(f"opus_encode: {n}")
            packets.append(buf.raw[:n])
            # Гранула Ogg/Opus всегда в отсчётах 48 кГц
            granule += 960
            last = i == total - 1
            if len(packets) == 25 or last:
                out.append(ogg_page(serial, seq, granule + pre_skip, packets, 0x04 if last else 0x00))
                seq += 1
                packets = []
        return b"".join(out)

    def close(self) -> None:
        if getattr(self, "_enc", None):
            self._lib.opus_encoder_destroy(self._enc)
            self._enc = None

    def __del__(self) -> None:
        self.close()


def opus_available() -> bool:
    return bool(ctypes.util.find_library("opus"))
