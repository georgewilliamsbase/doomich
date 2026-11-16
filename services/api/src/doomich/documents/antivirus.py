"""Проверка файлов в ClamAV через clamd (команда INSTREAM).

ClamAV работает отдельным контейнером (GPL, без изменений), мы только шлём ему поток.
"""

from __future__ import annotations

import asyncio
import struct
from pathlib import Path

CHUNK = 64 * 1024


class VirusFound(Exception):
    def __init__(self, signature: str) -> None:
        super().__init__(signature)
        self.signature = signature


class ScanUnavailable(Exception):
    pass


async def scan_file(path: Path, host: str, port: int, read_timeout: float = 60.0) -> None:
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=5)
    except (OSError, TimeoutError) as e:
        raise ScanUnavailable(f"clamd недоступен: {e}") from e
    try:
        writer.write(b"zINSTREAM\0")
        with path.open("rb") as f:
            while True:
                data = f.read(CHUNK)
                if not data:
                    break
                writer.write(struct.pack(">I", len(data)) + data)
                await writer.drain()
        writer.write(struct.pack(">I", 0))
        await writer.drain()
        raw = await asyncio.wait_for(reader.read(4096), timeout=read_timeout)
        reply = raw.decode(errors="replace").strip("\0\n ")
    finally:
        writer.close()
    # Ответ вида "stream: OK" или "stream: Eicar-Signature FOUND"
    if reply.endswith("FOUND"):
        raise VirusFound(reply.split(":", 1)[-1].replace("FOUND", "").strip())
    if not reply.endswith("OK"):
        raise ScanUnavailable(f"неожиданный ответ clamd: {reply[:100]}")
