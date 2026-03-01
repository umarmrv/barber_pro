from __future__ import annotations

from barber_bot.i18n import tr


def test_tr_tj_returns_tajik_message() -> None:
    assert tr("tj", "choose_service") == "Хизматро интихоб кунед:"


def test_tr_tj_fallback_to_ru_for_missing_key() -> None:
    assert tr("tj", "non_existing_key") == "non_existing_key"
