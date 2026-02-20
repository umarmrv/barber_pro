from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from barber_bot.db.models import WorkShift


@dataclass(slots=True)
class Slot:
    starts_at_utc: datetime
    ends_at_utc: datetime


@dataclass(slots=True)
class Interval:
    starts_at_utc: datetime
    ends_at_utc: datetime


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and a_end > b_start


def generate_slots(
    *,
    local_day: date,
    tz_name: str,
    duration_min: int,
    shifts: list[WorkShift],
    busy_intervals: list[tuple[datetime, datetime]],
    min_start_utc: datetime,
    max_start_utc: datetime,
) -> list[Slot]:
    tz = ZoneInfo(tz_name)
    duration = timedelta(minutes=duration_min)
    slots: list[Slot] = []

    for shift in shifts:
        shift_start_local = datetime.combine(local_day, shift.start_local_time, tz)
        shift_end_local = datetime.combine(local_day, shift.end_local_time, tz)

        cursor_local = shift_start_local
        # Dynamic step by selected service duration.
        while cursor_local + duration <= shift_end_local:
            start_utc = cursor_local.astimezone(UTC)
            end_utc = (cursor_local + duration).astimezone(UTC)

            if start_utc < min_start_utc or start_utc > max_start_utc:
                cursor_local += duration
                continue

            conflict = any(
                overlaps(start_utc, end_utc, busy_start, busy_end)
                for busy_start, busy_end in busy_intervals
            )
            if not conflict:
                slots.append(Slot(starts_at_utc=start_utc, ends_at_utc=end_utc))

            cursor_local += duration

    slots.sort(key=lambda x: x.starts_at_utc)
    return slots
