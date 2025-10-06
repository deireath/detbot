from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from psycopg import AsyncConnection

from app.infrastructure.database.db import get_districts, get_tags

button_adminreg = InlineKeyboardButton(text='ADMIN', callback_data='admin_reg')
button_usereg = InlineKeyboardButton(text='USER', callback_data='user_reg')

reg_kb = InlineKeyboardMarkup(inline_keyboard=[[button_adminreg], [button_usereg]])


tag_button = InlineKeyboardButton(text='КАТЕГОРИИ', callback_data='tag')
district_button = InlineKeyboardButton(text='РАЙОНЫ', callback_data='district')

user_start_kb = InlineKeyboardMarkup(inline_keyboard=[[tag_button], [district_button]])

async def make_tags_keyboard(conn: AsyncConnection):
    tags = await get_tags(conn)
    tags = [tag if tag is not None else "Без категории" for tag in tags]
    tags = [tag if tag else "Без категории" for tag in tags]
    buttons= [InlineKeyboardButton(text=tag, callback_data=f"tag_{tag}")
            for tag in tags]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i+2] for i in range(0, len(buttons), 2)])
    return keyboard

async def make_district_keyboard(conn: AsyncConnection):
    districts = await get_districts(conn)
    buttons = [InlineKeyboardButton(text=district, callback_data=f"district_{district}")
            for district in districts]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i+3] for i in range(0, len(buttons), 3)])
    return keyboard