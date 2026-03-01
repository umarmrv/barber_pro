from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from barber_bot.bot.keyboards import (
    admin_menu_texts,
    admin_back_menu_keyboard,
    admin_booking_barbers_keyboard,
    admin_booking_clients_keyboard,
    admin_booking_confirm_keyboard,
    admin_booking_stats_calendar_keyboard,
    admin_booking_dates_keyboard,
    admin_booking_delete_confirm_keyboard,
    admin_booking_delete_list_keyboard,
    admin_booking_stats_menu_keyboard,
    admin_booking_stats_result_keyboard,
    admin_booking_services_keyboard,
    admin_booking_slots_keyboard,
    admin_visit_actions_keyboard,
    admin_visits_list_keyboard,
    admin_barber_actions_keyboard,
    admin_barbers_keyboard,
    admin_confirm_barber_delete_keyboard,
    admin_confirm_service_delete_keyboard,
    admin_main_keyboard,
    admin_main_reply_keyboard,
    admin_service_actions_keyboard,
    admin_services_keyboard,
    admin_shift_weekday_keyboard,
    admin_shifts_keyboard,
    admin_visits_calendar_keyboard,
)
from barber_bot.bot.states import AdminStates
from barber_bot.bot.utils import get_client_context, get_client_from_user
from barber_bot.container import AppContainer
from barber_bot.db.models import BookingStatus, WorkShift
from barber_bot.db.repositories import Repository, TodayBookingDetailed, service_name_by_locale
from barber_bot.i18n import tr
from barber_bot.services.booking import BookingWindow, format_booking_local, validate_booking_window
from barber_bot.services.drafts import get_draft, save_draft
from barber_bot.services.export_xlsx import build_booking_stats_filename, build_booking_stats_workbook_bytes
from barber_bot.services.phone import normalize_phone
from barber_bot.services.slots import generate_slots

router = Router(name="admin")

_WEEKDAY_LABELS: dict[str, list[str]] = {
    "ru": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
    "uz": ["Ду", "Се", "Чор", "Пай", "Жу", "Шан", "Як"],
    "tj": ["Дш", "Сш", "Чш", "Пш", "Ҷм", "Шн", "Як"],
}


def _parse_bool_on_off(value: str) -> bool | None:
    value = value.strip().lower()
    if value == "on":
        return True
    if value == "off":
        return False
    return None


def _parse_time_range(value: str) -> tuple[time, time] | None:
    raw = value.strip()
    if "-" not in raw:
        return None
    start_raw, end_raw = raw.split("-", maxsplit=1)
    try:
        start = time.fromisoformat(start_raw.strip())
        end = time.fromisoformat(end_raw.strip())
    except ValueError:
        return None
    return start, end


def _is_off_token(value: str) -> bool:
    return value.strip().lower() in {
        "off",
        "-",
        "none",
        "closed",
        "dayoff",
        "выходной",
        "yoq",
    }


def _format_weekly_rows(locale: str, shifts: list[WorkShift]) -> str:
    grouped: dict[int, list[str]] = {}
    for shift in shifts:
        grouped.setdefault(int(shift.weekday), []).append(
            f"{shift.start_local_time.strftime('%H:%M')}-{shift.end_local_time.strftime('%H:%M')}"
        )

    lines: list[str] = []
    for weekday in range(7):
        intervals = grouped.get(weekday, [])
        intervals_text = ",".join(intervals) if intervals else "off"
        lines.append(f"{weekday + 1} {intervals_text}")
    return "\n".join(lines)


def _parse_weekday_token(value: str) -> int | None:
    raw = value.strip()
    try:
        weekday_number = int(raw)
    except ValueError:
        weekday_number = None

    if weekday_number is not None:
        if weekday_number < 1 or weekday_number > 7:
            return None
        return (weekday_number - 1) % 7

    normalized = raw.casefold()
    for labels in _WEEKDAY_LABELS.values():
        for weekday, label in enumerate(labels):
            if normalized == label.casefold():
                return weekday
    return None


def _parse_weekly_schedule(
    text: str,
) -> tuple[dict[int, list[tuple[time, time]]] | None, str | None]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None, "invalid"

    parsed: dict[int, list[tuple[time, time]]] = {}
    for line in lines:
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            return None, "invalid"

        day_raw, intervals_raw = parts
        weekday = _parse_weekday_token(day_raw)
        if weekday is None:
            return None, "invalid"
        if weekday in parsed:
            return None, "invalid"

        intervals_text = intervals_raw.strip()
        if _is_off_token(intervals_text):
            parsed[weekday] = []
            continue

        intervals: list[tuple[time, time]] = []
        for raw_interval in intervals_text.split(","):
            parsed_interval = _parse_time_range(raw_interval.strip())
            if parsed_interval is None:
                return None, "invalid"
            start_local, end_local = parsed_interval
            if start_local >= end_local:
                return None, "invalid"
            intervals.append((start_local, end_local))

        intervals.sort(key=lambda item: item[0])
        for index in range(1, len(intervals)):
            prev_start, prev_end = intervals[index - 1]
            curr_start, _ = intervals[index]
            if curr_start < prev_end:
                return None, "invalid"
            if prev_start == curr_start:
                return None, "invalid"

        parsed[weekday] = intervals

    if set(parsed.keys()) != set(range(7)):
        return None, "missing_days"

    return parsed, None


async def _replace_barber_weekly_schedule(
    repo: Repository,
    barber_id: int,
    weekly_schedule: dict[int, list[tuple[time, time]]],
) -> bool:
    existing_shifts = await repo.list_work_shifts(barber_id)
    for shift in existing_shifts:
        deleted = await repo.delete_work_shift(shift.id)
        if not deleted:
            return False

    for weekday in range(7):
        intervals = weekly_schedule.get(weekday, [])
        for start_local, end_local in intervals:
            shift = await repo.create_work_shift(
                barber_id=barber_id,
                weekday=weekday,
                start_local_time=start_local,
                end_local_time=end_local,
            )
            if shift is None:
                return False

    return True


def _weekday_label(locale: str, weekday: int) -> str:
    lang = locale if locale in _WEEKDAY_LABELS else "ru"
    labels = _WEEKDAY_LABELS[lang]
    if weekday < 0 or weekday >= len(labels):
        return str(weekday)
    return labels[weekday]


def _next_step(locale: str, step_key: str) -> str:
    return tr(locale, "next_step_hint", value=tr(locale, step_key))


async def _admin_slots_for_day(
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


async def _admin_available_days(
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
        slots = await _admin_slots_for_day(
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


async def _check_admin(message: Message, repo: Repository, container: AppContainer) -> tuple[bool, str]:
    if message.from_user is None:
        return False, "ru"
    client = await get_client_context(message, repo, container)
    is_admin = await repo.is_admin(message.from_user.id, container.settings.admin_ids)
    if not is_admin:
        await message.answer(tr(client.locale, "admin_only"))
        return False, client.locale
    return True, client.locale


async def _check_admin_callback(
    callback: CallbackQuery,
    repo: Repository,
    container: AppContainer,
) -> tuple[bool, str]:
    if callback.from_user is None:
        return False, "ru"
    client = await get_client_from_user(callback.from_user, repo, container)
    is_admin = await repo.is_admin(callback.from_user.id, container.settings.admin_ids)
    if not is_admin:
        await callback.answer(tr(client.locale, "admin_only"), show_alert=True)
        return False, client.locale
    return True, client.locale


async def _show_admin_menu(message: Message, locale: str) -> None:
    await message.answer(
        tr(locale, "admin_menu_title"),
        reply_markup=admin_main_keyboard(locale),
    )
    await message.answer(
        _next_step(locale, "next_step_admin_menu"),
        reply_markup=admin_main_reply_keyboard(locale),
    )


def _booking_username(booking: TodayBookingDetailed) -> str:
    if booking.client_tg_username:
        return f"@{booking.client_tg_username}"
    if booking.client_tg_user_id:
        return str(booking.client_tg_user_id)
    return "-"


def _booking_service_name(locale: str, booking: TodayBookingDetailed) -> str:
    return service_name_by_locale(
        locale,
        name_ru=booking.service_name_ru,
        name_uz=booking.service_name_uz,
        name_tj=booking.service_name_tj,
    )


def _booking_status(locale: str, status: str) -> str:
    key = f"booking_status_{status}"
    value = tr(locale, key)
    return status if value == key else value


def _booking_detail_row(
    *,
    locale: str,
    booking: TodayBookingDetailed,
    tz_name: str,
    with_date: bool,
) -> str:
    fmt = "%d.%m %H:%M" if with_date else "%H:%M"
    local_time = booking.starts_at_utc.astimezone(ZoneInfo(tz_name)).strftime(fmt)
    return tr(
        locale,
        "admin_today_row",
        booking_id=booking.booking_id,
        time=local_time,
        status=_booking_status(locale, booking.status),
        barber=booking.barber_name or "-",
        service=_booking_service_name(locale, booking),
        username=_booking_username(booking),
        phone=booking.client_phone_e164 or "-",
    )


def _chunk_booking_rows(rows: list[str], *, max_chars: int = 3500) -> list[str]:
    if not rows:
        return []

    chunks: list[str] = []
    current = ""
    for row in rows:
        candidate = row if not current else f"{current}\n\n{row}"
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = row
            continue
        current = candidate

    if current:
        chunks.append(current)
    return chunks


async def _answer_booking_rows(
    *,
    message: Message,
    locale: str,
    title_key: str,
    rows: list[str],
    reply_markup=None,
) -> None:
    chunks = _chunk_booking_rows(rows)
    if not chunks:
        return

    first_text = tr(locale, title_key, rows=chunks[0])
    if reply_markup is None:
        await message.answer(first_text)
    else:
        await message.answer(first_text, reply_markup=reply_markup)

    for chunk in chunks[1:]:
        await message.answer(chunk)


def _period_bounds_utc(
    *,
    tz_name: str,
    local_start_day: date,
    local_end_day_exclusive: date,
) -> tuple[datetime, datetime]:
    day_start_local = datetime.combine(local_start_day, datetime.min.time(), ZoneInfo(tz_name))
    day_end_local = datetime.combine(local_end_day_exclusive, datetime.min.time(), ZoneInfo(tz_name))
    return day_start_local.astimezone(UTC), day_end_local.astimezone(UTC)


def _parse_year_month(raw: str) -> tuple[int, int] | None:
    try:
        year_str, month_str = raw.strip().split("-", maxsplit=1)
        year = int(year_str)
        month = int(month_str)
    except (ValueError, AttributeError):
        return None
    if year < 1970 or year > 2100:
        return None
    if month < 1 or month > 12:
        return None
    return year, month


def _status_counters(bookings: list[TodayBookingDetailed]) -> tuple[int, int, int, int]:
    confirmed = sum(1 for booking in bookings if booking.status == "confirmed")
    completed = sum(1 for booking in bookings if booking.status == "completed")
    cancelled = sum(1 for booking in bookings if booking.status == "cancelled")
    blocked = sum(1 for booking in bookings if booking.status == "blocked")
    return confirmed, completed, cancelled, blocked


def _format_tjs(amount_minor: int) -> str:
    return f"{amount_minor / 100:.2f}"


async def _load_stats_period_data(
    *,
    repo: Repository,
    container: AppContainer,
    local_start_day: date,
    local_end_day_exclusive: date,
) -> tuple[list[TodayBookingDetailed], str, str, int]:
    starts_from_utc, starts_to_utc = _period_bounds_utc(
        tz_name=container.settings.salon_timezone,
        local_start_day=local_start_day,
        local_end_day_exclusive=local_end_day_exclusive,
    )
    bookings = await repo.list_bookings_detailed_for_range(
        starts_from_utc=starts_from_utc,
        starts_to_utc=starts_to_utc,
        include_statuses=(
            BookingStatus.CONFIRMED.value,
            BookingStatus.COMPLETED.value,
            BookingStatus.BLOCKED.value,
            BookingStatus.CANCELLED.value,
        ),
    )
    cash_total_minor = await repo.sum_cash_for_range(
        starts_from_utc=starts_from_utc,
        starts_to_utc=starts_to_utc,
        include_statuses=(BookingStatus.COMPLETED.value,),
    )
    from_date = local_start_day.strftime("%d.%m.%Y")
    to_date = (local_end_day_exclusive - timedelta(days=1)).strftime("%d.%m.%Y")
    return bookings, from_date, to_date, cash_total_minor


async def _show_booking_stats_for_period(
    *,
    message: Message,
    repo: Repository,
    container: AppContainer,
    locale: str,
    local_start_day: date,
    local_end_day_exclusive: date,
    export_callback: str,
) -> None:
    bookings, from_date, to_date, cash_total_minor = await _load_stats_period_data(
        repo=repo,
        container=container,
        local_start_day=local_start_day,
        local_end_day_exclusive=local_end_day_exclusive,
    )
    result_keyboard = admin_booking_stats_result_keyboard(locale, export_callback)

    if not bookings:
        await message.answer(
            tr(locale, "admin_booking_stats_empty", from_date=from_date, to_date=to_date),
            reply_markup=result_keyboard,
        )
        await message.answer(_next_step(locale, "next_step_choose_stats"))
        return

    confirmed, completed, cancelled, blocked = _status_counters(bookings)
    await message.answer(
        tr(
            locale,
            "admin_booking_stats_summary",
            from_date=from_date,
            to_date=to_date,
            total=len(bookings),
            confirmed=confirmed,
            completed=completed,
            cancelled=cancelled,
            blocked=blocked,
            cash_total=_format_tjs(cash_total_minor),
        ),
        reply_markup=result_keyboard,
    )

    rows = [
        _booking_detail_row(
            locale=locale,
            booking=booking,
            tz_name=container.settings.salon_timezone,
            with_date=True,
        )
        for booking in bookings
    ]
    await _answer_booking_rows(
        message=message,
        locale=locale,
        title_key="admin_booking_stats_rows",
        rows=rows,
    )
    await message.answer(_next_step(locale, "next_step_choose_stats"))


async def _send_stats_export_for_period(
    *,
    message: Message,
    repo: Repository,
    container: AppContainer,
    locale: str,
    mode: str,
    local_start_day: date,
    local_end_day_exclusive: date,
) -> None:
    bookings, from_date, to_date, cash_total_minor = await _load_stats_period_data(
        repo=repo,
        container=container,
        local_start_day=local_start_day,
        local_end_day_exclusive=local_end_day_exclusive,
    )
    confirmed, completed, cancelled, blocked = _status_counters(bookings)

    try:
        file_bytes = build_booking_stats_workbook_bytes(
            locale=locale,
            tz_name=container.settings.salon_timezone,
            period_from_local=local_start_day,
            period_to_local=local_end_day_exclusive - timedelta(days=1),
            total=len(bookings),
            confirmed=confirmed,
            completed=completed,
            cancelled=cancelled,
            blocked=blocked,
            cash_total_minor=cash_total_minor,
            bookings=bookings,
        )
    except Exception:
        await message.answer(tr(locale, "admin_export_failed"))
        await message.answer(_next_step(locale, "next_step_choose_stats"))
        return

    now_local = datetime.now(ZoneInfo(container.settings.salon_timezone))
    filename = build_booking_stats_filename(
        mode=mode,
        now_local=now_local,
        local_day=local_start_day if mode == "date" else None,
    )
    input_file = BufferedInputFile(file_bytes, filename=filename)
    await message.answer_document(
        input_file,
        caption=tr(
            locale,
            "admin_export_done",
            from_date=from_date,
            to_date=to_date,
            total=len(bookings),
            cash_total=_format_tjs(cash_total_minor),
        ),
    )
    await message.answer(_next_step(locale, "next_step_choose_stats"))


def _visit_label_for_list(
    *,
    locale: str,
    booking: TodayBookingDetailed,
    tz_name: str,
) -> str:
    local_time = booking.starts_at_utc.astimezone(ZoneInfo(tz_name)).strftime("%H:%M")
    client = _booking_username(booking)
    if client == "-":
        client = booking.client_phone_e164 or "-"
    label = (
        f"#{booking.booking_id} {local_time} | "
        f"{_booking_status(locale, booking.status)} | "
        f"{client}"
    )
    if len(label) > 64:
        return f"{label[:61]}..."
    return label


def _visit_local_day_from_starts(starts_at_utc: datetime, tz_name: str) -> date:
    return starts_at_utc.astimezone(ZoneInfo(tz_name)).date()


def _parse_visit_booking_callback(raw: str, action: str) -> tuple[int, date | None] | None:
    parts = raw.split(":")
    if len(parts) not in {4, 5}:
        return None
    if parts[:3] != ["admin", "visit", action]:
        return None
    try:
        booking_id = int(parts[3])
    except ValueError:
        return None
    if len(parts) == 4:
        return booking_id, None
    try:
        local_day = date.fromisoformat(parts[4])
    except ValueError:
        return None
    return booking_id, local_day


async def _show_visits_today_list(
    message: Message,
    repo: Repository,
    container: AppContainer,
    locale: str,
) -> None:
    today_local = datetime.now(ZoneInfo(container.settings.salon_timezone)).date()
    await message.answer(
        tr(locale, "admin_visits_pick_date"),
        reply_markup=admin_visits_calendar_keyboard(
            locale,
            year=today_local.year,
            month=today_local.month,
        ),
    )
    await message.answer(tr(locale, "admin_visits_enter_date"))
    await message.answer(_next_step(locale, "next_step_pick_calendar_date"))


async def _show_visits_for_local_day(
    message: Message,
    repo: Repository,
    container: AppContainer,
    locale: str,
    local_day: date,
) -> None:
    starts_from_utc, starts_to_utc = _period_bounds_utc(
        tz_name=container.settings.salon_timezone,
        local_start_day=local_day,
        local_end_day_exclusive=local_day + timedelta(days=1),
    )
    bookings = await repo.list_bookings_detailed_for_range(
        starts_from_utc=starts_from_utc,
        starts_to_utc=starts_to_utc,
        include_statuses=(
            BookingStatus.CONFIRMED.value,
            BookingStatus.COMPLETED.value,
            BookingStatus.BLOCKED.value,
            BookingStatus.CANCELLED.value,
        ),
    )

    formatted_day = local_day.strftime("%d.%m.%Y")
    if not bookings:
        await message.answer(
            tr(locale, "admin_visits_empty", date=formatted_day),
            reply_markup=admin_visits_calendar_keyboard(
                locale,
                year=local_day.year,
                month=local_day.month,
            ),
        )
        await message.answer(_next_step(locale, "next_step_pick_calendar_date"))
        return

    await message.answer(tr(locale, "admin_visits_title", date=formatted_day))
    rows = [
        (
            booking.booking_id,
            _visit_label_for_list(
                locale=locale,
                booking=booking,
                tz_name=container.settings.salon_timezone,
            ),
        )
        for booking in bookings
    ]
    await message.answer(
        tr(locale, "admin_visits_choose"),
        reply_markup=admin_visits_list_keyboard(rows, locale, local_day),
    )
    await message.answer(_next_step(locale, "next_step_visit_pick"))


async def _show_visit_booking_card(
    message: Message,
    repo: Repository,
    container: AppContainer,
    locale: str,
    booking_id: int,
    local_day: date | None = None,
) -> bool:
    booking = await repo.get_booking_detailed(booking_id)
    if booking is None:
        await message.answer(tr(locale, "admin_booking_not_found"))
        return False

    effective_local_day = local_day or _visit_local_day_from_starts(
        booking.starts_at_utc,
        container.settings.salon_timezone,
    )

    start_local = booking.starts_at_utc.astimezone(ZoneInfo(container.settings.salon_timezone)).strftime(
        "%d.%m %H:%M"
    )
    await message.answer(
        tr(
            locale,
            "admin_visit_card",
            booking_id=booking.booking_id,
            time=start_local,
            status=_booking_status(locale, booking.status),
            barber=booking.barber_name or "-",
            service=_booking_service_name(locale, booking),
            username=_booking_username(booking),
            phone=booking.client_phone_e164 or "-",
        ),
        reply_markup=admin_visit_actions_keyboard(
            booking.booking_id,
            booking.status,
            locale,
            effective_local_day,
        ),
    )
    await message.answer(_next_step(locale, "next_step_visit_action"))
    return True


async def _show_booking_stats_menu(message: Message, locale: str) -> None:
    await message.answer(
        tr(locale, "admin_booking_stats_choose"),
        reply_markup=admin_booking_stats_menu_keyboard(locale),
    )
    await message.answer(_next_step(locale, "next_step_choose_stats"))


async def _show_today_bookings(message: Message, repo: Repository, container: AppContainer, locale: str) -> None:
    bookings = await repo.list_monitoring_bookings_detailed(
        container.settings.salon_timezone,
        days=container.settings.booking_max_days,
    )
    today_local = datetime.now(ZoneInfo(container.settings.salon_timezone)).date()
    today_starts_utc, today_ends_utc = _period_bounds_utc(
        tz_name=container.settings.salon_timezone,
        local_start_day=today_local,
        local_end_day_exclusive=today_local + timedelta(days=1),
    )
    today_cash_minor = await repo.sum_cash_for_range(
        starts_from_utc=today_starts_utc,
        starts_to_utc=today_ends_utc,
        include_statuses=(BookingStatus.COMPLETED.value,),
    )
    await message.answer(
        tr(locale, "admin_today_cash_summary", cash_total=_format_tjs(today_cash_minor)),
        reply_markup=admin_back_menu_keyboard(locale),
    )
    if not bookings:
        await message.answer(tr(locale, "admin_today_empty"))
        await message.answer(_next_step(locale, "next_step_admin_menu"))
        return

    rows = [
        _booking_detail_row(
            locale=locale,
            booking=booking,
            tz_name=container.settings.salon_timezone,
            with_date=True,
        )
        for booking in bookings
    ]
    await _answer_booking_rows(
        message=message,
        locale=locale,
        title_key="admin_today",
        rows=rows,
        reply_markup=admin_back_menu_keyboard(locale),
    )
    await message.answer(_next_step(locale, "next_step_back_menu"))


async def _show_barbers_list(message: Message, repo: Repository, locale: str) -> None:
    barbers = await repo.list_barbers(include_inactive=True)
    await message.answer(
        tr(locale, "admin_barbers_title"),
        reply_markup=admin_barbers_keyboard(barbers, locale),
    )
    await message.answer(_next_step(locale, "next_step_back_menu"))


async def _show_barber_details(message: Message, repo: Repository, locale: str, barber_id: int) -> bool:
    barber = await repo.get_barber(barber_id)
    if barber is None:
        await message.answer(tr(locale, "admin_item_not_found"))
        return False

    status_key = "admin_status_active" if barber.is_active else "admin_status_inactive"
    await message.answer(
        tr(locale, "admin_barber_card", name=barber.name, status=tr(locale, status_key)),
        reply_markup=admin_barber_actions_keyboard(barber.id, barber.is_active, locale),
    )
    return True


async def _show_barber_shifts(message: Message, repo: Repository, locale: str, barber_id: int) -> bool:
    barber = await repo.get_barber(barber_id)
    if barber is None:
        await message.answer(tr(locale, "admin_item_not_found"))
        return False

    shifts = await repo.list_work_shifts(barber_id)
    if not shifts:
        rows = "-"
    else:
        rows = "\n".join(
            (
                f"#{shift.id} "
                f"{_weekday_label(locale, shift.weekday)} "
                f"{shift.start_local_time.strftime('%H:%M')}-"
                f"{shift.end_local_time.strftime('%H:%M')}"
            )
            for shift in shifts
        )

    await message.answer(
        tr(locale, "admin_shift_list", barber_name=barber.name, rows=rows),
        reply_markup=admin_shifts_keyboard(barber_id, shifts, locale),
    )
    await message.answer(
        tr(locale, "admin_shift_choose_weekday"),
        reply_markup=admin_shift_weekday_keyboard(barber_id, locale),
    )
    return True


async def _show_services_list(message: Message, repo: Repository, locale: str) -> None:
    services = await repo.list_services(include_inactive=True)
    await message.answer(
        tr(locale, "admin_services_title"),
        reply_markup=admin_services_keyboard(services, locale),
    )
    await message.answer(_next_step(locale, "next_step_back_menu"))


async def _show_service_details(message: Message, repo: Repository, locale: str, service_id: int) -> bool:
    service = await repo.get_service(service_id)
    if service is None:
        await message.answer(tr(locale, "admin_item_not_found"))
        return False

    status_key = "admin_status_active" if service.is_active else "admin_status_inactive"
    name = service_name_by_locale(
        locale,
        name_ru=service.name_ru,
        name_uz=service.name_uz,
        name_tj=service.name_tj,
    )
    await message.answer(
        tr(
            locale,
            "admin_service_card",
            name=name,
            duration=service.duration_min,
            price=service.price_minor,
            status=tr(locale, status_key),
        ),
        reply_markup=admin_service_actions_keyboard(service.id, service.is_active, locale),
    )
    return True


def _booking_label_for_delete(
    *,
    locale: str,
    booking_id: int,
    starts_at_utc: datetime,
    tz_name: str,
    status: str,
    barber: str | None,
    service: str | None,
    username: str,
    phone: str | None,
) -> str:
    local_time = starts_at_utc.astimezone(ZoneInfo(tz_name)).strftime("%d.%m %H:%M")
    client = username if username != "-" else (phone or "-")
    label = (
        f"#{booking_id} {local_time} | "
        f"{barber or '-'} | "
        f"{service or '-'} | "
        f"{client} | "
        f"{_booking_status(locale, status)}"
    )
    if len(label) > 64:
        return f"{label[:61]}..."
    return label


async def _show_admin_delete_booking_list(
    message: Message,
    repo: Repository,
    container: AppContainer,
    locale: str,
) -> None:
    bookings_all = await repo.list_monitoring_bookings_detailed(
        container.settings.salon_timezone,
        days=container.settings.booking_max_days,
    )
    bookings = [b for b in bookings_all if b.status != BookingStatus.COMPLETED.value]
    if not bookings:
        await message.answer(
            tr(locale, "admin_booking_delete_no_deletable"),
            reply_markup=admin_back_menu_keyboard(locale),
        )
        await message.answer(_next_step(locale, "next_step_back_menu"))
        return

    detail_rows = [
        _booking_detail_row(
            locale=locale,
            booking=row,
            tz_name=container.settings.salon_timezone,
            with_date=True,
        )
        for row in bookings
    ]
    await _answer_booking_rows(
        message=message,
        locale=locale,
        title_key="admin_booking_delete_details",
        rows=detail_rows,
    )

    labels = [
        (
            row.booking_id,
            _booking_label_for_delete(
                locale=locale,
                booking_id=row.booking_id,
                starts_at_utc=row.starts_at_utc,
                tz_name=container.settings.salon_timezone,
                status=row.status,
                barber=row.barber_name,
                service=_booking_service_name(locale, row),
                username=_booking_username(row),
                phone=row.client_phone_e164,
            ),
        )
        for row in bookings
    ]
    await message.answer(
        tr(locale, "admin_booking_delete_choose"),
        reply_markup=admin_booking_delete_list_keyboard(labels, locale),
    )
    await message.answer(_next_step(locale, "next_step_delete_pick"))


@router.message(Command("admin"))
async def cmd_admin(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    await state.set_state(AdminStates.menu)
    await state.update_data(admin_edit_barber_id=None, admin_edit_service_id=None)
    await _show_admin_menu(message, locale)


@router.message(F.text.in_(admin_menu_texts("bookings_today")))
async def menu_admin_bookings_today(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return
    await state.set_state(AdminStates.menu)
    await _show_booking_stats_menu(message, locale)


@router.message(F.text.in_(admin_menu_texts("visits_today")))
async def menu_admin_visits_today(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return
    await state.set_state(AdminStates.visit_date_input)
    await _show_visits_today_list(message, repo, container, locale)


@router.message(F.text.in_(admin_menu_texts("booking_add")))
async def menu_admin_booking_add(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return
    await state.set_state(AdminStates.booking_create_phone)
    await message.answer(
        tr(locale, "admin_booking_add_phone"),
        reply_markup=admin_back_menu_keyboard(locale),
    )
    await message.answer(_next_step(locale, "next_step_enter_phone"))


@router.message(F.text.in_(admin_menu_texts("booking_delete")))
async def menu_admin_booking_delete(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return
    await state.set_state(AdminStates.booking_delete_select)
    await _show_admin_delete_booking_list(message, repo, container, locale)


@router.message(F.text.in_(admin_menu_texts("barbers")))
async def menu_admin_barbers(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return
    await state.set_state(AdminStates.menu)
    await state.update_data(admin_edit_barber_id=None)
    await _show_barbers_list(message, repo, locale)


@router.message(F.text.in_(admin_menu_texts("services")))
async def menu_admin_services(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return
    await state.set_state(AdminStates.menu)
    await state.update_data(admin_edit_service_id=None)
    await _show_services_list(message, repo, locale)


@router.callback_query(F.data == "admin:menu")
async def cb_admin_menu(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    await state.set_state(AdminStates.menu)
    await state.update_data(admin_edit_barber_id=None, admin_edit_service_id=None)
    await _show_admin_menu(callback.message, locale)
    await callback.answer()


@router.callback_query(F.data == "admin:today")
async def cb_admin_today(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    await state.set_state(AdminStates.menu)
    await _show_today_bookings(callback.message, repo, container, locale)
    await callback.answer()


@router.callback_query(F.data == "admin:booking:list:today")
async def cb_admin_booking_stats_menu(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    await state.set_state(AdminStates.menu)
    await _show_booking_stats_menu(callback.message, locale)
    await callback.answer()


@router.callback_query(F.data == "admin:booking:stats:horizon")
async def cb_admin_booking_stats_horizon(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    today_local = datetime.now(ZoneInfo(container.settings.salon_timezone)).date()
    await state.set_state(AdminStates.menu)
    await _show_booking_stats_for_period(
        message=callback.message,
        repo=repo,
        container=container,
        locale=locale,
        local_start_day=today_local,
        local_end_day_exclusive=today_local + timedelta(days=container.settings.booking_max_days + 1),
        export_callback="admin:booking:stats:export:horizon",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:booking:stats:week")
async def cb_admin_booking_stats_week(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    today_local = datetime.now(ZoneInfo(container.settings.salon_timezone)).date()
    await state.set_state(AdminStates.menu)
    await _show_booking_stats_for_period(
        message=callback.message,
        repo=repo,
        container=container,
        locale=locale,
        local_start_day=today_local,
        local_end_day_exclusive=today_local + timedelta(days=7),
        export_callback="admin:booking:stats:export:week",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:booking:stats:date")
async def cb_admin_booking_stats_date(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    today_local = datetime.now(ZoneInfo(container.settings.salon_timezone)).date()
    await state.set_state(AdminStates.booking_stats_date_input)
    await callback.message.answer(
        tr(locale, "admin_booking_stats_pick_date"),
        reply_markup=admin_booking_stats_calendar_keyboard(
            locale,
            year=today_local.year,
            month=today_local.month,
        ),
    )
    await callback.message.answer(_next_step(locale, "next_step_pick_calendar_date"))
    await callback.answer()


@router.message(AdminStates.booking_stats_date_input)
async def on_admin_booking_stats_date_input(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if message.text is None:
        return
    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    try:
        local_day = date.fromisoformat(message.text.strip())
    except ValueError:
        await message.answer(tr(locale, "admin_booking_stats_invalid_date"))
        await message.answer(_next_step(locale, "next_step_enter_stats_date"))
        return

    await state.set_state(AdminStates.menu)
    await _show_booking_stats_for_period(
        message=message,
        repo=repo,
        container=container,
        locale=locale,
        local_start_day=local_day,
        local_end_day_exclusive=local_day + timedelta(days=1),
        export_callback=f"admin:booking:stats:export:date:{local_day.isoformat()}",
    )


@router.callback_query(F.data == "admin:noop")
async def cb_admin_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("admin:booking:stats:date:month:"))
async def cb_admin_booking_stats_date_month(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    parsed = _parse_year_month(callback.data.split(":")[-1])
    if parsed is None:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return
    year, month = parsed

    await state.set_state(AdminStates.booking_stats_date_input)
    await callback.message.edit_text(
        tr(locale, "admin_booking_stats_pick_date"),
        reply_markup=admin_booking_stats_calendar_keyboard(
            locale,
            year=year,
            month=month,
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:booking:stats:date:pick:"))
async def cb_admin_booking_stats_date_pick(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        local_day = date.fromisoformat(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    await state.set_state(AdminStates.menu)
    await _show_booking_stats_for_period(
        message=callback.message,
        repo=repo,
        container=container,
        locale=locale,
        local_start_day=local_day,
        local_end_day_exclusive=local_day + timedelta(days=1),
        export_callback=f"admin:booking:stats:export:date:{local_day.isoformat()}",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:booking:stats:export:horizon")
async def cb_admin_booking_stats_export_horizon(
    callback: CallbackQuery,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    today_local = datetime.now(ZoneInfo(container.settings.salon_timezone)).date()
    await _send_stats_export_for_period(
        message=callback.message,
        repo=repo,
        container=container,
        locale=locale,
        mode="horizon",
        local_start_day=today_local,
        local_end_day_exclusive=today_local + timedelta(days=container.settings.booking_max_days + 1),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:booking:stats:export:week")
async def cb_admin_booking_stats_export_week(
    callback: CallbackQuery,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    today_local = datetime.now(ZoneInfo(container.settings.salon_timezone)).date()
    await _send_stats_export_for_period(
        message=callback.message,
        repo=repo,
        container=container,
        locale=locale,
        mode="week",
        local_start_day=today_local,
        local_end_day_exclusive=today_local + timedelta(days=7),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:booking:stats:export:date:"))
async def cb_admin_booking_stats_export_date(
    callback: CallbackQuery,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        local_day = date.fromisoformat(callback.data.split(":", maxsplit=5)[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    await _send_stats_export_for_period(
        message=callback.message,
        repo=repo,
        container=container,
        locale=locale,
        mode="date",
        local_start_day=local_day,
        local_end_day_exclusive=local_day + timedelta(days=1),
    )
    await callback.answer()


@router.message(AdminStates.visit_date_input)
async def on_admin_visit_date_input(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if message.text is None:
        return
    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    try:
        local_day = date.fromisoformat(message.text.strip())
    except ValueError:
        await message.answer(tr(locale, "admin_visits_invalid_date"))
        await message.answer(tr(locale, "admin_visits_enter_date"))
        await message.answer(_next_step(locale, "next_step_pick_calendar_date"))
        return

    await state.set_state(AdminStates.menu)
    await _show_visits_for_local_day(message, repo, container, locale, local_day)


@router.callback_query(F.data.startswith("admin:visit:date:month:"))
async def cb_admin_visit_date_month(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    parsed = _parse_year_month(callback.data.split(":")[-1])
    if parsed is None:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return
    year, month = parsed

    await state.set_state(AdminStates.visit_date_input)
    await callback.message.edit_text(
        tr(locale, "admin_visits_pick_date"),
        reply_markup=admin_visits_calendar_keyboard(
            locale,
            year=year,
            month=month,
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:visit:list:date:"))
async def cb_admin_visit_list_date(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        local_day = date.fromisoformat(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    await state.set_state(AdminStates.menu)
    await _show_visits_for_local_day(callback.message, repo, container, locale, local_day)
    await callback.answer()


@router.callback_query(F.data == "admin:visit:list")
async def cb_admin_visit_list(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    await state.set_state(AdminStates.visit_date_input)
    await _show_visits_today_list(callback.message, repo, container, locale)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:visit:pick:"))
async def cb_admin_visit_pick(
    callback: CallbackQuery,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    parsed = _parse_visit_booking_callback(callback.data, "pick")
    if parsed is None:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return
    booking_id, local_day = parsed

    await _show_visit_booking_card(callback.message, repo, container, locale, booking_id, local_day)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:visit:complete:"))
async def cb_admin_visit_complete(
    callback: CallbackQuery,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None or callback.from_user is None:
        return

    parsed = _parse_visit_booking_callback(callback.data, "complete")
    if parsed is None:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return
    booking_id, local_day = parsed

    booking = await repo.get_booking(booking_id)
    if booking is None:
        await callback.message.answer(tr(locale, "admin_booking_not_found"))
        await callback.answer()
        return
    if booking.status != BookingStatus.CONFIRMED.value:
        await callback.message.answer(tr(locale, "admin_visit_action_not_allowed"))
        await callback.answer()
        return

    updated = await repo.set_booking_status(
        booking_id=booking_id,
        new_status=BookingStatus.COMPLETED.value,
        reason="admin_marked_completed",
        actor_tg_user_id=callback.from_user.id,
    )
    if updated is None:
        await session.rollback()
        await callback.message.answer(tr(locale, "admin_visit_action_not_allowed"))
        await callback.answer()
        return

    await session.commit()
    await callback.message.answer(tr(locale, "admin_visit_completed"))
    effective_local_day = local_day or _visit_local_day_from_starts(
        booking.starts_at_utc,
        container.settings.salon_timezone,
    )
    await _show_visit_booking_card(callback.message, repo, container, locale, booking_id, effective_local_day)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:visit:revert:"))
async def cb_admin_visit_revert(
    callback: CallbackQuery,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None or callback.from_user is None:
        return

    parsed = _parse_visit_booking_callback(callback.data, "revert")
    if parsed is None:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return
    booking_id, local_day = parsed

    booking = await repo.get_booking(booking_id)
    if booking is None:
        await callback.message.answer(tr(locale, "admin_booking_not_found"))
        await callback.answer()
        return
    if booking.status != BookingStatus.COMPLETED.value:
        await callback.message.answer(tr(locale, "admin_visit_action_not_allowed"))
        await callback.answer()
        return

    updated = await repo.set_booking_status(
        booking_id=booking_id,
        new_status=BookingStatus.CONFIRMED.value,
        reason="admin_reverted_completed",
        actor_tg_user_id=callback.from_user.id,
    )
    if updated is None:
        await session.rollback()
        await callback.message.answer(tr(locale, "admin_visit_action_not_allowed"))
        await callback.answer()
        return

    await session.commit()
    await callback.message.answer(tr(locale, "admin_visit_reverted"))
    effective_local_day = local_day or _visit_local_day_from_starts(
        booking.starts_at_utc,
        container.settings.salon_timezone,
    )
    await _show_visit_booking_card(callback.message, repo, container, locale, booking_id, effective_local_day)
    await callback.answer()


@router.callback_query(F.data == "admin:booking:add")
@router.callback_query(F.data == "admin:booking:client:phone")
async def cb_admin_booking_add(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return
    await state.set_state(AdminStates.booking_create_phone)
    await callback.message.answer(
        tr(locale, "admin_booking_add_phone"),
        reply_markup=admin_back_menu_keyboard(locale),
    )
    await callback.message.answer(_next_step(locale, "next_step_enter_phone"))
    await callback.answer()


@router.message(AdminStates.booking_create_phone)
async def on_admin_booking_phone(
    message: Message,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    if message.text is None:
        return
    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    normalized = normalize_phone(message.text, container.settings.default_region)
    if normalized is None:
        await message.answer(tr(locale, "invalid_phone"))
        await message.answer(_next_step(locale, "next_step_enter_phone"))
        return

    client = await repo.get_client_by_phone(normalized)
    is_guest = False
    if client is None:
        client = await repo.create_guest_client(normalized, locale)
        is_guest = True
        await message.answer(tr(locale, "admin_booking_client_guest_created", phone=normalized))
    else:
        username = f"@{client.tg_username}" if client.tg_username else "-"
        await message.answer(
            tr(
                locale,
                "admin_booking_client_selected",
                username=username,
                phone=client.phone_e164 or "-",
            )
        )

    await session.commit()
    await state.update_data(
        admin_booking_client_id=client.id,
        admin_booking_is_guest=is_guest,
    )
    await state.set_state(AdminStates.booking_create_choose_client)
    await message.answer(
        tr(locale, "admin_booking_choose_client"),
        reply_markup=admin_booking_clients_keyboard([client], locale),
    )
    await message.answer(_next_step(locale, "next_step_choose_service"))


@router.callback_query(F.data.startswith("admin:booking:client:select:"))
async def cb_admin_booking_choose_client(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        client_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    data = await state.get_data()
    expected_client_id = data.get("admin_booking_client_id")
    if expected_client_id is None or int(expected_client_id) != client_id:
        await callback.answer(tr(locale, "admin_item_not_found"), show_alert=True)
        return

    services = await repo.list_active_services()
    if not services:
        await callback.message.answer(tr(locale, "no_active_services"))
        await callback.answer()
        return

    await state.set_state(AdminStates.booking_create_choose_service)
    await callback.message.answer(
        tr(locale, "admin_booking_choose_service"),
        reply_markup=admin_booking_services_keyboard(services, locale),
    )
    await callback.message.answer(_next_step(locale, "next_step_choose_service"))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:booking:service:"))
async def cb_admin_booking_choose_service(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return
    try:
        service_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    service = await repo.get_service(service_id)
    if service is None or not service.is_active:
        await callback.answer(tr(locale, "admin_item_not_found"), show_alert=True)
        return

    barbers = await repo.list_active_barbers()
    if not barbers:
        await callback.answer(tr(locale, "no_active_barbers"), show_alert=True)
        return

    await state.update_data(admin_booking_service_id=service_id)
    await state.set_state(AdminStates.booking_create_choose_barber)
    await callback.message.answer(
        tr(locale, "admin_booking_choose_barber"),
        reply_markup=admin_booking_barbers_keyboard(barbers, locale),
    )
    await callback.message.answer(_next_step(locale, "next_step_choose_barber"))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:booking:barber:"))
async def cb_admin_booking_choose_barber(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return
    try:
        barber_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    data = await state.get_data()
    service_id = data.get("admin_booking_service_id")
    if service_id is None:
        await callback.answer(tr(locale, "flow_expired_admin"), show_alert=True)
        return
    service = await repo.get_service(int(service_id))
    barber = await repo.get_barber(barber_id)
    if service is None or barber is None or not barber.is_active:
        await callback.answer(tr(locale, "admin_item_not_found"), show_alert=True)
        return

    days = await _admin_available_days(
        repo=repo,
        barber_id=barber_id,
        duration_min=service.duration_min,
        container=container,
    )
    await state.update_data(admin_booking_barber_id=barber_id)
    await state.set_state(AdminStates.booking_create_choose_date)
    if not days:
        await callback.message.answer(
            tr(locale, "no_available_dates"),
            reply_markup=admin_back_menu_keyboard(locale),
        )
    else:
        await callback.message.answer(
            tr(locale, "admin_booking_choose_date"),
            reply_markup=admin_booking_dates_keyboard(days, locale),
        )
    await callback.message.answer(_next_step(locale, "next_step_choose_date"))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:booking:date:"))
async def cb_admin_booking_choose_date(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return
    try:
        local_day = date.fromisoformat(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    data = await state.get_data()
    barber_id = data.get("admin_booking_barber_id")
    service_id = data.get("admin_booking_service_id")
    if barber_id is None or service_id is None:
        await callback.answer(tr(locale, "flow_expired_admin"), show_alert=True)
        return
    service = await repo.get_service(int(service_id))
    if service is None:
        await callback.answer(tr(locale, "admin_item_not_found"), show_alert=True)
        return

    now_utc = datetime.now(UTC)
    slots = await _admin_slots_for_day(
        repo=repo,
        barber_id=int(barber_id),
        local_day=local_day,
        duration_min=service.duration_min,
        container=container,
        now_utc=now_utc,
    )
    if not slots:
        days = await _admin_available_days(
            repo=repo,
            barber_id=int(barber_id),
            duration_min=service.duration_min,
            container=container,
        )
        if not days:
            await callback.message.answer(
                tr(locale, "no_available_dates"),
                reply_markup=admin_back_menu_keyboard(locale),
            )
        else:
            await callback.message.answer(
                tr(locale, "admin_booking_choose_date"),
                reply_markup=admin_booking_dates_keyboard(days, locale),
            )
        await callback.answer()
        return

    slot_map = {
        str(int(slot.starts_at_utc.timestamp())): {
            "starts_at_utc": slot.starts_at_utc.isoformat(),
            "ends_at_utc": slot.ends_at_utc.isoformat(),
        }
        for slot in slots
    }
    await state.update_data(admin_booking_slot_map=slot_map)
    await state.set_state(AdminStates.booking_create_choose_slot)
    await callback.message.answer(
        tr(locale, "admin_booking_choose_slot"),
        reply_markup=admin_booking_slots_keyboard(slots, container.settings.salon_timezone, locale),
    )
    await callback.message.answer(_next_step(locale, "next_step_choose_slot"))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:booking:slot:"))
async def cb_admin_booking_choose_slot(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None or callback.from_user is None:
        return

    slot_id = callback.data.split(":")[-1]
    data = await state.get_data()
    slot_map = data.get("admin_booking_slot_map") or {}
    slot_data = slot_map.get(slot_id)
    if slot_data is None:
        await callback.answer(tr(locale, "slot_expired_admin"), show_alert=True)
        return

    draft_id = uuid4().hex[:12]
    await save_draft(
        container.redis,
        draft_id,
        {
            "client_id": int(data["admin_booking_client_id"]),
            "service_id": int(data["admin_booking_service_id"]),
            "barber_id": int(data["admin_booking_barber_id"]),
            "starts_at_utc": slot_data["starts_at_utc"],
            "ends_at_utc": slot_data["ends_at_utc"],
            "admin_tg_user_id": callback.from_user.id,
            "is_guest": bool(data.get("admin_booking_is_guest")),
        },
        container.settings.draft_ttl_seconds,
    )
    await state.set_state(AdminStates.booking_create_confirm)
    start = datetime.fromisoformat(slot_data["starts_at_utc"])
    await callback.message.answer(
        tr(
            locale,
            "admin_booking_confirm",
            date_time=format_booking_local(start, container.settings.salon_timezone),
        ),
        reply_markup=admin_booking_confirm_keyboard(draft_id, locale),
    )
    await callback.message.answer(_next_step(locale, "next_step_confirm"))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:booking:confirm:"))
async def cb_admin_booking_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return
    if callback.from_user is None:
        return

    draft_id = callback.data.split(":")[-1]
    payload = await get_draft(container.redis, draft_id)
    if payload is None:
        await callback.answer(tr(locale, "draft_expired_admin"), show_alert=True)
        return

    starts_at_utc = datetime.fromisoformat(payload["starts_at_utc"])
    ends_at_utc = datetime.fromisoformat(payload["ends_at_utc"])
    window = BookingWindow(
        min_lead_hours=container.settings.booking_min_lead_hours,
        max_days=container.settings.booking_max_days,
    )
    if not validate_booking_window(starts_at_utc, datetime.now(UTC), window):
        await callback.answer(tr(locale, "slot_no_longer_valid"), show_alert=True)
        return

    booking = await repo.create_confirmed_booking_admin(
        client_id=int(payload["client_id"]),
        barber_id=int(payload["barber_id"]),
        service_id=int(payload["service_id"]),
        starts_at_utc=starts_at_utc,
        ends_at_utc=ends_at_utc,
        admin_tg_user_id=callback.from_user.id,
    )
    if booking is None:
        await session.rollback()
        await callback.message.answer(tr(locale, "booking_conflict_refresh"))
        await callback.answer()
        return

    await repo.create_reminder_jobs_for_booking(booking)
    await session.commit()
    await state.set_state(AdminStates.menu)
    await state.update_data(
        admin_booking_client_id=None,
        admin_booking_service_id=None,
        admin_booking_barber_id=None,
        admin_booking_slot_map=None,
        admin_booking_is_guest=None,
    )

    dt = format_booking_local(booking.starts_at_utc, container.settings.salon_timezone)
    await callback.message.answer(tr(locale, "admin_booking_created", date_time=dt))
    if bool(payload.get("is_guest")):
        await callback.message.answer(tr(locale, "admin_booking_guest_no_reminders"))
    await callback.message.answer(_next_step(locale, "next_step_back_menu"))
    await callback.answer()


@router.callback_query(F.data == "admin:booking:delete:list")
async def cb_admin_booking_delete_list(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return
    await state.set_state(AdminStates.booking_delete_select)
    await _show_admin_delete_booking_list(callback.message, repo, container, locale)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:booking:delete:\d+$"))
async def cb_admin_booking_delete_pick(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return
    try:
        booking_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    booking = await repo.get_booking(booking_id)
    if booking is None:
        await callback.message.answer(tr(locale, "admin_booking_not_found"))
        await callback.answer()
        return
    if booking.status == BookingStatus.COMPLETED.value:
        await callback.message.answer(tr(locale, "admin_booking_delete_completed_forbidden"))
        await callback.answer()
        return

    await state.set_state(AdminStates.booking_delete_confirm)
    await state.update_data(admin_delete_booking_id=booking_id)
    await callback.message.answer(
        tr(locale, "admin_booking_delete_confirm", booking_id=booking_id),
        reply_markup=admin_booking_delete_confirm_keyboard(booking_id, locale),
    )
    await callback.message.answer(_next_step(locale, "next_step_confirm"))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:booking:delete:confirm:"))
async def cb_admin_booking_delete_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        booking_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    booking = await repo.get_booking(booking_id)
    if booking is None:
        await session.rollback()
        await callback.message.answer(tr(locale, "admin_booking_not_found"))
        await callback.answer()
        return
    if booking.status == BookingStatus.COMPLETED.value:
        await session.rollback()
        await callback.message.answer(tr(locale, "admin_booking_delete_completed_forbidden"))
        await callback.answer()
        return

    deleted = await repo.delete_booking_hard(booking_id)
    if not deleted:
        await session.rollback()
        await callback.message.answer(tr(locale, "admin_booking_not_found"))
        await callback.answer()
        return

    await session.commit()
    await state.set_state(AdminStates.menu)
    await callback.message.answer(tr(locale, "admin_booking_deleted"))
    await callback.message.answer(_next_step(locale, "next_step_back_menu"))
    await _show_admin_delete_booking_list(callback.message, repo, container, locale)
    await callback.answer()


@router.callback_query(F.data == "admin:barber:list")
async def cb_admin_barber_list(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    await state.set_state(AdminStates.menu)
    await state.update_data(admin_edit_barber_id=None)
    await _show_barbers_list(callback.message, repo, locale)
    await callback.answer()


@router.callback_query(F.data == "admin:barber:add")
async def cb_admin_barber_add(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    await state.set_state(AdminStates.barber_create_name)
    await callback.message.answer(
        tr(locale, "admin_enter_barber_name"),
        reply_markup=admin_back_menu_keyboard(locale),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:barber:edit:"))
@router.callback_query(F.data.startswith("admin:barber:view:"))
async def cb_admin_barber_open(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    parts = callback.data.split(":")
    try:
        barber_id = int(parts[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    await state.set_state(AdminStates.menu)
    await state.update_data(admin_edit_barber_id=barber_id)
    await _show_barber_details(callback.message, repo, locale, barber_id)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:barber:rename:"))
async def cb_admin_barber_rename(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    parts = callback.data.split(":")
    try:
        barber_id = int(parts[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    barber = await repo.get_barber(barber_id)
    if barber is None:
        await callback.message.answer(tr(locale, "admin_item_not_found"))
        await callback.answer()
        return

    await state.set_state(AdminStates.barber_edit_name)
    await state.update_data(admin_edit_barber_id=barber_id)
    await callback.message.answer(
        tr(locale, "admin_enter_barber_name"),
        reply_markup=admin_back_menu_keyboard(locale),
    )
    await callback.answer()


@router.message(AdminStates.barber_create_name)
async def on_admin_barber_create_name(
    message: Message,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    if message.text is None:
        return

    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    name = message.text.strip()
    if not name:
        await message.answer(tr(locale, "admin_enter_barber_name"))
        return

    await repo.create_barber(name)
    await session.commit()

    await state.set_state(AdminStates.menu)
    await message.answer(tr(locale, "admin_barber_added"))
    await _show_barbers_list(message, repo, locale)


@router.message(AdminStates.barber_edit_name)
async def on_admin_barber_edit_name(
    message: Message,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    if message.text is None:
        return

    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    data = await state.get_data()
    barber_id = data.get("admin_edit_barber_id")
    if barber_id is None:
        await state.set_state(AdminStates.menu)
        await message.answer(tr(locale, "admin_item_not_found"))
        await _show_barbers_list(message, repo, locale)
        return

    name = message.text.strip()
    if not name:
        await message.answer(tr(locale, "admin_enter_barber_name"))
        return

    updated = await repo.update_barber_name(int(barber_id), name)
    if not updated:
        await session.rollback()
        await state.set_state(AdminStates.menu)
        await message.answer(tr(locale, "admin_item_not_found"))
        await _show_barbers_list(message, repo, locale)
        return

    await session.commit()
    await state.set_state(AdminStates.menu)
    await message.answer(tr(locale, "admin_barber_updated"))
    await _show_barber_details(message, repo, locale, int(barber_id))


@router.callback_query(F.data.startswith("admin:barber:archive:"))
async def cb_admin_barber_archive(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        barber_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    updated = await repo.archive_barber(barber_id)
    if not updated:
        await session.rollback()
        await callback.message.answer(tr(locale, "admin_item_not_found"))
        await callback.answer()
        return

    await session.commit()
    await state.set_state(AdminStates.menu)
    await callback.message.answer(tr(locale, "admin_barber_archived"))
    await _show_barbers_list(callback.message, repo, locale)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:barber:restore:"))
async def cb_admin_barber_restore(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        barber_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    updated = await repo.restore_barber(barber_id)
    if not updated:
        await session.rollback()
        await callback.message.answer(tr(locale, "admin_item_not_found"))
        await callback.answer()
        return

    await session.commit()
    await state.set_state(AdminStates.menu)
    await callback.message.answer(tr(locale, "admin_barber_restored"))
    await _show_barbers_list(callback.message, repo, locale)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:barber:delete:\d+$"))
async def cb_admin_barber_delete(
    callback: CallbackQuery,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return
    try:
        barber_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    await callback.message.answer(
        tr(locale, "admin_barber_delete_confirm"),
        reply_markup=admin_confirm_barber_delete_keyboard(barber_id, locale),
    )
    await callback.message.answer(_next_step(locale, "next_step_confirm"))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:barber:delete:confirm:"))
async def cb_admin_barber_delete_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return
    try:
        barber_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    deleted = await repo.delete_barber_hard(barber_id)
    if not deleted:
        await session.rollback()
        await callback.message.answer(tr(locale, "admin_item_not_found"))
        await callback.answer()
        return

    await session.commit()
    await state.set_state(AdminStates.menu)
    await callback.message.answer(tr(locale, "admin_barber_deleted"))
    await _show_barbers_list(callback.message, repo, locale)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:barber:shift:list:"))
async def cb_admin_shift_list(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        barber_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    await state.set_state(AdminStates.menu)
    await state.update_data(admin_shift_barber_id=barber_id)
    await _show_barber_shifts(callback.message, repo, locale, barber_id)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:barber:shift:weekly:"))
async def cb_admin_shift_weekly(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        barber_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    barber = await repo.get_barber(barber_id)
    if barber is None:
        await callback.message.answer(tr(locale, "admin_item_not_found"))
        await callback.answer()
        return

    shifts = await repo.list_work_shifts(barber_id)
    await state.set_state(AdminStates.shift_weekly_edit)
    await state.update_data(admin_shift_barber_id=barber_id)
    await callback.message.answer(
        tr(locale, "admin_weekly_shift_prompt", rows=_format_weekly_rows(locale, shifts)),
        reply_markup=admin_back_menu_keyboard(locale),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:barber:shift:add:"))
async def cb_admin_shift_add(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    parts = callback.data.split(":")
    if len(parts) != 6:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    try:
        barber_id = int(parts[4])
        weekday = int(parts[5])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    if weekday < 0 or weekday > 7:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return
    if weekday == 7:
        weekday = 6

    barber = await repo.get_barber(barber_id)
    if barber is None:
        await callback.message.answer(tr(locale, "admin_item_not_found"))
        await callback.answer()
        return

    await state.set_state(AdminStates.shift_add_time_range)
    await state.update_data(admin_shift_barber_id=barber_id, admin_shift_weekday=weekday)
    await callback.message.answer(
        tr(
            locale,
            "admin_shift_enter_range_with_day",
            weekday=_weekday_label(locale, weekday),
        ),
        reply_markup=admin_back_menu_keyboard(locale),
    )
    await callback.answer()


@router.message(AdminStates.shift_add_time_range)
async def on_admin_shift_add_time_range(
    message: Message,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    if message.text is None:
        return

    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    parsed = _parse_time_range(message.text)
    if parsed is None:
        await message.answer(tr(locale, "admin_invalid_time_range"))
        return

    start_local_time, end_local_time = parsed

    data = await state.get_data()
    barber_id = data.get("admin_shift_barber_id")
    weekday = data.get("admin_shift_weekday")
    if barber_id is None or weekday is None:
        await state.set_state(AdminStates.menu)
        await message.answer(tr(locale, "admin_item_not_found"))
        await _show_admin_menu(message, locale)
        return

    shift = await repo.create_work_shift(
        barber_id=int(barber_id),
        weekday=int(weekday),
        start_local_time=start_local_time,
        end_local_time=end_local_time,
    )
    if shift is None:
        await session.rollback()
        await message.answer(tr(locale, "admin_shift_add_failed"))
        return

    await session.commit()
    await state.set_state(AdminStates.menu)
    await message.answer(tr(locale, "admin_shift_added"))
    await _show_barber_shifts(message, repo, locale, int(barber_id))


@router.message(AdminStates.shift_weekly_edit)
async def on_admin_shift_weekly_edit(
    message: Message,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    if message.text is None:
        return

    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    schedule, parse_error = _parse_weekly_schedule(message.text)
    if schedule is None:
        if parse_error == "missing_days":
            await message.answer(tr(locale, "admin_weekly_shift_missing_days"))
        else:
            await message.answer(tr(locale, "admin_weekly_shift_invalid"))
        return

    data = await state.get_data()
    barber_id = data.get("admin_shift_barber_id")
    if barber_id is None:
        await state.set_state(AdminStates.menu)
        await message.answer(tr(locale, "admin_item_not_found"))
        await _show_admin_menu(message, locale)
        return

    updated = await _replace_barber_weekly_schedule(repo, int(barber_id), schedule)
    if not updated:
        await session.rollback()
        await message.answer(tr(locale, "admin_shift_add_failed"))
        return

    await session.commit()
    await state.set_state(AdminStates.menu)
    await message.answer(tr(locale, "admin_weekly_shift_saved"))
    await _show_barber_shifts(message, repo, locale, int(barber_id))


@router.callback_query(F.data.startswith("admin:barber:shift:del:"))
async def cb_admin_shift_delete(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        shift_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    shift = await session.get(WorkShift, shift_id)
    if shift is None:
        await callback.message.answer(tr(locale, "admin_shift_not_found"))
        await callback.answer()
        return

    barber_id = int(shift.barber_id)
    deleted = await repo.delete_work_shift(shift_id)
    if not deleted:
        await session.rollback()
        await callback.message.answer(tr(locale, "admin_shift_not_found"))
        await callback.answer()
        return

    await session.commit()
    await state.set_state(AdminStates.menu)
    await callback.message.answer(tr(locale, "admin_shift_deleted"))
    await _show_barber_shifts(callback.message, repo, locale, barber_id)
    await callback.answer()


@router.callback_query(F.data == "admin:service:list")
async def cb_admin_service_list(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    await state.set_state(AdminStates.menu)
    await state.update_data(admin_edit_service_id=None)
    await _show_services_list(callback.message, repo, locale)
    await callback.answer()


@router.callback_query(F.data == "admin:service:add")
async def cb_admin_service_add(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    await state.set_state(AdminStates.service_create_ru_name)
    await state.update_data(
        admin_service_create_name_ru=None,
        admin_service_create_name_uz=None,
        admin_service_create_name_tj=None,
        admin_service_create_duration=None,
    )
    await callback.message.answer(
        tr(locale, "admin_enter_service_ru_name"),
        reply_markup=admin_back_menu_keyboard(locale),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:service:edit:"))
async def cb_admin_service_open(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        service_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    await state.set_state(AdminStates.menu)
    await state.update_data(admin_edit_service_id=service_id)
    await _show_service_details(callback.message, repo, locale, service_id)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:service:update:"))
async def cb_admin_service_update(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        service_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    service = await repo.get_service(service_id)
    if service is None:
        await callback.message.answer(tr(locale, "admin_item_not_found"))
        await callback.answer()
        return

    await state.set_state(AdminStates.service_edit_ru_name)
    await state.update_data(
        admin_edit_service_id=service_id,
        admin_service_edit_name_ru=None,
        admin_service_edit_name_uz=None,
        admin_service_edit_name_tj=None,
        admin_service_edit_duration=None,
    )
    await callback.message.answer(
        tr(locale, "admin_enter_service_ru_name"),
        reply_markup=admin_back_menu_keyboard(locale),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:service:archive:"))
async def cb_admin_service_archive(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        service_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    updated = await repo.archive_service(service_id)
    if not updated:
        await session.rollback()
        await callback.message.answer(tr(locale, "admin_item_not_found"))
        await callback.answer()
        return

    await session.commit()
    await state.set_state(AdminStates.menu)
    await callback.message.answer(tr(locale, "admin_service_archived"))
    await _show_services_list(callback.message, repo, locale)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:service:restore:"))
async def cb_admin_service_restore(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        service_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    updated = await repo.restore_service(service_id)
    if not updated:
        await session.rollback()
        await callback.message.answer(tr(locale, "admin_item_not_found"))
        await callback.answer()
        return

    await session.commit()
    await state.set_state(AdminStates.menu)
    await callback.message.answer(tr(locale, "admin_service_restored"))
    await _show_services_list(callback.message, repo, locale)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:service:delete:\d+$"))
async def cb_admin_service_delete(
    callback: CallbackQuery,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        service_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    await callback.message.answer(
        tr(locale, "admin_service_delete_confirm"),
        reply_markup=admin_confirm_service_delete_keyboard(service_id, locale),
    )
    await callback.message.answer(_next_step(locale, "next_step_confirm"))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:service:delete:confirm:"))
async def cb_admin_service_delete_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin_callback(callback, repo, container)
    if not ok or callback.message is None:
        return

    try:
        service_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer(tr(locale, "bad_admin_args"), show_alert=True)
        return

    deleted = await repo.delete_service_hard(service_id)
    if not deleted:
        await session.rollback()
        await callback.message.answer(tr(locale, "admin_item_not_found"))
        await callback.answer()
        return

    await session.commit()
    await state.set_state(AdminStates.menu)
    await callback.message.answer(tr(locale, "admin_service_deleted"))
    await _show_services_list(callback.message, repo, locale)
    await callback.answer()


@router.message(AdminStates.service_create_ru_name)
async def on_admin_service_create_ru_name(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if message.text is None:
        return

    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    name_ru = message.text.strip()
    if not name_ru:
        await message.answer(tr(locale, "admin_enter_service_ru_name"))
        return

    await state.update_data(admin_service_create_name_ru=name_ru)
    await state.set_state(AdminStates.service_create_uz_name)
    await message.answer(tr(locale, "admin_enter_service_uz_name"))


@router.message(AdminStates.service_create_uz_name)
async def on_admin_service_create_uz_name(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if message.text is None:
        return

    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    name_uz = message.text.strip()
    if not name_uz:
        await message.answer(tr(locale, "admin_enter_service_uz_name"))
        return

    await state.update_data(admin_service_create_name_uz=name_uz)
    await state.set_state(AdminStates.service_create_tj_name)
    await message.answer(tr(locale, "admin_enter_service_tj_name"))


@router.message(AdminStates.service_create_tj_name)
async def on_admin_service_create_tj_name(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if message.text is None:
        return

    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    name_tj = message.text.strip()
    if not name_tj:
        await message.answer(tr(locale, "admin_enter_service_tj_name"))
        return

    await state.update_data(admin_service_create_name_tj=name_tj)
    await state.set_state(AdminStates.service_create_duration)
    await message.answer(tr(locale, "admin_enter_service_duration"))


@router.message(AdminStates.service_create_duration)
async def on_admin_service_create_duration(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if message.text is None:
        return

    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    try:
        duration = int(message.text.strip())
    except ValueError:
        await message.answer(tr(locale, "admin_invalid_number"))
        return

    if duration <= 0:
        await message.answer(tr(locale, "admin_invalid_number"))
        return

    await state.update_data(admin_service_create_duration=duration)
    await state.set_state(AdminStates.service_create_price)
    await message.answer(tr(locale, "admin_enter_service_price"))


@router.message(AdminStates.service_create_price)
async def on_admin_service_create_price(
    message: Message,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    if message.text is None:
        return

    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    try:
        price_minor = int(message.text.strip())
    except ValueError:
        await message.answer(tr(locale, "admin_invalid_number"))
        return

    if price_minor < 0:
        await message.answer(tr(locale, "admin_invalid_number"))
        return

    data = await state.get_data()
    name_ru = data.get("admin_service_create_name_ru")
    name_uz = data.get("admin_service_create_name_uz")
    name_tj = data.get("admin_service_create_name_tj")
    duration = data.get("admin_service_create_duration")
    if not name_ru or not name_uz or not name_tj or duration is None:
        await state.set_state(AdminStates.menu)
        await message.answer(tr(locale, "admin_item_not_found"))
        await _show_services_list(message, repo, locale)
        return

    await repo.create_service(
        duration_min=int(duration),
        price_minor=price_minor,
        name_ru=str(name_ru),
        name_uz=str(name_uz),
        name_tj=str(name_tj),
    )
    await session.commit()

    await state.set_state(AdminStates.menu)
    await message.answer(tr(locale, "admin_service_added"))
    await _show_services_list(message, repo, locale)


@router.message(AdminStates.service_edit_ru_name)
async def on_admin_service_edit_ru_name(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if message.text is None:
        return

    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    name_ru = message.text.strip()
    if not name_ru:
        await message.answer(tr(locale, "admin_enter_service_ru_name"))
        return

    await state.update_data(admin_service_edit_name_ru=name_ru)
    await state.set_state(AdminStates.service_edit_uz_name)
    await message.answer(tr(locale, "admin_enter_service_uz_name"))


@router.message(AdminStates.service_edit_uz_name)
async def on_admin_service_edit_uz_name(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if message.text is None:
        return

    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    name_uz = message.text.strip()
    if not name_uz:
        await message.answer(tr(locale, "admin_enter_service_uz_name"))
        return

    await state.update_data(admin_service_edit_name_uz=name_uz)
    await state.set_state(AdminStates.service_edit_tj_name)
    await message.answer(tr(locale, "admin_enter_service_tj_name"))


@router.message(AdminStates.service_edit_tj_name)
async def on_admin_service_edit_tj_name(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if message.text is None:
        return

    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    name_tj = message.text.strip()
    if not name_tj:
        await message.answer(tr(locale, "admin_enter_service_tj_name"))
        return

    await state.update_data(admin_service_edit_name_tj=name_tj)
    await state.set_state(AdminStates.service_edit_duration)
    await message.answer(tr(locale, "admin_enter_service_duration"))


@router.message(AdminStates.service_edit_duration)
async def on_admin_service_edit_duration(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    if message.text is None:
        return

    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    try:
        duration = int(message.text.strip())
    except ValueError:
        await message.answer(tr(locale, "admin_invalid_number"))
        return

    if duration <= 0:
        await message.answer(tr(locale, "admin_invalid_number"))
        return

    await state.update_data(admin_service_edit_duration=duration)
    await state.set_state(AdminStates.service_edit_price)
    await message.answer(tr(locale, "admin_enter_service_price"))


@router.message(AdminStates.service_edit_price)
async def on_admin_service_edit_price(
    message: Message,
    state: FSMContext,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    if message.text is None:
        return

    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    try:
        price_minor = int(message.text.strip())
    except ValueError:
        await message.answer(tr(locale, "admin_invalid_number"))
        return

    if price_minor < 0:
        await message.answer(tr(locale, "admin_invalid_number"))
        return

    data = await state.get_data()
    service_id = data.get("admin_edit_service_id")
    name_ru = data.get("admin_service_edit_name_ru")
    name_uz = data.get("admin_service_edit_name_uz")
    name_tj = data.get("admin_service_edit_name_tj")
    duration = data.get("admin_service_edit_duration")

    if service_id is None or not name_ru or not name_uz or not name_tj or duration is None:
        await state.set_state(AdminStates.menu)
        await message.answer(tr(locale, "admin_item_not_found"))
        await _show_services_list(message, repo, locale)
        return

    updated = await repo.update_service(
        int(service_id),
        duration_min=int(duration),
        price_minor=price_minor,
        name_ru=str(name_ru),
        name_uz=str(name_uz),
        name_tj=str(name_tj),
    )
    if not updated:
        await session.rollback()
        await state.set_state(AdminStates.menu)
        await message.answer(tr(locale, "admin_item_not_found"))
        await _show_services_list(message, repo, locale)
        return

    await session.commit()
    await state.set_state(AdminStates.menu)
    await message.answer(tr(locale, "admin_service_updated"))
    await _show_service_details(message, repo, locale, int(service_id))


# Fallback command-based admin API remains enabled.


@router.message(Command("admin_today"))
async def cmd_admin_today(message: Message, repo: Repository, container: AppContainer) -> None:
    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    await _show_today_bookings(message, repo, container, locale)


@router.message(Command("admin_visits"))
async def cmd_admin_visits(
    message: Message,
    state: FSMContext,
    repo: Repository,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin(message, repo, container)
    if not ok:
        return

    await state.set_state(AdminStates.visit_date_input)
    await _show_visits_today_list(message, repo, container, locale)


@router.message(Command("admin_schedule"))
async def cmd_admin_schedule(message: Message, repo: Repository, container: AppContainer) -> None:
    ok, locale = await _check_admin(message, repo, container)
    if not ok or message.text is None:
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer(tr(locale, "bad_admin_args"))
        return

    try:
        barber_id = int(parts[1])
        local_day = date.fromisoformat(parts[2])
    except ValueError:
        await message.answer(tr(locale, "bad_admin_args"))
        return

    shifts = await repo.list_shifts_for_barber_weekday(barber_id, local_day.weekday())
    busy = await repo.list_busy_intervals_for_local_day(barber_id, local_day, container.settings.salon_timezone)

    shift_rows = [
        f"{s.start_local_time.strftime('%H:%M')} - {s.end_local_time.strftime('%H:%M')}" for s in shifts
    ]
    salon_tz = ZoneInfo(container.settings.salon_timezone)
    busy_rows = [
        f"{start.astimezone(salon_tz).strftime('%H:%M')} - {end.astimezone(salon_tz).strftime('%H:%M')}"
        for start, end in busy
    ]
    text = tr(
        locale,
        "admin_schedule_overview",
        shifts=chr(10).join(shift_rows) if shift_rows else "-",
        busy=chr(10).join(busy_rows) if busy_rows else "-",
    )
    await message.answer(text)


@router.message(Command("admin_block"))
async def cmd_admin_block(
    message: Message,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin(message, repo, container)
    if not ok or message.text is None:
        return

    parts = message.text.split(maxsplit=4)
    if len(parts) < 4:
        await message.answer(tr(locale, "bad_admin_args"))
        return

    try:
        barber_id = int(parts[1])
        local_start = datetime.fromisoformat(parts[2])
        duration_min = int(parts[3])
    except ValueError:
        await message.answer(tr(locale, "bad_admin_args"))
        return

    note = parts[4] if len(parts) == 5 else None

    if local_start.tzinfo is None:
        local_start = local_start.replace(tzinfo=ZoneInfo(container.settings.salon_timezone))

    starts_at_utc = local_start.astimezone(UTC)
    ends_at_utc = starts_at_utc + timedelta(minutes=duration_min)

    booking = await repo.create_blocked_booking(
        barber_id=barber_id,
        starts_at_utc=starts_at_utc,
        ends_at_utc=ends_at_utc,
        admin_id=None,
        note=note,
    )
    if booking is None:
        await session.rollback()
        await message.answer(tr(locale, "conflict"))
        return

    await session.commit()
    await message.answer(tr(locale, "admin_done"))


@router.message(Command("admin_service_add"))
async def cmd_admin_service_add(
    message: Message,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin(message, repo, container)
    if not ok or message.text is None:
        return

    parts = message.text.split(maxsplit=3)
    if len(parts) != 4:
        await message.answer(tr(locale, "bad_admin_args"))
        return

    try:
        duration_min = int(parts[1])
        price_minor = int(parts[2])
    except ValueError:
        await message.answer(tr(locale, "bad_admin_args"))
        return

    names = [part.strip() for part in parts[3].split("|", maxsplit=2)]
    if len(names) not in {2, 3}:
        await message.answer(tr(locale, "bad_admin_args"))
        return

    name_ru = names[0]
    name_uz = names[1]
    name_tj = names[2] if len(names) == 3 else name_ru
    if not name_ru or not name_uz or not name_tj:
        await message.answer(tr(locale, "bad_admin_args"))
        return

    await repo.create_service(
        duration_min=duration_min,
        price_minor=price_minor,
        name_ru=name_ru,
        name_uz=name_uz,
        name_tj=name_tj,
    )
    await session.commit()
    await message.answer(tr(locale, "admin_done"))


@router.message(Command("admin_service_toggle"))
async def cmd_admin_service_toggle(
    message: Message,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin(message, repo, container)
    if not ok or message.text is None:
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer(tr(locale, "bad_admin_args"))
        return

    try:
        service_id = int(parts[1])
    except ValueError:
        await message.answer(tr(locale, "bad_admin_args"))
        return

    is_active = _parse_bool_on_off(parts[2])
    if is_active is None:
        await message.answer(tr(locale, "bad_admin_args"))
        return

    updated = await repo.toggle_service(service_id, is_active)
    if not updated:
        await session.rollback()
        await message.answer(tr(locale, "service_not_found"))
        return

    await session.commit()
    await message.answer(tr(locale, "admin_done"))


@router.message(Command("admin_barber_toggle"))
async def cmd_admin_barber_toggle(
    message: Message,
    repo: Repository,
    session: AsyncSession,
    container: AppContainer,
) -> None:
    ok, locale = await _check_admin(message, repo, container)
    if not ok or message.text is None:
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer(tr(locale, "bad_admin_args"))
        return

    try:
        barber_id = int(parts[1])
    except ValueError:
        await message.answer(tr(locale, "bad_admin_args"))
        return

    is_active = _parse_bool_on_off(parts[2])
    if is_active is None:
        await message.answer(tr(locale, "bad_admin_args"))
        return

    updated = await repo.toggle_barber(barber_id, is_active)
    if not updated:
        await session.rollback()
        await message.answer(tr(locale, "barber_not_found"))
        return

    await session.commit()
    await message.answer(tr(locale, "admin_done"))
