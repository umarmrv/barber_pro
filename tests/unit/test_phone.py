from __future__ import annotations

from barber_bot.services.phone import normalize_phone


def test_normalize_phone_uses_tajik_default_region() -> None:
    assert normalize_phone("901234567", "TJ") == "+992901234567"


def test_normalize_phone_accepts_explicit_international_prefixes() -> None:
    assert normalize_phone("+992901234567", "TJ") == "+992901234567"
    assert normalize_phone("+998901234567", "TJ") == "+998901234567"
