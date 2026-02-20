from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from barber_bot.bot.handlers import get_routers
from barber_bot.bot.middlewares import ContainerMiddleware, DbSessionMiddleware
from barber_bot.container import AppContainer


def _detach_router_if_needed(router) -> None:
    # Tests can create multiple app instances in one process.
    # aiogram routers are module-level singletons, so we detach before re-attach.
    if getattr(router, "parent_router", None) is not None:
        router._parent_router = None  # type: ignore[attr-defined]


def create_bot_and_dispatcher(container: AppContainer) -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=container.settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = RedisStorage(redis=container.redis)
    dispatcher = Dispatcher(storage=storage)

    dispatcher.update.outer_middleware(ContainerMiddleware(container))
    dispatcher.update.outer_middleware(DbSessionMiddleware(container.session_factory))

    for router in get_routers():
        _detach_router_if_needed(router)
        dispatcher.include_router(router)

    return bot, dispatcher
