import logging

from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from app.bot.enums.roles import UserRole
from app.bot.keyboards.keyboards import reg_kb
from app.infrastructure.database.db import (
    add_user,
    get_user
)
from psycopg.connection_async import AsyncConnection


from lexicon.lexicon import LEXICON_RU

logger = logging.getLogger(__name__)

user_router = Router()

@user_router.message(CommandStart())
async def process_start_command(message: Message,
                                conn: AsyncConnection,
                                # bot: Bot,
                                # admin_ids: list[int],
                                # admin_pass: int
):
    user_row = await get_user(conn, user_id=message.from_user.id)

    if user_row is None:
        await message.answer(text="Регистрация", reply_markup=reg_kb )

@user_router.callback_query(F.data == "admin_reg")
async def admin_registration(callback: CallbackQuery):
    await callback.message.answer(text="password please")
    await callback.answer()

@user_router.callback_query(F.data == "user_reg")
async def user_registration(callback: CallbackQuery):
    await callback.message.answer(text="user registration here")
    await callback.answer()

@user_router.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(text=LEXICON_RU['/help'])
