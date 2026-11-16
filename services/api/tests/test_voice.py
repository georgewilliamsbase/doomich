from __future__ import annotations

import json
import math
import struct
from datetime import date, datetime, timedelta

import pytest
from starlette.testclient import TestClient

from doomich.voice.text import SentenceSplitter, to_speakable
from tests.conftest import register


def tone(seconds: float = 1.0, rate: int = 16000) -> bytes:
    return b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 300 * i / rate)))
                    for i in range(int(seconds * rate)))


def collect(ws) -> tuple[list[dict], list[bytes]]:  # type: ignore[no-untyped-def]
    msgs, audio = [], []
    while True:
        m = ws.receive()
        if m.get("bytes") is not None:
            audio.append(m["bytes"])
            continue
        data = json.loads(m["text"])
        msgs.append(data)
        if data["type"] in ("done", "error"):
            return msgs, audio


async def _setup(client, env):
    from doomich.common.timeutil import tz
    from doomich.db import get_db
    from doomich.models import Tenant
    from doomich.schedule.records import LessonRecord
    from doomich.schedule.sync import apply_records, manual_source

    zone = tz("Europe/Moscow")
    d = date.today() + timedelta(days=1)
    async with get_db().sys_session() as s:
        tenant = await s.get(Tenant, env.tenant_id)
        src = await manual_source(s, env.tenant_id)
        await apply_records(s, tenant=tenant, source=src, force=True, records=[LessonRecord(
            group="ИВТ-21", subject="Матанализ", room="305",
            starts_at=datetime(d.year, d.month, d.day, 8, 30, tzinfo=zone),
            ends_at=datetime(d.year, d.month, d.day, 10, 0, tzinfo=zone))])
    user = await register(client, env.codes[0])
    chat = (await client.post("/v1/chats", json={}, headers=user["headers"])).json()
    return user, chat


async def test_push_to_talk_roundtrip(app, client, env):
    user, chat = await _setup(client, env)
    with TestClient(app) as tc, tc.websocket_connect("/v1/voice", headers=user["headers"]) as ws:
        assert json.loads(ws.receive_text())["type"] == "ready"
        ws.send_text(json.dumps({"type": "start", "chat_id": chat["id"], "codec": "pcm16", "lang": "ru"}))
        pcm = tone(1.2)
        for i in range(0, len(pcm), 3200):
            ws.send_bytes(pcm[i : i + 3200])
        ws.send_text(json.dumps({"type": "end"}))
        msgs, audio = collect(ws)
    kinds = [m["type"] for m in msgs]
    assert kinds[0] == "transcript" and msgs[0]["text"] == "что у меня завтра"
    assert "answer_delta" in kinds and kinds[-1] == "done"
    done = msgs[-1]
    assert "Матанализ" in done["text"] and done["message_id"]
    assert audio and audio[0][0] == 0x41 and audio[0][5] == 1  # кадр "A", формат wav
    assert audio[0][6:10] == b"RIFF"
    assert "first_audio" in done["timings"]
    r = await client.get(f"/v1/chats/{chat['id']}/messages", headers=user["headers"])
    assert [m["mode"] for m in r.json()] == ["voice", "voice"]


async def test_silence_and_auth(app, client, env):
    user, _ = await _setup(client, env)
    with TestClient(app) as tc:
        with tc.websocket_connect("/v1/voice") as ws:
            ws.send_text(json.dumps({"type": "auth", "token": "bad"}))
            assert json.loads(ws.receive_text())["type"] == "error"
        with tc.websocket_connect("/v1/voice") as ws:
            ws.send_text(json.dumps({"type": "auth", "token": user["tokens"]["access_token"]}))
            assert json.loads(ws.receive_text())["type"] == "ready"
            ws.send_text(json.dumps({"type": "start", "codec": "pcm16", "tts": False}))
            ws.send_bytes(b"\x00\x00" * 16000)
            ws.send_text(json.dumps({"type": "end"}))
            msgs, _ = collect(ws)
            assert msgs[-1]["code"] == "no_speech"
            # Текстовый запрос через голосовой канал (без сохранения, без озвучки)
            ws.send_text(json.dumps({"type": "start", "text": "привет", "tts": False}))
            msgs, audio = collect(ws)
            assert msgs[-1]["type"] == "done" and not audio


def test_speakable_text():
    md = "## Итог\n**Сила** равна $m \\cdot a$ [1]. Код:\n```python\nprint(1)\n```\nСм. https://example.com"
    out = to_speakable(md)
    assert "**" not in out and "[1]" not in out and "```" not in out and "https" not in out
    assert "умножить на" in out and "Код показан на экране" in out


def test_sentence_splitter():
    sp = SentenceSplitter(min_chars=10)
    parts = []
    for chunk in ["Первое предложение, т.е. ", "длинное. Число 3.14 не режем. ", "Конец"]:
        parts += sp.feed(chunk)
    parts += sp.flush()
    assert parts == ["Первое предложение, т.е. длинное.", "Число 3.14 не режем.", "Конец"]


def test_opus_frames_split():
    from doomich.voice.audio import AudioError, split_opus_frames

    payload = struct.pack(">H", 3) + b"abc" + struct.pack(">H", 2) + b"de"
    assert split_opus_frames(payload) == [b"abc", b"de"]
    with pytest.raises(AudioError):
        split_opus_frames(struct.pack(">H", 10) + b"abc")


def test_opus_decode_if_available():
    import ctypes.util

    if not ctypes.util.find_library("opus"):
        pytest.skip("libopus не установлена")
    from doomich.voice.audio import OpusDecoder

    lib = ctypes.CDLL(ctypes.util.find_library("opus"))
    lib.opus_encoder_create.restype = ctypes.c_void_p
    lib.opus_encoder_create.argtypes = [ctypes.c_int32, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    lib.opus_encode.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int16), ctypes.c_int, ctypes.c_char_p,
                                ctypes.c_int32]
    err = ctypes.c_int()
    enc = lib.opus_encoder_create(16000, 1, 2048, ctypes.byref(err))
    frame = tone(0.02)
    samples = (ctypes.c_int16 * 320).from_buffer_copy(frame)
    out = ctypes.create_string_buffer(400)
    n = lib.opus_encode(enc, samples, 320, out, 400)
    assert n > 0
    pcm = OpusDecoder(16000).decode(out.raw[:n])
    assert len(pcm) == 640
