from __future__ import annotations

from datetime import time

from barber_bot.bot.handlers.admin import _parse_weekly_schedule


def test_parse_weekly_schedule_valid() -> None:
    payload = """\
1 10:00-14:00,15:00-19:00
2 10:00-18:00
3 off
4 10:00-18:00
5 10:00-18:00
6 off
7 off
"""

    parsed, error = _parse_weekly_schedule(payload)

    assert error is None
    assert parsed is not None
    assert parsed[0] == [(time(10, 0), time(14, 0)), (time(15, 0), time(19, 0))]
    assert parsed[2] == []


def test_parse_weekly_schedule_missing_days() -> None:
    payload = """\
1 10:00-14:00
2 off
3 off
"""

    parsed, error = _parse_weekly_schedule(payload)

    assert parsed is None
    assert error == "missing_days"


def test_parse_weekly_schedule_rejects_overlap() -> None:
    payload = """\
1 10:00-14:00,13:00-18:00
2 off
3 off
4 off
5 off
6 off
7 off
"""

    parsed, error = _parse_weekly_schedule(payload)

    assert parsed is None
    assert error == "invalid"
