"""Голосовой шлюз (WebSocket /v1/voice).

Протокол описан в docs/api/voice-protocol.md. Кратко:
клиент: auth? -> start -> бинарные кадры аудио -> end | cancel
сервер: ready, transcript, answer_delta, tool, audio_meta + бинарный кадр, sources, done, error

Аудио пользователя живёт только в памяти этого соединения.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import struct
import time
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, ValidationError

from doomich import bindings
from doomich.ai.registry import get_ai
from doomich.chats import service as chats
from doomich.chats.router import model_version_for
from doomich.chats.schemas import ClientContextIn
from doomich.common.errors import AppError
from doomich.common.timeutil import local_now
from doomich.config import settings
from doomich.db import get_db
from doomich.deps import CurrentUser, authenticate, user_cipher_for
from doomich.observability.metrics import ACTIVE_VOICE, VOICE_STAGE, VOICE_TOTAL
from doomich.orchestrator.engine import HistoryItem, TurnResult, run_turn
from doomich.orchestrator.prompts import detect_lang
from doomich.orchestrator.tools import ClientContext, ToolContext
from doomich.security import kv
from doomich.voice.audio import AudioError, OpusDecoder, resample_pcm16, rms, split_opus_frames
from doomich.voice.text import SentenceSplitter, to_speakable

router = APIRouter(tags=["voice"])
log = logging.getLogger(__name__)

AUDIO_FRAME = 0x41  # "A"
FORMATS = {"wav": 1, "ogg_opus": 2}
SILENCE_RMS = 120.0


class StartMsg(BaseModel):
    type: str = "start"
    lang: str = Field(default="auto", pattern="^(auto|ru|en)$")
    chat_id: uuid.UUID | None = None
    mode: str = Field(default="ptt", pattern="^(ptt|handsfree)$")
    codec: str = Field(default="pcm16", pattern="^(pcm16|opus)$")
    sample_rate: int = Field(default=16000, ge=8000, le=48000)
    tts: bool = True
    voice: str | None = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    context: ClientContextIn = Field(default_factory=ClientContextIn)
    text: str | None = Field(default=None, max_length=4000)


class Turn:
    def __init__(self, start: StartMsg) -> None:
        self.start = start
        self.pcm = bytearray()
        self.decoder: OpusDecoder | None = None
        self.max_bytes = settings().voice_max_seconds * start.sample_rate * 2

    def add(self, payload: bytes) -> None:
        if self.start.codec == "opus":
            if self.decoder is None:
                self.decoder = OpusDecoder(self.start.sample_rate)
            for packet in split_opus_frames(payload):
                self.pcm.extend(self.decoder.decode(packet))
        else:
            self.pcm.extend(payload)
        if len(self.pcm) > self.max_bytes:
            raise AppError("слишком длинная запись", code="audio_too_long")

    def pcm16k(self) -> bytes:
        return resample_pcm16(bytes(self.pcm), self.start.sample_rate, 16000)


async def send_json(ws: WebSocket, data: dict[str, Any]) -> None:
    await ws.send_text(json.dumps(data, ensure_ascii=False, default=str))


def audio_frame(seq: int, fmt: str, data: bytes) -> bytes:
    return struct.pack(">BIB", AUDIO_FRAME, seq, FORMATS.get(fmt, 1)) + data


async def _auth(ws: WebSocket) -> CurrentUser:
    header = ws.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return await authenticate(header[7:].strip())
    raw = await asyncio.wait_for(ws.receive_text(), timeout=10)
    msg = json.loads(raw)
    if msg.get("type") != "auth" or not msg.get("token"):
        raise AppError("нужна авторизация", code="unauthorized", status_code=401)
    return await authenticate(str(msg["token"]))


async def process_turn(ws: WebSocket, user: CurrentUser, turn: Turn, end_ts: float) -> None:
    st = settings()
    ai = get_ai()
    start = turn.start
    timings: dict[str, float] = {}
    if start.text:
        question = start.text.strip()
        lang = detect_lang(question) if start.lang == "auto" else start.lang
    else:
        pcm = turn.pcm16k()
        if len(pcm) < 16000 * 2 * 0.3 or rms(pcm) < SILENCE_RMS:
            await send_json(ws, {"type": "error", "code": "no_speech", "message": "речь не распознана"})
            return
        asr_profile = await bindings.resolve("asr_profile", user.tenant_id)
        t0 = time.monotonic()
        tr = await ai.asr.transcribe(pcm, lang=start.lang,
                                     hotwords=(asr_profile.params.get("hotwords") if asr_profile else None),
                                     tenant=user.tenant.slug)
        timings["asr"] = time.monotonic() - t0
        VOICE_STAGE.labels(stage="asr").observe(timings["asr"])
        question = tr.text.strip()
        lang = tr.lang if tr.lang in ("ru", "en") else detect_lang(question)
        if not question:
            await send_json(ws, {"type": "error", "code": "no_speech", "message": "речь не распознана"})
            return
        await send_json(ws, {"type": "transcript", "text": question, "final": True})

    history: list[HistoryItem] = []
    chat = None
    if start.chat_id is not None and user.history_days > 0:
        async with get_db().user_session(user.id, user.tenant_id) as s:
            cipher = await user_cipher_for(s, user.id)
            chat = await chats.get_chat(s, start.chat_id)
            history = await chats.history(s, cipher, chat.id)
            await chats.add_message(s, cipher, chat=chat, user_id=user.id, role="user", content=question, mode="voice")
            doc_ids = list(chat.document_ids or [])
            lecture_id = chat.lecture_id
    else:
        doc_ids, lecture_id = [], None

    c = start.context
    ctx = ToolContext(
        user=user, client=ClientContext(group_id=c.group_id, subgroup=c.subgroup, teacher_key=c.teacher_key,
                                        campus_id=c.campus_id, location_node_id=c.location_node_id),
        now=local_now(user.tenant.timezone), lang=lang, document_ids=doc_ids, lecture_id=lecture_id,
    )
    model, version = await model_version_for(user)
    result = TurnResult(model_version=version)
    splitter = SentenceSplitter()
    voice_binding = await bindings.resolve("tts_voice", user.tenant_id)
    voice = start.voice or (voice_binding.model_ref if voice_binding else None)
    tts_queue: asyncio.Queue[str | None] = asyncio.Queue()
    first_audio_sent = asyncio.Event()

    async def tts_worker() -> None:
        seq = 0
        pending: list[asyncio.Task[Any]] = []

        async def synth(sentence: str) -> Any:
            return await ai.tts.synthesize(sentence, lang=lang, voice=voice, speed=start.speed,
                                           fmt=st.tts_format, tenant=user.tenant.slug)

        # Синтез следующего предложения начинается, пока играет предыдущее (до двух вперёд)
        while True:
            sentence = await tts_queue.get()
            if sentence is None:
                break
            pending.append(asyncio.create_task(synth(sentence)))
            pending_texts.append(sentence)
            while len(pending) >= 2 or (pending and pending[0].done()):
                seq = await _send_audio(pending.pop(0), pending_texts.pop(0), seq)
        while pending:
            seq = await _send_audio(pending.pop(0), pending_texts.pop(0), seq)

    pending_texts: list[str] = []

    async def _send_audio(task: asyncio.Task[Any], text: str, seq: int) -> int:
        audio = await task
        if not first_audio_sent.is_set():
            first_audio_sent.set()
            total = time.monotonic() - end_ts
            timings["first_audio"] = total
            VOICE_TOTAL.observe(total)
        await send_json(ws, {"type": "audio_meta", "seq": seq, "text": text, "format": audio.format,
                             "duration": round(audio.duration_sec, 2)})
        await ws.send_bytes(audio_frame(seq, audio.format, audio.data))
        return seq + 1

    worker = asyncio.create_task(tts_worker()) if start.tts else None
    t_llm = time.monotonic()
    try:
        async for ev in run_turn(ctx, question=question, history=history, mode="voice", model=model,
                                 tenant_prompt=user.tenant.settings.get("assistant_prompt"), result=result):
            if ev["type"] == "delta":
                if "first_token" not in timings:
                    timings["first_token"] = time.monotonic() - t_llm
                    VOICE_STAGE.labels(stage="first_token").observe(timings["first_token"])
                await send_json(ws, {"type": "answer_delta", "text": ev["text"]})
                if worker is not None:
                    for sentence in splitter.feed(ev["text"]):
                        speakable = to_speakable(sentence, lang)
                        if speakable:
                            await tts_queue.put(speakable)
            else:
                await send_json(ws, ev)
        if worker is not None:
            for sentence in splitter.flush():
                speakable = to_speakable(sentence, lang)
                if speakable:
                    await tts_queue.put(speakable)
            await tts_queue.put(None)
            await worker
    finally:
        if worker is not None and not worker.done():
            worker.cancel()

    message_id = None
    if chat is not None and result.text:
        async with get_db().user_session(user.id, user.tenant_id) as s:
            cipher = await user_cipher_for(s, user.id)
            fresh = await chats.get_chat(s, chat.id)
            msg = await chats.add_message(s, cipher, chat=fresh, user_id=user.id, role="assistant",
                                          content=result.text, mode="voice", sources=result.sources,
                                          model_version=version)
            message_id = str(msg.id)
    if result.sources:
        await send_json(ws, {"type": "sources", "items": result.sources})
    await send_json(ws, {"type": "done", "message_id": message_id, "chat_id": str(chat.id) if chat else None,
                         "model_version": version, "text": result.text,
                         "timings": {k: round(v, 3) for k, v in timings.items()}})


@router.websocket("/v1/voice")
async def voice(ws: WebSocket) -> None:
    await ws.accept()
    try:
        user = await _auth(ws)
    except (AppError, TimeoutError, json.JSONDecodeError, WebSocketDisconnect) as e:
        code = getattr(e, "code", "unauthorized")
        with contextlib.suppress(Exception):
            await send_json(ws, {"type": "error", "code": code, "message": "авторизация не пройдена"})
            await ws.close(code=4401)
        return
    ACTIVE_VOICE.inc()
    await send_json(ws, {"type": "ready"})
    turn: Turn | None = None
    task: asyncio.Task[None] | None = None
    try:
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break
            if msg.get("bytes") is not None:
                if turn is None:
                    continue
                try:
                    turn.add(msg["bytes"])
                except (AppError, AudioError) as e:
                    await send_json(ws, {"type": "error", "code": getattr(e, "code", "bad_audio"), "message": str(e)})
                    turn = None
                continue
            try:
                data = json.loads(msg.get("text") or "{}")
            except json.JSONDecodeError:
                continue
            kind = data.get("type")
            if kind == "ping":
                await send_json(ws, {"type": "pong"})
            elif kind == "start":
                if task is not None and not task.done():
                    task.cancel()
                try:
                    start = StartMsg.model_validate(data)
                except ValidationError:
                    await send_json(ws, {"type": "error", "code": "bad_start", "message": "неверный start"})
                    continue
                try:
                    await kv.hit(f"voice:{user.id}", settings().messages_per_minute, 60)
                except AppError as e:
                    await send_json(ws, e.to_dict()["error"] | {"type": "error"})
                    continue
                turn = Turn(start)
                if start.text:
                    task = asyncio.create_task(_guarded(ws, user, turn, time.monotonic()))
                    turn = None
            elif kind == "end":
                if turn is None:
                    continue
                current, turn = turn, None
                task = asyncio.create_task(_guarded(ws, user, current, time.monotonic()))
            elif kind == "cancel":
                turn = None
                if task is not None and not task.done():
                    task.cancel()
                await send_json(ws, {"type": "cancelled"})
    except WebSocketDisconnect:
        pass
    finally:
        ACTIVE_VOICE.dec()
        if task is not None and not task.done():
            task.cancel()


async def _guarded(ws: WebSocket, user: CurrentUser, turn: Turn, end_ts: float) -> None:
    try:
        await process_turn(ws, user, turn, end_ts)
    except asyncio.CancelledError:
        raise
    except AppError as e:
        with contextlib.suppress(Exception):
            await send_json(ws, {"type": "error", "code": e.code, "message": e.message})
    except Exception:
        log.exception("ошибка голосового запроса")
        with contextlib.suppress(Exception):
            await send_json(ws, {"type": "error", "code": "internal", "message": "внутренняя ошибка"})
