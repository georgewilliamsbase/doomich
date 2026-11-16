"""Сборка ИИ-клиентов по настройкам. Тесты подменяют их через set_ai()."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from doomich.ai.llm import ChatLLM, MockLLM, OpenAICompatLLM
from doomich.ai.retrieval import (
    Embedder,
    HashEmbedder,
    LexicalReranker,
    NoReranker,
    OpenAICompatEmbedder,
    OpenAICompatReranker,
    Reranker,
)
from doomich.ai.speech import ASR, TTS, HttpASR, HttpTTS, MockASR, MockTTS
from doomich.config import Settings, settings

log = logging.getLogger(__name__)


@dataclass
class AIServices:
    llm: ChatLLM
    embedder: Embedder
    reranker: Reranker
    asr: ASR
    tts: TTS
    llm_model: str


def build_ai(s: Settings) -> AIServices:
    llm: ChatLLM
    if s.llm_backend == "mock":
        llm = MockLLM()
    else:
        llm = OpenAICompatLLM(s.llm_url, s.llm_model, s.llm_api_key.get_secret_value(),
                              timeout=s.llm_timeout_sec, max_tokens=s.llm_max_tokens,
                              temperature=s.llm_temperature)
    embedder: Embedder = (
        HashEmbedder(s.embed_dim) if s.embed_backend == "mock"
        else OpenAICompatEmbedder(s.embed_url, s.embed_model, s.embed_dim)
    )
    reranker: Reranker
    if s.rerank_backend == "mock":
        reranker = LexicalReranker()
    elif s.rerank_backend == "none":
        reranker = NoReranker()
    else:
        reranker = OpenAICompatReranker(s.rerank_url, s.rerank_model)
    asr: ASR = MockASR() if s.asr_backend == "mock" else HttpASR(s.asr_url)
    tts: TTS = MockTTS() if s.tts_backend == "mock" else HttpTTS(s.tts_url)
    mocks = s.mock_components()
    if mocks:
        log.warning("ИИ-компоненты в режиме заглушек: %s", ", ".join(mocks))
    return AIServices(llm=llm, embedder=embedder, reranker=reranker, asr=asr, tts=tts,
                      llm_model="mock-llm" if s.llm_backend == "mock" else s.llm_model)


_ai: dict[str, AIServices] = {}


def get_ai() -> AIServices:
    if "default" not in _ai:
        _ai["default"] = build_ai(settings())
    return _ai["default"]


def set_ai(ai: AIServices | None) -> None:
    if ai is None:
        _ai.pop("default", None)
    else:
        _ai["default"] = ai
