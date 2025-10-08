from operator import truediv
from aiogram import Router
from aiogram.types import Message



other_router = Router()

@other_router.message()
async def send_echo(message: Message):
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.reply(text='no_echo')
