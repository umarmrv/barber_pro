from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo


def now_utc() -> datetime:
    return datetime.now(UTC)


def to_local(dt_utc: datetime, tz_name: str) -> datetime:
    return dt_utc.astimezone(ZoneInfo(tz_name))


def from_local(dt_local: datetime, tz_name: str) -> datetime:
    if dt_local.tzinfo is None:
        dt_local = dt_local.replace(tzinfo=ZoneInfo(tz_name))
    return dt_local.astimezone(UTC)
