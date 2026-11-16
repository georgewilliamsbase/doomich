"""Подготовка текста ответа к озвучке: очистка разметки и нарезка на предложения.

Нормализация чисел, дат и ударения делаются в сервисе TTS. Здесь только то,
что нужно для потоковой озвучки: убрать то, что нельзя произнести, и вовремя
отдать готовое предложение.
"""

from __future__ import annotations

import re

CODE_BLOCK = re.compile(r"```.*?```", re.S)
INLINE_CODE = re.compile(r"`([^`]*)`")
LINK = re.compile(r"\[([^\]]+)\]\((?:[^)]+)\)")
URL = re.compile(r"https?://\S+")
CITE = re.compile(r"\s?\[\d{1,2}\]")
BLOCK_MATH = re.compile(r"\$\$.*?\$\$", re.S)
INLINE_MATH = re.compile(r"\$([^$\n]{1,80})\$")
EMPH = re.compile(r"(\*\*|__|\*|_|~~)(?=\S)(.+?)(?<=\S)\1")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s*", re.M)
LIST_MARK = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+", re.M)
TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$", re.M)

ABBREVIATIONS = ("т.е.", "т.к.", "т.д.", "т.п.", "др.", "пр.", "см.", "рис.", "стр.", "ул.", "г.", "гг.",
                 "в.", "вв.", "им.", "ауд.", "корп.", "e.g.", "i.e.", "etc.", "vs.", "mr.", "dr.")


def simple_math(expr: str, lang: str) -> str:
    ru = lang != "en"
    s = expr
    s = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"\1 " + ("делить на" if ru else "over") + r" \2", s)
    s = re.sub(r"\\sqrt\{([^{}]+)\}", ("корень из " if ru else "square root of ") + r"\1", s)
    s = s.replace("^2", " в квадрате" if ru else " squared").replace("^3", " в кубе" if ru else " cubed")
    s = s.replace("\\cdot", "умножить на" if ru else "times").replace("\\times", "умножить на" if ru else "times")
    s = s.replace("\\le", "меньше или равно" if ru else "less or equal").replace(
        "\\ge", "больше или равно" if ru else "greater or equal")
    s = s.replace("=", " равно " if ru else " equals ").replace("+", " плюс " if ru else " plus ")
    s = re.sub(r"\\[a-zA-Z]+", " ", s)
    s = re.sub(r"[{}_^\\]", " ", s)
    return " ".join(s.split())


def to_speakable(text: str, lang: str = "ru") -> str:
    ru = lang != "en"
    t = CODE_BLOCK.sub(" Код показан на экране. " if ru else " The code is on the screen. ", text)
    t = BLOCK_MATH.sub(" Формула показана на экране. " if ru else " The formula is on the screen. ", t)
    t = INLINE_MATH.sub(lambda m: simple_math(m.group(1), lang), t)
    t = TABLE_LINE.sub(" ", t)
    t = LINK.sub(r"\1", t)
    t = URL.sub(" ссылка " if ru else " link ", t)
    t = INLINE_CODE.sub(r"\1", t)
    t = CITE.sub("", t)
    t = HEADING.sub("", t)
    t = LIST_MARK.sub("", t)
    for _ in range(2):
        t = EMPH.sub(r"\2", t)
    t = t.replace("&nbsp;", " ").replace("\u00a0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\s*\n\s*", ". ", t.strip())
    t = re.sub(r"\.\s*\.", ".", t)
    return t.strip()


class SentenceSplitter:
    """Накапливает поток текста и отдаёт законченные предложения."""

    def __init__(self, min_chars: int = 25, max_chars: int = 220) -> None:
        self.buf = ""
        self.min_chars = min_chars
        self.max_chars = max_chars

    def _is_boundary(self, text: str, i: int) -> bool:
        ch = text[i]
        if ch not in ".!?…;":
            return False
        if i + 1 >= len(text) or not text[i + 1].isspace():
            return False
        if ch == ".":
            before = text[: i + 1].lower()
            if any(before.endswith(" " + a) or before == a for a in ABBREVIATIONS):
                return False
            if i > 0 and text[i - 1].isdigit() and i + 2 < len(text) and text[i + 2].isdigit():
                return False
        return True

    def feed(self, chunk: str) -> list[str]:
        self.buf += chunk
        out: list[str] = []
        start = 0
        i = 0
        while i < len(self.buf):
            if self._is_boundary(self.buf, i) and i + 1 - start >= self.min_chars:
                out.append(self.buf[start : i + 1].strip())
                start = i + 1
            elif i - start >= self.max_chars:
                cut = self.buf.rfind(",", start, i)
                if cut > start + self.min_chars:
                    out.append(self.buf[start : cut + 1].strip())
                    start = cut + 1
            i += 1
        self.buf = self.buf[start:]
        return [s for s in out if s]

    def flush(self) -> list[str]:
        rest = self.buf.strip()
        self.buf = ""
        return [rest] if rest else []
