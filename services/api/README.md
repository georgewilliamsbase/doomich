# Core API

FastAPI-сервис: аккаунты без ПД, вузы, чаты и оркестратор ИИ, расписание, документы (RAG), голосовой шлюз, админ-API и фоновые задачи Celery. Всё в одном Python-пакете `doomich`, API и воркеры запускаются из одного образа разными командами.

## Модули

| Каталог | Что внутри |
|---|---|
| `accounts/` | регистрация по коду приглашения, вход, refresh-токены с ротацией, восстановление по коду, вход на ПК по QR |
| `chats/` | чаты, сообщения (шифруются ключом пользователя), SSE-поток ответа, инкогнито, оценки |
| `orchestrator/` | системные промпты, белый список инструментов, цикл "модель и инструменты", ссылки на источники |
| `schedule/` | модель расписания, импорт Excel/CSV/iCal, адаптеры источников, сравнение версий, инструменты ассистента |
| `documents/` | загрузка, антивирус, разбор (Docling или лёгкие разборщики), нарезка, эмбеддинги, гибридный поиск |
| `voice/` | WebSocket `/v1/voice`: PCM16/Opus, ASR, потоковый ответ, озвучка по предложениям |
| `admin/` | админ-API с TOTP, журнал действий, печать кодов приглашения |
| `ai/` | клиенты LLM, эмбеддингов, реранкера, ASR, TTS и их заглушки |
| `worker/` | Celery: очереди, периодические задачи, постановка задач |
| `security/` | Argon2id, JWT, AES-256-GCM, лимиты частоты |

Схема БД лежит в `migrations/versions`. Таблицы с данными пользователей закрыты политиками Row-Level Security, API работает под ролью без права обходить RLS.

## Запуск локально

Нужны PostgreSQL 16+ с расширением pgvector и Valkey (или Redis). Проще всего поднять весь стек из корня репозитория командой `make dev`. Если хочется запускать API из IDE:

```bash
uv sync
```

```bash
export DOOMICH_DATABASE_URL=postgresql+asyncpg://doomich_app:doomich@localhost:5432/doomich
export DOOMICH_DATABASE_SYS_URL=postgresql+asyncpg://doomich_sys:doomich@localhost:5432/doomich
uv run doomich-manage migrate
uv run doomich-manage seed-demo
uv run uvicorn --factory doomich.main:create_app --reload
```

Роли БД создаёт скрипт `infra/compose/postgres/init.sql`: `doomich_sys` (владелец схемы, BYPASSRLS, миграции и воркеры) и `doomich_app` (API, только через RLS).

Без GPU все ИИ-компоненты работают в режиме заглушек (`DOOMICH_LLM_BACKEND=mock` и т. д.). На prod проверка `/ready` не проходит, если хоть одна заглушка включена.

## Тесты

```bash
uv run pytest
```

Тестам нужен суперпользователь PostgreSQL с установленным pgvector, адрес задаётся `DOOMICH_TEST_PG` (по умолчанию сокет `/tmp`, порт 5433). Каждый прогон создаёт свою временную БД и удаляет её в конце.

## Основные настройки

| Переменная | Назначение |
|---|---|
| `DOOMICH_ENV` | dev, test, stage, prod |
| `DOOMICH_MASTER_KEYS` | мастер-ключи шифрования `kid:base64,...`, первый активный. Новый ключ: `doomich-manage gen-master-key` |
| `DOOMICH_JWT_SECRET` | секрет подписи токенов |
| `DOOMICH_INVITE_PEPPER` | перец для хэшей кодов приглашения |
| `DOOMICH_LLM_BACKEND`, `DOOMICH_LLM_URL`, `DOOMICH_LLM_MODEL` | LLM (vllm или mock) |
| `DOOMICH_EMBED_*`, `DOOMICH_RERANK_*` | эмбеддинги и реранкер |
| `DOOMICH_ASR_*`, `DOOMICH_TTS_*` | сервисы речи |
| `DOOMICH_CLAMD_HOST` | ClamAV для проверки файлов (на stage и prod обязателен) |
| `DOOMICH_PARSER_BACKEND` | auto, docling, basic |
| `DOOMICH_RAG_MIN_SCORE` | порог реранкера, ниже которого ассистент говорит "в документах нет" |

Секреты можно класть файлами в `/run/secrets/doomich_<имя>` (docker secrets).

## Адаптер расписания для своего вуза

Встроенные источники: `xlsx_url`, `csv_url`, `ics_url`, `json_api`, `html_table`. Если формат вуза особенный, адаптер пишется одним классом (см. `schedule/adapters/base.py`) и подключается либо как `kind: python` с `config.class = "модуль:Класс"`, либо через entry point `doomich.schedule_adapters` в отдельном пакете.
