"""Метрики Prometheus. Только агрегаты, без идентификаторов пользователей."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

REQUESTS = Counter("doomich_http_requests_total", "HTTP запросы", ["route", "method", "status"])
LATENCY = Histogram(
    "doomich_http_request_seconds", "Длительность HTTP запросов", ["route", "method"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30),
)
FIRST_TOKEN = Histogram(
    "doomich_llm_first_token_seconds", "Время до первого токена ответа", ["mode"],
    buckets=(0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 5, 10),
)
LLM_TOKENS = Counter("doomich_llm_tokens_total", "Токены LLM", ["kind"])
TOOL_CALLS = Counter("doomich_tool_calls_total", "Вызовы инструментов", ["tool", "status"])
VOICE_STAGE = Histogram(
    "doomich_voice_stage_seconds", "Этапы голосового запроса", ["stage"],
    buckets=(0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 5),
)
VOICE_TOTAL = Histogram(
    "doomich_voice_end_to_audio_seconds", "От конца речи до первого звука",
    buckets=(0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 8),
)
DOCS_PROCESSED = Counter("doomich_documents_processed_total", "Обработанные документы", ["status", "kind"])
DOC_SECONDS = Histogram("doomich_document_processing_seconds", "Время обработки документа",
                        buckets=(1, 5, 10, 30, 60, 120, 300, 600))
SCHEDULE_SYNC = Counter("doomich_schedule_sync_total", "Синхронизации расписания", ["status"])
FEEDBACK = Counter("doomich_feedback_total", "Оценки ответов", ["rating"])
ACTIVE_VOICE = Gauge("doomich_voice_sessions", "Открытые голосовые сессии")
REGISTRATIONS = Counter("doomich_registrations_total", "Регистрации", ["role"])
