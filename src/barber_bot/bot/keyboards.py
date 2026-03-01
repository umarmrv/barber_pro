from __future__ import annotations

import calendar
from datetime import date
from zoneinfo import ZoneInfo

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from barber_bot.db.models import Barber, Client, Service, WorkShift
from barber_bot.services.slots import Slot

_CLIENT_INLINE_LABELS: dict[str, dict[str, str]] = {
    "ru": {
        "confirm": "Подтвердить",
        "cancel": "Отменить",
    },
    "uz": {
        "confirm": "Тасдиқлаш",
        "cancel": "Бекор қилиш",
    },
    "tj": {
        "confirm": "Тасдиқ кардан",
        "cancel": "Бекор кардан",
    },
}


def lang_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Русский", callback_data="lang:ru")
    builder.button(text="Ўзбекча", callback_data="lang:uz")
    builder.button(text="Тоҷикӣ", callback_data="lang:tj")
    builder.adjust(3)
    return builder.as_markup()


def _service_name(service: Service, locale: str) -> str:
    if locale == "uz":
        return service.name_uz
    if locale == "tj":
        return service.name_tj
    return service.name_ru


def services_keyboard(services: list[Service], locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for service in services:
        name = _service_name(service, locale)
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


def confirm_keyboard(draft_id: str, locale: str) -> InlineKeyboardMarkup:
    lang = locale if locale in _CLIENT_INLINE_LABELS else "ru"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_CLIENT_INLINE_LABELS[lang]["confirm"], callback_data=f"confirm:{draft_id}")],
        ]
    )


def cancel_keyboard(booking_id: int, locale: str) -> InlineKeyboardMarkup:
    lang = locale if locale in _CLIENT_INLINE_LABELS else "ru"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_CLIENT_INLINE_LABELS[lang]["cancel"], callback_data=f"cancel_booking:{booking_id}")],
        ]
    )


_ADMIN_LABELS: dict[str, dict[str, str]] = {
    "ru": {
        "barbers": "Мастера",
        "services": "Услуги",
        "today": "Записи сегодня",
        "bookings_today": "Записи сегодня (детально)",
        "visits_today": "Визиты",
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
        "stats_horizon": "Сегодня + ближайшие дни",
        "stats_week": "Статистика за 7 дней",
        "stats_date": "Статистика по дате",
        "export_excel": "Скачать Excel",
        "stats_pick_other": "Выбрать другой период",
        "mark_completed": "Подтвердить обслуживание",
        "revert_completed": "Снять подтверждение",
    },
    "uz": {
        "barbers": "Сартарошлар",
        "services": "Хизматлар",
        "today": "Бугунги ёзувлар",
        "bookings_today": "Бугунги ёзувлар (батафсил)",
        "visits_today": "Ташрифлар",
        "booking_add": "Ёзув қўшиш",
        "booking_delete": "Ёзувни ўчириш",
        "back_menu": "Менюга қайтиш",
        "add": "Қўшиш",
        "edit": "Таҳрирлаш",
        "rename": "Номини ўзгартириш",
        "shifts": "Сменалар",
        "weekly_shifts": "Ҳафталик жадвал",
        "archive": "Архивлаш",
        "restore": "Тиклаш",
        "back_list": "Рўйхатга қайтиш",
        "weekday_0": "Ду",
        "weekday_1": "Се",
        "weekday_2": "Чор",
        "weekday_3": "Пай",
        "weekday_4": "Жу",
        "weekday_5": "Шан",
        "weekday_6": "Як",
        "delete_shift": "Ўчириш",
        "delete": "Ўчириш",
        "confirm_delete": "Ўчиришни тасдиқлаш",
        "cancel": "Бекор қилиш",
        "confirm_booking": "Ёзувни тасдиқлаш",
        "choose": "Танлаш",
        "no_slots_back": "Бошқа устани танлаш",
        "stats_horizon": "Бугун + яқин кунлар",
        "stats_week": "7 кун статистикаси",
        "stats_date": "Сана бўйича статистика",
        "export_excel": "Excel юклаш",
        "stats_pick_other": "Бошқа даврни танлаш",
        "mark_completed": "Хизматни тасдиқлаш",
        "revert_completed": "Тасдиқни бекор қилиш",
    },
    "tj": {
        "barbers": "Устоҳо",
        "services": "Хизматҳо",
        "today": "Сабтҳои имрӯз",
        "bookings_today": "Сабтҳои имрӯз (муфассал)",
        "visits_today": "Ташрифҳо",
        "booking_add": "Иловаи сабт",
        "booking_delete": "Ҳазфи сабт",
        "back_menu": "Бозгашт ба меню",
        "add": "Илова",
        "edit": "Таҳрир",
        "rename": "Иваз кардани ном",
        "shifts": "Сменаҳо",
        "weekly_shifts": "Ҷадвали ҳафтаина",
        "archive": "Бойгонӣ",
        "restore": "Барқарор кардан",
        "back_list": "Бозгашт ба рӯйхат",
        "weekday_0": "Дш",
        "weekday_1": "Сш",
        "weekday_2": "Чш",
        "weekday_3": "Пш",
        "weekday_4": "Ҷм",
        "weekday_5": "Шн",
        "weekday_6": "Як",
        "delete_shift": "Ҳазфи смена",
        "delete": "Ҳазф",
        "confirm_delete": "Тасдиқи ҳазф",
        "cancel": "Бекор кардан",
        "confirm_booking": "Тасдиқи сабт",
        "choose": "Интихоб",
        "no_slots_back": "Интихоби устои дигар",
        "stats_horizon": "Имрӯз + рӯзҳои наздик",
        "stats_week": "Статистикаи 7 рӯз",
        "stats_date": "Статистика аз рӯи сана",
        "export_excel": "Боргирии Excel",
        "stats_pick_other": "Интихоби давраи дигар",
        "mark_completed": "Тасдиқи хизмат",
        "revert_completed": "Бардоштани тасдиқ",
    },
}

_CALENDAR_WEEKDAYS: dict[str, list[str]] = {
    "ru": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
    "uz": ["Ду", "Се", "Чо", "Пай", "Жу", "Ша", "Як"],
    "tj": ["Дш", "Сш", "Чш", "Пш", "Ҷм", "Шн", "Як"],
}

_CLIENT_MENU_LABELS: dict[str, dict[str, str]] = {
    "ru": {
        "book": "🗓 Записаться",
        "my_bookings": "📒 Мои записи",
        "cancel": "❌ Отмена записи",
        "lang": "🌐 Язык",
        "help": "ℹ️ Помощь",
    },
    "uz": {
        "book": "🗓 Ёзилиш",
        "my_bookings": "📒 Менинг ёзувларим",
        "cancel": "❌ Ёзувни бекор қилиш",
        "lang": "🌐 Тил",
        "help": "ℹ️ Ёрдам",
    },
    "tj": {
        "book": "🗓 Сабт шудан",
        "my_bookings": "📒 Сабтҳои ман",
        "cancel": "❌ Бекор кардани сабт",
        "lang": "🌐 Забон",
        "help": "ℹ️ Кӯмак",
    },
}

_CLIENT_MENU_ALIASES: dict[str, set[str]] = {
    "book": {
        "Записаться",
        "Yozilish",
        "Ёзилиш",
        "Сабт шудан",
        "/book",
    },
    "my_bookings": {
        "Мои записи",
        "Mening yozuvlarim",
        "Менинг ёзувларим",
        "Сабтҳои ман",
        "/my_bookings",
    },
    "cancel": {
        "Отмена записи",
        "Yozuvni bekor qilish",
        "Ёзувни бекор қилиш",
        "Бекор кардани сабт",
        "/cancel",
    },
    "lang": {
        "Язык",
        "Til",
        "Тил",
        "Забон",
        "/lang",
    },
    "help": {
        "Помощь",
        "Yordam",
        "Ёрдам",
        "Кӯмак",
        "/help",
    },
}

_ADMIN_REPLY_MENU_LABELS: dict[str, dict[str, str]] = {
    "ru": {
        "bookings_today": "📋 Записи (детально)",
        "visits_today": "✅ Визиты",
        "booking_add": "➕ Добавить запись",
        "booking_delete": "🗑 Удалить запись",
        "barbers": "💈 Мастера",
        "services": "✂️ Услуги",
    },
    "uz": {
        "bookings_today": "📋 Ёзувлар (батафсил)",
        "visits_today": "✅ Ташрифлар",
        "booking_add": "➕ Ёзув қўшиш",
        "booking_delete": "🗑 Ёзувни ўчириш",
        "barbers": "💈 Сартарошлар",
        "services": "✂️ Хизматлар",
    },
    "tj": {
        "bookings_today": "📋 Сабтҳо (муфассал)",
        "visits_today": "✅ Ташрифҳо",
        "booking_add": "➕ Иловаи сабт",
        "booking_delete": "🗑 Ҳазфи сабт",
        "barbers": "💈 Устоҳо",
        "services": "✂️ Хизматҳо",
    },
}

_ADMIN_MENU_ALIASES: dict[str, set[str]] = {
    "bookings_today": {
        "Записи сегодня (детально)",
        "Bugungi yozuvlar (batafsil)",
        "Бугунги ёзувлар (батафсил)",
        "Сабтҳои имрӯз (муфассал)",
    },
    "visits_today": {
        "Визиты",
        "Визиты сегодня",
        "Bugungi tashriflar",
        "Ташрифлар",
        "Ташрифҳои имрӯз",
        "Ташрифҳо",
    },
    "booking_add": {
        "Добавить запись",
        "Yozuv qo'shish",
        "Ёзув қўшиш",
        "Иловаи сабт",
    },
    "booking_delete": {
        "Удалить запись",
        "Yozuvni o'chirish",
        "Ёзувни ўчириш",
        "Ҳазфи сабт",
    },
    "barbers": {
        "Мастера",
        "Sartaroshlar",
        "Сартарошлар",
        "Устоҳо",
    },
    "services": {
        "Услуги",
        "Xizmatlar",
        "Хизматлар",
        "Хизматҳо",
    },
}


def client_main_reply_keyboard(locale: str) -> ReplyKeyboardMarkup:
    lang = locale if locale in _CLIENT_MENU_LABELS else "ru"
    labels = _CLIENT_MENU_LABELS[lang]
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text=labels["book"])],
            [KeyboardButton(text=labels["my_bookings"])],
            [KeyboardButton(text=labels["cancel"])],
            [KeyboardButton(text=labels["lang"]), KeyboardButton(text=labels["help"])],
        ],
    )


def client_menu_texts(action: str) -> set[str]:
    base = {
        labels[action]
        for labels in _CLIENT_MENU_LABELS.values()
        if action in labels
    }
    return base | _CLIENT_MENU_ALIASES.get(action, set())


def admin_main_reply_keyboard(locale: str) -> ReplyKeyboardMarkup:
    lang = locale if locale in _ADMIN_REPLY_MENU_LABELS else "ru"
    labels = _ADMIN_REPLY_MENU_LABELS[lang]
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text=labels["bookings_today"])],
            [KeyboardButton(text=labels["visits_today"])],
            [KeyboardButton(text=labels["booking_add"])],
            [KeyboardButton(text=labels["booking_delete"])],
            [KeyboardButton(text=labels["barbers"])],
            [KeyboardButton(text=labels["services"])],
        ],
    )


def admin_menu_texts(action: str) -> set[str]:
    base = {
        labels[action]
        for labels in _ADMIN_REPLY_MENU_LABELS.values()
        if action in labels
    }
    return base | _ADMIN_MENU_ALIASES.get(action, set())


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
    builder.button(text=_al(locale, "visits_today"), callback_data="admin:visit:list")
    builder.button(text=_al(locale, "booking_add"), callback_data="admin:booking:add")
    builder.button(text=_al(locale, "booking_delete"), callback_data="admin:booking:delete:list")
    builder.button(text=_al(locale, "barbers"), callback_data="admin:barber:list")
    builder.button(text=_al(locale, "services"), callback_data="admin:service:list")
    builder.adjust(1)
    return builder.as_markup()


def admin_booking_stats_menu_keyboard(locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_al(locale, "stats_horizon"), callback_data="admin:booking:stats:horizon")
    builder.button(text=_al(locale, "stats_week"), callback_data="admin:booking:stats:week")
    builder.button(text=_al(locale, "stats_date"), callback_data="admin:booking:stats:date")
    builder.button(text=_al(locale, "back_menu"), callback_data="admin:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_booking_stats_result_keyboard(locale: str, export_callback: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_al(locale, "export_excel"), callback_data=export_callback)
    builder.button(text=_al(locale, "stats_pick_other"), callback_data="admin:booking:list:today")
    builder.button(text=_al(locale, "back_menu"), callback_data="admin:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_booking_stats_calendar_keyboard(
    locale: str,
    *,
    year: int,
    month: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)

    builder.button(
        text="‹",
        callback_data=f"admin:booking:stats:date:month:{prev_year:04d}-{prev_month:02d}",
    )
    builder.button(text=f"{month:02d}.{year:04d}", callback_data="admin:noop")
    builder.button(
        text="›",
        callback_data=f"admin:booking:stats:date:month:{next_year:04d}-{next_month:02d}",
    )

    weekday_headers = _CALENDAR_WEEKDAYS["ru"]
    if locale in _CALENDAR_WEEKDAYS:
        weekday_headers = _CALENDAR_WEEKDAYS[locale]
    for header in weekday_headers:
        builder.button(text=header, callback_data="admin:noop")

    weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)
    for week in weeks:
        for day in week:
            if day == 0:
                builder.button(text="·", callback_data="admin:noop")
                continue
            builder.button(
                text=str(day),
                callback_data=f"admin:booking:stats:date:pick:{year:04d}-{month:02d}-{day:02d}",
            )

    builder.button(text=_al(locale, "stats_pick_other"), callback_data="admin:booking:list:today")
    builder.button(text=_al(locale, "back_menu"), callback_data="admin:menu")

    layout = [3, 7]
    layout.extend([7 for _ in weeks])
    layout.extend([1, 1])
    builder.adjust(*layout)
    return builder.as_markup()


def admin_visits_calendar_keyboard(
    locale: str,
    *,
    year: int,
    month: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)

    builder.button(
        text="‹",
        callback_data=f"admin:visit:date:month:{prev_year:04d}-{prev_month:02d}",
    )
    builder.button(text=f"{month:02d}.{year:04d}", callback_data="admin:noop")
    builder.button(
        text="›",
        callback_data=f"admin:visit:date:month:{next_year:04d}-{next_month:02d}",
    )

    weekday_headers = _CALENDAR_WEEKDAYS["ru"]
    if locale in _CALENDAR_WEEKDAYS:
        weekday_headers = _CALENDAR_WEEKDAYS[locale]
    for header in weekday_headers:
        builder.button(text=header, callback_data="admin:noop")

    weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)
    for week in weeks:
        for day in week:
            if day == 0:
                builder.button(text="·", callback_data="admin:noop")
                continue
            builder.button(
                text=str(day),
                callback_data=f"admin:visit:list:date:{year:04d}-{month:02d}-{day:02d}",
            )

    builder.button(text=_al(locale, "back_menu"), callback_data="admin:menu")

    layout = [3, 7]
    layout.extend([7 for _ in weeks])
    layout.append(1)
    builder.adjust(*layout)
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
        name = _service_name(service, locale)
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
        name = _service_name(service, locale)
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


def admin_visits_list_keyboard(rows: list[tuple[int, str]], locale: str, local_day: date) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    day_token = local_day.isoformat()
    for booking_id, label in rows:
        builder.button(text=label, callback_data=f"admin:visit:pick:{booking_id}:{day_token}")
    builder.button(text=_al(locale, "back_menu"), callback_data="admin:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_visit_actions_keyboard(booking_id: int, status: str, locale: str, local_day: date) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    day_token = local_day.isoformat()
    if status == "confirmed":
        builder.button(
            text=_al(locale, "mark_completed"),
            callback_data=f"admin:visit:complete:{booking_id}:{day_token}",
        )
    elif status == "completed":
        builder.button(
            text=_al(locale, "revert_completed"),
            callback_data=f"admin:visit:revert:{booking_id}:{day_token}",
        )
    builder.button(text=_al(locale, "back_list"), callback_data=f"admin:visit:list:date:{day_token}")
    builder.button(text=_al(locale, "back_menu"), callback_data="admin:menu")
    builder.adjust(1)
    return builder.as_markup()
