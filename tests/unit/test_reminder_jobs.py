from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from barber_bot.db.models import Booking, BookingStatus, Client, ReminderJob
from barber_bot.db.repositories import Repository


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeSession:
    def __init__(self, client: Client | None):
        self.client = client
        self.added: list[ReminderJob] = []

    async def get(self, model, obj_id):  # noqa: ARG002
        if model is Client:
            return self.client
        return None

    async def execute(self, query):  # noqa: ARG002
        return _FakeResult(None)

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_create_reminders_includes_30m_for_client_with_tg_profile() -> None:
    client = Client(tg_user_id=123456789, locale="ru")
    session = _FakeSession(client)
    repo = Repository(session)

    starts = datetime.now(UTC) + timedelta(days=2)
    booking = Booking(
        id=10,
        client_id=1,
        barber_id=1,
        service_id=1,
        starts_at_utc=starts,
        ends_at_utc=starts + timedelta(minutes=30),
        status=BookingStatus.CONFIRMED.value,
    )

    created = await repo.create_reminder_jobs_for_booking(booking)

    kinds = sorted(item.kind for item in session.added)
    assert created == 3
    assert kinds == ["24h", "2h", "30m"]


@pytest.mark.asyncio
async def test_create_reminders_skips_guest_client_without_tg_profile() -> None:
    client = Client(tg_user_id=None, locale="ru")
    session = _FakeSession(client)
    repo = Repository(session)

    starts = datetime.now(UTC) + timedelta(days=1)
    booking = Booking(
        id=11,
        client_id=2,
        barber_id=1,
        service_id=1,
        starts_at_utc=starts,
        ends_at_utc=starts + timedelta(minutes=30),
        status=BookingStatus.CONFIRMED.value,
    )

    created = await repo.create_reminder_jobs_for_booking(booking)

    assert created == 0
    assert session.added == []
