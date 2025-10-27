from aiogram.types import BotCommand

from app.bot.enums.roles import UserRole

def get_main_menu_command(user_role: UserRole):
    if user_role == UserRole.USER:
        return [
            BotCommand(
                command='/start',
                description='Посмотреть категории и районы'
            ),
            BotCommand(
                command='/answer',
                description='Дать ответ'
            )
        ]
    elif user_role == UserRole.ADMIN:
        return [
            BotCommand(
                command='start',
                description='Это старт'
            ),
            BotCommand(
                command='/visits',
                description='Посмотреть посещенные командой места /visits <номер команды>'
            ),
            BotCommand(
                command='/all',
                description='Написать всем'
            ),
            BotCommand(
                command='/delete_visits',
                description='Удалить посещенные командой места /delete_visits <номер команды>'
            ),
            BotCommand(
                command='/delete_visits',
                description='Удалить посещенные командой места /delete_visits <номер команды>'
            ),
            BotCommand(
                command='/delete_team',
                description='Удалить команду /delete_team <номер команды>'
            )

        ]