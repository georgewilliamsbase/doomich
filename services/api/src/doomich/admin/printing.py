"""Листы с кодами приглашения для печати: A4, 12 карточек с QR на странице."""

from __future__ import annotations

import io
from pathlib import Path

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]


def _font() -> str:
    if "DoomichSans" in pdfmetrics.getRegisteredFontNames():
        return "DoomichSans"
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont("DoomichSans", path))
            return "DoomichSans"
    return "Helvetica"


def invite_link(code: str, server: str) -> str:
    return f"doomich://invite/{code}?server={server}"


def _qr_image(data: str) -> ImageReader:
    img = qrcode.make(data, box_size=6, border=1)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def invite_sheet(codes: list[str], *, tenant_name: str, label: str, server: str, site: str) -> bytes:
    font = _font()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Коды приглашения: {label}")
    width, height = A4
    cols, rows = 3, 4
    margin = 10 * mm
    cell_w = (width - 2 * margin) / cols
    cell_h = (height - 2 * margin) / rows
    for i, code in enumerate(codes):
        pos = i % (cols * rows)
        if i > 0 and pos == 0:
            c.showPage()
        col, row = pos % cols, pos // cols
        x = margin + col * cell_w
        y = height - margin - (row + 1) * cell_h
        c.setDash(2, 3)
        c.rect(x + 1, y + 1, cell_w - 2, cell_h - 2)
        c.setDash()
        qr = 32 * mm
        c.drawImage(_qr_image(invite_link(code, server)), x + (cell_w - qr) / 2, y + cell_h - qr - 8 * mm,
                    qr, qr)
        c.setFont(font, 9)
        c.drawCentredString(x + cell_w / 2, y + cell_h - 5 * mm, tenant_name[:40])
        c.setFont(font, 15)
        c.drawCentredString(x + cell_w / 2, y + 22 * mm, code)
        c.setFont(font, 7.5)
        c.drawCentredString(x + cell_w / 2, y + 16 * mm, f"Думыч: {label[:40]}")
        c.drawCentredString(x + cell_w / 2, y + 11 * mm, f"Скачать: {site}")
        c.drawCentredString(x + cell_w / 2, y + 6 * mm, "Без телефона и почты, только псевдоним")
    c.save()
    return buf.getvalue()
