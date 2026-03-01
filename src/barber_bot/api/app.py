from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.types import BotCommand, Update
from fastapi import FastAPI, Header, HTTPException, Request
from redis.asyncio import Redis

from barber_bot.bot.factory import create_bot_and_dispatcher
from barber_bot.config import Settings, get_settings
from barber_bot.container import AppContainer
from barber_bot.db import (
    Repository,
    create_engine_and_sessionmaker,
    create_schema,
    ensure_runtime_compatibility,
)
from barber_bot.logging_utils import setup_logging
from barber_bot.services.idempotency import consume_update_id

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


def _expected_admin_secret(settings: Settings) -> str:
    if settings.admin_api_secret:
        return settings.admin_api_secret
    return settings.webhook_secret


def _validate_admin_secret(settings: Settings, header_value: str | None) -> None:
    if header_value != _expected_admin_secret(settings):
        raise HTTPException(status_code=403, detail="Invalid admin api secret")


async def _configure_telegram_webhook(
    bot: Bot,
    settings: Settings,
    *,
    drop_pending_updates: bool,
) -> None:
    if not settings.webhook_url:
        raise HTTPException(status_code=400, detail="WEBHOOK_URL is not configured")

    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=settings.webhook_secret,
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=drop_pending_updates,
    )


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()

    engine, session_factory = create_engine_and_sessionmaker(settings.postgres_dsn)
    redis = Redis.from_url(settings.redis_dsn)

    container = AppContainer(
        settings=settings,
        bot=None,
        dispatcher=None,
        session_factory=session_factory,
        redis=redis,
    )
    bot, dispatcher = create_bot_and_dispatcher(container)
    container.bot = bot
    container.dispatcher = dispatcher

    app = FastAPI(title="barber-bot-api", version="0.1.0")
    app.state.container = container
    app.state.engine = engine

    @app.on_event("startup")
    async def on_startup() -> None:
        if settings.auto_create_schema:
            await create_schema(engine)
        await ensure_runtime_compatibility(engine)

        if not settings.skip_bot_api_calls:
            try:
                localized = _localized_commands()
                await bot.set_my_commands(localized["ru"])
                await bot.set_my_commands(localized["ru"], language_code="ru")
                await bot.set_my_commands(localized["uz"], language_code="uz")
                await bot.set_my_commands(localized["tj"], language_code="tg")
                await bot.set_my_commands(localized["tj"], language_code="tj")
            except TelegramAPIError:
                logger.exception("Failed to set bot commands")

            if settings.webhook_url:
                try:
                    await _configure_telegram_webhook(
                        bot,
                        settings,
                        drop_pending_updates=False,
                    )
                    logger.info("Webhook configured by api-service")
                except TelegramRetryAfter as exc:
                    logger.warning(
                        "Webhook setup rate-limited by Telegram, retry_after=%s sec",
                        exc.retry_after,
                    )
                except TelegramAPIError:
                    logger.exception("Failed to configure webhook on startup")
            else:
                logger.warning("WEBHOOK_URL is empty. Telegram webhook setup skipped")

        logger.info("API service started")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await redis.aclose()
        await bot.session.close()
        await engine.dispose()

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz() -> dict[str, str]:
        try:
            if not await redis.ping():
                raise RuntimeError("Redis ping failed")
            async with session_factory() as session:
                repo = Repository(session)
                await repo.ping()
            return {"status": "ready"}
        except Exception as exc:
            logger.exception("Readiness failed")
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/telegram/webhook")
    async def telegram_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: str | None = Header(
            default=None,
            alias="X-Telegram-Bot-Api-Secret-Token",
        ),
    ) -> dict[str, bool]:
        if x_telegram_bot_api_secret_token != settings.webhook_secret:
            raise HTTPException(status_code=403, detail="Invalid webhook secret")

        payload = await request.json()
        update_id = payload.get("update_id")
        if update_id is not None:
            accepted = await consume_update_id(
                redis,
                int(update_id),
                settings.idempotency_ttl_seconds,
            )
            if not accepted:
                return {"ok": True, "duplicate": True}

        update = Update.model_validate(payload)
        assert container.dispatcher is not None
        assert container.bot is not None
        await container.dispatcher.feed_update(container.bot, update)
        return {"ok": True}

    @app.get("/telegram/webhook_info")
    async def telegram_webhook_info(
        x_admin_api_secret: str | None = Header(default=None, alias="X-Admin-Api-Secret"),
    ) -> dict[str, Any]:
        _validate_admin_secret(settings, x_admin_api_secret)

        if settings.skip_bot_api_calls:
            return {"ok": True, "skipped": True, "configured_url": settings.webhook_url or ""}

        info = await bot.get_webhook_info()
        return {
            "ok": True,
            "url": info.url,
            "pending_update_count": info.pending_update_count,
            "last_error_message": info.last_error_message,
            "max_connections": info.max_connections,
            "allowed_updates": info.allowed_updates,
        }

    @app.post("/telegram/webhook_sync")
    async def telegram_webhook_sync(
        drop_pending_updates: bool = False,
        x_admin_api_secret: str | None = Header(default=None, alias="X-Admin-Api-Secret"),
    ) -> dict[str, Any]:
        _validate_admin_secret(settings, x_admin_api_secret)

        if settings.skip_bot_api_calls:
            return {
                "ok": True,
                "skipped": True,
                "webhook_url": settings.webhook_url or "",
                "drop_pending_updates": drop_pending_updates,
            }

        await _configure_telegram_webhook(
            bot,
            settings,
            drop_pending_updates=drop_pending_updates,
        )
        return {
            "ok": True,
            "webhook_url": settings.webhook_url,
            "drop_pending_updates": drop_pending_updates,
        }

    @app.post("/telegram/webhook_delete")
    async def telegram_webhook_delete(
        drop_pending_updates: bool = False,
        x_admin_api_secret: str | None = Header(default=None, alias="X-Admin-Api-Secret"),
    ) -> dict[str, Any]:
        _validate_admin_secret(settings, x_admin_api_secret)

        if settings.skip_bot_api_calls:
            return {"ok": True, "skipped": True, "drop_pending_updates": drop_pending_updates}

        await bot.delete_webhook(drop_pending_updates=drop_pending_updates)
        return {"ok": True, "drop_pending_updates": drop_pending_updates}

    return app
