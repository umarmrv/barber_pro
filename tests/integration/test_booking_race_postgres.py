from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, time, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from barber_bot.db.models import Base, Barber, Client, Service, WorkShift
from barber_bot.db.repositories import Repository
from barber_bot.db.session import create_engine_and_sessionmaker


pytestmark = pytest.mark.asyncio


async def _attempt_booking(
    session_factory,
    *,
    client_id: int,
    barber_id: int,
    service_id: int,
    starts_at: datetime,
    ends_at: datetime,
) -> bool:
    async with session_factory() as session:
        repo = Repository(session)
        booking = await repo.create_confirmed_booking(
            client_id=client_id,
            barber_id=barber_id,
            service_id=service_id,
            starts_at_utc=starts_at,
            ends_at_utc=ends_at,
        )
        if booking is None:
            await session.rollback()
            return False
        try:
            await session.commit()
            return True
        except IntegrityError:
            await session.rollback()
            return False


async def test_parallel_booking_conflict_postgres() -> None:
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("Set TEST_POSTGRES_DSN to run postgres race-condition test")

    engine, session_factory = create_engine_and_sessionmaker(dsn)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        client = Client(
            tg_user_id=int(datetime.now(UTC).timestamp() * 1_000_000),
            phone_e164="+998901111111",
            locale="ru",
        )
        service = Service(
            name_ru="Стрижка",
            name_uz="Soch",
            name_tj="Мӯйсаргирӣ",
            duration_min=30,
            price_minor=100_000,
        )
        barber = Barber(name="Akmal")
        session.add(client)
        session.add(service)
        session.add(barber)
        await session.flush()
        session.add(
            WorkShift(
                barber_id=barber.id,
                weekday=0,
                start_local_time=time(10, 0),
                end_local_time=time(19, 0),
                is_active=True,
            )
        )
        await session.commit()

    starts_at = datetime.now(UTC) + timedelta(days=1)
    starts_at = starts_at.replace(minute=0, second=0, microsecond=0)
    ends_at = starts_at + timedelta(minutes=30)

    results = await asyncio.gather(
        _attempt_booking(
            session_factory,
            client_id=client.id,
            barber_id=barber.id,
            service_id=service.id,
            starts_at=starts_at,
            ends_at=ends_at,
        ),
        _attempt_booking(
            session_factory,
            client_id=client.id,
            barber_id=barber.id,
            service_id=service.id,
            starts_at=starts_at,
            ends_at=ends_at,
        ),
    )

    assert sum(results) == 1

    await engine.dispose()
