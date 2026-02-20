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


async def test_monitoring_bookings_detailed_includes_today_and_horizon_days() -> None:
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("Set TEST_POSTGRES_DSN to run postgres detail test")

    engine, session_factory = create_engine_and_sessionmaker(dsn)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    now = datetime.now(UTC)
    day_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
    start_today = day_start + timedelta(hours=10)
    start_tomorrow = day_start + timedelta(days=1, hours=11)
    start_after_horizon = day_start + timedelta(days=2, hours=12)

    async with session_factory() as session:
        client = Client(
            tg_user_id=int(now.timestamp() * 1_000_000) + 1,
            tg_username="monitor_client",
            phone_e164="+998900000001",
            locale="ru",
        )
        barber = Barber(name="MonitorAli")
        service = Service(name_ru="Стрижка", name_uz="Soch", duration_min=30, price_minor=100_000)
        session.add_all([client, barber, service])
        await session.flush()

        session.add_all(
            [
                Booking(
                    client_id=client.id,
                    barber_id=barber.id,
                    service_id=service.id,
                    starts_at_utc=start_today,
                    ends_at_utc=start_today + timedelta(minutes=30),
                    status=BookingStatus.CANCELLED.value,
                ),
                Booking(
                    client_id=client.id,
                    barber_id=barber.id,
                    service_id=service.id,
                    starts_at_utc=start_tomorrow,
                    ends_at_utc=start_tomorrow + timedelta(minutes=30),
                    status=BookingStatus.CONFIRMED.value,
                ),
                Booking(
                    client_id=client.id,
                    barber_id=barber.id,
                    service_id=service.id,
                    starts_at_utc=start_after_horizon,
                    ends_at_utc=start_after_horizon + timedelta(minutes=30),
                    status=BookingStatus.CONFIRMED.value,
                ),
            ]
        )
        await session.commit()

    async with session_factory() as session:
        repo = Repository(session)
        rows = await repo.list_monitoring_bookings_detailed("UTC", days=1)

    starts = {row.starts_at_utc for row in rows}
    assert start_today in starts
    assert start_tomorrow in starts
    assert start_after_horizon not in starts

    await engine.dispose()
