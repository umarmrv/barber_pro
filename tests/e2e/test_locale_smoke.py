from barber_bot.i18n import MESSAGES


def test_ru_uz_locales_have_core_keys() -> None:
    required_keys = {
        "welcome",
        "choose_service",
        "choose_barber",
        "choose_date",
        "choose_slot",
        "booked",
        "cancelled",
    }
    for locale in ("ru", "uz"):
        for key in required_keys:
            assert key in MESSAGES[locale]
