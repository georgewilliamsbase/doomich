"""Настройки Core API.

Все параметры читаются из переменных окружения с префиксом DOOMICH_.
Секреты можно передавать файлами (docker secrets): например,
DOOMICH_JWT_SECRET берётся из /run/secrets/doomich_jwt_secret, если файл есть.
"""

from __future__ import annotations

import base64
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Env = Literal["dev", "test", "stage", "prod"]
AIBackend = Literal["vllm", "openai", "mock"]


def _secrets_dir() -> str | None:
    path = os.environ.get("DOOMICH_SECRETS_DIR", "/run/secrets")
    return path if os.path.isdir(path) else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DOOMICH_",
        env_file=".env",
        extra="ignore",
        secrets_dir=_secrets_dir(),
    )

    env: Env = "dev"
    public_base_url: str = "http://localhost:8000"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # БД. app работает под ролью без BYPASSRLS, sys под ролью с BYPASSRLS
    # (воркеры, админ-API, регистрация и вход до того, как известен пользователь).
    database_url: str = "postgresql+asyncpg://doomich_app:doomich@localhost:5432/doomich"
    database_sys_url: str = "postgresql+asyncpg://doomich_sys:doomich@localhost:5432/doomich"
    database_migrate_url: str | None = None
    db_pool_size: int = 10
    db_null_pool: bool = False

    # Valkey (протокол Redis). "memory://" включает хранилище в памяти для тестов.
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str | None = None
    celery_eager: bool = False

    # Секреты
    jwt_secret: SecretStr = SecretStr("dev-only-jwt-secret-change-me-0123456789")
    # Мастер-ключи прикладного шифрования: "kid:base64,kid2:base64". Первый ключ активный.
    master_keys: SecretStr = SecretStr("dev1:" + base64.b64encode(b"d" * 32).decode())
    # Перец для хэшей кодов приглашения (поиск по хэшу должен быть детерминированным)
    invite_pepper: SecretStr = SecretStr("dev-invite-pepper")

    access_token_ttl_sec: int = 15 * 60
    refresh_token_ttl_days: int = 30
    admin_token_ttl_sec: int = 8 * 3600
    refresh_reuse_grace_sec: int = 10

    # Argon2id. В тестах параметры понижаются, чтобы тесты шли быстро.
    argon2_time_cost: int = 3
    argon2_memory_kib: int = 64 * 1024
    argon2_parallelism: int = 2

    data_dir: Path = Path("./var/data")

    # ИИ-сервисы
    llm_backend: AIBackend = "mock"
    llm_url: str = "http://vllm-llm:8000/v1"
    llm_model: str = "qwen3.6-35b-a3b"
    llm_api_key: SecretStr = SecretStr("not-needed")
    llm_max_tokens: int = 1200
    llm_temperature: float = 0.4
    llm_context_tokens: int = 16000
    llm_timeout_sec: float = 120.0

    embed_backend: AIBackend = "mock"
    embed_url: str = "http://vllm-embed:8000/v1"
    embed_model: str = "qwen3-embedding-0.6b"
    embed_dim: int = 1024

    rerank_backend: Literal["vllm", "mock", "none"] = "mock"
    # Порог оценки реранкера: ниже него фрагмент считается нерелевантным ("в документах нет").
    # Подбирается по оценочному набору RAG для конкретной модели реранкера.
    rag_min_score: float = 0.05
    rerank_url: str = "http://vllm-rerank:8000/v1"
    rerank_model: str = "qwen3-reranker-0.6b"

    asr_backend: Literal["http", "mock"] = "mock"
    asr_url: str = "http://asr:8000"
    tts_backend: Literal["http", "mock"] = "mock"
    tts_url: str = "http://tts:8000"
    tts_format: Literal["ogg_opus", "wav"] = "wav"
    nav_backend: Literal["http", "mock"] = "mock"
    nav_url: str = "http://nav:8000"

    # Разбор документов
    parser_backend: Literal["auto", "docling", "basic"] = "auto"
    clamd_host: str | None = None
    clamd_port: int = 3310
    ocr_enabled: bool = False

    # Лимиты (значения из плана R1)
    max_document_mb: int = 20
    max_document_pages: int = 300
    max_documents_per_user: int = 50
    max_message_chars: int = 8000
    messages_per_minute: int = 12
    messages_per_day: int = 400
    voice_max_seconds: int = 60
    login_attempts_per_minute: int = 5
    login_attempts_per_hour: int = 20

    # Лекции (R1.1)
    lecture_max_mb: int = 500
    lecture_max_seconds: int = 2 * 3600
    lecture_month_seconds: int = 10 * 3600

    sentry_dsn: str | None = None
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @property
    def is_prod_like(self) -> bool:
        return self.env in ("stage", "prod")

    @property
    def migrate_url(self) -> str:
        return self.database_migrate_url or self.database_sys_url

    def mock_components(self) -> list[str]:
        """Компоненты, которые работают в режиме заглушек."""
        pairs = {
            "llm": self.llm_backend,
            "embeddings": self.embed_backend,
            "reranker": self.rerank_backend,
            "asr": self.asr_backend,
            "tts": self.tts_backend,
            "nav": self.nav_backend,
        }
        return [name for name, backend in pairs.items() if backend == "mock"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def override_settings(settings: Settings) -> None:
    """Подменяет настройки (используется в тестах и CLI)."""
    get_settings.cache_clear()
    _override["value"] = settings


_override: dict[str, Settings] = {}


def settings() -> Settings:
    if "value" in _override:
        return _override["value"]
    return get_settings()
