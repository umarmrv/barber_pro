from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

from barber_bot.config import get_settings
from barber_bot.db import Repository, create_engine_and_sessionmaker
from barber_bot.i18n import tr
from barber_bot.logging_utils import setup_logging
from barber_bot.services.booking import format_booking_local

logger = logging.getLogger(__name__)


async def run() -> None:
    setup_logging()
    settings = get_settings()

    engine, session_factory = create_engine_and_sessionmaker(settings.postgres_dsn)
    bot = Bot(token=settings.bot_token)

    logger.info("Scheduler started")
    try:
        while True:
            async with session_factory() as session:
                repo = Repository(session)
                reminders = await repo.list_due_reminders()

                for reminder in reminders:
                    try:
                        local_dt = format_booking_local(reminder.starts_at_utc, settings.salon_timezone)
                        if reminder.kind == "24h":
                            text = tr(reminder.locale, "reminder_24h", date_time=local_dt)
                        elif reminder.kind == "2h":
                            text = tr(reminder.locale, "reminder_2h", date_time=local_dt)
                        else:
                            text = tr(reminder.locale, "reminder_30m", date_time=local_dt)

                        await bot.send_message(reminder.tg_user_id, text)
                        await repo.mark_reminder_sent(reminder.reminder_id)
                    except Exception:
                        logger.exception("Reminder send failed", extra={"reminder_id": reminder.reminder_id})
                        await repo.increment_reminder_attempt(reminder.reminder_id)

                await session.commit()

            await asyncio.sleep(settings.reminder_poll_seconds)
    finally:
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run())
