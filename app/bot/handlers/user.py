import logging
import re

from redis.asyncio import Redis
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from psycopg.connection_async import AsyncConnection
from app.bot.enums.roles import UserRole
from app.bot.keyboards.keyboards import make_district_keyboard, user_start_kb, make_tags_keyboard
from app.bot.filters.filters import parse_location
from app.infrastructure.database.db import (
    add_clue,
    add_travel,
    add_user,
    get_admins,
    get_answer,
    get_places_by_district,
    get_places_by_tag,
    get_team_by_user,
    get_user,
    get_tags
)


logger = logging.getLogger(__name__)

user_router = Router()

@user_router.message(CommandStart())
async def user_start_command(message: Message):
    await message.answer(text='Категории и районы', reply_markup=user_start_kb)

@user_router.callback_query(F.data == "tag")
async def show_tags(callback: CallbackQuery, conn):
    keyboard= await make_tags_keyboard(conn)
    await callback.message.answer(text="Выберите категорию:", reply_markup=keyboard)
    await callback.answer()

@user_router.callback_query(F.data == "district")
async def show_districts(callback: CallbackQuery, conn):
    keyboard = await make_district_keyboard(conn)
    await callback.message.answer(text="Выберите район:", reply_markup=keyboard)
    await callback.answer()

@user_router.callback_query(F.data.startswith("tag_"))
async def show_places_by_tag(callback: CallbackQuery, conn):
    tag = callback.data.removeprefix("tag_")
    rows = await get_places_by_tag(conn, tag)
    text = f"<b>{tag}</b>:\n"
    for district, number, name in rows:
        text += f"{district}-{number} {name}\n"
    await callback.message.answer(text)
    await callback.answer()

@user_router.callback_query(F.data.startswith("district_"))
async def show_places_by_district(callback: CallbackQuery, conn):
    district = callback.data.removeprefix("district_")
    rows = await get_places_by_district(conn, district)
    text = f"<b>{district}</b>:\n"
    for district, number, name in rows:
        text += f"{district}-{number} {name}\n"
    await callback.message.answer(text)
    await callback.answer()

@user_router.message(Command(commands='help'))
async def admin_help_command(message: Message):
    await message.answer(text='user help')

@user_router.message(Command(commands='getteam'))
async def test_command(message: Message, conn: AsyncConnection):
    user_id = message.from_user.id
    row = await get_team_by_user(conn, user_id)
    team = str(row[0])
    await message.answer(text=team)


@user_router.message(F.text)
async def handle_district_number(message: Message, conn: AsyncConnection, redis: Redis, bot):
    parsed = parse_location(message.text)
    if not parsed:
        await message.reply("Формат: <район>-<номер>, например: СЗ-4, Ю - 16, В-7.")
        return

    district, number = parsed

    row = await get_answer(conn, district, number)
    if row is None:
        await message.answer("Такой локации не существует")
        return
    name, answer, papka = row
    user_id = message.from_user.id

    team_row = await get_team_by_user(conn, user_id)
    team = str(team_row[0])
    if not team:
        await message.answer("У тебя нет команды ...")
        return
    
    visit_key = f"team:{team}:visited"
    place_code = f"{district}-{number}"

    already = await redis.sismember(visit_key, place_code)
    if already:
        await message.answer("Вы уже были здесь")
        return
    await redis.sadd(visit_key, place_code)
    await add_travel(conn, team)

    if not answer or answer.strip() == '':
        await message.answer("Здесь ничего нет ...")
    else:
        text = f"<b>{district} - {number}\n {name}</b>\n\n{answer}"
        await message.answer(text=text, reply_markup=user_start_kb)

    if papka:
        await add_clue(conn, team)
        admins = await get_admins(conn)
        for admin_id in admins:
            try:
                await bot.send_message(admin_id, f"Команда {team} - папка {papka}")
            except:
                pass
