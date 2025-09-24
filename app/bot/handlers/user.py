import logging

from aiogram import Bot, Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from app.bot.enums.roles import UserRole
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
                                bot: Bot,
                                admin_ids: list[int],
):
    user_row = await get_user(conn, user_id=message.from_user.id)
    if user_row is None:
        if message.from_user_id in admin_ids:
            user_role = UserRole.ADMIN
        else:
            user_role = UserRole.USER

        await add_user(
            conn,
            user_id=message.from_user.id,
            username=message.from_user.id,
            role=user_role
        )
    else:
        user_role =  UserRole(user_row[3])


    await message.answer(text=LEXICON_RU['/start'])

@user_router.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(text=LEXICON_RU['/help'])
