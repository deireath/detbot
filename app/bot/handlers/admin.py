import logging

from aiogram import Bot, Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from psycopg import AsyncConnection
from app.bot.enums.roles import UserRole
from app.bot.filters.filters import UserRoleFilter
from app.bot.states.states import AdminState
from app.infrastructure.database.db import delete_team, get_users

logger =  logging.getLogger(__name__)

admin_router = Router()

admin_router.message.filter(UserRoleFilter(UserRole.ADMIN))

@admin_router.message(Command('start'))
async def admin_start_command(message: Message):
    await message.answer(text='admin start')


@admin_router.message(Command('help'))
async def admin_help_command(message: Message):
    await message.answer(text='admin help')

@admin_router.message(Command("all"))
async def message_to_all(message: Message, state: FSMContext):
    await message.answer("Напишите сообщение для всех игроков или отмените - /cancel")
    await state.set_state(AdminState.message_to_all)

@admin_router.message(Command(commands="cancel"), StateFilter(AdminState.message_to_all))
async def message_cancel(message: Message, state: FSMContext):
    await message.answer("Ввод cообщения отменен")
    await state.clear()

@admin_router.message(StateFilter(AdminState.message_to_all))
async def send_message_to_all(message: Message, state: FSMContext, conn: AsyncConnection, bot: Bot):
    users = await get_users(conn)
    for user_id in users:
        try:
            if message.text:
                await bot.send_message(user_id, message.text)
            elif message.photo:
                photo = message.photo[-1].file_id
                caption = message.caption if message.caption else None
                await bot.send_photo(user_id, photo, caption=caption)
            elif message.animation:
                animation = message.animation.file_id
                caption = message.caption if message.caption else None
                await bot.send_animation(user_id, animation, caption=caption)
            else:
                pass
        except:
            pass
    await state.clear()

@admin_router.message(Command("visits"))
async def show_team_visits(message: Message, redis):
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer('Неправильно, попробуй /visits <номер команды>', parse_mode=None)
        return
    team = int(args[1])
    visit_key = f"team:{team}:visited"

    visited = await redis.smembers(visit_key)
    if not visited:
        await message.answer("Команда ничего не посетила")
        return
    visited_places = [place for place in visited]
    text = f"Команда {team} посетила:\n" + "\n".join(visited_places)
    await message.answer(text=text)

@admin_router.message(Command("delete_visits"))
async def delete_visits(message: Message, redis):
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer('Неправильно, попробуй /delete_visits <номер команды>', parse_mode=None)
        return
    team = int(args[1])
    visit_key = f"team:{team}:visited"
    await redis.delete(visit_key)
    await message.answer(f"Вот и все, история команды {team} сброшена")

@admin_router.message(Command("delete_team"))
async def delete_team_everywhere(message: Message, conn: AsyncConnection, redis):
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("Неправильно, попробуй /delete_team <номер команды>", parse_mode=None)
        return
    team = int(args[1])
    visit_key = f"team:{team}:visited"
    await redis.delete(visit_key)
    deleted =await delete_team(conn, team)
    if deleted:
        await message.answer(f"Вот и все. Команды {team} больше нет")
    else:
        await message.answer(f"Команда {team} не найдена")
    
