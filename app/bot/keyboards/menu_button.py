from aiogram.types import BotCommand

def get_main_menu_command():
    return [
        BotCommand(
            command='start'
        )
    ]