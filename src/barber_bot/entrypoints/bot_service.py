from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.types import BotCommand

from barber_bot.config import get_settings
from barber_bot.logging_utils import setup_logging

logger = logging.getLogger(__name__)


async def run() -> None:
    setup_logging()
    settings = get_settings()
    bot = Bot(token=settings.bot_token)

    if not settings.skip_bot_api_calls:
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Start bot"),
                BotCommand(command="book", description="Book appointment"),
                BotCommand(command="my_bookings", description="My bookings"),
                BotCommand(command="cancel", description="Cancel booking"),
                BotCommand(command="lang", description="Language"),
                BotCommand(command="help", description="Help"),
                BotCommand(command="admin", description="Admin commands"),
            ]
        )

        if settings.webhook_url:
            await bot.set_webhook(
                url=settings.webhook_url,
                secret_token=settings.webhook_secret,
                allowed_updates=[
                    "message",
                    "callback_query",
                ],
                drop_pending_updates=False,
            )
            logger.info("Webhook configured")

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(run())
