from __future__ import annotations

from typing import Any

MESSAGES: dict[str, dict[str, str]] = {
    "ru": {
        "welcome": "Привет! Я бот для записи в барбершоп.",
        "choose_lang": "Выберите язык / Tilni tanlang",
        "ask_phone": "Отправьте номер телефона в формате +998901234567",
        "phone_saved": "Телефон сохранен.",
        "invalid_phone": "Неверный формат телефона. Пример: +998901234567",
        "help": "Команды: /book /my_bookings /cancel /lang /help",
        "need_phone_before_booking": "Перед записью сначала укажите номер телефона.",
        "choose_service": "Выберите услугу:",
        "choose_barber": "Выберите барбера:",
        "choose_date": "Выберите дату:",
        "choose_slot": "Выберите время:",
        "confirm_booking": "Подтвердить запись на {date_time}?",
        "booked": "Запись подтверждена: {date_time}",
        "booking_conflict": "Этот слот уже занят. Выберите другое время.",
        "no_slots": "Нет доступных слотов на выбранную дату.",
        "future_bookings": "Ваши будущие записи:",
        "no_future_bookings": "У вас нет будущих записей.",
        "cancelled": "Запись отменена.",
        "cancel_too_late": "Отмена недоступна менее чем за 2 часа.",
        "booking_not_found": "Запись не найдена.",
        "lang_updated": "Язык обновлен.",
        "admin_only": "Команда доступна только администратору.",
        "admin_help": (
            "Админ команды:\n"
            "/admin_today\n"
            "/admin_schedule <barber_id> <YYYY-MM-DD>\n"
            "/admin_block <barber_id> <YYYY-MM-DDTHH:MM> <duration_min> [note]\n"
            "/admin_service_add <duration_min> <price_minor> <name_ru>|<name_uz>\n"
            "/admin_service_toggle <service_id> <on|off>\n"
            "/admin_barber_toggle <barber_id> <on|off>"
        ),
        "admin_today": "Записи (сегодня + ближайшие дни):\n{rows}",
        "admin_today_empty": "Записей на сегодня и ближайшие дни нет.",
        "admin_today_row": (
            "#{booking_id} {time} {status}\n"
            "Мастер: {barber}\n"
            "Услуга: {service}\n"
            "Клиент: {username}\n"
            "Телефон: {phone}"
        ),
        "booking_status_confirmed": "подтверждена",
        "booking_status_blocked": "блок",
        "booking_status_cancelled": "отменена",
        "admin_done": "Готово.",
        "bad_admin_args": "Неверные аргументы команды.",
        "admin_menu_title": "Админ-панель",
        "admin_barbers_title": "Мастера:",
        "admin_services_title": "Услуги:",
        "admin_status_active": "Активен",
        "admin_status_inactive": "В архиве",
        "admin_barber_card": "Мастер: {name}\nСтатус: {status}",
        "admin_service_card": (
            "Услуга: {name}\n"
            "Длительность: {duration} мин\n"
            "Цена: {price}\n"
            "Статус: {status}"
        ),
        "admin_enter_barber_name": "Введите имя мастера:",
        "admin_barber_added": "Мастер добавлен.",
        "admin_barber_updated": "Имя мастера обновлено.",
        "admin_barber_archived": "Мастер архивирован.",
        "admin_barber_restored": "Мастер восстановлен.",
        "admin_shift_list": "Смены мастера {barber_name}:\n{rows}",
        "admin_shift_choose_weekday": "Выберите день недели для добавления смены:",
        "admin_shift_enter_range": "Введите интервал в формате HH:MM-HH:MM",
        "admin_shift_enter_range_with_day": "Введите интервал для {weekday} в формате HH:MM-HH:MM",
        "admin_weekly_shift_prompt": (
            "Отправьте недельный график (заменит текущие смены).\n"
            "Формат: каждая строка = <день> <интервалы|off>\n"
            "Дни: 1..7 (1=Пн, 7=Вс).\n"
            "Пример:\n"
            "1 10:00-14:00,15:00-19:00\n"
            "2 10:00-18:00\n"
            "3 off\n"
            "4 10:00-18:00\n"
            "5 10:00-18:00\n"
            "6 off\n"
            "7 off\n\n"
            "Текущий график:\n{rows}"
        ),
        "admin_weekly_shift_saved": "Недельный график обновлен.",
        "admin_weekly_shift_invalid": (
            "Не удалось разобрать график. Проверьте формат строк: <1..7> <HH:MM-HH:MM[,HH:MM-HH:MM]|off>"
        ),
        "admin_weekly_shift_missing_days": "Укажите все дни недели 1..7 ровно по одному разу.",
        "admin_shift_added": "Смена добавлена.",
        "admin_shift_deleted": "Смена удалена.",
        "admin_shift_add_failed": "Не удалось добавить смену (проверьте формат/пересечения).",
        "admin_shift_not_found": "Смена не найдена.",
        "admin_booking_add_phone": "Введите телефон клиента в формате +998901234567",
        "admin_booking_client_selected": "Клиент выбран: {username} | {phone}",
        "admin_booking_client_guest_created": "Клиент не найден. Создан guest-клиент по телефону {phone}.",
        "admin_booking_choose_client": "Выберите клиента:",
        "admin_booking_choose_service": "Выберите услугу для записи:",
        "admin_booking_choose_barber": "Выберите мастера:",
        "admin_booking_choose_date": "Выберите дату:",
        "admin_booking_choose_slot": "Выберите слот:",
        "admin_booking_confirm": "Подтвердить админ-запись на {date_time}?",
        "admin_booking_created": "Запись создана: {date_time}",
        "admin_booking_guest_no_reminders": (
            "У клиента нет Telegram-профиля. Напоминания клиенту в Telegram не будут отправлены."
        ),
        "admin_booking_delete_details": "Детали записей:\n{rows}",
        "admin_booking_delete_choose": "Выберите запись для удаления:",
        "admin_booking_delete_confirm": "Точно удалить запись #{booking_id}?",
        "admin_booking_deleted": "Запись удалена.",
        "admin_booking_not_found": "Запись не найдена.",
        "admin_service_delete_confirm": "Точно удалить услугу? Действие необратимо.",
        "admin_service_deleted": "Услуга удалена.",
        "admin_barber_delete_confirm": "Точно удалить мастера? Действие необратимо.",
        "admin_barber_deleted": "Мастер удален.",
        "admin_enter_service_ru_name": "Введите название услуги на русском:",
        "admin_enter_service_uz_name": "Введите название услуги на узбекском:",
        "admin_enter_service_duration": "Введите длительность (минуты):",
        "admin_enter_service_price": "Введите цену (в minor units):",
        "admin_service_added": "Услуга добавлена.",
        "admin_service_updated": "Услуга обновлена.",
        "admin_service_archived": "Услуга архивирована.",
        "admin_service_restored": "Услуга восстановлена.",
        "admin_invalid_number": "Введите корректное число.",
        "admin_invalid_time_range": "Неверный формат времени. Пример: 10:00-14:30",
        "admin_item_not_found": "Элемент не найден.",
        "admin_list_empty": "Список пуст.",
        "next_step_hint": "Следующий шаг: {value}",
        "next_step_admin_menu": "выберите нужный раздел в админ-меню.",
        "next_step_choose_service": "выберите услугу.",
        "next_step_choose_barber": "выберите мастера.",
        "next_step_choose_date": "выберите дату.",
        "next_step_choose_slot": "выберите время.",
        "next_step_confirm": "подтвердите действие кнопкой ниже.",
        "next_step_enter_phone": "введите телефон клиента в формате +998....",
        "next_step_delete_pick": "выберите запись, которую нужно удалить.",
        "next_step_back_menu": "вернитесь в меню или продолжите с текущим разделом.",
        "no_available_dates": "Нет доступных дат для выбранного мастера и услуги.",
        "booking_conflict_refresh": "Слот занят. Показал обновленные доступные даты.",
        "reminder_24h": "Напоминание: ваша запись {date_time} (через 24 часа).",
        "reminder_2h": "Напоминание: ваша запись {date_time} (через 2 часа).",
        "reminder_30m": "Напоминание: ваша запись {date_time} (через 30 минут).",
    },
    "uz": {
        "welcome": "Salom! Men barber shop yozuv botiman.",
        "choose_lang": "Tilni tanlang / Выберите язык",
        "ask_phone": "Telefon raqamingizni yuboring: +998901234567",
        "phone_saved": "Telefon saqlandi.",
        "invalid_phone": "Telefon formati noto'g'ri. Masalan: +998901234567",
        "help": "Buyruqlar: /book /my_bookings /cancel /lang /help",
        "need_phone_before_booking": "Yozilishdan oldin telefon kiriting.",
        "choose_service": "Xizmatni tanlang:",
        "choose_barber": "Sartaroshni tanlang:",
        "choose_date": "Sanani tanlang:",
        "choose_slot": "Vaqtni tanlang:",
        "confirm_booking": "{date_time} ga yozilishni tasdiqlaysizmi?",
        "booked": "Yozuv tasdiqlandi: {date_time}",
        "booking_conflict": "Bu vaqt band. Boshqa vaqt tanlang.",
        "no_slots": "Tanlangan sanada bo'sh vaqt yo'q.",
        "future_bookings": "Kelgusi yozuvlaringiz:",
        "no_future_bookings": "Kelgusi yozuvlar yo'q.",
        "cancelled": "Yozuv bekor qilindi.",
        "cancel_too_late": "Yozuvni 2 soatdan kam qolganda bekor qilib bo'lmaydi.",
        "booking_not_found": "Yozuv topilmadi.",
        "lang_updated": "Til yangilandi.",
        "admin_only": "Buyruq faqat admin uchun.",
        "admin_help": (
            "Admin buyruqlar:\n"
            "/admin_today\n"
            "/admin_schedule <barber_id> <YYYY-MM-DD>\n"
            "/admin_block <barber_id> <YYYY-MM-DDTHH:MM> <duration_min> [note]\n"
            "/admin_service_add <duration_min> <price_minor> <name_ru>|<name_uz>\n"
            "/admin_service_toggle <service_id> <on|off>\n"
            "/admin_barber_toggle <barber_id> <on|off>"
        ),
        "admin_today": "Yozuvlar (bugun + yaqin kunlar):\n{rows}",
        "admin_today_empty": "Bugun va yaqin kunlarda yozuvlar yo'q.",
        "admin_today_row": (
            "#{booking_id} {time} {status}\n"
            "Usta: {barber}\n"
            "Xizmat: {service}\n"
            "Mijoz: {username}\n"
            "Telefon: {phone}"
        ),
        "booking_status_confirmed": "tasdiqlangan",
        "booking_status_blocked": "bandlangan",
        "booking_status_cancelled": "bekor qilingan",
        "admin_done": "Bajarildi.",
        "bad_admin_args": "Buyruq argumentlari noto'g'ri.",
        "admin_menu_title": "Admin panel",
        "admin_barbers_title": "Sartaroshlar:",
        "admin_services_title": "Xizmatlar:",
        "admin_status_active": "Faol",
        "admin_status_inactive": "Arxivda",
        "admin_barber_card": "Sartarosh: {name}\nHolat: {status}",
        "admin_service_card": (
            "Xizmat: {name}\n"
            "Davomiyligi: {duration} daqiqa\n"
            "Narx: {price}\n"
            "Holat: {status}"
        ),
        "admin_enter_barber_name": "Sartarosh ismini kiriting:",
        "admin_barber_added": "Sartarosh qo'shildi.",
        "admin_barber_updated": "Sartarosh nomi yangilandi.",
        "admin_barber_archived": "Sartarosh arxivlandi.",
        "admin_barber_restored": "Sartarosh tiklandi.",
        "admin_shift_list": "Usta {barber_name} smenalari:\n{rows}",
        "admin_shift_choose_weekday": "Smena qo'shish uchun hafta kunini tanlang:",
        "admin_shift_enter_range": "Oraliqni HH:MM-HH:MM formatida kiriting",
        "admin_shift_enter_range_with_day": "{weekday} uchun oraliqni HH:MM-HH:MM formatida kiriting",
        "admin_weekly_shift_prompt": (
            "Haftalik jadvalni yuboring (joriy smenalar almashtiriladi).\n"
            "Format: har qatorda = <kun> <oraliqlar|off>\n"
            "Kunlar: 1..7 (1=Dushanba, 7=Yakshanba).\n"
            "Misol:\n"
            "1 10:00-14:00,15:00-19:00\n"
            "2 10:00-18:00\n"
            "3 off\n"
            "4 10:00-18:00\n"
            "5 10:00-18:00\n"
            "6 off\n"
            "7 off\n\n"
            "Joriy jadval:\n{rows}"
        ),
        "admin_weekly_shift_saved": "Haftalik jadval yangilandi.",
        "admin_weekly_shift_invalid": (
            "Jadvalni o'qib bo'lmadi. Qator formatini tekshiring: <1..7> <HH:MM-HH:MM[,HH:MM-HH:MM]|off>"
        ),
        "admin_weekly_shift_missing_days": "1..7 haftaning barcha kunlarini bittadan kiriting.",
        "admin_shift_added": "Smena qo'shildi.",
        "admin_shift_deleted": "Smena o'chirildi.",
        "admin_shift_add_failed": "Smenani qo'shib bo'lmadi (format/ustma-ustlikni tekshiring).",
        "admin_shift_not_found": "Smena topilmadi.",
        "admin_booking_add_phone": "Mijoz telefonini +998901234567 formatida kiriting",
        "admin_booking_client_selected": "Mijoz tanlandi: {username} | {phone}",
        "admin_booking_client_guest_created": "Mijoz topilmadi. {phone} bo'yicha guest-mijoz yaratildi.",
        "admin_booking_choose_client": "Mijozni tanlang:",
        "admin_booking_choose_service": "Yozuv uchun xizmatni tanlang:",
        "admin_booking_choose_barber": "Ustani tanlang:",
        "admin_booking_choose_date": "Sanani tanlang:",
        "admin_booking_choose_slot": "Vaqtni tanlang:",
        "admin_booking_confirm": "{date_time} uchun admin yozuvini tasdiqlaysizmi?",
        "admin_booking_created": "Yozuv yaratildi: {date_time}",
        "admin_booking_guest_no_reminders": (
            "Mijozda Telegram profil yo'q. Telegram eslatmalari yuborilmaydi."
        ),
        "admin_booking_delete_details": "Yozuv tafsilotlari:\n{rows}",
        "admin_booking_delete_choose": "O'chirish uchun yozuvni tanlang:",
        "admin_booking_delete_confirm": "#{booking_id} yozuvini o'chirishni tasdiqlaysizmi?",
        "admin_booking_deleted": "Yozuv o'chirildi.",
        "admin_booking_not_found": "Yozuv topilmadi.",
        "admin_service_delete_confirm": "Xizmatni o'chirishni tasdiqlaysizmi? Amalni qaytarib bo'lmaydi.",
        "admin_service_deleted": "Xizmat o'chirildi.",
        "admin_barber_delete_confirm": "Ustani o'chirishni tasdiqlaysizmi? Amalni qaytarib bo'lmaydi.",
        "admin_barber_deleted": "Usta o'chirildi.",
        "admin_enter_service_ru_name": "Xizmat nomini rus tilida kiriting:",
        "admin_enter_service_uz_name": "Xizmat nomini o'zbek tilida kiriting:",
        "admin_enter_service_duration": "Davomiyligini kiriting (daqiqa):",
        "admin_enter_service_price": "Narxni kiriting (minor units):",
        "admin_service_added": "Xizmat qo'shildi.",
        "admin_service_updated": "Xizmat yangilandi.",
        "admin_service_archived": "Xizmat arxivlandi.",
        "admin_service_restored": "Xizmat tiklandi.",
        "admin_invalid_number": "To'g'ri son kiriting.",
        "admin_invalid_time_range": "Vaqt formati noto'g'ri. Masalan: 10:00-14:30",
        "admin_item_not_found": "Element topilmadi.",
        "admin_list_empty": "Ro'yxat bo'sh.",
        "next_step_hint": "Keyingi qadam: {value}",
        "next_step_admin_menu": "admin menyudan bo'lim tanlang.",
        "next_step_choose_service": "xizmatni tanlang.",
        "next_step_choose_barber": "ustani tanlang.",
        "next_step_choose_date": "sanani tanlang.",
        "next_step_choose_slot": "vaqtni tanlang.",
        "next_step_confirm": "pastdagi tugma bilan tasdiqlang.",
        "next_step_enter_phone": "mijoz telefonini +998... formatida kiriting.",
        "next_step_delete_pick": "o'chirish kerak bo'lgan yozuvni tanlang.",
        "next_step_back_menu": "menyuga qayting yoki shu bo'limda davom eting.",
        "no_available_dates": "Tanlangan usta va xizmat uchun bo'sh sana yo'q.",
        "booking_conflict_refresh": "Vaqt band. Yangilangan bo'sh sanalar ko'rsatildi.",
        "reminder_24h": "Eslatma: yozuvingiz {date_time} (24 soatdan keyin).",
        "reminder_2h": "Eslatma: yozuvingiz {date_time} (2 soatdan keyin).",
        "reminder_30m": "Eslatma: yozuvingiz {date_time} (30 daqiqadan keyin).",
    },
}


def tr(locale: str | None, key: str, **kwargs: Any) -> str:
    lang = locale if locale in MESSAGES else "ru"
    template = MESSAGES[lang].get(key, MESSAGES["ru"].get(key, key))
    return template.format(**kwargs)
