"""Сборка приложения FastAPI."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from doomich import __version__
from doomich.common.errors import AppError, TooManyRequests
from doomich.config import settings
from doomich.db import close_db, get_db, init_db
from doomich.observability.logs import log_event, setup_logging
from doomich.observability.metrics import LATENCY, REQUESTS

log = logging.getLogger("doomich")


def _register_tools() -> None:
    # Модули регистрируют инструменты ассистента при импорте
    import doomich.documents.tools
    import doomich.schedule.tools  # noqa: F401

    for optional in ("doomich.knowledge.tools", "doomich.campus.tools", "doomich.courses.tools"):
        _optional_import(optional)


def _optional_import(name: str):
    """Импорт модуля следующего релиза, если он уже есть в сборке."""
    import importlib

    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as e:
        if e.name and name.startswith(e.name):
            return None
        raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    st = settings()
    init_db(st)
    st.data_dir.mkdir(parents=True, exist_ok=True)
    if st.is_prod_like and st.mock_components():
        log.error("в %s включены заглушки ИИ: %s", st.env, ", ".join(st.mock_components()))
    yield
    await close_db()


def create_app() -> FastAPI:
    st = settings()
    setup_logging(st.log_level)
    if st.sentry_dsn:
        try:
            import sentry_sdk

            # Свой GlitchTip, без IP и тел запросов
            sentry_sdk.init(dsn=st.sentry_dsn, send_default_pii=False, max_request_body_size="never",
                            traces_sample_rate=0.0, environment=st.env, release=__version__)
        except ImportError:
            log.warning("sentry-sdk не установлен, ошибки в GlitchTip не отправляются")

    app = FastAPI(
        title="Doomich Core API", version=__version__, lifespan=lifespan,
        docs_url="/docs" if not st.is_prod_like else None, redoc_url=None,
        openapi_url="/openapi.json",
    )
    app.add_middleware(CORSMiddleware, allow_origins=st.cors_origins, allow_credentials=False,
                       allow_methods=["*"], allow_headers=["Authorization", "Content-Type"])

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        started = time.monotonic()
        response = await call_next(request)
        route = request.scope.get("route")
        path = getattr(route, "path", "unmatched")
        elapsed = time.monotonic() - started
        REQUESTS.labels(route=path, method=request.method, status=str(response.status_code)).inc()
        LATENCY.labels(route=path, method=request.method).observe(elapsed)
        if path not in ("/health", "/metrics"):
            # Без IP, query-строк и идентификаторов: только шаблон маршрута
            log_event(log, "request", method=request.method, route=path, status=response.status_code,
                      ms=int(elapsed * 1000))
        return response

    @app.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError) -> JSONResponse:
        headers = {"Retry-After": str(exc.retry_after)} if isinstance(exc, TooManyRequests) else None
        return JSONResponse(exc.to_dict(), status_code=exc.status_code, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [{"field": ".".join(str(x) for x in e["loc"][1:]), "msg": e["msg"]} for e in exc.errors()]
        return JSONResponse({"error": {"code": "validation_failed", "message": "неверные данные",
                                       "details": {"fields": details}}}, status_code=422)

    @app.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/ready", include_in_schema=False)
    async def ready() -> JSONResponse:
        problems: list[str] = []
        try:
            async with get_db().sys_session() as s:
                await s.execute(text("select 1"))
        except Exception:
            problems.append("db")
        if st.env == "prod" and st.mock_components():
            problems.append("mock:" + ",".join(st.mock_components()))
        return JSONResponse({"ready": not problems, "problems": problems}, status_code=200 if not problems else 503)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> PlainTextResponse:
        return PlainTextResponse(generate_latest().decode(), media_type=CONTENT_TYPE_LATEST)

    from doomich.accounts.router import router as accounts
    from doomich.admin.router import router as admin
    from doomich.chats.router import router as chats
    from doomich.documents.router import router as documents
    from doomich.schedule.router import router as schedule
    from doomich.tenants.router import router as tenants
    from doomich.voice.gateway import router as voice

    for r in (accounts, tenants, chats, schedule, documents, voice, admin):
        app.include_router(r)
    for optional in ("doomich.lectures.router", "doomich.knowledge.router", "doomich.campus.router",
                     "doomich.courses.router"):
        module = _optional_import(optional)
        if module is not None:
            app.include_router(module.router)
    _register_tools()
    return app
