from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest

from barber_bot.db.models import Base, Barber, Booking, BookingStatus, Client, Service
from barber_bot.db.repositories import Repository
from barber_bot.db.session import create_engine_and_sessionmaker

pytestmark = pytest.mark.asyncio


async def test_hard_delete_service_and_barber_nullifies_booking_links() -> None:
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("Set TEST_POSTGRES_DSN to run postgres hard delete test")

    engine, session_factory = create_engine_and_sessionmaker(dsn)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    now = datetime.now(UTC)
    start = now + timedelta(days=1)

    async with session_factory() as session:
        repo = Repository(session)
        client = await repo.get_or_create_client(int(now.timestamp() * 1_000_000), "ru")
        barber = Barber(name="ToDelete")
        service = Service(
            name_ru="Удалить",
            name_uz="Ochir",
            name_tj="Ҳазф",
            duration_min=30,
            price_minor=100_000,
        )
        session.add_all([barber, service])
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
        await session.flush()
        booking_id = booking.id
        barber_id = barber.id
        service_id = service.id
        await session.commit()

    async with session_factory() as session:
        repo = Repository(session)
        assert await repo.delete_service_hard(service_id)
        assert await repo.delete_barber_hard(barber_id)
        await session.commit()

    async with session_factory() as session:
        booking = await session.get(Booking, booking_id)
        assert booking is not None
        assert booking.service_id is None
        assert booking.barber_id is None

    await engine.dispose()


async def test_hard_delete_booking_blocks_completed_status() -> None:
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("Set TEST_POSTGRES_DSN to run postgres hard delete test")

    engine, session_factory = create_engine_and_sessionmaker(dsn)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    now = datetime.now(UTC)
    start_completed = now + timedelta(days=2)
    start_confirmed = now + timedelta(days=2, hours=1)

    async with session_factory() as session:
        repo = Repository(session)
        client = await repo.get_or_create_client(int(now.timestamp() * 1_000_000) + 77, "ru")
        barber = Barber(name="DeleteGuardBarber")
        service = Service(
            name_ru="Удалить guard",
            name_uz="Guard",
            name_tj="Guard",
            duration_min=30,
            price_minor=100_000,
        )
        session.add_all([barber, service])
        await session.flush()

        completed_booking = Booking(
            client_id=client.id,
            barber_id=barber.id,
            service_id=service.id,
            starts_at_utc=start_completed,
            ends_at_utc=start_completed + timedelta(minutes=30),
            status=BookingStatus.COMPLETED.value,
        )
        confirmed_booking = Booking(
            client_id=client.id,
            barber_id=barber.id,
            service_id=service.id,
            starts_at_utc=start_confirmed,
            ends_at_utc=start_confirmed + timedelta(minutes=30),
            status=BookingStatus.CONFIRMED.value,
        )
        session.add_all([completed_booking, confirmed_booking])
        await session.flush()
        completed_booking_id = completed_booking.id
        confirmed_booking_id = confirmed_booking.id
        await session.commit()

    async with session_factory() as session:
        repo = Repository(session)
        deleted_completed = await repo.delete_booking_hard(completed_booking_id)
        deleted_confirmed = await repo.delete_booking_hard(confirmed_booking_id)
        await session.commit()

    assert deleted_completed is False
    assert deleted_confirmed is True

    async with session_factory() as session:
        completed_after = await session.get(Booking, completed_booking_id)
        confirmed_after = await session.get(Booking, confirmed_booking_id)
        assert completed_after is not None
        assert confirmed_after is None

    await engine.dispose()
