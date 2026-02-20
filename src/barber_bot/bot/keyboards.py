from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from barber_bot.db.models import Barber, Client, Service, WorkShift
from barber_bot.services.slots import Slot


def lang_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Русский", callback_data="lang:ru")
    builder.button(text="O'zbek", callback_data="lang:uz")
    builder.adjust(2)
    return builder.as_markup()


def services_keyboard(services: list[Service], locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for service in services:
        name = service.name_ru if locale == "ru" else service.name_uz
        builder.button(text=f"{name} ({service.duration_min}m)", callback_data=f"svc:{service.id}")
    builder.adjust(1)
    return builder.as_markup()


def barbers_keyboard(barbers: list[Barber]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for barber in barbers:
        builder.button(text=barber.name, callback_data=f"barber:{barber.id}")
    builder.adjust(2)
    return builder.as_markup()


def dates_keyboard(days: list[date]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for day in days:
        builder.button(text=day.strftime("%d.%m (%a)"), callback_data=f"date:{day.isoformat()}")
    builder.adjust(2)
    return builder.as_markup()


def slots_keyboard(slots: list[Slot], tz_name: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    tz = ZoneInfo(tz_name)
    for slot in slots:
        text = slot.starts_at_utc.astimezone(tz).strftime("%H:%M")
        slot_id = int(slot.starts_at_utc.timestamp())
        builder.button(text=text, callback_data=f"slot:{slot_id}")
    builder.adjust(4)
    return builder.as_markup()


def confirm_keyboard(draft_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Confirm", callback_data=f"confirm:{draft_id}")],
        ]
    )


def cancel_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Cancel", callback_data=f"cancel_booking:{booking_id}")],
        ]
    )


_ADMIN_LABELS: dict[str, dict[str, str]] = {
    "ru": {
        "barbers": "Мастера",
        "services": "Услуги",
        "today": "Записи сегодня",
        "bookings_today": "Записи сегодня (детально)",
        "booking_add": "Добавить запись",
        "booking_delete": "Удалить запись",
        "back_menu": "Назад в меню",
        "add": "Добавить",
        "edit": "Редактировать",
        "rename": "Переименовать",
        "shifts": "Смены",
        "weekly_shifts": "Недельный график",
        "archive": "Архивировать",
        "restore": "Восстановить",
        "back_list": "Назад к списку",
        "weekday_0": "Пн",
        "weekday_1": "Вт",
        "weekday_2": "Ср",
        "weekday_3": "Чт",
        "weekday_4": "Пт",
        "weekday_5": "Сб",
        "weekday_6": "Вс",
        "delete_shift": "Удалить",
        "delete": "Удалить",
        "confirm_delete": "Подтвердить удаление",
        "cancel": "Отмена",
        "confirm_booking": "Подтвердить запись",
        "choose": "Выбрать",
        "no_slots_back": "Выбрать другого мастера",
    },
    "uz": {
        "barbers": "Sartaroshlar",
        "services": "Xizmatlar",
        "today": "Bugungi yozuvlar",
        "bookings_today": "Bugungi yozuvlar (batafsil)",
        "booking_add": "Yozuv qo'shish",
        "booking_delete": "Yozuvni o'chirish",
        "back_menu": "Menyuga qaytish",
        "add": "Qo'shish",
        "edit": "Tahrirlash",
        "rename": "Nomini o'zgartirish",
        "shifts": "Smenalar",
        "weekly_shifts": "Haftalik jadval",
        "archive": "Arxivlash",
        "restore": "Tiklash",
        "back_list": "Ro'yxatga qaytish",
        "weekday_0": "Du",
        "weekday_1": "Se",
        "weekday_2": "Chor",
        "weekday_3": "Pay",
        "weekday_4": "Ju",
        "weekday_5": "Shan",
        "weekday_6": "Yak",
        "delete_shift": "O'chirish",
        "delete": "O'chirish",
        "confirm_delete": "O'chirishni tasdiqlash",
        "cancel": "Bekor qilish",
        "confirm_booking": "Yozuvni tasdiqlash",
        "choose": "Tanlash",
        "no_slots_back": "Boshqa ustani tanlash",
    },
}


def _al(locale: str, key: str) -> str:
    lang = locale if locale in _ADMIN_LABELS else "ru"
    return _ADMIN_LABELS[lang][key]


def no_slots_back_keyboard(locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_al(locale, "no_slots_back"),
                    callback_data="back:barbers",
                )
            ]
        ]
    )


def admin_main_keyboard(locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_al(locale, "bookings_today"), callback_data="admin:booking:list:today")
    builder.button(text=_al(locale, "booking_add"), callback_data="admin:booking:add")
    builder.button(text=_al(locale, "booking_delete"), callback_data="admin:booking:delete:list")
    builder.button(text=_al(locale, "barbers"), callback_data="admin:barber:list")
    builder.button(text=_al(locale, "services"), callback_data="admin:service:list")
    builder.adjust(1)
    return builder.as_markup()


def admin_back_menu_keyboard(locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_al(locale, "back_menu"), callback_data="admin:menu")]
        ]
    )


def admin_barbers_keyboard(barbers: list[Barber], locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for barber in barbers:
        icon = "🟢" if barber.is_active else "⚪"
        builder.button(
            text=f"{icon} {barber.name}",
            callback_data=f"admin:barber:edit:{barber.id}",
        )
    builder.button(text=f"➕ {_al(locale, 'add')}", callback_data="admin:barber:add")
    builder.button(text=_al(locale, "back_menu"), callback_data="admin:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_barber_actions_keyboard(barber_id: int, is_active: bool, locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_al(locale, "rename"), callback_data=f"admin:barber:rename:{barber_id}")
    builder.button(text=_al(locale, "shifts"), callback_data=f"admin:barber:shift:list:{barber_id}")
    builder.button(
        text=_al(locale, "weekly_shifts"),
        callback_data=f"admin:barber:shift:weekly:{barber_id}",
    )
    builder.button(text=_al(locale, "delete"), callback_data=f"admin:barber:delete:{barber_id}")
    if is_active:
        builder.button(
            text=_al(locale, "archive"),
            callback_data=f"admin:barber:archive:{barber_id}",
        )
    else:
        builder.button(
            text=_al(locale, "restore"),
            callback_data=f"admin:barber:restore:{barber_id}",
        )
    builder.button(text=_al(locale, "back_list"), callback_data="admin:barber:list")
    builder.adjust(1)
    return builder.as_markup()


def admin_shift_weekday_keyboard(barber_id: int, locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for weekday in range(7):
        builder.button(
            text=f"➕ {_al(locale, f'weekday_{weekday}')}",
            callback_data=f"admin:barber:shift:add:{barber_id}:{weekday}",
        )
    builder.button(text=_al(locale, "back_list"), callback_data=f"admin:barber:view:{barber_id}")
    builder.adjust(2)
    return builder.as_markup()


def admin_shifts_keyboard(barber_id: int, shifts: list[WorkShift], locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for shift in shifts:
        weekday_text = _al(locale, f"weekday_{shift.weekday}")
        text = (
            f"{_al(locale, 'delete_shift')} {weekday_text} "
            f"{shift.start_local_time.strftime('%H:%M')}-{shift.end_local_time.strftime('%H:%M')}"
        )
        builder.button(text=text, callback_data=f"admin:barber:shift:del:{shift.id}")
    builder.button(text=_al(locale, "back_list"), callback_data=f"admin:barber:view:{barber_id}")
    builder.adjust(1)
    return builder.as_markup()


def admin_services_keyboard(services: list[Service], locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for service in services:
        icon = "🟢" if service.is_active else "⚪"
        name = service.name_ru if locale == "ru" else service.name_uz
        builder.button(
            text=f"{icon} {name} ({service.duration_min}m)",
            callback_data=f"admin:service:edit:{service.id}",
        )
    builder.button(text=f"➕ {_al(locale, 'add')}", callback_data="admin:service:add")
    builder.button(text=_al(locale, "back_menu"), callback_data="admin:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_service_actions_keyboard(service_id: int, is_active: bool, locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_al(locale, "edit"), callback_data=f"admin:service:update:{service_id}")
    builder.button(text=_al(locale, "delete"), callback_data=f"admin:service:delete:{service_id}")
    if is_active:
        builder.button(
            text=_al(locale, "archive"),
            callback_data=f"admin:service:archive:{service_id}",
        )
    else:
        builder.button(
            text=_al(locale, "restore"),
            callback_data=f"admin:service:restore:{service_id}",
        )
    builder.button(text=_al(locale, "back_list"), callback_data="admin:service:list")
    builder.adjust(1)
    return builder.as_markup()


def admin_confirm_service_delete_keyboard(service_id: int, locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_al(locale, "confirm_delete"),
                    callback_data=f"admin:service:delete:confirm:{service_id}",
                )
            ],
            [InlineKeyboardButton(text=_al(locale, "cancel"), callback_data=f"admin:service:edit:{service_id}")],
        ]
    )


def admin_confirm_barber_delete_keyboard(barber_id: int, locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_al(locale, "confirm_delete"),
                    callback_data=f"admin:barber:delete:confirm:{barber_id}",
                )
            ],
            [InlineKeyboardButton(text=_al(locale, "cancel"), callback_data=f"admin:barber:view:{barber_id}")],
        ]
    )


def admin_booking_clients_keyboard(clients: list[Client], locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for client in clients:
        username = f"@{client.tg_username}" if client.tg_username else "-"
        phone = client.phone_e164 or "-"
        builder.button(
            text=f"{username} | {phone}",
            callback_data=f"admin:booking:client:select:{client.id}",
        )
    builder.button(text=_al(locale, "back_menu"), callback_data="admin:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_booking_services_keyboard(services: list[Service], locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for service in services:
        name = service.name_ru if locale == "ru" else service.name_uz
        builder.button(text=f"{name} ({service.duration_min}m)", callback_data=f"admin:booking:service:{service.id}")
    builder.button(text=_al(locale, "back_menu"), callback_data="admin:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_booking_barbers_keyboard(barbers: list[Barber], locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for barber in barbers:
        builder.button(text=barber.name, callback_data=f"admin:booking:barber:{barber.id}")
    builder.button(text=_al(locale, "back_menu"), callback_data="admin:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_booking_dates_keyboard(days: list[date], locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for day in days:
        builder.button(text=day.strftime("%d.%m (%a)"), callback_data=f"admin:booking:date:{day.isoformat()}")
    builder.button(text=_al(locale, "back_menu"), callback_data="admin:menu")
    builder.adjust(2)
    return builder.as_markup()


def admin_booking_slots_keyboard(slots: list[Slot], tz_name: str, locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    tz = ZoneInfo(tz_name)
    for slot in slots:
        text = slot.starts_at_utc.astimezone(tz).strftime("%H:%M")
        slot_id = int(slot.starts_at_utc.timestamp())
        builder.button(text=text, callback_data=f"admin:booking:slot:{slot_id}")
    builder.button(text=_al(locale, "back_menu"), callback_data="admin:menu")
    builder.adjust(4)
    return builder.as_markup()


def admin_booking_confirm_keyboard(draft_id: str, locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_al(locale, "confirm_booking"),
                    callback_data=f"admin:booking:confirm:{draft_id}",
                )
            ],
            [InlineKeyboardButton(text=_al(locale, "back_menu"), callback_data="admin:menu")],
        ]
    )


def admin_booking_delete_list_keyboard(
    bookings: list[tuple[int, str]],
    locale: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for booking_id, label in bookings:
        builder.button(text=label, callback_data=f"admin:booking:delete:{booking_id}")
    builder.button(text=_al(locale, "back_menu"), callback_data="admin:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_booking_delete_confirm_keyboard(booking_id: int, locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_al(locale, "confirm_delete"),
                    callback_data=f"admin:booking:delete:confirm:{booking_id}",
                )
            ],
            [InlineKeyboardButton(text=_al(locale, "cancel"), callback_data="admin:booking:delete:list")],
        ]
    )
