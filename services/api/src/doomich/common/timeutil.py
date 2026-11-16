from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo


def utcnow() -> datetime:
    return datetime.now(UTC)


def today_utc() -> date:
    return utcnow().date()


def tz(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("Europe/Moscow")


def local_now(tz_name: str) -> datetime:
    return utcnow().astimezone(tz(tz_name))


def day_bounds(day: date, tz_name: str) -> tuple[datetime, datetime]:
    """Начало и конец суток в часовом поясе вуза, в UTC."""
    zone = tz(tz_name)
    start = datetime(day.year, day.month, day.day, tzinfo=zone)
    end = start + timedelta(days=1)
    return start.astimezone(UTC), end.astimezone(UTC)


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def month_key(dt: datetime | None = None) -> str:
    dt = dt or utcnow()
    return f"{dt.year:04d}-{dt.month:02d}"


def combine_local(day: date, hhmm: str, tz_name: str) -> datetime:
    hours, minutes = hhmm.split(":")
    return datetime(day.year, day.month, day.day, int(hours), int(minutes), tzinfo=tz(tz_name))


def utc_offset_minutes(tz_name: str) -> int:
    offset = local_now(tz_name).utcoffset()
    return int(offset.total_seconds() // 60) if offset else 0
