from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest

from barber_bot.db.models import Base, Barber, Booking, BookingStatus, Client, Service
from barber_bot.db.repositories import Repository
from barber_bot.db.session import create_engine_and_sessionmaker

pytestmark = pytest.mark.asyncio


async def test_today_bookings_detailed_contains_client_profile_fields() -> None:
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("Set TEST_POSTGRES_DSN to run postgres detail test")

    engine, session_factory = create_engine_and_sessionmaker(dsn)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    now = datetime.now(UTC)
    start = now + timedelta(minutes=5)

    async with session_factory() as session:
        client = Client(
            tg_user_id=int(now.timestamp() * 1_000_000),
            tg_username="client_nick",
            phone_e164="+998901234567",
            locale="ru",
        )
        barber = Barber(name="Ali")
        service = Service(name_ru="Стрижка", name_uz="Soch", duration_min=30, price_minor=100_000)
        session.add_all([client, barber, service])
        await session.flush()

        booking = Booking(
            client_id=client.id,
            barber_id=barber.id,
            service_id=service.id,
            starts_at_utc=start,
            ends_at_utc=start + timedelta(minutes=30),
            status=BookingStatus.CONFIRMED.value,
        )
        session.add(booking)
        await session.commit()

    async with session_factory() as session:
        repo = Repository(session)
        rows = await repo.list_today_bookings_detailed("UTC")

    assert any(
        row.client_tg_username == "client_nick" and row.client_phone_e164 == "+998901234567"
        for row in rows
    )

    await engine.dispose()
