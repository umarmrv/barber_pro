from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from barber_bot.db.models import Base


def create_engine_and_sessionmaker(postgres_dsn: str) -> tuple[AsyncEngine, async_sessionmaker]:
    engine = create_async_engine(postgres_dsn, future=True, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, session_factory


async def create_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def ensure_runtime_compatibility(engine: AsyncEngine) -> None:
    # Keep existing Postgres volumes working when new columns are introduced.
    async with engine.begin() as conn:
        exists = await conn.execute(text("SELECT to_regclass('public.services')"))
        if exists.scalar_one_or_none() is None:
            return
        await conn.execute(text("ALTER TABLE services ADD COLUMN IF NOT EXISTS name_tj TEXT"))
        await conn.execute(text("UPDATE services SET name_tj = name_ru WHERE name_tj IS NULL"))
        await conn.execute(text("ALTER TABLE services ALTER COLUMN name_tj SET NOT NULL"))
