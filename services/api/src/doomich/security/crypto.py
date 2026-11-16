"""Прикладное шифрование (AES-256-GCM).

Схема ключей:
- мастер-ключи лежат вне БД (настройка DOOMICH_MASTER_KEYS или файл секрета);
- у каждого пользователя свой ключ данных, в БД он хранится зашифрованным
  активным мастер-ключом (поле kid позволяет ротацию);
- сообщения, названия и файлы шифруются ключом пользователя.

Формат зашифрованного значения: версия (1 байт) + nonce (12) + шифротекст с тегом.
Связанные данные (AAD) привязывают шифротекст к конкретной записи, поэтому
блок нельзя незаметно переставить в другую строку.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import struct
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import BinaryIO

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from doomich.config import settings

VERSION = 1
NONCE = 12
FILE_MAGIC = b"DMF1"
FILE_SEGMENT = 1024 * 1024


class CryptoError(Exception):
    pass


@dataclass(frozen=True)
class Keyring:
    keys: dict[str, bytes]
    active_kid: str

    @classmethod
    def parse(cls, spec: str) -> Keyring:
        keys: dict[str, bytes] = {}
        order: list[str] = []
        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue
            kid, _, b64 = part.partition(":")
            key = base64.b64decode(b64)
            if len(key) != 32:
                raise CryptoError(f"master key {kid}: нужно 32 байта")
            keys[kid] = key
            order.append(kid)
        if not order:
            raise CryptoError("не задан ни один мастер-ключ")
        return cls(keys=keys, active_kid=order[0])


_keyring: dict[str, Keyring] = {}


def keyring() -> Keyring:
    spec = settings().master_keys.get_secret_value()
    cached = _keyring.get(spec)
    if cached is None:
        cached = Keyring.parse(spec)
        _keyring.clear()
        _keyring[spec] = cached
    return cached


def _seal(key: bytes, plaintext: bytes, aad: bytes) -> bytes:
    nonce = os.urandom(NONCE)
    return bytes([VERSION]) + nonce + AESGCM(key).encrypt(nonce, plaintext, aad)


def _open(key: bytes, blob: bytes, aad: bytes) -> bytes:
    if len(blob) < 1 + NONCE + 16 or blob[0] != VERSION:
        raise CryptoError("неизвестный формат шифротекста")
    try:
        return AESGCM(key).decrypt(blob[1 : 1 + NONCE], blob[1 + NONCE :], aad)
    except Exception as e:
        raise CryptoError("не удалось расшифровать") from e


def new_data_key() -> bytes:
    return AESGCM.generate_key(bit_length=256)


def wrap_user_key(user_id: uuid.UUID, key: bytes) -> tuple[str, bytes]:
    ring = keyring()
    return ring.active_kid, _seal(ring.keys[ring.active_kid], key, b"user-key:" + user_id.bytes)


def unwrap_user_key(user_id: uuid.UUID, kid: str, wrapped: bytes) -> bytes:
    ring = keyring()
    if kid not in ring.keys:
        raise CryptoError(f"мастер-ключ {kid} недоступен")
    return _open(ring.keys[kid], wrapped, b"user-key:" + user_id.bytes)


def system_key(purpose: str) -> bytes:
    """Производный ключ для служебных данных (коды приглашения, секреты TOTP)."""
    ring = keyring()
    return hmac.new(ring.keys[ring.active_kid], b"system:" + purpose.encode(), hashlib.sha256).digest()


class UserCipher:
    """Шифрование данных одного пользователя."""

    def __init__(self, key: bytes) -> None:
        self._key = key

    def encrypt(self, plaintext: str | bytes, context: str) -> bytes:
        data = plaintext.encode() if isinstance(plaintext, str) else plaintext
        return _seal(self._key, data, context.encode())

    def decrypt(self, blob: bytes, context: str) -> bytes:
        return _open(self._key, blob, context.encode())

    def decrypt_str(self, blob: bytes | None, context: str) -> str | None:
        if blob is None:
            return None
        return self.decrypt(blob, context).decode()

    def file_key(self) -> tuple[bytes, bytes]:
        """Новый ключ файла и он же в зашифрованном ключом пользователя виде."""
        fk = new_data_key()
        return fk, self.encrypt(fk, "file-key")

    def open_file_key(self, wrapped: bytes) -> bytes:
        return self.decrypt(wrapped, "file-key")


def seal_system(purpose: str, plaintext: bytes) -> bytes:
    return _seal(system_key(purpose), plaintext, purpose.encode())


def open_system(purpose: str, blob: bytes) -> bytes:
    return _open(system_key(purpose), blob, purpose.encode())


# Потоковое шифрование файлов: файл режется на сегменты по 1 МБ, у каждого
# сегмента свой nonce (случайный префикс + номер) и флаг последнего сегмента в AAD.
# Так нельзя обрезать файл или переставить сегменты.


def encrypt_stream(src: BinaryIO, dst: BinaryIO, key: bytes, file_id: str) -> int:
    prefix = os.urandom(7)
    dst.write(FILE_MAGIC + prefix)
    aes = AESGCM(key)
    total = 0
    index = 0
    chunk = src.read(FILE_SEGMENT)
    while True:
        nxt = src.read(FILE_SEGMENT)
        last = not nxt
        nonce = prefix + struct.pack(">IB", index, 1 if last else 0)
        ct = aes.encrypt(nonce, chunk, f"{file_id}:{index}:{int(last)}".encode())
        dst.write(struct.pack(">I", len(ct)) + ct)
        total += len(chunk)
        if last:
            break
        chunk = nxt
        index += 1
    return total


def decrypt_stream(src: BinaryIO, key: bytes, file_id: str) -> Iterator[bytes]:
    head = src.read(len(FILE_MAGIC) + 7)
    if head[:4] != FILE_MAGIC:
        raise CryptoError("не зашифрованный файл")
    prefix = head[4:]
    aes = AESGCM(key)
    index = 0
    while True:
        size_raw = src.read(4)
        if len(size_raw) < 4:
            raise CryptoError("файл обрезан")
        (size,) = struct.unpack(">I", size_raw)
        ct = src.read(size)
        # Сначала пробуем как промежуточный сегмент, потом как последний
        for last in (0, 1):
            nonce = prefix + struct.pack(">IB", index, last)
            try:
                pt = aes.decrypt(nonce, ct, f"{file_id}:{index}:{last}".encode())
            except Exception:  # noqa: S112
                continue
            yield pt
            if last:
                return
            break
        else:
            raise CryptoError("сегмент повреждён")
        index += 1


def hmac_lookup(purpose: str, value: str) -> bytes:
    """Детерминированный хэш для поиска (коды приглашения)."""
    pepper = settings().invite_pepper.get_secret_value().encode()
    return hmac.new(pepper, f"{purpose}:{value}".encode(), hashlib.sha256).digest()
