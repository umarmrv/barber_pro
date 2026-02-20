from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from barber_bot.bot.handlers import booking as booking_handler


class _Settings:
    salon_timezone = "UTC"
    booking_max_days = 2


class _Container:
    settings = _Settings()


@pytest.mark.asyncio
async def test_available_days_include_only_days_with_slots(monkeypatch: pytest.MonkeyPatch) -> None:
    today = datetime.now(UTC).astimezone(ZoneInfo("UTC")).date()
    target_day = today + timedelta(days=1)

    async def fake_slots_for_day(
        *,
        repo,
        barber_id: int,
        local_day,
        duration_min: int,
        container,
        now_utc,
    ):
        return [object()] if local_day == target_day else []

    monkeypatch.setattr(booking_handler, "_slots_for_day", fake_slots_for_day)

    days = await booking_handler._available_days(
        repo=object(),
        barber_id=1,
        duration_min=30,
        container=_Container(),
    )

    assert days == [target_day]
