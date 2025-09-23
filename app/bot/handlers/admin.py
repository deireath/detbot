import logging

from aiogram import Router
from aiogram.flters import Command
from aiogram.types import Message
from app.bot.enums.roles import UserRole
from app.bot filters.filters import UserRoleFilter

logger =  logging.getLogger(__name__)

admin_router = Router()

admin_router.message.filter(UserRoleFilter(UserRole.ADMIN))

@admin_router.message(Cammand('help'))
async def process_admin_help_command(message: Message):
    await message.answer(text='admin help')

