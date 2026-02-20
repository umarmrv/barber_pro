from datetime import UTC, date, datetime, time

from barber_bot.db.models import WorkShift
from barber_bot.services.slots import generate_slots


def test_generate_slots_respects_busy_intervals() -> None:
    local_day = date(2026, 2, 16)
    shifts = [
        WorkShift(
            barber_id=1,
            weekday=local_day.weekday(),
            start_local_time=time(10, 0),
            end_local_time=time(12, 0),
            is_active=True,
        )
    ]

    busy_start = datetime(2026, 2, 16, 10, 30, tzinfo=UTC)
    busy_end = datetime(2026, 2, 16, 11, 0, tzinfo=UTC)

    slots = generate_slots(
        local_day=local_day,
        tz_name="UTC",
        duration_min=30,
        shifts=shifts,
        busy_intervals=[(busy_start, busy_end)],
        min_start_utc=datetime(2026, 2, 16, 0, 0, tzinfo=UTC),
        max_start_utc=datetime(2026, 2, 16, 23, 59, tzinfo=UTC),
    )

    starts = [slot.starts_at_utc.strftime("%H:%M") for slot in slots]
    assert starts == ["10:00", "11:00", "11:30"]


def test_generate_slots_dynamic_step_by_service_duration() -> None:
    local_day = date(2026, 2, 16)
    shifts = [
        WorkShift(
            barber_id=1,
            weekday=local_day.weekday(),
            start_local_time=time(10, 0),
            end_local_time=time(12, 0),
            is_active=True,
        )
    ]

    slots = generate_slots(
        local_day=local_day,
        tz_name="UTC",
        duration_min=45,
        shifts=shifts,
        busy_intervals=[],
        min_start_utc=datetime(2026, 2, 16, 0, 0, tzinfo=UTC),
        max_start_utc=datetime(2026, 2, 16, 23, 59, tzinfo=UTC),
    )

    starts = [slot.starts_at_utc.strftime("%H:%M") for slot in slots]
    assert starts == ["10:00", "10:45"]
