from aiogram import Router

from barber_bot.bot.handlers.admin import router as admin_router
from barber_bot.bot.handlers.booking import router as booking_router
from barber_bot.bot.handlers.common import router as common_router


def get_routers() -> list[Router]:
    return [common_router, booking_router, admin_router]
