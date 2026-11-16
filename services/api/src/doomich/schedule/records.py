"""Нормализованная запись о занятии. Все импортёры и адаптеры приводят данные к ней."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

KINDS = {
    "лекция": "lecture", "лек": "lecture", "лк": "lecture", "lecture": "lecture",
    "практика": "practice", "практ": "practice", "пр": "practice", "практическое": "practice",
    "семинар": "practice", "сем": "practice", "practice": "practice", "seminar": "practice",
    "лабораторная": "lab", "лаб": "lab", "лр": "lab", "lab": "lab",
    "экзамен": "exam", "экз": "exam", "exam": "exam",
    "зачёт": "credit", "зачет": "credit", "зач": "credit", "диф. зачёт": "credit", "credit": "credit",
    "консультация": "consultation", "конс": "consultation", "consultation": "consultation",
}

WEEKDAYS = {
    "пн": 0, "понедельник": 0, "mon": 0, "monday": 0, "1": 0,
    "вт": 1, "вторник": 1, "tue": 1, "tuesday": 1, "2": 1,
    "ср": 2, "среда": 2, "wed": 2, "wednesday": 2, "3": 2,
    "чт": 3, "четверг": 3, "thu": 3, "thursday": 3, "4": 3,
    "пт": 4, "пятница": 4, "fri": 4, "friday": 4, "5": 4,
    "сб": 5, "суббота": 5, "sat": 5, "saturday": 5, "6": 5,
    "вс": 6, "воскресенье": 6, "sun": 6, "sunday": 6, "7": 6,
}

CANCEL_WORDS = ("отмен", "cancel", "перенесен", "перенесён")


@dataclass
class LessonRecord:
    group: str
    subject: str
    starts_at: datetime
    ends_at: datetime
    kind: str = "other"
    subgroup: str | None = None
    room: str | None = None
    building: str | None = None
    teacher: str | None = None
    note: str | None = None
    status: str = "scheduled"
    extra: dict[str, Any] = field(default_factory=dict)

    def slot(self) -> str:
        return f"{self.starts_at.isoformat()}|{self.subgroup or ''}"

    def ext_key(self, salt: str = "") -> str:
        raw = f"{norm_group(self.group)}|{self.slot()}|{salt}"
        return hashlib.sha1(raw.encode()).hexdigest()[:20]  # noqa: S324 - не для безопасности

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["starts_at"] = self.starts_at.isoformat()
        d["ends_at"] = self.ends_at.isoformat()
        return d

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> LessonRecord:
        d = dict(d)
        d["starts_at"] = datetime.fromisoformat(d["starts_at"])
        d["ends_at"] = datetime.fromisoformat(d["ends_at"])
        return cls(**d)


def norm_group(code: str) -> str:
    return re.sub(r"\s+", "", code.strip().upper()).replace("–", "-").replace("—", "-")


def norm_kind(value: str | None) -> str:
    if not value:
        return "other"
    v = value.strip().lower().rstrip(".")
    if v in KINDS:
        return KINDS[v]
    for key, kind in KINDS.items():
        if v.startswith(key):
            return kind
    return "other"


def parse_time(value: Any) -> time:
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, (int, float)) and 0 <= float(value) < 1:  # время в Excel как доля суток
        minutes = round(float(value) * 24 * 60)
        return time(minutes // 60, minutes % 60)
    s = str(value).strip().replace(".", ":").replace("-", ":")
    m = re.fullmatch(r"(\d{1,2}):(\d{2})(?::\d{2})?", s)
    if not m:
        raise ValueError(f"не похоже на время: {value!r}")
    return time(int(m.group(1)), int(m.group(2)))


def parse_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    for pattern, order in ((r"(\d{4})-(\d{1,2})-(\d{1,2})", "ymd"), (r"(\d{1,2})\.(\d{1,2})\.(\d{4})", "dmy"),
                           (r"(\d{1,2})\.(\d{1,2})\.(\d{2})", "dmy2"), (r"(\d{1,2})/(\d{1,2})/(\d{4})", "dmy")):
        m = re.fullmatch(pattern, s)
        if m:
            a, b, c = (int(x) for x in m.groups())
            if order == "ymd":
                return date(a, b, c)
            if order == "dmy2":
                return date(2000 + c, b, a)
            return date(c, b, a)
    raise ValueError(f"не похоже на дату: {value!r}")


def parse_weekday(value: Any) -> int:
    key = str(value).strip().lower().rstrip(".")
    if key in WEEKDAYS:
        return WEEKDAYS[key]
    raise ValueError(f"неизвестный день недели: {value!r}")


def combine(day: date, t: time, tz: ZoneInfo) -> datetime:
    return datetime(day.year, day.month, day.day, t.hour, t.minute, tzinfo=tz)


@dataclass
class Term:
    starts_on: date
    ends_on: date
    first_week_odd: bool = True
    holidays: set[date] = field(default_factory=set)

    def week_number(self, day: date) -> int:
        monday0 = self.starts_on - timedelta(days=self.starts_on.weekday())
        monday = day - timedelta(days=day.weekday())
        return (monday - monday0).days // 7 + 1

    def is_odd(self, day: date) -> bool:
        first = (self.week_number(day) - 1) % 2 == 0
        return first if self.first_week_odd else not first


def parse_weeks(value: Any) -> tuple[str, set[int]]:
    """Возвращает режим: all | odd | even | list и набор номеров недель для list."""
    if value is None or str(value).strip() == "":
        return "all", set()
    v = str(value).strip().lower()
    if v in ("все", "всё", "all", "каждая", "еженедельно", "*"):
        return "all", set()
    if v.startswith(("неч", "odd", "числ", "1/2")) and not v.startswith("чет"):
        return "odd", set()
    if v.startswith(("чёт", "чет", "even", "знам", "2/2")):
        return "even", set()
    nums: set[int] = set()
    for part in re.split(r"[,;\s]+", v):
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            nums.update(range(int(a), int(b) + 1))
        else:
            nums.add(int(part))
    return "list", nums


def expand_weekly(term: Term, weekday: int, weeks: tuple[str, set[int]], date_from: date | None,
                  date_to: date | None) -> list[date]:
    start = max(term.starts_on, date_from or term.starts_on)
    end = min(term.ends_on, date_to or term.ends_on)
    mode, nums = weeks
    day = start + timedelta(days=(weekday - start.weekday()) % 7)
    out: list[date] = []
    while day <= end:
        if day not in term.holidays:
            if mode == "all" or (mode == "odd" and term.is_odd(day)) or (mode == "even" and not term.is_odd(day)) \
                    or (mode == "list" and term.week_number(day) in nums):
                out.append(day)
        day += timedelta(days=7)
    return out


def is_cancel(value: Any) -> bool:
    return bool(value) and any(w in str(value).lower() for w in CANCEL_WORDS)
