import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

from lexicon.lexicon import LEXICON_RU

logger = logging.getLogger(__name__)

user_router = Router()

@user_router.message(CommandStart())
async def process_start_command(message: Message,
                                conn: AsyncCennection,
                                bot: Bot,
                                admin_ids: list[int],
):
    user_row = await get_user(conn, user_id=message,from_user.id)
    if user_row is None:
        if message.from_user_id in admins_ids:
            user.role = UserRole.ADMIN
        else:
            user.role = UserRole.USER

        await add_user(
            conn,
            user_id=message.from_user.id,
            username=message.from_user.id,
            role=user.role
        )
    else:
        user_role =  UserRole(user_row[3])


     await message.answer(text=LEXICON_RU['/start'])

@user_router.message(Command(commands='help'))
async def process_help_command(message: Message):
     await message.answer(text=LEXICON_RU['/help'])
