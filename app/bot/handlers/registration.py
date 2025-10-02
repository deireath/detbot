import logging

from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from app.bot.filters.filters import UnregisteredUserFilter
from app.bot.enums.roles import UserRole


logger = logging.getLogger(__name__)

registration_router = Router()
registration_router.message.filter(UnregisteredUserFilter())

@registration_router.message(CommandStart())
async def start_registartion(message: Message):
    registartion_button = InlineKeyboardButton(text='Регистрация', callback_data="registration_button")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[registartion_button]])
    await message.answer(
        text='Зарегестрируйтесь плиз',
        reply_markup=keyboard
    )


