from aiogram.fsm.state import State, StatesGroup

class RegState(StatesGroup):
    admin_pass = State()
    user_team = State()

class UserState(StatesGroup):
    write_answer = State()

class AdminState(StatesGroup):
    message_to_all = State()