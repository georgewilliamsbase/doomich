"""Логи в JSON без персональных данных.

Правила: в логах нет IP-адресов, токенов, текстов сообщений и документов.
Фильтр дополнительно вычищает IPv4/IPv6 и значения известных полей,
если они случайно попали в сообщение.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime

IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6 = re.compile(r"\b(?:[0-9a-f]{1,4}:){2,7}[0-9a-f]{1,4}\b", re.I)
BEARER = re.compile(r"(Bearer\s+)[A-Za-z0-9._-]+")
SENSITIVE_KEYS = {"password", "token", "refresh_token", "access_token", "recovery_code", "text", "content",
                  "authorization", "invite_code", "totp", "code"}


def scrub(value: str) -> str:
    value = IPV4.sub("[ip]", value)
    value = IPV6.sub("[ip]", value)
    return BEARER.sub(r"\1[token]", value)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": scrub(record.getMessage()),
        }
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            for k, v in extra.items():
                data[k] = "[hidden]" if k.lower() in SENSITIVE_KEYS else (scrub(v) if isinstance(v, str) else v)
        if record.exc_info:
            data["exc"] = scrub(self.formatException(record.exc_info))
        return json.dumps(data, ensure_ascii=False, default=str)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    # uvicorn.access пишет IP клиента, его отключаем, свой журнал запросов без IP
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("httpx").setLevel(logging.WARNING)


def log_event(logger: logging.Logger, msg: str, level: int = logging.INFO, **fields: object) -> None:
    logger.log(level, msg, extra={"extra_fields": fields})
