from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from barber_bot.db.models import Base


def create_engine_and_sessionmaker(postgres_dsn: str) -> tuple[AsyncEngine, async_sessionmaker]:
    engine = create_async_engine(postgres_dsn, future=True, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, session_factory


async def create_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
