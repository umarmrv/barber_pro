from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from barber_bot.db.models import Base, Barber, Booking, BookingEvent, BookingStatus, Client, Service
from barber_bot.db.repositories import Repository
from barber_bot.db.session import create_engine_and_sessionmaker

pytestmark = pytest.mark.asyncio


async def test_visit_status_transition_and_events_postgres() -> None:
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("Set TEST_POSTGRES_DSN to run postgres visit-status test")

    engine, session_factory = create_engine_and_sessionmaker(dsn)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    starts = datetime.now(UTC).replace(second=0, microsecond=0) + timedelta(days=1)
    ends = starts + timedelta(minutes=30)
    tg_seed = int(datetime.now(UTC).timestamp() * 1_000_000)
    phone = f"+998{tg_seed % 1_000_000_000:09d}"

    async with session_factory() as session:
        client = Client(tg_user_id=tg_seed, phone_e164=phone, locale="ru")
        barber = Barber(name="VisitBarber")
        service = Service(
            name_ru="Стрижка",
            name_uz="Soch",
            name_tj="Мӯйсаргирӣ",
            duration_min=30,
            price_minor=100_000,
        )
        session.add_all([client, barber, service])
        await session.flush()

        repo = Repository(session)
        booking = await repo.create_confirmed_booking(
            client_id=client.id,
            barber_id=barber.id,
            service_id=service.id,
            starts_at_utc=starts,
            ends_at_utc=ends,
        )
        assert booking is not None
        booking_id = booking.id
        await session.commit()

    async with session_factory() as session:
        repo = Repository(session)
        updated = await repo.set_booking_status(
            booking_id=booking_id,
            new_status=BookingStatus.COMPLETED.value,
            reason="test_completed",
            actor_tg_user_id=111,
        )
        assert updated is not None
        await session.commit()

    async with session_factory() as session:
        repo = Repository(session)
        reverted = await repo.set_booking_status(
            booking_id=booking_id,
            new_status=BookingStatus.CONFIRMED.value,
            reason="test_revert",
            actor_tg_user_id=222,
        )
        assert reverted is not None
        await session.commit()

    async with session_factory() as session:
        booking = await session.get(Booking, booking_id)
        assert booking is not None
        assert booking.status == BookingStatus.CONFIRMED.value

        events = await session.execute(
            select(BookingEvent.event_type).where(BookingEvent.booking_id == booking_id)
        )
        event_types = [row[0] for row in events]
        assert "service_completed" in event_types
        assert "service_completion_reverted" in event_types

    await engine.dispose()


async def test_completed_booking_blocks_overlapping_booking_postgres() -> None:
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("Set TEST_POSTGRES_DSN to run postgres overlap test")

    engine, session_factory = create_engine_and_sessionmaker(dsn)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    starts = datetime.now(UTC).replace(second=0, microsecond=0) + timedelta(days=2)
    ends = starts + timedelta(minutes=30)
    tg_seed = int(datetime.now(UTC).timestamp() * 1_000_000) + 10
    phone = f"+998{tg_seed % 1_000_000_000:09d}"

    async with session_factory() as session:
        client = Client(tg_user_id=tg_seed, phone_e164=phone, locale="ru")
        barber = Barber(name="OverlapBarber")
        service = Service(
            name_ru="Стрижка",
            name_uz="Soch",
            name_tj="Мӯйсаргирӣ",
            duration_min=30,
            price_minor=100_000,
        )
        session.add_all([client, barber, service])
        await session.flush()

        repo = Repository(session)
        booking = await repo.create_confirmed_booking(
            client_id=client.id,
            barber_id=barber.id,
            service_id=service.id,
            starts_at_utc=starts,
            ends_at_utc=ends,
        )
        assert booking is not None
        client_id = client.id
        barber_id = barber.id
        service_id = service.id
        await session.flush()

        updated = await repo.set_booking_status(
            booking_id=booking.id,
            new_status=BookingStatus.COMPLETED.value,
            reason="test_completed",
            actor_tg_user_id=333,
        )
        assert updated is not None
        await session.commit()

    async with session_factory() as session:
        repo = Repository(session)
        overlap = await repo.create_confirmed_booking(
            client_id=client_id,
            barber_id=barber_id,
            service_id=service_id,
            starts_at_utc=starts,
            ends_at_utc=ends,
        )
        assert overlap is None
        await session.rollback()

    await engine.dispose()
