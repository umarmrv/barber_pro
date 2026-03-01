from __future__ import annotations

from barber_bot.bot.keyboards import admin_booking_stats_calendar_keyboard


def _callbacks(markup) -> list[str]:
    return [
        button.callback_data or ""
        for row in markup.inline_keyboard
        for button in row
    ]


def test_admin_booking_stats_calendar_keyboard_callbacks() -> None:
    markup = admin_booking_stats_calendar_keyboard("ru", year=2026, month=2)
    callbacks = _callbacks(markup)

    assert "admin:booking:stats:date:month:2026-01" in callbacks
    assert "admin:booking:stats:date:month:2026-03" in callbacks
    assert "admin:booking:list:today" in callbacks
    assert "admin:menu" in callbacks
    assert any(cb.startswith("admin:booking:stats:date:pick:2026-02-") for cb in callbacks)


def test_admin_booking_stats_calendar_keyboard_tj_weekdays() -> None:
    markup = admin_booking_stats_calendar_keyboard("tj", year=2026, month=2)
    weekday_row = markup.inline_keyboard[1]
    weekday_labels = [button.text for button in weekday_row]
    assert weekday_labels == ["Дш", "Сш", "Чш", "Пш", "Ҷм", "Шн", "Як"]
