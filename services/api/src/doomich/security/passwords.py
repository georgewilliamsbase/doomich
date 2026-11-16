"""Хэши паролей и кодов восстановления (Argon2id)."""

from __future__ import annotations

import secrets
import unicodedata

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from doomich.config import settings

# Алфавит Crockford base32 без похожих символов (нет I, L, O, U)
RECOVERY_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

_hasher: dict[tuple[int, int, int], PasswordHasher] = {}

COMMON_PASSWORDS = {
    "1234567890", "0123456789", "qwertyuiop", "password123", "qwerty1234", "1q2w3e4r5t",
    "йцукенгшщз", "пароль1234", "1111111111", "abcdefghij", "iloveyou12", "password12",
}


def _ph() -> PasswordHasher:
    s = settings()
    key = (s.argon2_time_cost, s.argon2_memory_kib, s.argon2_parallelism)
    if key not in _hasher:
        _hasher[key] = PasswordHasher(time_cost=key[0], memory_cost=key[1], parallelism=key[2])
    return _hasher[key]


def hash_secret(value: str) -> str:
    return _ph().hash(value)


def verify_secret(stored_hash: str, value: str) -> bool:
    try:
        return _ph().verify(stored_hash, value)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    try:
        return _ph().check_needs_rehash(stored_hash)
    except InvalidHashError:
        return True


# Хэш для пустой проверки, чтобы время ответа не выдавало, есть ли такой логин
_DUMMY: dict[str, str] = {}


def dummy_verify(value: str) -> None:
    if "h" not in _DUMMY:
        _DUMMY["h"] = hash_secret("dummy-password-for-timing")
    verify_secret(_DUMMY["h"], value)


def generate_recovery_code() -> str:
    """20 символов base32, около 100 бит. Группы по 5 для удобства записи."""
    raw = "".join(secrets.choice(RECOVERY_ALPHABET) for _ in range(20))
    return "-".join(raw[i : i + 5] for i in range(0, 20, 5))


def normalize_recovery_code(code: str) -> str:
    code = code.upper().replace("-", "").replace(" ", "")
    # Частые опечатки при ручном вводе
    return code.replace("O", "0").replace("I", "1").replace("L", "1")


def password_problems(password: str, login: str | None = None) -> list[str]:
    """Проверка стойкости на сервере. Клиент дополнительно показывает индикатор."""
    problems: list[str] = []
    pw = unicodedata.normalize("NFKC", password)
    if len(pw) < 10:
        problems.append("too_short")
    if len(pw) > 128:
        problems.append("too_long")
    if pw.lower() in COMMON_PASSWORDS:
        problems.append("too_common")
    if len(set(pw)) < 4:
        problems.append("too_simple")
    if login and login.lower() in pw.lower():
        problems.append("contains_login")
    return problems
