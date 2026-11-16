from __future__ import annotations

import io
import json
import math
import struct
import wave

import numpy as np
from fastapi.testclient import TestClient

from doomich_asr.app import create_app, settings
from doomich_asr.backends.base import split_on_silence
from doomich_asr.profiles import correct


def tone(seconds: float, rate: int = 16000) -> bytes:
    return b"".join(struct.pack("<h", int(6000 * math.sin(2 * math.pi * 220 * i / rate)))
                    for i in range(int(seconds * rate)))


def test_transcribe_pcm_and_wav(tmp_path, monkeypatch):
    monkeypatch.setenv("ASR_PROFILES_DIR", str(tmp_path))
    settings.cache_clear()
    (tmp_path / "demo.json").write_text(json.dumps({
        "tenant": "demo", "version": "v1", "hotwords": ["матанализ"], "corrections": {"у меня": "у меня"},
    }), encoding="utf-8")
    client = TestClient(create_app())
    r = client.post("/v1/transcribe?lang=ru&tenant=demo&timestamps=true", content=tone(1.0),
                    headers={"Content-Type": "audio/l16"})
    assert r.status_code == 200
    body = r.json()
    assert body["text"] == "что у меня завтра" and body["profile"] == "v1"
    assert body["segments"][0]["end"] == 1.0

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(48000)
        w.writeframes(tone(0.5, 48000) * 2)
    r = client.post("/v1/transcribe", content=buf.getvalue(), headers={"Content-Type": "audio/wav"})
    assert r.status_code == 200 and r.json()["duration"] > 0.4

    r = client.post("/v1/transcribe", content=b"\x00\x00" * 16000, headers={"Content-Type": "audio/l16"})
    assert r.json()["text"] == ""


def test_corrections_with_terms():
    text = "завтра мат анализ в деканати и потом физкультуро"
    out = correct(text, ["деканате", "физкультура", "матанализ"], {"мат анализ": "матанализ"})
    assert out == "завтра матанализ в деканате и потом физкультура"
    assert correct("простой текст", [], {}) == "простой текст"


def test_split_long_audio_on_silence():
    sr = 16000
    speech = np.full(sr * 20, 0.3, dtype=np.float32)
    silence = np.zeros(sr, dtype=np.float32)
    audio = np.concatenate([speech, silence, speech, silence, speech])
    parts = split_on_silence(audio, sr, max_sec=25)
    assert len(parts) == 3
    assert parts[0][0] == 0 and parts[-1][1] == len(audio)
    for a, b in parts:
        assert (b - a) <= 25 * sr
