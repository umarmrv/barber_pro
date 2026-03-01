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
        service = Service(
            name_ru="Стрижка",
            name_uz="Soch",
            name_tj="Мӯйсаргирӣ",
            duration_min=30,
            price_minor=100_000,
        )
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
        service = Service(
            name_ru="Стрижка",
            name_uz="Soch",
            name_tj="Мӯйсаргирӣ",
            duration_min=30,
            price_minor=100_000,
        )
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


async def test_sum_cash_for_range_counts_completed_bookings_only_by_default() -> None:
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("Set TEST_POSTGRES_DSN to run postgres detail test")

    engine, session_factory = create_engine_and_sessionmaker(dsn)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    now = datetime.now(UTC)
    start = now + timedelta(hours=1)

    async with session_factory() as session:
        client = Client(
            tg_user_id=int(now.timestamp() * 1_000_000) + 7,
            tg_username="cash_client",
            phone_e164="+998900000777",
            locale="ru",
        )
        barber = Barber(name="CashBarber")
        service1 = Service(
            name_ru="Стрижка 1",
            name_uz="Soch 1",
            name_tj="Мӯйсаргирӣ 1",
            duration_min=30,
            price_minor=120_000,
        )
        service2 = Service(
            name_ru="Стрижка 2",
            name_uz="Soch 2",
            name_tj="Мӯйсаргирӣ 2",
            duration_min=30,
            price_minor=80_000,
        )
        session.add_all([client, barber, service1, service2])
        await session.flush()

        session.add_all(
            [
                Booking(
                    client_id=client.id,
                    barber_id=barber.id,
                    service_id=service1.id,
                    starts_at_utc=start,
                    ends_at_utc=start + timedelta(minutes=30),
                    status=BookingStatus.COMPLETED.value,
                ),
                Booking(
                    client_id=client.id,
                    barber_id=barber.id,
                    service_id=service2.id,
                    starts_at_utc=start + timedelta(minutes=45),
                    ends_at_utc=start + timedelta(minutes=75),
                    status=BookingStatus.CONFIRMED.value,
                ),
            ]
        )
        await session.commit()

    async with session_factory() as session:
        repo = Repository(session)
        from_utc = start - timedelta(minutes=15)
        to_utc = start + timedelta(hours=2)
        cash_completed = await repo.sum_cash_for_range(
            starts_from_utc=from_utc,
            starts_to_utc=to_utc,
        )
        cash_all = await repo.sum_cash_for_range(
            starts_from_utc=from_utc,
            starts_to_utc=to_utc,
            include_statuses=(BookingStatus.COMPLETED.value, BookingStatus.CONFIRMED.value),
        )

    assert cash_completed == 120_000
    assert cash_all == 200_000

    await engine.dispose()
