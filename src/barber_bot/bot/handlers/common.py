from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from barber_bot.bot.keyboards import (
    client_main_reply_keyboard,
    client_menu_texts,
    lang_keyboard,
    services_keyboard,
)
from barber_bot.bot.states import BookingStates, OnboardingStates
from barber_bot.bot.utils import get_client_context, get_client_from_user, help_text
from barber_bot.container import AppContainer
from barber_bot.db.repositories import Repository
from barber_bot.i18n import tr
from barber_bot.services.phone import normalize_phone

router = Router(name="common")


async def _show_lang_picker(message: Message, locale: str) -> None:
    await message.answer(
        tr(locale, "choose_lang"),
        reply_markup=lang_keyboard(),
    )
    await message.answer(
        tr(locale, "next_step_hint", value=tr(locale, "next_step_back_menu")),
        reply_markup=client_main_reply_keyboard(locale),
    )


@router.message(Command("start"))
async def cmd_start(
    message: Message,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    client = await get_client_context(message, repo, container)
    await message.answer(tr(client.locale, "welcome"), reply_markup=client_main_reply_keyboard(client.locale))
    await message.answer(tr(client.locale, "choose_lang"), reply_markup=lang_keyboard())
    if not client.phone_e164:
        await state.set_state(OnboardingStates.waiting_phone)
        await message.answer(tr(client.locale, "ask_phone"))
        await message.answer(tr(client.locale, "next_step_hint", value=tr(client.locale, "next_step_enter_phone")))
    await session.commit()


@router.message(Command("help"))
async def cmd_help(message: Message, repo: Repository, container: AppContainer) -> None:
    locale = (await get_client_context(message, repo, container)).locale
    await message.answer(help_text(locale), reply_markup=client_main_reply_keyboard(locale))


@router.message(Command("lang"))
async def cmd_lang(message: Message, repo: Repository, container: AppContainer) -> None:
    locale = (await get_client_context(message, repo, container)).locale
    await _show_lang_picker(message, locale)


@router.message(F.text.in_(client_menu_texts("lang")))
async def menu_lang(message: Message, repo: Repository, container: AppContainer) -> None:
    locale = (await get_client_context(message, repo, container)).locale
    await _show_lang_picker(message, locale)


@router.message(F.text.in_(client_menu_texts("help")))
async def menu_help(message: Message, repo: Repository, container: AppContainer) -> None:
    locale = (await get_client_context(message, repo, container)).locale
    await message.answer(help_text(locale), reply_markup=client_main_reply_keyboard(locale))


@router.callback_query(F.data.startswith("lang:"))
async def cb_lang(
    callback: CallbackQuery,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    if callback.from_user is None:
        return
    locale = callback.data.split(":", maxsplit=1)[1]
    if locale not in {"ru", "uz", "tj"}:
        current_locale = (await get_client_from_user(callback.from_user, repo, container)).locale
        await callback.answer(tr(current_locale, "unsupported_locale"))
        return

    client = await get_client_from_user(callback.from_user, repo, container)
    await repo.update_client_locale(client.id, locale)
    await session.commit()

    await callback.message.answer(tr(locale, "lang_updated"), reply_markup=client_main_reply_keyboard(locale))
    await callback.message.answer(
        tr(locale, "next_step_hint", value=tr(locale, "next_step_back_menu")),
        reply_markup=client_main_reply_keyboard(locale),
    )
    await callback.answer()


@router.message(OnboardingStates.waiting_phone)
async def on_phone_input(
    message: Message,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    if message.from_user is None or message.text is None:
        return

    client = await get_client_from_user(message.from_user, repo, container)
    normalized = normalize_phone(message.text, container.settings.default_region)
    if not normalized:
        await message.answer(tr(client.locale, "invalid_phone"))
        return

    await repo.update_client_phone(client.id, normalized)
    await session.commit()
    await message.answer(tr(client.locale, "phone_saved"), reply_markup=client_main_reply_keyboard(client.locale))

    data = await state.get_data()
    after_phone = data.get("after_phone")
    await state.clear()
    if after_phone == "book":
        services = await repo.list_active_services()
        if services:
            await state.set_state(BookingStates.choose_service)
            await message.answer(
                tr(client.locale, "choose_service"),
                reply_markup=services_keyboard(services, client.locale),
            )
            await message.answer(
                tr(client.locale, "next_step_hint", value=tr(client.locale, "next_step_choose_service"))
            )
