from __future__ import annotations

from aiogram.types import Message, User

from barber_bot.container import AppContainer
from barber_bot.db.repositories import Repository
from barber_bot.i18n import tr


async def get_client_from_user(user: User, repo: Repository, container: AppContainer):
    return await repo.upsert_client_profile(
        tg_user_id=user.id,
        locale=container.settings.default_locale,
        tg_username=user.username,
        tg_first_name=user.first_name,
        tg_last_name=user.last_name,
    )


async def get_client_context(message: Message, repo: Repository, container: AppContainer):
    if not message.from_user:
        raise ValueError("Message has no from_user")
    return await get_client_from_user(message.from_user, repo, container)


async def get_locale_from_message(message: Message, repo: Repository, container: AppContainer) -> str:
    client = await get_client_context(message, repo, container)
    return client.locale


async def notify_admin_group(container: AppContainer, text: str) -> None:
    if not container.settings.admin_group_id:
        return
    if container.bot is None:
        return
    try:
        await container.bot.send_message(container.settings.admin_group_id, text)
    except Exception:
        # Notification failures must not break user actions.
        return


def help_text(locale: str) -> str:
    return tr(locale, "help")
