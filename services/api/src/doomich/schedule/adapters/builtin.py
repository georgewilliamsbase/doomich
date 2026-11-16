"""Встроенные адаптеры: файлы по ссылке, iCalendar, HTML-таблица, JSON API."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from doomich.schedule.adapters.base import AdapterError, ScheduleAdapter, register
from doomich.schedule.importers import parse_ics, parse_rows, parse_template
from doomich.schedule.records import LessonRecord, combine, norm_kind, parse_date, parse_time


def _check(result: Any, strict: bool) -> list[LessonRecord]:
    if result.errors and (strict or not result.records):
        first = result.errors[0]
        raise AdapterError(f"ошибка разбора (строка {first.row}): {first.message}; всего ошибок {len(result.errors)}")
    return list(result.records)


@register("xlsx_url")
class XlsxUrlAdapter(ScheduleAdapter):
    """config: {"url": "...", "strict": false}. Файл в формате шаблона Думыча."""

    async def fetch(self) -> list[LessonRecord]:
        url = self.config["url"]
        resp = await self.http_get(url)
        name = "file.xlsx" if not url.lower().endswith(".csv") else "file.csv"
        res = parse_template(resp.content, name, tz=self.ctx.tz, term=self.ctx.term, bells=self.ctx.bells)
        return _check(res, bool(self.config.get("strict")))


@register("csv_url")
class CsvUrlAdapter(XlsxUrlAdapter):
    async def fetch(self) -> list[LessonRecord]:
        resp = await self.http_get(self.config["url"])
        res = parse_template(resp.content, "file.csv", tz=self.ctx.tz, term=self.ctx.term, bells=self.ctx.bells)
        return _check(res, bool(self.config.get("strict")))


@register("ics_url")
class IcsUrlAdapter(ScheduleAdapter):
    """config: {"feeds": [{"group": "ИВТ-21", "url": "https://.../ivt21.ics"}]}."""

    async def fetch(self) -> list[LessonRecord]:
        feeds = self.config.get("feeds") or []
        if not feeds and self.config.get("url"):
            feeds = [{"group": self.config.get("group", ""), "url": self.config["url"]}]
        out: list[LessonRecord] = []
        for feed in feeds:
            resp = await self.http_get(feed["url"])
            res = parse_ics(resp.content, group=feed["group"], tz=self.ctx.tz, window=self.ctx.window)
            out.extend(_check(res, False))
        return out


def _dig(obj: Any, path: str) -> Any:
    """Достаёт значение по пути "a.b.0.c"."""
    cur = obj
    for part in path.split("."):
        if part == "":
            continue
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
        if cur is None:
            return None
    return cur


@register("json_api")
class JsonApiAdapter(ScheduleAdapter):
    """Универсальный JSON.

    config:
      url: адрес, можно с {group} и {date_from}/{date_to}
      groups: ["ИВТ-21", ...]  если API отдаёт по одной группе за запрос
      items_path: "data.lessons"
      fields: {group, subject, start, end, date, kind, room, building, teacher, subgroup, note, status}
        start/end: либо полная дата-время ISO, либо время HH:MM вместе с полем date
    """

    async def fetch(self) -> list[LessonRecord]:
        cfg = self.config
        fields: dict[str, str] = cfg.get("fields") or {}
        urls: list[tuple[str | None, str]] = []
        d_from, d_to = self.ctx.window
        template = cfg["url"]
        for g in cfg.get("groups") or [None]:
            urls.append((g, template.format(group=g or "", date_from=d_from.isoformat(), date_to=d_to.isoformat())))
        out: list[LessonRecord] = []
        for group, url in urls:
            data = (await self.http_get(url)).json()
            items = _dig(data, cfg.get("items_path", "")) if cfg.get("items_path") else data
            if not isinstance(items, list):
                raise AdapterError("items_path не указывает на список")
            for item in items:
                out.append(self._record(item, fields, group))
        return out

    def _record(self, item: dict[str, Any], f: dict[str, str], group: str | None) -> LessonRecord:
        def get(key: str) -> Any:
            return _dig(item, f[key]) if key in f else None

        start, end = get("start"), get("end")
        if start is None or end is None:
            raise AdapterError("в записи нет начала или конца занятия")
        if get("date") is not None:
            day = parse_date(get("date"))
            starts_at = combine(day, parse_time(start), self.ctx.tz)
            ends_at = combine(day, parse_time(end), self.ctx.tz)
        else:
            starts_at = datetime.fromisoformat(str(start))
            ends_at = datetime.fromisoformat(str(end))
            if starts_at.tzinfo is None:
                starts_at = starts_at.replace(tzinfo=self.ctx.tz)
                ends_at = ends_at.replace(tzinfo=self.ctx.tz)
        return LessonRecord(
            group=str(get("group") or group or ""), subject=str(get("subject") or ""), starts_at=starts_at,
            ends_at=ends_at, kind=norm_kind(get("kind")), room=_s(get("room")), building=_s(get("building")),
            teacher=_s(get("teacher")), subgroup=_s(get("subgroup")), note=_s(get("note")),
            status="cancelled" if "cancel" in str(get("status") or "").lower() else "scheduled",
        )


def _s(v: Any) -> str | None:
    return None if v is None or str(v).strip() == "" else str(v).strip()


@register("html_table")
class HtmlTableAdapter(ScheduleAdapter):
    """HTML-таблица на сайте вуза, по странице на группу.

    config:
      pages: [{"group": "ИВТ-21", "url": "https://.../ivt21.html"}]
      table: CSS-селектор таблицы (по умолчанию первая table)
      header_row: номер строки заголовков (0)
    Заголовки таблицы сопоставляются так же, как в шаблоне Excel
    (Дата/День недели, Начало, Конец, Дисциплина, Аудитория...).
    Колонку с группой можно не иметь: группа берётся из pages.
    """

    async def fetch(self) -> list[LessonRecord]:
        from bs4 import BeautifulSoup

        out: list[LessonRecord] = []
        for page in self.config.get("pages") or []:
            html = (await self.http_get(page["url"])).text
            soup = BeautifulSoup(html, "html.parser")
            table = soup.select_one(self.config.get("table", "table"))
            if table is None:
                raise AdapterError(f"{page['url']}: таблица не найдена")
            rows: list[list[Any]] = []
            for tr in table.select("tr"):
                cells = [re.sub(r"\s+", " ", td.get_text(" ", strip=True)) for td in tr.select("th,td")]
                if cells:
                    rows.append(cells)
            header_idx = int(self.config.get("header_row", 0))
            rows = rows[header_idx:]
            if not rows:
                continue
            if not any(str(h).strip().lower() in ("группа", "group") for h in rows[0]):
                rows = [["Группа", *rows[0]]] + [[page["group"], *r] for r in rows[1:]]
            res = parse_rows(rows, tz=self.ctx.tz, term=self.ctx.term, bells=self.ctx.bells)
            out.extend(_check(res, bool(self.config.get("strict"))))
        return out
