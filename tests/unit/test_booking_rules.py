from datetime import UTC, datetime, timedelta

from barber_bot.services.booking import BookingWindow, can_cancel_booking, validate_booking_window


def test_booking_window_valid_range() -> None:
    now = datetime(2026, 2, 15, 9, 0, tzinfo=UTC)
    window = BookingWindow(min_lead_hours=1, max_days=14)

    assert validate_booking_window(now + timedelta(hours=2), now, window)
    assert not validate_booking_window(now + timedelta(minutes=30), now, window)
    assert not validate_booking_window(now + timedelta(days=15), now, window)


def test_cancel_deadline() -> None:
    now = datetime(2026, 2, 15, 9, 0, tzinfo=UTC)
    starts = now + timedelta(hours=3)
    assert can_cancel_booking(starts, now, cancel_min_lead_hours=2)

    starts_too_close = now + timedelta(minutes=119)
    assert not can_cancel_booking(starts_too_close, now, cancel_min_lead_hours=2)
