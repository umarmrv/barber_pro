from __future__ import annotations

import phonenumbers


def normalize_phone(raw: str, default_region: str) -> str | None:
    cleaned = raw.strip()
    if not cleaned:
        return None
    try:
        number = phonenumbers.parse(cleaned, default_region)
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_possible_number(number) or not phonenumbers.is_valid_number(number):
        return None
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
