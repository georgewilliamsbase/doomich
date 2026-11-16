"""Ошибки приложения.

Клиенту уходит JSON вида {"error": {"code": "...", "message": "..."}}.
code стабилен и используется клиентом для локализованных сообщений,
message нужен для отладки и не показывается пользователю как есть.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str | None = None, *, code: str | None = None,
                 status_code: int | None = None, details: dict[str, Any] | None = None) -> None:
        super().__init__(message or self.code)
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        self.message = message or self.code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details:
            body["details"] = self.details
        return {"error": body}


class NotFound(AppError):
    status_code = 404
    code = "not_found"


class Unauthorized(AppError):
    status_code = 401
    code = "unauthorized"


class Forbidden(AppError):
    status_code = 403
    code = "forbidden"


class Conflict(AppError):
    status_code = 409
    code = "conflict"


class TooManyRequests(AppError):
    status_code = 429
    code = "rate_limited"

    def __init__(self, message: str | None = None, *, retry_after: int = 60, **kw: Any) -> None:
        super().__init__(message, **kw)
        self.retry_after = retry_after


class PayloadTooLarge(AppError):
    status_code = 413
    code = "payload_too_large"


class ValidationFailed(AppError):
    status_code = 422
    code = "validation_failed"


class ServiceUnavailable(AppError):
    status_code = 503
    code = "service_unavailable"
