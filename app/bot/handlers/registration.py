import logging
from operator import imod
from typing import Any

from aiogram import Router, F, Bot
from aiogram.enums import BotCommandScopeType
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, BotCommandScopeChat
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from psycopg import AsyncConnection


from app.bot.filters.filters import UnregisteredUserFilter
from app.bot.enums.roles import UserRole
from app.bot.keyboards.keyboards import reg_kb
from app.bot.keyboards.menu_button import get_main_menu_command
from app.bot.states.states import RegState
from app.infrastructure.database.db import add_team, add_user


logger = logging.getLogger(__name__)

registration_router = Router()
registration_router.message.filter(UnregisteredUserFilter())

@registration_router.message(CommandStart())
async def start_registartion(message: Message):
    await message.answer(
        text='Выберете роль плиз',
        reply_markup=reg_kb
    )

@registration_router.message(Command(commands="cancel"))
async def reg_cancel(message: Message, state: FSMContext):
    await message.answer("Ну и не надо. не очень и хотелось\nНачать заново - /start")
    await state.clear()

@registration_router.callback_query(F.data == "admin_reg")
async def admin_registration_starting(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите пароль или отмените регистрацию - /cancel")
    await state.set_state(RegState.admin_pass)
    await callback.answer()

@registration_router.message(StateFilter(RegState.admin_pass))
async def admin_pass_verification(message: Message, state: FSMContext, admin_pass: int, conn: AsyncConnection, bot: Bot):
    if message.text == str(admin_pass):
        await message.answer("Пароль верный, регистрация успешна")
        user_role = UserRole.ADMIN
        await add_user(
            conn,
            user_id=message.from_user.id,
            username=message.from_user.username,
            role=user_role
        )
        await bot.set_my_commands(
            commands=get_main_menu_command(user_role=user_role),
            scope=BotCommandScopeChat(
                type=BotCommandScopeType.CHAT,
                chat_id=message.from_user.id
            )
        )
        await state.clear()
    else:
        await message.answer("Неверный пароль, попробуйте еще\nОтмена регистрации - /cancel")


@registration_router.callback_query(F.data == "user_reg")
async def user_registration_starting(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите номер команды или отмените регистрацию - /cancel")
    await state.set_state(RegState.user_team)
    await callback.answer()

@registration_router.message(StateFilter(RegState.user_team))
async def user_team_verification(message: Message, state: FSMContext, conn: AsyncConnection, bot: Bot):
    if not message.text.isdigit():
        await message.answer("Введите только номер команды плиз")
        return
    team_number = int(message.text)
    user_role = UserRole.USER
    added = await add_team(
        conn,
        user_id=message.from_user.id,
        team=team_number,
        role=user_role
    )
    if not added:
        await message.answer(f"Команда {team_number} уже зарегистрирована, попробуйте другой номер")
        return

    await add_user(
        conn,
        user_id=message.from_user.id,
        username=message.from_user.username,
        role=user_role
    )
    await bot.set_my_commands(
            commands=get_main_menu_command(user_role=user_role),
            scope=BotCommandScopeChat(
                type=BotCommandScopeType.CHAT,
                chat_id=message.from_user.id
            )
        )
    await message.answer(f"Регистрация команды {team_number} успешна")
    await state.clear()
