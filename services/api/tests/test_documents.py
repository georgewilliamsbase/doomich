from __future__ import annotations

import io
import uuid

from tests.conftest import parse_sse, register


def make_docx(*paragraphs: str, heading: str = "Введение") -> bytes:
    import docx

    d = docx.Document()
    d.add_heading(heading, level=1)
    for p in paragraphs:
        d.add_paragraph(p)
    table = d.add_table(rows=2, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = "Параметр", "Значение"
    table.cell(1, 0).text, table.cell(1, 1).text = "Скорость света", "299792458 м/с"
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def make_pdf(pages: list[str]) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    from doomich.admin.printing import _font

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    font = _font()
    for text in pages:
        c.setFont(font, 12)
        y = 800
        for line in text.split("\n"):
            c.drawString(60, y, line)
            y -= 18
        c.showPage()
    c.save()
    return buf.getvalue()


def make_xlsx() -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Измерения"
    ws.append(["Опыт", "Температура", "Давление"])
    for i in range(1, 6):
        ws.append([i, 20 + i, 100 + i * 3])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


async def upload(client, headers, name: str, data: bytes):
    files = {"file": (name, io.BytesIO(data), "application/octet-stream")}
    return await client.post("/v1/documents", files=files, headers=headers)


async def test_pdf_upload_search_and_answer_with_citation(client, env):
    user = await register(client, env.codes[0])
    h = user["headers"]
    pdf = make_pdf([
        "Глава 1. Механика\nВторой закон Ньютона: сила равна массе, умноженной на ускорение.",
        "Глава 2. Термодинамика\nПервое начало термодинамики описывает сохранение энергии в системе.",
    ])
    r = await upload(client, h, "методичка.pdf", pdf)
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["status"] == "ready", doc
    assert doc["kind"] == "pdf" and doc["pages"] == 2 and doc["title"] == "методичка.pdf"

    chat = (await client.post("/v1/chats", json={"document_ids": [doc["id"]]}, headers=h)).json()
    r = await client.post(f"/v1/chats/{chat['id']}/messages", json={"text": "что говорит первое начало термодинамики"},
                          headers=h)
    events = parse_sse(r.text)
    text = "".join(d["text"] for e, d in events if e == "delta")
    sources = next(d for e, d in events if e == "sources")["items"]
    assert "[1]" in text
    assert sources and sources[0]["page"] == 2 and sources[0]["title"] == "методичка.pdf"
    assert "сохранение энергии" in text

    src = sources[0]
    r = await client.get(f"/v1/documents/{doc['id']}/chunks/{src['chunk_id']}", headers=h)
    assert r.status_code == 200
    assert "термодинамики" in r.json()["text"]


async def test_docx_xlsx_parsing(client, env):
    user = await register(client, env.codes[0])
    h = user["headers"]
    r = await upload(client, h, "лабораторная.docx", make_docx("Лабораторная работа номер три про маятник."))
    assert r.json()["status"] == "ready"
    r = await upload(client, h, "данные.xlsx", make_xlsx())
    doc = r.json()
    assert doc["status"] == "ready" and doc["kind"] == "xlsx"

    from sqlalchemy import select

    from doomich.db import get_db
    from doomich.models import Chunk

    async with get_db().sys_session() as s:
        chunks = (await s.scalars(select(Chunk).where(Chunk.document_id == uuid.UUID(doc["id"])))).all()
    assert chunks[0].sheet == "Измерения"
    assert "| Опыт | Температура | Давление |" in chunks[0].body
    docs = (await client.get("/v1/documents", headers=h)).json()
    assert len(docs) == 2


async def test_rejects_unsupported_and_large(client, env, database):
    user = await register(client, env.codes[0])
    r = await upload(client, user["headers"], "virus.exe", b"MZ\x90\x00" + b"0" * 100)
    assert r.status_code == 415
    big = b"%PDF-1.4\n" + b"0" * (database.max_document_mb * 1024 * 1024 + 10)
    r = await upload(client, user["headers"], "big.pdf", big)
    assert r.status_code == 413


async def test_delete_removes_file_and_chunks(client, env, database):
    from sqlalchemy import func, select

    from doomich.db import get_db
    from doomich.models import Chunk, Document

    user = await register(client, env.codes[0])
    doc = (await upload(client, user["headers"], "a.docx", make_docx("Текст для удаления."))).json()
    async with get_db().sys_session() as s:
        key = (await s.get(Document, uuid.UUID(doc["id"]))).storage_key
    path = database.data_dir / "files" / key
    assert path.exists()
    assert b"\xd0\xa2\xd0\xb5\xd0\xba\xd1\x81\xd1\x82" not in path.read_bytes()  # файл зашифрован
    r = await client.request("DELETE", f"/v1/documents/{doc['id']}", headers=user["headers"])
    assert r.status_code == 204
    assert not path.exists()
    async with get_db().sys_session() as s:
        n = await s.scalar(select(func.count()).select_from(Chunk).where(Chunk.document_id == uuid.UUID(doc["id"])))
    assert n == 0


async def test_not_found_answer(client, env):
    user = await register(client, env.codes[0])
    doc = (await upload(client, user["headers"], "a.docx", make_docx("Здесь только про ботанику и листья."))).json()
    chat = (await client.post("/v1/chats", json={"document_ids": [doc["id"]]}, headers=user["headers"])).json()
    r = await client.post(f"/v1/chats/{chat['id']}/messages", json={"text": "квантовая хромодинамика глюоны"},
                          headers=user["headers"])
    text = "".join(d["text"] for e, d in parse_sse(r.text) if e == "delta")
    assert "нет" in text.lower()


def test_chunking_keeps_tables_and_sections():
    from doomich.documents.chunking import chunk_document
    from doomich.documents.parsers.base import Block, ParsedDocument

    doc = ParsedDocument(blocks=[
        Block("heading", "Раздел 1", page=1, level=1),
        Block("text", "А" * 1000, page=1),
        Block("text", "Б" * 1000, page=2),
        Block("heading", "Подраздел 1.1", page=2, level=2),
        Block("table", "| a | b |\n| --- | --- |\n| 1 | 2 |", page=3),
    ])
    chunks = chunk_document(doc)
    assert chunks[0].section == "Раздел 1" and chunks[0].page == 1
    table = [c for c in chunks if c.body.startswith("|")]
    assert table and table[0].section == "Раздел 1 / Подраздел 1.1" and table[0].page == 3
