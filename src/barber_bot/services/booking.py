from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo


@dataclass(slots=True)
class BookingWindow:
    min_lead_hours: int
    max_days: int


def validate_booking_window(
    starts_at_utc: datetime,
    now_utc: datetime,
    window: BookingWindow,
) -> bool:
    min_allowed = now_utc + timedelta(hours=window.min_lead_hours)
    max_allowed = now_utc + timedelta(days=window.max_days)
    return min_allowed <= starts_at_utc <= max_allowed


def can_cancel_booking(starts_at_utc: datetime, now_utc: datetime, cancel_min_lead_hours: int) -> bool:
    return starts_at_utc - now_utc >= timedelta(hours=cancel_min_lead_hours)


def format_booking_local(starts_at_utc: datetime, tz_name: str) -> str:
    dt = starts_at_utc.astimezone(ZoneInfo(tz_name))
    return dt.strftime("%Y-%m-%d %H:%M")


def utc_now() -> datetime:
    return datetime.now(UTC)
