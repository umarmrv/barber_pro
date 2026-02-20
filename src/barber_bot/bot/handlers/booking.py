from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from barber_bot.bot.keyboards import (
    no_slots_back_keyboard,
    barbers_keyboard,
    cancel_keyboard,
    confirm_keyboard,
    dates_keyboard,
    services_keyboard,
    slots_keyboard,
)
from barber_bot.bot.states import BookingStates, OnboardingStates
from barber_bot.bot.utils import get_client_context, get_client_from_user, notify_admin_group
from barber_bot.container import AppContainer
from barber_bot.db.repositories import Repository
from barber_bot.i18n import tr
from barber_bot.services.booking import (
    BookingWindow,
    can_cancel_booking,
    format_booking_local,
    validate_booking_window,
)
from barber_bot.services.drafts import get_draft, save_draft
from barber_bot.services.slots import generate_slots

router = Router(name="booking")


async def _send_next_step(message: Message, locale: str, step_key: str) -> None:
    await message.answer(tr(locale, "next_step_hint", value=tr(locale, step_key)))


async def _prompt_services(message: Message, client_locale: str, repo: Repository) -> None:
    services = await repo.list_active_services()
    if not services:
        await message.answer("No services configured")
        return
    await message.answer(
        tr(client_locale, "choose_service"),
        reply_markup=services_keyboard(services, client_locale),
    )
    await _send_next_step(message, client_locale, "next_step_choose_service")


async def _slots_for_day(
    *,
    repo: Repository,
    barber_id: int,
    local_day: date,
    duration_min: int,
    container: AppContainer,
    now_utc: datetime,
):
    shifts = await repo.list_shifts_for_barber_weekday(barber_id, local_day.weekday())
    busy = await repo.list_busy_intervals_for_local_day(
        barber_id,
        local_day,
        container.settings.salon_timezone,
    )
    return generate_slots(
        local_day=local_day,
        tz_name=container.settings.salon_timezone,
        duration_min=duration_min,
        shifts=shifts,
        busy_intervals=busy,
        min_start_utc=now_utc + timedelta(hours=container.settings.booking_min_lead_hours),
        max_start_utc=now_utc + timedelta(days=container.settings.booking_max_days),
    )


async def _available_days(
    *,
    repo: Repository,
    barber_id: int,
    duration_min: int,
    container: AppContainer,
) -> list[date]:
    salon_tz = ZoneInfo(container.settings.salon_timezone)
    now_utc = datetime.now(UTC)
    now_local = now_utc.astimezone(salon_tz).date()
    days: list[date] = []
    for i in range(container.settings.booking_max_days + 1):
        day = now_local + timedelta(days=i)
        slots = await _slots_for_day(
            repo=repo,
            barber_id=barber_id,
            local_day=day,
            duration_min=duration_min,
            container=container,
            now_utc=now_utc,
        )
        if slots:
            days.append(day)
    return days


@router.message(Command("book"))
async def cmd_book(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    client = await get_client_context(message, repo, container)
    if not client.phone_e164:
        await state.set_state(OnboardingStates.waiting_phone)
        await state.update_data(after_phone="book")
        await message.answer(tr(client.locale, "need_phone_before_booking"))
        await message.answer(tr(client.locale, "ask_phone"))
        await _send_next_step(message, client.locale, "next_step_enter_phone")
        return

    await state.set_state(BookingStates.choose_service)
    await _prompt_services(message, client.locale, repo)


@router.callback_query(F.data.startswith("svc:"))
async def cb_service(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if callback.from_user is None:
        return
    client = await get_client_from_user(callback.from_user, repo, container)
    service_id = int(callback.data.split(":", maxsplit=1)[1])

    service = await repo.get_service(service_id)
    if service is None or not service.is_active:
        await callback.answer("Service not found", show_alert=True)
        return

    barbers = await repo.list_active_barbers()
    if not barbers:
        await callback.answer("No active barbers", show_alert=True)
        return

    await state.update_data(service_id=service_id)
    await state.set_state(BookingStates.choose_barber)
    await callback.message.answer(
        tr(client.locale, "choose_barber"),
        reply_markup=barbers_keyboard(barbers),
    )
    await _send_next_step(callback.message, client.locale, "next_step_choose_barber")
    await callback.answer()


@router.callback_query(F.data.startswith("barber:"))
async def cb_barber(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if callback.from_user is None:
        return
    client = await get_client_from_user(callback.from_user, repo, container)
    state_data = await state.get_data()
    service_id = state_data.get("service_id")
    if not service_id:
        await callback.answer("Flow expired. Use /book", show_alert=True)
        return
    service = await repo.get_service(int(service_id))
    if service is None or not service.is_active:
        await callback.answer("Service not found", show_alert=True)
        return

    barber_id = int(callback.data.split(":", maxsplit=1)[1])
    barber = await repo.get_barber(barber_id)
    if barber is None or not barber.is_active:
        await callback.answer("Barber not found", show_alert=True)
        return

    days = await _available_days(
        repo=repo,
        barber_id=barber_id,
        duration_min=service.duration_min,
        container=container,
    )
    await state.update_data(barber_id=barber_id)
    await state.set_state(BookingStates.choose_date)
    if not days:
        await callback.message.answer(
            tr(client.locale, "no_available_dates"),
            reply_markup=no_slots_back_keyboard(client.locale),
        )
    else:
        await callback.message.answer(tr(client.locale, "choose_date"), reply_markup=dates_keyboard(days))
    await _send_next_step(callback.message, client.locale, "next_step_choose_date")
    await callback.answer()


@router.callback_query(F.data == "back:barbers")
async def cb_back_barbers(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if callback.from_user is None:
        return
    client = await get_client_from_user(callback.from_user, repo, container)
    barbers = await repo.list_active_barbers()
    if not barbers:
        await callback.answer("No active barbers", show_alert=True)
        return
    await state.set_state(BookingStates.choose_barber)
    await callback.message.answer(
        tr(client.locale, "choose_barber"),
        reply_markup=barbers_keyboard(barbers),
    )
    await _send_next_step(callback.message, client.locale, "next_step_choose_barber")
    await callback.answer()


@router.callback_query(F.data.startswith("date:"))
async def cb_date(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if callback.from_user is None:
        return

    client = await get_client_from_user(callback.from_user, repo, container)
    data = await state.get_data()
    service_id = data.get("service_id")
    barber_id = data.get("barber_id")
    if not service_id or not barber_id:
        await callback.answer("Flow expired. Use /book", show_alert=True)
        return

    service = await repo.get_service(int(service_id))
    if service is None:
        await callback.answer("Service not found", show_alert=True)
        return

    local_day = date.fromisoformat(callback.data.split(":", maxsplit=1)[1])
    now = datetime.now(UTC)
    slots = await _slots_for_day(
        repo=repo,
        barber_id=int(barber_id),
        local_day=local_day,
        duration_min=service.duration_min,
        container=container,
        now_utc=now,
    )

    if not slots:
        days = await _available_days(
            repo=repo,
            barber_id=int(barber_id),
            duration_min=service.duration_min,
            container=container,
        )
        if not days:
            await callback.message.answer(
                tr(client.locale, "no_available_dates"),
                reply_markup=no_slots_back_keyboard(client.locale),
            )
        else:
            await callback.message.answer(
                tr(client.locale, "choose_date"),
                reply_markup=dates_keyboard(days),
            )
        await _send_next_step(callback.message, client.locale, "next_step_choose_date")
        await callback.answer()
        return

    slot_map = {
        str(int(slot.starts_at_utc.timestamp())): {
            "starts_at_utc": slot.starts_at_utc.isoformat(),
            "ends_at_utc": slot.ends_at_utc.isoformat(),
        }
        for slot in slots
    }
    await state.update_data(slot_map=slot_map)
    await state.set_state(BookingStates.choose_slot)
    await callback.message.answer(
        tr(client.locale, "choose_slot"),
        reply_markup=slots_keyboard(slots, container.settings.salon_timezone),
    )
    await _send_next_step(callback.message, client.locale, "next_step_choose_slot")
    await callback.answer()


@router.callback_query(F.data.startswith("slot:"))
async def cb_slot(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if callback.from_user is None:
        return

    client = await get_client_from_user(callback.from_user, repo, container)
    data = await state.get_data()
    slot_map = data.get("slot_map") or {}
    slot_id = callback.data.split(":", maxsplit=1)[1]
    slot_data = slot_map.get(slot_id)
    if slot_data is None:
        await callback.answer("Slot expired. Re-open date", show_alert=True)
        return

    service_id = int(data["service_id"])
    barber_id = int(data["barber_id"])

    draft_id = uuid4().hex[:12]
    draft_payload = {
        "client_tg_user_id": callback.from_user.id,
        "service_id": service_id,
        "barber_id": barber_id,
        "starts_at_utc": slot_data["starts_at_utc"],
        "ends_at_utc": slot_data["ends_at_utc"],
    }
    await save_draft(container.redis, draft_id, draft_payload, container.settings.draft_ttl_seconds)
    await state.set_state(BookingStates.confirm)

    start = datetime.fromisoformat(slot_data["starts_at_utc"])
    text = tr(
        client.locale,
        "confirm_booking",
        date_time=format_booking_local(start, container.settings.salon_timezone),
    )
    await callback.message.answer(text, reply_markup=confirm_keyboard(draft_id))
    await _send_next_step(callback.message, client.locale, "next_step_confirm")
    await callback.answer()


@router.callback_query(F.data.startswith("confirm:"))
async def cb_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    if callback.from_user is None:
        return

    draft_id = callback.data.split(":", maxsplit=1)[1]
    payload = await get_draft(container.redis, draft_id)
    if payload is None:
        await callback.answer("Draft expired. Please restart /book", show_alert=True)
        return
    if payload["client_tg_user_id"] != callback.from_user.id:
        await callback.answer("Forbidden", show_alert=True)
        return

    client = await get_client_from_user(callback.from_user, repo, container)
    starts_at_utc = datetime.fromisoformat(payload["starts_at_utc"])
    ends_at_utc = datetime.fromisoformat(payload["ends_at_utc"])

    window = BookingWindow(
        min_lead_hours=container.settings.booking_min_lead_hours,
        max_days=container.settings.booking_max_days,
    )
    if not validate_booking_window(starts_at_utc, datetime.now(UTC), window):
        await callback.answer("Slot no longer valid", show_alert=True)
        return

    booking = await repo.create_confirmed_booking(
        client_id=client.id,
        barber_id=int(payload["barber_id"]),
        service_id=int(payload["service_id"]),
        starts_at_utc=starts_at_utc,
        ends_at_utc=ends_at_utc,
    )
    if booking is None:
        await session.rollback()
        await callback.message.answer(tr(client.locale, "booking_conflict_refresh"))
        service = await repo.get_service(int(payload["service_id"]))
        if service is not None:
            days = await _available_days(
                repo=repo,
                barber_id=int(payload["barber_id"]),
                duration_min=service.duration_min,
                container=container,
            )
            await state.set_state(BookingStates.choose_date)
            if not days:
                await callback.message.answer(
                    tr(client.locale, "no_available_dates"),
                    reply_markup=no_slots_back_keyboard(client.locale),
                )
            else:
                await callback.message.answer(
                    tr(client.locale, "choose_date"),
                    reply_markup=dates_keyboard(days),
                )
            await _send_next_step(callback.message, client.locale, "next_step_choose_date")
        await callback.answer()
        return

    await repo.create_reminder_jobs_for_booking(booking)
    await session.commit()

    dt = format_booking_local(booking.starts_at_utc, container.settings.salon_timezone)
    await callback.message.answer(tr(client.locale, "booked", date_time=dt))
    await notify_admin_group(
        container,
        f"[NEW] booking_id={booking.id} user={callback.from_user.id} start={dt}",
    )

    await state.clear()
    await _send_next_step(callback.message, client.locale, "next_step_back_menu")
    await callback.answer()


@router.message(Command("my_bookings"))
@router.message(Command("cancel"))
async def cmd_my_bookings(
    message: Message,
    repo: Repository,
    container: AppContainer,
) -> None:
    client = await get_client_context(message, repo, container)
    bookings = await repo.list_future_bookings_for_client(client.id)
    if not bookings:
        await message.answer(tr(client.locale, "no_future_bookings"))
        return

    await message.answer(tr(client.locale, "future_bookings"))
    for booking in bookings:
        barber = await repo.get_barber(booking.barber_id)
        service = await repo.get_service(booking.service_id) if booking.service_id else None
        service_name = "-"
        if service is not None:
            service_name = service.name_ru if client.locale == "ru" else service.name_uz
        start_local = format_booking_local(booking.starts_at_utc, container.settings.salon_timezone)
        text = (
            f"#{booking.id} | {start_local}\n"
            f"Barber: {barber.name if barber else '-'}\n"
            f"Service: {service_name}"
        )
        await message.answer(text, reply_markup=cancel_keyboard(booking.id))
    await _send_next_step(message, client.locale, "next_step_back_menu")


@router.callback_query(F.data.startswith("cancel_booking:"))
async def cb_cancel_booking(
    callback: CallbackQuery,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    if callback.from_user is None:
        return

    client = await get_client_from_user(callback.from_user, repo, container)
    booking_id = int(callback.data.split(":", maxsplit=1)[1])
    booking = await repo.get_booking_for_client(booking_id, client.id)
    if booking is None or booking.status != "confirmed":
        await callback.message.answer(tr(client.locale, "booking_not_found"))
        await callback.answer()
        return

    if not can_cancel_booking(
        booking.starts_at_utc,
        datetime.now(UTC),
        container.settings.cancel_min_lead_hours,
    ):
        await callback.message.answer(tr(client.locale, "cancel_too_late"))
        await callback.answer()
        return

    await repo.cancel_booking(booking)
    await session.commit()

    await callback.message.answer(tr(client.locale, "cancelled"))
    dt = format_booking_local(booking.starts_at_utc, container.settings.salon_timezone)
    await notify_admin_group(
        container,
        f"[CANCEL] booking_id={booking.id} user={callback.from_user.id} start={dt}",
    )
    await _send_next_step(callback.message, client.locale, "next_step_back_menu")
    await callback.answer()
