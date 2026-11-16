"""Импорт расписания из шаблона Excel/CSV и из iCalendar.

Шаблон: первая строка с заголовками (русские или английские, регистр не важен).
Обязательные колонки: Группа, Начало, Конец, Дисциплина и либо Дата, либо День недели.
Пример лежит в docs/api/schedule-template.md и выгружается из админки.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from doomich.schedule.records import (
    LessonRecord,
    Term,
    combine,
    expand_weekly,
    is_cancel,
    norm_kind,
    parse_date,
    parse_time,
    parse_weekday,
    parse_weeks,
)

COLUMNS: dict[str, tuple[str, ...]] = {
    "group": ("группа", "group", "гр", "гр."),
    "subgroup": ("подгруппа", "subgroup", "подгр", "подгр."),
    "date": ("дата", "date"),
    "weekday": ("день недели", "день", "weekday", "day"),
    "weeks": ("неделя", "недели", "week", "weeks", "чётность", "четность"),
    "date_from": ("с", "с даты", "from", "date_from", "начало периода"),
    "date_to": ("по", "по дату", "to", "date_to", "конец периода"),
    "pair": ("пара", "№ пары", "номер пары", "pair"),
    "start": ("начало", "время начала", "start", "start_time"),
    "end": ("конец", "окончание", "время окончания", "end", "end_time"),
    "subject": ("дисциплина", "предмет", "subject", "discipline", "course"),
    "kind": ("тип", "вид", "вид занятия", "type", "kind"),
    "room": ("аудитория", "ауд", "ауд.", "room", "auditorium"),
    "building": ("корпус", "building"),
    "teacher": ("преподаватель", "teacher", "lecturer"),
    "note": ("примечание", "комментарий", "note", "comment"),
    "status": ("статус", "status"),
}


@dataclass
class RowError:
    row: int
    column: str | None
    message: str


@dataclass
class ImportResult:
    records: list[LessonRecord] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)
    rows_total: int = 0
    rows_ok: int = 0

    def report(self) -> dict[str, Any]:
        return {
            "rows_total": self.rows_total,
            "rows_ok": self.rows_ok,
            "lessons": len(self.records),
            "groups": sorted({r.group for r in self.records}),
            "errors": [e.__dict__ for e in self.errors[:500]],
            "errors_total": len(self.errors),
        }


def _map_header(header: list[Any]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for idx, raw in enumerate(header):
        name = str(raw or "").strip().lower()
        for key, aliases in COLUMNS.items():
            if name in aliases and key not in mapping:
                mapping[key] = idx
    return mapping


def _cell(row: list[Any], mapping: dict[str, int], key: str) -> Any:
    idx = mapping.get(key)
    if idx is None or idx >= len(row):
        return None
    value = row[idx]
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def parse_rows(rows: list[list[Any]], *, tz: ZoneInfo, term: Term | None,
               bells: list[tuple[str, str]] | None = None, first_row: int = 1) -> ImportResult:
    result = ImportResult()
    if not rows:
        result.errors.append(RowError(0, None, "файл пустой"))
        return result
    mapping = _map_header(rows[0])
    missing = [k for k in ("group", "subject") if k not in mapping]
    if "start" not in mapping and "pair" not in mapping:
        missing.append("start")
    if "date" not in mapping and "weekday" not in mapping:
        missing.append("date|weekday")
    if missing:
        result.errors.append(RowError(first_row, None, f"нет обязательных колонок: {', '.join(missing)}"))
        return result
    for offset, row in enumerate(rows[1:], start=first_row + 1):
        if not any(c not in (None, "") for c in row):
            continue
        result.rows_total += 1
        try:
            recs = _parse_row(row, mapping, tz=tz, term=term, bells=bells)
        except ValueError as e:
            column = str(e.args[1]) if len(e.args) > 1 else None
            result.errors.append(RowError(offset, column, str(e.args[0])))
            continue
        result.rows_ok += 1
        result.records.extend(recs)
    return result


def _parse_row(row: list[Any], m: dict[str, int], *, tz: ZoneInfo, term: Term | None,
               bells: list[tuple[str, str]] | None) -> list[LessonRecord]:
    group = _cell(row, m, "group")
    subject = _cell(row, m, "subject")
    if not group:
        raise ValueError("не указана группа", "group")
    if not subject:
        raise ValueError("не указана дисциплина", "subject")
    start_raw, end_raw = _cell(row, m, "start"), _cell(row, m, "end")
    pair = _cell(row, m, "pair")
    if start_raw is None and pair is not None:
        if not bells:
            raise ValueError("указан номер пары, но в настройках вуза нет расписания звонков", "pair")
        try:
            start_raw, end_raw = bells[int(pair) - 1]
        except (ValueError, IndexError):
            raise ValueError(f"нет пары с номером {pair}", "pair") from None
    try:
        t_start = parse_time(start_raw)
    except ValueError as e:
        raise ValueError(str(e), "start") from None
    try:
        t_end = parse_time(end_raw) if end_raw is not None else None
    except ValueError as e:
        raise ValueError(str(e), "end") from None
    if t_end is None:
        dt = datetime.combine(date(2000, 1, 1), t_start) + timedelta(minutes=90)
        t_end = dt.time()
    if t_end <= t_start:
        raise ValueError("конец занятия раньше начала", "end")

    raw_date = _cell(row, m, "date")
    if raw_date is not None:
        try:
            days = [parse_date(raw_date)]
        except ValueError as e:
            raise ValueError(str(e), "date") from None
    else:
        if term is None:
            raise ValueError("для повторяющихся занятий нужен учебный период (семестр) в настройках вуза", "weekday")
        try:
            weekday = parse_weekday(_cell(row, m, "weekday"))
        except ValueError as e:
            raise ValueError(str(e), "weekday") from None
        try:
            weeks = parse_weeks(_cell(row, m, "weeks"))
        except ValueError:
            raise ValueError("непонятная чётность или список недель", "weeks") from None
        d_from = _cell(row, m, "date_from")
        d_to = _cell(row, m, "date_to")
        try:
            days = expand_weekly(term, weekday, weeks, parse_date(d_from) if d_from else None,
                                 parse_date(d_to) if d_to else None)
        except ValueError as e:
            raise ValueError(str(e), "date_from") from None

    status = "cancelled" if is_cancel(_cell(row, m, "status")) else "scheduled"
    room = _cell(row, m, "room")
    out = []
    for d in days:
        out.append(LessonRecord(
            group=str(group), subject=str(subject), starts_at=combine(d, t_start, tz),
            ends_at=combine(d, t_end, tz), kind=norm_kind(_cell(row, m, "kind")),
            subgroup=str(_cell(row, m, "subgroup")) if _cell(row, m, "subgroup") is not None else None,
            room=str(room) if room is not None else None,
            building=str(_cell(row, m, "building")) if _cell(row, m, "building") is not None else None,
            teacher=_cell(row, m, "teacher"), note=_cell(row, m, "note"), status=status,
        ))
    return out


def read_xlsx(data: bytes) -> list[list[Any]]:
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    ws = wb.worksheets[0]
    return [list(r) for r in ws.iter_rows(values_only=True)]


def read_csv(data: bytes) -> list[list[Any]]:
    text = None
    for enc in ("utf-8-sig", "cp1251"):
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("не удалось определить кодировку CSV")
    sample = text[:4096]
    delimiter = ";" if sample.count(";") >= sample.count(",") else ","
    return [list(r) for r in csv.reader(io.StringIO(text), delimiter=delimiter)]


def parse_template(data: bytes, filename: str, *, tz: ZoneInfo, term: Term | None,
                   bells: list[tuple[str, str]] | None = None) -> ImportResult:
    name = filename.lower()
    if name.endswith((".xlsx", ".xlsm")):
        rows = read_xlsx(data)
    elif name.endswith((".csv", ".txt")):
        rows = read_csv(data)
    else:
        res = ImportResult()
        res.errors.append(RowError(0, None, "поддерживаются .xlsx, .csv и .ics"))
        return res
    return parse_rows(rows, tz=tz, term=term, bells=bells)


def parse_ics(data: bytes, *, group: str, tz: ZoneInfo, window: tuple[date, date]) -> ImportResult:
    """Разворачивает повторения (RRULE, EXDATE) в окне дат."""
    from dateutil.rrule import rrulestr
    from icalendar import Calendar

    result = ImportResult()
    try:
        cal = Calendar.from_ical(data)
    except ValueError as e:
        result.errors.append(RowError(0, None, f"не iCalendar: {e}"))
        return result
    start_w = datetime(window[0].year, window[0].month, window[0].day, tzinfo=tz)
    end_w = datetime(window[1].year, window[1].month, window[1].day, 23, 59, tzinfo=tz)
    for n, comp in enumerate(cal.walk("VEVENT"), start=1):
        result.rows_total += 1
        try:
            dtstart = comp.decoded("DTSTART")
            dtend = comp.decoded("DTEND") if comp.get("DTEND") else dtstart + timedelta(minutes=90)
            if not isinstance(dtstart, datetime):
                raise ValueError("событие на целый день, пропущено")
            if dtstart.tzinfo is None:
                dtstart = dtstart.replace(tzinfo=tz)
                dtend = dtend.replace(tzinfo=tz)
            duration = dtend - dtstart
            summary = str(comp.get("SUMMARY", "")).strip()
            if not summary:
                raise ValueError("нет SUMMARY")
            starts = [dtstart]
            if comp.get("RRULE"):
                rule = rrulestr(comp.get("RRULE").to_ical().decode(), dtstart=dtstart)
                starts = list(rule.between(start_w, end_w, inc=True))
            exdates: set[datetime] = set()
            ex = comp.get("EXDATE")
            for item in ex if isinstance(ex, list) else ([ex] if ex else []):
                for d in item.dts:
                    v = d.dt if isinstance(d.dt, datetime) else datetime.combine(d.dt, dtstart.timetz())
                    exdates.add(v if v.tzinfo else v.replace(tzinfo=tz))
            kind_guess, subject = _split_kind(summary)
            for st in starts:
                if st in exdates or not (start_w <= st <= end_w):
                    continue
                result.records.append(LessonRecord(
                    group=group, subject=subject, starts_at=st.astimezone(tz), ends_at=(st + duration).astimezone(tz),
                    kind=norm_kind(str(comp.get("CATEGORIES").cats[0]) if comp.get("CATEGORIES") else kind_guess),
                    room=str(comp.get("LOCATION")) if comp.get("LOCATION") else None,
                    note=str(comp.get("DESCRIPTION"))[:500] if comp.get("DESCRIPTION") else None,
                    status="cancelled" if str(comp.get("STATUS", "")).upper() == "CANCELLED" else "scheduled",
                ))
            result.rows_ok += 1
        except (ValueError, KeyError, AttributeError) as e:
            result.errors.append(RowError(n, None, str(e)))
    return result


def _split_kind(summary: str) -> tuple[str | None, str]:
    """"Лекция: Математический анализ" или "Матанализ (практика)"."""
    if ":" in summary:
        head, tail = summary.split(":", 1)
        if norm_kind(head) != "other":
            return head, tail.strip()
    if summary.endswith(")") and "(" in summary:
        head, _, tail = summary.rpartition("(")
        if norm_kind(tail.rstrip(")")) != "other":
            return tail.rstrip(")"), head.strip()
    return None, summary
