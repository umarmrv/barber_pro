from __future__ import annotations

import os
from datetime import time

import pytest

from barber_bot.db.models import Base
from barber_bot.db.repositories import Repository
from barber_bot.db.session import create_engine_and_sessionmaker

pytestmark = pytest.mark.asyncio


async def test_soft_delete_lists_and_shift_overlap_postgres() -> None:
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("Set TEST_POSTGRES_DSN to run postgres CRUD test")

    engine, session_factory = create_engine_and_sessionmaker(dsn)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        repo = Repository(session)
        active_barber = await repo.create_barber("Active Barber")
        archived_barber = await repo.create_barber("Archived Barber")

        active_service = await repo.create_service(
            duration_min=30,
            price_minor=100_000,
            name_ru="Стрижка актив",
            name_uz="Faol xizmat",
        )
        archived_service = await repo.create_service(
            duration_min=45,
            price_minor=150_000,
            name_ru="Стрижка архив",
            name_uz="Arxiv xizmat",
        )

        await repo.archive_barber(archived_barber.id)
        await repo.archive_service(archived_service.id)
        await session.commit()

        active_barbers = await repo.list_barbers()
        active_services = await repo.list_services()

        active_barber_ids = {barber.id for barber in active_barbers}
        active_service_ids = {service.id for service in active_services}

        assert active_barber.id in active_barber_ids
        assert archived_barber.id not in active_barber_ids
        assert active_service.id in active_service_ids
        assert archived_service.id not in active_service_ids

        created_shift = await repo.create_work_shift(
            barber_id=active_barber.id,
            weekday=1,
            start_local_time=time(10, 0),
            end_local_time=time(14, 0),
        )
        overlapping_shift = await repo.create_work_shift(
            barber_id=active_barber.id,
            weekday=1,
            start_local_time=time(13, 0),
            end_local_time=time(15, 0),
        )

        assert created_shift is not None
        assert overlapping_shift is None
        await session.commit()

    await engine.dispose()
