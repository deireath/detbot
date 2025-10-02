from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

button_adminreg = InlineKeyboardButton(text='ADMIN', callback_data='admin_reg')
button_usereg = InlineKeyboardButton(text='USER', callback_data='user_reg')

reg_kb = InlineKeyboardMarkup(inline_keyboard=[[button_adminreg], [button_usereg]])
