from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot, Dispatcher
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from barber_bot.config import Settings


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    bot: Bot | None
    dispatcher: Dispatcher | None
    session_factory: async_sessionmaker[AsyncSession]
    redis: Redis
