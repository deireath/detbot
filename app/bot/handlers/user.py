import logging
import re
import os
import asyncio

from redis.asyncio import Redis
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from psycopg.connection_async import AsyncConnection
from app.bot.enums.roles import UserRole
from app.bot.keyboards.keyboards import make_district_keyboard, user_start_kb, make_tags_keyboard
from app.bot.filters.filters import parse_location
from app.bot.states.states import UserState
from app.infrastructure.database.db import (
    add_answer,
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

MEDIA_ROOT = "media"

EXTENSIONS = {
    "photo": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "video": [".mp4", ".mov", ".avi", ".mkv"],
    "audio": [".mp3", ".ogg", ".wav", ".m4a"],
}

def get_media_type(filename: str) -> str | None:
    ext = os.path.splitext(filename.lower())[1]
    for kind, exts in EXTENSIONS.items():
        if ext in exts:
            return kind
    return None


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

@user_router.message(Command(commands='answer'))
async def answer_command(message: Message, state: FSMContext):
    cancel_button = InlineKeyboardButton(text='ОТМЕНА ОТВЕТА', callback_data="answer_cancel")
    kb = InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])
    await message.answer("Введите свой ответ или отмените - /cancel", reply_markup=kb)
    await state.set_state(UserState.write_answer)

@user_router.message(Command(commands="cancel"), StateFilter(UserState.write_answer))
async def reg_cancel(message: Message, state: FSMContext):
    await message.answer("Ввод ответа отменен")
    await state.clear()

@user_router.callback_query(F.data == "answer_cancel", StateFilter(UserState.write_answer))
async def reg_cancel_button(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Ввод ответа отменен")
    await state.clear()
    await callback.answer()

@user_router.message(StateFilter(UserState.write_answer))
async def write_answer(message: Message, state: FSMContext, conn: AsyncConnection):
    if not message.text:
        await message.answer("Введите ответ текстом только")
        return
    text = message.text
    user_id= message.from_user.id
    result = await add_answer(conn, text=text, user_id=user_id)
    if not result:
        await message.answer("Не удалось добавить ответ ((")
        return
    await message.answer("Ваш ответ добавлен")
    await state.clear()



@user_router.message(F.text)
async def handle_district_number(message: Message, conn: AsyncConnection, redis: Redis, bot: Bot):
    processing = await message.answer("Обрабобка запроса...")
    parsed = parse_location(message.text)
    if not parsed:
        await processing.edit_text("Непрааавильно. Нужный формат: <район>-<номер>, например: СЗ-4, Ю - 16, В-7.", parse_mode=None)
        return
    district, number = parsed

    row = await get_answer(conn, district, number)
    if row is None:
        await processing.edit_text("Такой локации не существует")
        return
    name, answer, papka = row
    user_id = message.from_user.id

    team_row = await get_team_by_user(conn, user_id)
    team = str(team_row[0]) if team_row else None
    if not team:
        await processing.edit_text("У тебя нет команды ...")
        return
    
    visit_key = f"team:{team}:visited"
    place_code = f"{district}-{number}"

    already = await redis.sismember(visit_key, place_code)
    if already:
        await processing.edit_text("Вы уже были здесь")
        return
    await add_travel(conn, team)

    if not answer or answer.strip() == '':
        await processing.edit_text("Здесь ничего нет ...")
        return
    
    header = f"<b>{district} - {number}\n{name}</b>"
    await processing.edit_text(header)

    parts = re.split(r"(\[[^\]]+\])", answer)
    for part in parts:
        part = part.strip()
        if not part:
            continue

        if part.startswith("[") and part.endswith("]"):
            filename = part[1:-1]
            file_path = os.path.join(MEDIA_ROOT, filename)

            if not os.path.exists(file_path):
                await message.answer(f" Файл {filename} не найден.")
                continue

            kind = get_media_type(filename)
            file = FSInputFile(file_path)

            if kind == "photo":
                await bot.send_chat_action(message.chat.id, "upload_photo")
                await message.answer_photo(file)
            elif kind == "video":
                await bot.send_chat_action(message.chat.id, "upload_video")
                await message.answer_video(file)
            elif kind == "audio":
                await bot.send_chat_action(message.chat.id, "upload_audio")
                await message.answer_audio(file)

        else:
            await bot.send_chat_action(message.chat.id, "typing")
            await asyncio.sleep(0.8)
            await message.answer(part)

    await bot.send_chat_action(message.chat.id, "cancel")
    await redis.sadd(visit_key, place_code)

    if papka:
        await add_clue(conn, team)
        admins = await get_admins(conn)
        for admin_id in admins:
            try:
                await bot.send_message(admin_id, f"Команда {team} - папка {papka}")
            except:
                pass

