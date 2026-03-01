from __future__ import annotations

from typing import Any

MESSAGES: dict[str, dict[str, str]] = {
    "ru": {
        "welcome": "Привет! Я бот для записи в барбершоп.",
        "choose_lang": "Выберите язык / Тилни танланг / Забонро интихоб кунед",
        "ask_phone": "Отправьте номер телефона в формате +992901234567",
        "phone_saved": "Телефон сохранен.",
        "invalid_phone": "Неверный формат телефона. Пример: +992901234567",
        "help": "Команды: /book /my_bookings /cancel /lang /help",
        "need_phone_before_booking": "Перед записью сначала укажите номер телефона.",
        "choose_service": "Выберите услугу:",
        "choose_barber": "Выберите барбера:",
        "choose_date": "Выберите дату:",
        "choose_slot": "Выберите время:",
        "confirm_booking": "Подтвердить запись на {date_time}?",
        "booked": "Запись подтверждено: {date_time}",
        "booking_conflict": "Этот слот уже занят. Выберите другое время.",
        "no_slots": "Нет доступных слотов на выбранную дату.",
        "future_bookings": "Ваши будущие записи:",
        "no_future_bookings": "У вас нет будущих записей.",
        "cancelled": "Запись отменена.",
        "cancel_too_late": "Отмена недоступна менее чем за 2 часа.",
        "booking_not_found": "Запись не найдена.",
        "lang_updated": "Язык обновлен.",
        "unsupported_locale": "Неподдерживаемый язык.",
        "no_services_configured": "Услуги пока не настроены.",
        "service_not_found": "Услуга не найдена.",
        "barber_not_found": "Мастер не найден.",
        "no_active_barbers": "Нет активных мастеров.",
        "no_active_services": "Нет активных услуг.",
        "flow_expired_book": "Сценарий истек. Запустите /book заново.",
        "flow_expired_admin": "Сценарий истек. Откройте /admin заново.",
        "slot_expired_reopen": "Слот устарел. Выберите дату заново.",
        "slot_expired_admin": "Слот устарел. Выберите заново.",
        "draft_expired_book": "Подтверждение истекло. Запустите /book заново.",
        "draft_expired_admin": "Подтверждение истекло. Запустите сценарий заново.",
        "forbidden": "Недостаточно прав для этого действия.",
        "slot_no_longer_valid": "Слот больше не актуален.",
        "conflict": "Конфликт слота: время уже занято.",
        "booking_row": (
            "#{booking_id} | {date_time}\n"
            "Мастер: {barber}\n"
            "Услуга: {service}"
        ),
        "admin_only": "Команда доступна только администратору.",
        "admin_help": (
            "Админ команды:\n"
            "/admin_today\n"
            "/admin_visits\n"
            "/admin_schedule <barber_id> <YYYY-MM-DD>\n"
            "/admin_block <barber_id> <YYYY-MM-DDTHH:MM> <duration_min> [note]\n"
            "/admin_service_add <duration_min> <price_minor> <name_ru>|<name_uz>|[name_tj]\n"
            "/admin_service_toggle <service_id> <on|off>\n"
            "/admin_barber_toggle <barber_id> <on|off>"
        ),
        "admin_today": "Статистика записей :\n{rows}",
        "admin_today_empty": "Записей на сегодня и ближайшие дни нет.",
        "admin_today_row": (
            "#{booking_id} {time} {status}\n"
            "Мастер: {barber}\n"
            "Услуга: {service}\n"
            "Клиент: {username}\n"
            "Телефон: {phone}"
        ),
        "booking_status_confirmed": "подтверждено",
        "booking_status_completed": "обслужено",
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
            "Дни: 1..7 или Пн..Вс (1=Пн, 7=Вс).\n"
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
            "Не удалось разобрать график. Проверьте формат строк: "
            "<1..7|Пн..Вс> <HH:MM-HH:MM[,HH:MM-HH:MM]|off>"
        ),
        "admin_weekly_shift_missing_days": "Укажите все дни недели 1..7 ровно по одному разу.",
        "admin_shift_added": "Смена добавлена.",
        "admin_shift_deleted": "Смена удалена.",
        "admin_shift_add_failed": "Не удалось добавить смену (проверьте формат/пересечения).",
        "admin_shift_not_found": "Смена не найдена.",
        "admin_booking_add_phone": "Введите телефон клиента в формате +992901234567",
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
        "admin_booking_stats_choose": "Выберите тип статистики:",
        "admin_booking_stats_enter_date": "Введите дату в формате YYYY-MM-DD (например, 2026-02-20):",
        "admin_booking_stats_pick_date": (
            "Выберите дату в календаре ниже.\n"
            "Можно также ввести вручную в формате YYYY-MM-DD."
        ),
        "admin_booking_stats_invalid_date": "Неверная дата. Используйте формат YYYY-MM-DD.",
        "admin_booking_stats_summary": (
            "Статистика за период {from_date} - {to_date}:\n"
            "Всего записей: {total}\n"
            "Подтверждено: {confirmed}\n"
            "Обслужено: {completed}\n"
            "Отменено: {cancelled}\n"
            "Блокировок: {blocked}\n"
            "Касса (обслужено): {cash_total} TJS"
        ),
        "admin_booking_stats_rows": "Детальные записи за период:\n{rows}",
        "admin_booking_stats_empty": "За период {from_date} - {to_date} записей нет.",
        "admin_export_done": "Excel выгружен: {from_date} - {to_date}, записей: {total}, касса: {cash_total} TJS.",
        "admin_export_failed": "Не удалось сформировать Excel-файл.",
        "admin_today_cash_summary": "Касса за сегодня (обслужено): {cash_total} TJS",
        "admin_visits_today_title": "Визиты на сегодня:",
        "admin_visits_today_empty": "На сегодня записей для визитов нет.",
        "admin_visits_pick_date": "Выберите дату в календаре ниже.",
        "admin_visits_enter_date": "Можно также ввести дату вручную в формате YYYY-MM-DD.",
        "admin_visits_invalid_date": "Неверная дата. Используйте формат YYYY-MM-DD.",
        "admin_visits_title": "Визиты на {date}:",
        "admin_visits_empty": "На {date} записей для визитов нет.",
        "admin_visits_choose": "Выберите запись для отметки обслуживания:",
        "admin_visit_card": (
            "#{booking_id} {time} {status}\n"
            "Мастер: {barber}\n"
            "Услуга: {service}\n"
            "Клиент: {username}\n"
            "Телефон: {phone}"
        ),
        "admin_visit_completed": "Обслуживание подтверждено.",
        "admin_visit_reverted": "Отметка обслуживания снята.",
        "admin_visit_action_not_allowed": "Для этой записи действие недоступно.",
        "admin_booking_delete_details": "Детали записей:\n{rows}",
        "admin_booking_delete_choose": "Выберите запись для удаления:",
        "admin_booking_delete_confirm": "Точно удалить запись #{booking_id}?",
        "admin_booking_deleted": "Запись удалена.",
        "admin_booking_not_found": "Запись не найдена.",
        "admin_booking_delete_no_deletable": (
            "Нет доступных для удаления записей. "
            "Записи со статусом 'обслужено' удалять нельзя."
        ),
        "admin_booking_delete_completed_forbidden": (
            "Нельзя удалить запись со статусом 'обслужено'."
        ),
        "admin_service_delete_confirm": "Точно удалить услугу? Действие необратимо.",
        "admin_service_deleted": "Услуга удалена.",
        "admin_barber_delete_confirm": "Точно удалить мастера? Действие необратимо.",
        "admin_barber_deleted": "Мастер удален.",
        "admin_enter_service_ru_name": "Введите название услуги на русском:",
        "admin_enter_service_uz_name": "Введите название услуги на узбекском:",
        "admin_enter_service_tj_name": "Введите название услуги на таджикском:",
        "admin_enter_service_duration": "Введите длительность (минуты):",
        "admin_enter_service_price": "Введите цену (в minor units):",
        "admin_service_added": "Услуга добавлена.",
        "admin_service_updated": "Услуга обновлена.",
        "admin_service_archived": "Услуга архивирована.",
        "admin_service_restored": "Услуга восстановлена.",
        "admin_invalid_number": "Введите корректное число.",
        "admin_invalid_time_range": "Неверный формат времени. Пример: 10:00-14:30",
        "admin_schedule_overview": "Смены:\n{shifts}\n\nЗанято:\n{busy}",
        "admin_item_not_found": "Элемент не найден.",
        "admin_list_empty": "Список пуст.",
        "next_step_hint": "Следующий шаг: {value}",
        "next_step_admin_menu": "выберите нужный раздел в админ-меню.",
        "next_step_choose_service": "выберите услугу.",
        "next_step_choose_barber": "выберите мастера.",
        "next_step_choose_date": "выберите дату.",
        "next_step_choose_slot": "выберите время.",
        "next_step_confirm": "подтвердите действие кнопкой ниже.",
        "next_step_enter_phone": "введите телефон клиента в формате +992....",
        "next_step_delete_pick": "выберите запись, которую нужно удалить.",
        "next_step_back_menu": "вернитесь в меню или продолжите с текущим разделом.",
        "next_step_choose_stats": "выберите статистику: сегодня, неделя или конкретная дата.",
        "next_step_enter_stats_date": "введите дату в формате YYYY-MM-DD.",
        "next_step_pick_calendar_date": "выберите дату на календаре или введите YYYY-MM-DD.",
        "next_step_visit_pick": "выберите запись для отметки визита.",
        "next_step_visit_action": "подтвердите обслуживание или вернитесь к списку.",
        "no_available_dates": "Нет доступных дат для выбранного мастера и услуги.",
        "booking_conflict_refresh": "Слот занят. Показал обновленные доступные даты.",
        "reminder_24h": "Напоминание: ваша запись {date_time} (через 24 часа).",
        "reminder_2h": "Напоминание: ваша запись {date_time} (через 2 часа).",
        "reminder_30m": "Напоминание: ваша запись {date_time} (через 30 минут).",
    },
    "uz": {
        "welcome": "Салом! Мен барбершопга ёзув ботиман.",
        "choose_lang": "Тилни танланг / Выберите язык / Забонро интихоб кунед",
        "ask_phone": "Телефон рақамингизни юборинг: +992901234567",
        "phone_saved": "Телефон сақланди.",
        "invalid_phone": "Телефон формати нотўғри. Масалан: +992901234567",
        "help": "Буйруқлар: /book /my_bookings /cancel /lang /help",
        "need_phone_before_booking": "Ёзилишдан олдин телефон киритинг.",
        "choose_service": "Хизматни танланг:",
        "choose_barber": "Сартарошни танланг:",
        "choose_date": "Санани танланг:",
        "choose_slot": "Вақтни танланг:",
        "confirm_booking": "{date_time} га ёзилишни тасдиқлайсизми?",
        "booked": "Ёзув тасдиқланди: {date_time}",
        "booking_conflict": "Бу вақт банд. Бошқа вақтни танланг.",
        "no_slots": "Танланган санада бўш вақт йўқ.",
        "future_bookings": "Келгуси ёзувларингиз:",
        "no_future_bookings": "Келгуси ёзувлар йўқ.",
        "cancelled": "Ёзув бекор қилинди.",
        "cancel_too_late": "Ёзувни 2 соатдан кам қолганда бекор қилиб бўлмайди.",
        "booking_not_found": "Ёзув топилмади.",
        "lang_updated": "Тил янгиланди.",
        "unsupported_locale": "Қўллаб-қувватланмайдиган тил.",
        "no_services_configured": "Хизматлар ҳали созланмаган.",
        "service_not_found": "Хизмат топилмади.",
        "barber_not_found": "Уста топилмади.",
        "no_active_barbers": "Фаол усталар йўқ.",
        "no_active_services": "Фаол хизматлар йўқ.",
        "flow_expired_book": "Сценарий тугади. /book ни қайта бошланг.",
        "flow_expired_admin": "Сценарий тугади. /admin ни қайта очинг.",
        "slot_expired_reopen": "Слот эскирди. Санани қайта танланг.",
        "slot_expired_admin": "Слот эскирди. Қайта танланг.",
        "draft_expired_book": "Тасдиқлаш муддати тугади. /book ни қайта бошланг.",
        "draft_expired_admin": "Тасдиқлаш муддати тугади. Сценарийни қайта бошланг.",
        "forbidden": "Бу амал учун рухсат йўқ.",
        "slot_no_longer_valid": "Бу слот энди яроқсиз.",
        "conflict": "Слот конфликти: вақт банд.",
        "booking_row": (
            "#{booking_id} | {date_time}\n"
            "Уста: {barber}\n"
            "Хизмат: {service}"
        ),
        "admin_only": "Буйруқ фақат админ учун.",
        "admin_help": (
            "Админ буйруқлар:\n"
            "/admin_today\n"
            "/admin_visits\n"
            "/admin_schedule <barber_id> <YYYY-MM-DD>\n"
            "/admin_block <barber_id> <YYYY-MM-DDTHH:MM> <duration_min> [note]\n"
            "/admin_service_add <duration_min> <price_minor> <name_ru>|<name_uz>|[name_tj]\n"
            "/admin_service_toggle <service_id> <on|off>\n"
            "/admin_barber_toggle <barber_id> <on|off>"
        ),
        "admin_today": "Ёзувлар (бугун + яқин кунлар):\n{rows}",
        "admin_today_empty": "Бугун ва яқин кунларда ёзувлар йўқ.",
        "admin_today_row": (
            "#{booking_id} {time} {status}\n"
            "Уста: {barber}\n"
            "Хизмат: {service}\n"
            "Мижоз: {username}\n"
            "Телефон: {phone}"
        ),
        "booking_status_confirmed": "тасдиқланган",
        "booking_status_completed": "хизмат кўрсатилган",
        "booking_status_blocked": "бандланган",
        "booking_status_cancelled": "бекор қилинган",
        "admin_done": "Бажарилди.",
        "bad_admin_args": "Буйруқ аргументлари нотўғри.",
        "admin_menu_title": "Админ панел",
        "admin_barbers_title": "Сартарошлар:",
        "admin_services_title": "Хизматлар:",
        "admin_status_active": "Фаол",
        "admin_status_inactive": "Архивда",
        "admin_barber_card": "Сартарош: {name}\nҲолат: {status}",
        "admin_service_card": (
            "Хизмат: {name}\n"
            "Давомийлиги: {duration} дақиқа\n"
            "Нарх: {price}\n"
            "Ҳолат: {status}"
        ),
        "admin_enter_barber_name": "Сартарош исмини киритинг:",
        "admin_barber_added": "Сартарош қўшилди.",
        "admin_barber_updated": "Сартарош номи янгиланди.",
        "admin_barber_archived": "Сартарош архивланди.",
        "admin_barber_restored": "Сартарош тикланди.",
        "admin_shift_list": "Уста {barber_name} сменалари:\n{rows}",
        "admin_shift_choose_weekday": "Смена қўшиш учун ҳафта кунини танланг:",
        "admin_shift_enter_range": "Оралиқни HH:MM-HH:MM форматида киритинг",
        "admin_shift_enter_range_with_day": "{weekday} учун оралиқни HH:MM-HH:MM форматида киритинг",
        "admin_weekly_shift_prompt": (
            "Ҳафталик жадвални юборинг (жорий сменалар алмаштирилади).\n"
            "Формат: ҳар қаторда = <кун> <оралиқлар|off>\n"
            "Кунлар: 1..7 ёки Ду..Як (1=Душанба, 7=Якшанба).\n"
            "Мисол:\n"
            "1 10:00-14:00,15:00-19:00\n"
            "2 10:00-18:00\n"
            "3 off\n"
            "4 10:00-18:00\n"
            "5 10:00-18:00\n"
            "6 off\n"
            "7 off\n\n"
            "Жорий жадвал:\n{rows}"
        ),
        "admin_weekly_shift_saved": "Ҳафталик жадвал янгиланди.",
        "admin_weekly_shift_invalid": (
            "Жадвални ўқиб бўлмади. Қатор форматини текширинг: "
            "<1..7|Ду..Як> <HH:MM-HH:MM[,HH:MM-HH:MM]|off>"
        ),
        "admin_weekly_shift_missing_days": "1..7 ҳафтанинг барча кунларини биттадан киритинг.",
        "admin_shift_added": "Смена қўшилди.",
        "admin_shift_deleted": "Смена ўчирилди.",
        "admin_shift_add_failed": "Сменани қўшиб бўлмади (формат/устма-устликни текширинг).",
        "admin_shift_not_found": "Смена топилмади.",
        "admin_booking_add_phone": "Мижоз телефонини +992901234567 форматида киритинг",
        "admin_booking_client_selected": "Мижоз танланди: {username} | {phone}",
        "admin_booking_client_guest_created": "Мижоз топилмади. {phone} бўйича guest-мижоз яратилди.",
        "admin_booking_choose_client": "Мижозни танланг:",
        "admin_booking_choose_service": "Ёзув учун хизматни танланг:",
        "admin_booking_choose_barber": "Устани танланг:",
        "admin_booking_choose_date": "Санани танланг:",
        "admin_booking_choose_slot": "Вақтни танланг:",
        "admin_booking_confirm": "{date_time} учун админ ёзувини тасдиқлайсизми?",
        "admin_booking_created": "Ёзув яратилди: {date_time}",
        "admin_booking_guest_no_reminders": (
            "Мижозда Telegram профил йўқ. Telegram эслатмалари юборилмайди."
        ),
        "admin_booking_stats_choose": "Статистика турини танланг:",
        "admin_booking_stats_enter_date": "Санани YYYY-MM-DD форматида киритинг (масалан, 2026-02-20):",
        "admin_booking_stats_pick_date": (
            "Қуйидаги календардан санани танланг.\n"
            "Ёки YYYY-MM-DD форматида қўлда киритинг."
        ),
        "admin_booking_stats_invalid_date": "Сана нотўғри. YYYY-MM-DD форматидан фойдаланинг.",
        "admin_booking_stats_summary": (
            "{from_date} - {to_date} даври статистикаси:\n"
            "Жами ёзувлар: {total}\n"
            "Тасдиқланган: {confirmed}\n"
            "Хизмат кўрсатилган: {completed}\n"
            "Бекор қилинган: {cancelled}\n"
            "Бандланган: {blocked}\n"
            "Касса (хизмат): {cash_total} TJS"
        ),
        "admin_booking_stats_rows": "Давр бўйича батафсил ёзувлар:\n{rows}",
        "admin_booking_stats_empty": "{from_date} - {to_date} даврида ёзувлар йўқ.",
        "admin_export_done": "Excel юкланди: {from_date} - {to_date}, ёзувлар: {total}, касса: {cash_total} TJS.",
        "admin_export_failed": "Excel файлини яратиб бўлмади.",
        "admin_today_cash_summary": "Бугунги касса (хизмат): {cash_total} TJS",
        "admin_visits_today_title": "Бугунги ташрифлар:",
        "admin_visits_today_empty": "Бугун ташрифлар учун ёзувлар йўқ.",
        "admin_visits_pick_date": "Қуйидаги календардан санани танланг.",
        "admin_visits_enter_date": "Ёки YYYY-MM-DD форматида санани қўлда киритинг.",
        "admin_visits_invalid_date": "Сана нотўғри. YYYY-MM-DD форматидан фойдаланинг.",
        "admin_visits_title": "{date} куниги ташрифлар:",
        "admin_visits_empty": "{date} куни учун ташриф ёзувлари йўқ.",
        "admin_visits_choose": "Хизмат белгилаш учун ёзувни танланг:",
        "admin_visit_card": (
            "#{booking_id} {time} {status}\n"
            "Уста: {barber}\n"
            "Хизмат: {service}\n"
            "Мижоз: {username}\n"
            "Телефон: {phone}"
        ),
        "admin_visit_completed": "Хизмат тасдиқланди.",
        "admin_visit_reverted": "Хизмат тасдиғи бекор қилинди.",
        "admin_visit_action_not_allowed": "Бу ёзув учун амал мавжуд эмас.",
        "admin_booking_delete_details": "Ёзув тафсилотлари:\n{rows}",
        "admin_booking_delete_choose": "Ўчириш учун ёзувни танланг:",
        "admin_booking_delete_confirm": "#{booking_id} ёзувини ўчиришни тасдиқлайсизми?",
        "admin_booking_deleted": "Ёзув ўчирилди.",
        "admin_booking_not_found": "Ёзув топилмади.",
        "admin_booking_delete_no_deletable": (
            "Ўчириш учун ёзувлар йўқ. "
            "'хизмат кўрсатилган' ҳолатдаги ёзувни ўчириб бўлмайди."
        ),
        "admin_booking_delete_completed_forbidden": (
            "'хизмат кўрсатилган' ҳолатдаги ёзувни ўчириб бўлмайди."
        ),
        "admin_service_delete_confirm": "Хизматни ўчиришни тасдиқлайсизми? Амални қайтариб бўлмайди.",
        "admin_service_deleted": "Хизмат ўчирилди.",
        "admin_barber_delete_confirm": "Устани ўчиришни тасдиқлайсизми? Амални қайтариб бўлмайди.",
        "admin_barber_deleted": "Уста ўчирилди.",
        "admin_enter_service_ru_name": "Хизмат номини рус тилида киритинг:",
        "admin_enter_service_uz_name": "Хизмат номини ўзбек тилида киритинг:",
        "admin_enter_service_tj_name": "Хизмат номини тожик тилида киритинг:",
        "admin_enter_service_duration": "Давомийлигини киритинг (дақиқа):",
        "admin_enter_service_price": "Нархни киритинг (minor units):",
        "admin_service_added": "Хизмат қўшилди.",
        "admin_service_updated": "Хизмат янгиланди.",
        "admin_service_archived": "Хизмат архивланди.",
        "admin_service_restored": "Хизмат тикланди.",
        "admin_invalid_number": "Тўғри сон киритинг.",
        "admin_invalid_time_range": "Вақт формати нотўғри. Масалан: 10:00-14:30",
        "admin_schedule_overview": "Сменалар:\n{shifts}\n\nБанд вақт:\n{busy}",
        "admin_item_not_found": "Элемент топилмади.",
        "admin_list_empty": "Рўйхат бўш.",
        "next_step_hint": "Кейинги қадам: {value}",
        "next_step_admin_menu": "админ менюдан бўлим танланг.",
        "next_step_choose_service": "хизматни танланг.",
        "next_step_choose_barber": "устани танланг.",
        "next_step_choose_date": "санани танланг.",
        "next_step_choose_slot": "вақтни танланг.",
        "next_step_confirm": "пастдаги тугма билан тасдиқланг.",
        "next_step_enter_phone": "мижоз телефонини +992... форматида киритинг.",
        "next_step_delete_pick": "ўчириш керак бўлган ёзувни танланг.",
        "next_step_back_menu": "менюга қайтинг ёки шу бўлимда давом этинг.",
        "next_step_choose_stats": "статистикани танланг: бугун, ҳафта ёки аниқ сана.",
        "next_step_enter_stats_date": "санани YYYY-MM-DD форматида киритинг.",
        "next_step_pick_calendar_date": "календардан санани танланг ёки YYYY-MM-DD киритинг.",
        "next_step_visit_pick": "ташриф белгилаш учун ёзувни танланг.",
        "next_step_visit_action": "хизматни тасдиқланг ёки рўйхатга қайтинг.",
        "no_available_dates": "Танланган уста ва хизмат учун бўш сана йўқ.",
        "booking_conflict_refresh": "Вақт банд. Янгиланган бўш саналар кўрсатилди.",
        "reminder_24h": "Эслатма: ёзувингиз {date_time} (24 соатдан кейин).",
        "reminder_2h": "Эслатма: ёзувингиз {date_time} (2 соатдан кейин).",
        "reminder_30m": "Эслатма: ёзувингиз {date_time} (30 дақиқадан кейин).",
    },
}


_TJ_MESSAGES: dict[str, str] = {
    "welcome": "Салом! Ман боти сабт барои барбершоп ҳастам.",
    "choose_lang": "Забонро интихоб кунед / Выберите язык / Тилни танланг",
    "ask_phone": "Рақами телефонро дар формат фиристед: +992901234567",
    "phone_saved": "Телефон захира шуд.",
    "invalid_phone": "Формати телефон нодуруст аст. Намуна: +992901234567",
    "help": "Фармонҳо: /book /my_bookings /cancel /lang /help",
    "need_phone_before_booking": "Пеш аз сабт аввал рақами телефонро ворид кунед.",
    "choose_service": "Хизматро интихоб кунед:",
    "choose_barber": "Усторо интихоб кунед:",
    "choose_date": "Санаро интихоб кунед:",
    "choose_slot": "Вақтро интихоб кунед:",
    "confirm_booking": "Сабт барои {date_time}-ро тасдиқ мекунед?",
    "booked": "Сабт тасдиқ шуд: {date_time}",
    "booking_conflict": "Ин вақт банд аст. Вақти дигарро интихоб кунед.",
    "no_slots": "Дар санаи интихобшуда вақти холӣ нест.",
    "future_bookings": "Сабтҳои ояндаи шумо:",
    "no_future_bookings": "Шумо сабти оянда надоред.",
    "cancelled": "Сабт бекор шуд.",
    "cancel_too_late": "Камтар аз 2 соат монда бошад, бекоркунӣ дастрас нест.",
    "booking_not_found": "Сабт ёфт нашуд.",
    "lang_updated": "Забон нав карда шуд.",
    "unsupported_locale": "Забони дастгиринашаванда.",
    "no_services_configured": "Хизматҳо ҳоло танзим нашудаанд.",
    "service_not_found": "Хизмат ёфт нашуд.",
    "barber_not_found": "Усто ёфт нашуд.",
    "no_active_barbers": "Устоҳои фаъол вуҷуд надоранд.",
    "no_active_services": "Хизматҳои фаъол вуҷуд надоранд.",
    "flow_expired_book": "Раванд анҷом ёфт. /book-ро дубора оғоз кунед.",
    "flow_expired_admin": "Раванд анҷом ёфт. /admin-ро дубора боз кунед.",
    "slot_expired_reopen": "Слот кӯҳна шуд. Санаро аз нав интихоб кунед.",
    "slot_expired_admin": "Слот кӯҳна шуд. Аз нав интихоб кунед.",
    "draft_expired_book": "Муҳлати тасдиқ гузашт. /book-ро дубора оғоз кунед.",
    "draft_expired_admin": "Муҳлати тасдиқ гузашт. Равандро аз нав оғоз кунед.",
    "forbidden": "Барои ин амал ҳуқуқ надоред.",
    "slot_no_longer_valid": "Ин слот дигар актуалӣ нест.",
    "conflict": "Конфликти слот: вақт банд аст.",
    "booking_row": (
        "#{booking_id} | {date_time}\n"
        "Усто: {barber}\n"
        "Хизмат: {service}"
    ),
    "admin_only": "Фармон танҳо барои админ дастрас аст.",
    "admin_help": (
        "Фармонҳои админ:\n"
        "/admin_today\n"
        "/admin_visits\n"
        "/admin_schedule <barber_id> <YYYY-MM-DD>\n"
        "/admin_block <barber_id> <YYYY-MM-DDTHH:MM> <duration_min> [note]\n"
        "/admin_service_add <duration_min> <price_minor> <name_ru>|<name_uz>|[name_tj]\n"
        "/admin_service_toggle <service_id> <on|off>\n"
        "/admin_barber_toggle <barber_id> <on|off>"
    ),
    "admin_today": "Сабтҳо (имрӯз + рӯзҳои наздик):\n{rows}",
    "admin_today_empty": "Барои имрӯз ва рӯзҳои наздик сабт нест.",
    "admin_today_row": (
        "#{booking_id} {time} {status}\n"
        "Усто: {barber}\n"
        "Хизмат: {service}\n"
        "Мизоҷ: {username}\n"
        "Телефон: {phone}"
    ),
    "booking_status_confirmed": "тасдиқшуда",
    "booking_status_completed": "хизмат расонида шуд",
    "booking_status_blocked": "бандшуда",
    "booking_status_cancelled": "бекоршуда",
    "admin_done": "Омода.",
    "bad_admin_args": "Аргументҳои фармон нодурустанд.",
    "admin_menu_title": "Панели админ",
    "admin_barbers_title": "Устоҳо:",
    "admin_services_title": "Хизматҳо:",
    "admin_status_active": "Фаъол",
    "admin_status_inactive": "Дар бойгонӣ",
    "admin_barber_card": "Усто: {name}\nҲолат: {status}",
    "admin_service_card": (
        "Хизмат: {name}\n"
        "Давомнокӣ: {duration} дақ\n"
        "Нарх: {price}\n"
        "Ҳолат: {status}"
    ),
    "admin_enter_barber_name": "Номи усторо ворид кунед:",
    "admin_barber_added": "Усто илова шуд.",
    "admin_barber_updated": "Номи усто нав шуд.",
    "admin_barber_archived": "Усто ба бойгонӣ гузошта шуд.",
    "admin_barber_restored": "Усто барқарор шуд.",
    "admin_shift_list": "Сменаҳои усто {barber_name}:\n{rows}",
    "admin_shift_choose_weekday": "Рӯзи ҳафтаро барои иловаи смена интихоб кунед:",
    "admin_shift_enter_range": "Фосиларо дар формат HH:MM-HH:MM ворид кунед",
    "admin_shift_enter_range_with_day": "Фосиларо барои {weekday} дар формат HH:MM-HH:MM ворид кунед",
    "admin_weekly_shift_prompt": (
        "Ҷадвали ҳафтаинаро фиристед (сменаҳои ҷорӣ иваз мешаванд).\n"
        "Формат: ҳар сатр = <рӯз> <фосилаҳо|off>\n"
        "Рӯзҳо: 1..7 ё Дш..Як (1=Дш, 7=Якш).\n"
        "Мисол:\n"
        "1 10:00-14:00,15:00-19:00\n"
        "2 10:00-18:00\n"
        "3 off\n"
        "4 10:00-18:00\n"
        "5 10:00-18:00\n"
        "6 off\n"
        "7 off\n\n"
        "Ҷадвали ҷорӣ:\n{rows}"
    ),
    "admin_weekly_shift_saved": "Ҷадвали ҳафтаина нав шуд.",
    "admin_weekly_shift_invalid": (
        "Формати ҷадвал нодуруст аст. Санҷед: <1..7|Дш..Як> <HH:MM-HH:MM[,HH:MM-HH:MM]|off>"
    ),
    "admin_weekly_shift_missing_days": "Ҳамаи рӯзҳои 1..7 бояд як маротиба нишон дода шаванд.",
    "admin_shift_added": "Смена илова шуд.",
    "admin_shift_deleted": "Смена ҳазф шуд.",
    "admin_shift_add_failed": "Иловаи смена муваффақ нашуд (формат/буришро санҷед).",
    "admin_shift_not_found": "Смена ёфт нашуд.",
    "admin_booking_add_phone": "Телефони мизоҷро дар формат +992... ворид кунед",
    "admin_booking_client_selected": "Мизоҷ интихоб шуд: {username} | {phone}",
    "admin_booking_client_guest_created": "Мизоҷ ёфт нашуд. Guest-мизоҷ бо телефони {phone} сохта шуд.",
    "admin_booking_choose_client": "Мизоҷро интихоб кунед:",
    "admin_booking_choose_service": "Барои сабт хизматро интихоб кунед:",
    "admin_booking_choose_barber": "Усторо интихоб кунед:",
    "admin_booking_choose_date": "Санаро интихоб кунед:",
    "admin_booking_choose_slot": "Слотро интихоб кунед:",
    "admin_booking_confirm": "Сабти админро барои {date_time} тасдиқ мекунед?",
    "admin_booking_created": "Сабт сохта шуд: {date_time}",
    "admin_booking_guest_no_reminders": "Мизоҷ профили Telegram надорад. Ёдраскуниҳо фиристода намешаванд.",
    "admin_booking_stats_choose": "Навъи статистикаро интихоб кунед:",
    "admin_booking_stats_enter_date": "Санаро дар формат YYYY-MM-DD ворид кунед (мисол, 2026-02-20):",
    "admin_booking_stats_pick_date": (
        "Санаро дар тақвим интихоб кунед.\n"
        "Ё дастӣ дар формат YYYY-MM-DD ворид кунед."
    ),
    "admin_booking_stats_invalid_date": "Сана нодуруст аст. Формати YYYY-MM-DD-ро истифода баред.",
    "admin_booking_stats_summary": (
        "Статистика барои давраи {from_date} - {to_date}:\n"
        "Ҳамагӣ сабтҳо: {total}\n"
        "Тасдиқшуда: {confirmed}\n"
        "Хизмат расонида шуд: {completed}\n"
        "Бекоршуда: {cancelled}\n"
        "Бандшуда: {blocked}\n"
        "Касса (хизмат): {cash_total} TJS"
    ),
    "admin_booking_stats_rows": "Сабтҳои муфассали давра:\n{rows}",
    "admin_booking_stats_empty": "Дар давраи {from_date} - {to_date} сабт нест.",
    "admin_export_done": "Excel омода шуд: {from_date} - {to_date}, сабтҳо: {total}, касса: {cash_total} TJS.",
    "admin_export_failed": "Сохтани файли Excel муваффақ нашуд.",
    "admin_today_cash_summary": "Касса барои имрӯз (хизмат): {cash_total} TJS",
    "admin_visits_today_title": "Ташрифҳои имрӯз:",
    "admin_visits_today_empty": "Барои ташрифҳои имрӯз сабт нест.",
    "admin_visits_pick_date": "Санаро дар тақвими поён интихоб кунед.",
    "admin_visits_enter_date": "Ё санаро дастӣ дар формати YYYY-MM-DD ворид кунед.",
    "admin_visits_invalid_date": "Сана нодуруст аст. Формати YYYY-MM-DD-ро истифода баред.",
    "admin_visits_title": "Ташрифҳо барои {date}:",
    "admin_visits_empty": "Барои {date} сабт барои ташрифҳо нест.",
    "admin_visits_choose": "Барои қайди хизмат сабтро интихоб кунед:",
    "admin_visit_card": (
        "#{booking_id} {time} {status}\n"
        "Усто: {barber}\n"
        "Хизмат: {service}\n"
        "Мизоҷ: {username}\n"
        "Телефон: {phone}"
    ),
    "admin_visit_completed": "Хизмат тасдиқ шуд.",
    "admin_visit_reverted": "Тасдиқи хизмат бекор шуд.",
    "admin_visit_action_not_allowed": "Барои ин сабт амал дастрас нест.",
    "admin_booking_delete_details": "Тафсилоти сабтҳо:\n{rows}",
    "admin_booking_delete_choose": "Сабтро барои ҳазф интихоб кунед:",
    "admin_booking_delete_confirm": "Ҳазфи сабти #{booking_id}-ро тасдиқ мекунед?",
    "admin_booking_deleted": "Сабт ҳазф шуд.",
    "admin_booking_not_found": "Сабт ёфт нашуд.",
    "admin_booking_delete_no_deletable": (
        "Барои ҳазф сабт нест. "
        "Сабт бо ҳолати 'хизмат расонида шуд' ҳазф намешавад."
    ),
    "admin_booking_delete_completed_forbidden": (
        "Сабт бо ҳолати 'хизмат расонида шуд' ҳазф намешавад."
    ),
    "admin_service_delete_confirm": "Ҳазфи хизматро тасдиқ мекунед? Амал бозгашт надорад.",
    "admin_service_deleted": "Хизмат ҳазф шуд.",
    "admin_barber_delete_confirm": "Ҳазфи усторо тасдиқ мекунед? Амал бозгашт надорад.",
    "admin_barber_deleted": "Усто ҳазф шуд.",
    "admin_enter_service_ru_name": "Номи хизматро ба русӣ ворид кунед:",
    "admin_enter_service_uz_name": "Номи хизматро ба ӯзбекӣ ворид кунед:",
    "admin_enter_service_tj_name": "Номи хизматро ба тоҷикӣ ворид кунед:",
    "admin_enter_service_duration": "Давомнокиро ворид кунед (дақиқа):",
    "admin_enter_service_price": "Нархро ворид кунед (minor units):",
    "admin_service_added": "Хизмат илова шуд.",
    "admin_service_updated": "Хизмат нав шуд.",
    "admin_service_archived": "Хизмат ба бойгонӣ гузошта шуд.",
    "admin_service_restored": "Хизмат барқарор шуд.",
    "admin_invalid_number": "Рақами дурустро ворид кунед.",
    "admin_invalid_time_range": "Формати вақт нодуруст аст. Мисол: 10:00-14:30",
    "admin_schedule_overview": "Сменаҳо:\n{shifts}\n\nБанд:\n{busy}",
    "admin_item_not_found": "Элемент ёфт нашуд.",
    "admin_list_empty": "Рӯйхат холӣ аст.",
    "next_step_hint": "Қадами навбатӣ: {value}",
    "next_step_admin_menu": "қисми лозимаро дар менюи админ интихоб кунед.",
    "next_step_choose_service": "хизматро интихоб кунед.",
    "next_step_choose_barber": "усторо интихоб кунед.",
    "next_step_choose_date": "санаро интихоб кунед.",
    "next_step_choose_slot": "вақтро интихоб кунед.",
    "next_step_confirm": "амалро бо тугмаи поён тасдиқ кунед.",
    "next_step_enter_phone": "телефони мизоҷро дар формати +992... ворид кунед.",
    "next_step_delete_pick": "сабтро барои ҳазф интихоб кунед.",
    "next_step_back_menu": "ба меню баргардед ё дар ҳамин бахш идома диҳед.",
    "next_step_choose_stats": "статистикаро интихоб кунед: имрӯз, ҳафта ё санаи мушаххас.",
    "next_step_enter_stats_date": "санаро дар формат YYYY-MM-DD ворид кунед.",
    "next_step_pick_calendar_date": "санаро дар тақвим интихоб кунед ё YYYY-MM-DD ворид кунед.",
    "next_step_visit_pick": "сабтро барои қайди ташриф интихоб кунед.",
    "next_step_visit_action": "хизматро тасдиқ кунед ё ба рӯйхат баргардед.",
    "no_available_dates": "Барои усто ва хизмат санаи холӣ нест.",
    "booking_conflict_refresh": "Вақт банд аст. Санаҳои нави дастрас нишон дода шуданд.",
    "reminder_24h": "Ёдрас: сабти шумо {date_time} (пас аз 24 соат).",
    "reminder_2h": "Ёдрас: сабти шумо {date_time} (пас аз 2 соат).",
    "reminder_30m": "Ёдрас: сабти шумо {date_time} (пас аз 30 дақиқа).",
}

MESSAGES["tj"] = {**MESSAGES["ru"], **_TJ_MESSAGES}


def tr(locale: str | None, key: str, **kwargs: Any) -> str:
    lang = locale if locale in MESSAGES else "ru"
    template = MESSAGES[lang].get(key, MESSAGES["ru"].get(key, key))
    return template.format(**kwargs)
