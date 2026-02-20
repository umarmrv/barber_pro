from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    waiting_phone = State()


class BookingStates(StatesGroup):
    choose_service = State()
    choose_barber = State()
    choose_date = State()
    choose_slot = State()
    confirm = State()


class AdminStates(StatesGroup):
    menu = State()

    booking_create_phone = State()
    booking_create_choose_client = State()
    booking_create_choose_service = State()
    booking_create_choose_barber = State()
    booking_create_choose_date = State()
    booking_create_choose_slot = State()
    booking_create_confirm = State()

    booking_delete_select = State()
    booking_delete_confirm = State()

    barber_create_name = State()
    barber_edit_name = State()
    shift_add_weekday = State()
    shift_add_time_range = State()
    shift_weekly_edit = State()

    service_create_ru_name = State()
    service_create_uz_name = State()
    service_create_duration = State()
    service_create_price = State()

    service_edit_ru_name = State()
    service_edit_uz_name = State()
    service_edit_duration = State()
    service_edit_price = State()
