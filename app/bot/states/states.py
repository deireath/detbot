from aiogram.fsm.state import State, StatesGroup

class RegState(StatesGroup):
    admin_pass = State()
    user_team = State()
