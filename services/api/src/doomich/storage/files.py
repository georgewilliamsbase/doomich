"""Хранилище файлов пользователей.

Файлы лежат на томе под LUKS и дополнительно зашифрованы ключом файла
(см. security/crypto.py). Ключ хранилища вида "<tenant>/<user>/<id>.bin".
Интерфейс простой, чтобы позже можно было подключить S3-совместимое хранилище.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import BinaryIO

from doomich.config import settings
from doomich.security import crypto


class FileStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, key: str) -> Path:
        p = (self.root / key).resolve()
        if not str(p).startswith(str(self.root.resolve())):
            raise ValueError("недопустимый ключ хранилища")
        return p

    def put_encrypted(self, key: str, src: BinaryIO, file_key: bytes, file_id: str) -> int:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".up-")
        try:
            with os.fdopen(fd, "wb") as dst:
                size = crypto.encrypt_stream(src, dst, file_key, file_id)
            os.replace(tmp, path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        return size

    def read_decrypted(self, key: str, file_key: bytes, file_id: str) -> Iterator[bytes]:
        with self._path(key).open("rb") as f:
            yield from crypto.decrypt_stream(f, file_key, file_id)

    def decrypt_to_temp(self, key: str, file_key: bytes, file_id: str, suffix: str = "") -> Path:
        fd, tmp = tempfile.mkstemp(prefix="dm-", suffix=suffix, dir=self.tmp_dir())
        with os.fdopen(fd, "wb") as out:
            for part in self.read_decrypted(key, file_key, file_id):
                out.write(part)
        return Path(tmp)

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def delete_prefix(self, prefix: str) -> None:
        path = self._path(prefix)
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def tmp_dir(self) -> str:
        d = self.root / ".tmp"
        d.mkdir(parents=True, exist_ok=True)
        return str(d)

    # Открытые служебные файлы (планы этажей, эталонные фото кампуса). Не шифруются,
    # потому что не относятся к пользователям и раздаются всем в пределах вуза.
    def put_plain(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def read_plain(self, key: str) -> bytes:
        return self._path(key).read_bytes()


def get_storage() -> FileStorage:
    root = settings().data_dir / "files"
    root.mkdir(parents=True, exist_ok=True)
    return FileStorage(root)
