from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.types import BotCommand

from barber_bot.config import get_settings
from barber_bot.logging_utils import setup_logging

logger = logging.getLogger(__name__)


def _localized_commands() -> dict[str, list[BotCommand]]:
    return {
        "ru": [
            BotCommand(command="start", description="Старт"),
            BotCommand(command="book", description="Записаться"),
            BotCommand(command="my_bookings", description="Мои записи"),
            BotCommand(command="cancel", description="Отменить запись"),
            BotCommand(command="lang", description="Язык"),
            BotCommand(command="help", description="Помощь"),
            BotCommand(command="admin", description="Админ-меню"),
            BotCommand(command="admin_visits", description="Визиты"),
        ],
        "uz": [
            BotCommand(command="start", description="Бошлаш"),
            BotCommand(command="book", description="Ёзилиш"),
            BotCommand(command="my_bookings", description="Менинг ёзувларим"),
            BotCommand(command="cancel", description="Ёзувни бекор қилиш"),
            BotCommand(command="lang", description="Тил"),
            BotCommand(command="help", description="Ёрдам"),
            BotCommand(command="admin", description="Админ меню"),
            BotCommand(command="admin_visits", description="Ташрифлар"),
        ],
        "tj": [
            BotCommand(command="start", description="Оғоз"),
            BotCommand(command="book", description="Сабт шудан"),
            BotCommand(command="my_bookings", description="Сабтҳои ман"),
            BotCommand(command="cancel", description="Бекор кардани сабт"),
            BotCommand(command="lang", description="Забон"),
            BotCommand(command="help", description="Кӯмак"),
            BotCommand(command="admin", description="Менюи админ"),
            BotCommand(command="admin_visits", description="Ташрифҳо"),
        ],
    }


async def run() -> None:
    setup_logging()
    settings = get_settings()
    bot = Bot(token=settings.bot_token)

    if not settings.skip_bot_api_calls:
        localized = _localized_commands()
        await bot.set_my_commands(localized["ru"])
        await bot.set_my_commands(localized["ru"], language_code="ru")
        await bot.set_my_commands(localized["uz"], language_code="uz")
        await bot.set_my_commands(localized["tj"], language_code="tg")
        await bot.set_my_commands(localized["tj"], language_code="tj")

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
