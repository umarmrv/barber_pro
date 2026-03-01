from __future__ import annotations

from datetime import date

from barber_bot.bot.keyboards import (
    admin_menu_texts,
    admin_visit_actions_keyboard,
    admin_visits_list_keyboard,
    client_menu_texts,
    lang_keyboard,
)


def test_lang_keyboard_contains_tajik_button() -> None:
    markup = lang_keyboard()
    callbacks = [button.callback_data for row in markup.inline_keyboard for button in row]
    texts = [button.text for row in markup.inline_keyboard for button in row]
    assert "lang:tj" in callbacks
    assert "Ўзбекча" in texts


def test_reply_menu_text_sets_include_tajik() -> None:
    assert "🗓 Сабт шудан" in client_menu_texts("book")
    assert "📋 Сабтҳо (муфассал)" in admin_menu_texts("bookings_today")


def test_menu_text_sets_include_legacy_labels() -> None:
    assert "Записаться" in client_menu_texts("book")
    assert "Мои записи" in client_menu_texts("my_bookings")
    assert "Записи сегодня (детально)" in admin_menu_texts("bookings_today")
    assert "Услуги" in admin_menu_texts("services")


def test_uzbek_menu_text_sets_use_cyrillic_and_keep_legacy_latin() -> None:
    assert "🗓 Ёзилиш" in client_menu_texts("book")
    assert "Yozilish" in client_menu_texts("book")
    assert "✅ Ташрифлар" in admin_menu_texts("visits_today")
    assert "Bugungi tashriflar" in admin_menu_texts("visits_today")


def test_visit_keyboards_keep_selected_date_in_callbacks() -> None:
    local_day = date(2026, 3, 1)

    list_markup = admin_visits_list_keyboard([(42, "#42")], "ru", local_day)
    list_callbacks = [button.callback_data for row in list_markup.inline_keyboard for button in row]
    assert f"admin:visit:pick:42:{local_day.isoformat()}" in list_callbacks

    action_markup = admin_visit_actions_keyboard(42, "confirmed", "ru", local_day)
    action_callbacks = [button.callback_data for row in action_markup.inline_keyboard for button in row]
    assert f"admin:visit:complete:42:{local_day.isoformat()}" in action_callbacks
    assert f"admin:visit:list:date:{local_day.isoformat()}" in action_callbacks
