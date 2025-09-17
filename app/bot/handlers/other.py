from operator import truediv
from aiogram import Router
from aiogram.types import Message
from lexicon.lexicon import LEXICON_RU


router =Router()

@router.message()
async def send_echo(message: Message):
    try:
        await message.send_copy(chat_id=message.chat.id)
        print(message.model_dump_json(indent=4, exclude_none=True))
    except TypeError:
        await message.reply(text=LEXICON_RU['no_echo'])
