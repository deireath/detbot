import re

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from psycopg import AsyncConnection

from app.bot.enums.roles import UserRole
from app.infrastructure.database.db import get_user_role

class UserRoleFilter(BaseFilter):
    def __init__(self, *roles: str | UserRole):
        if not roles:
            raise ValueError('At least one role must be provided to UserRoleFilter')

        self.roles = frozenset(
        UserRole(role) if isinstance(role, str) else role
        for role in roles
        if isinstance(role, (str, UserRole))
        )

        if not self.roles:
            raise ValueError('No valid roles provided to UserRoleFilter')
    async def __call__(self, event: Message | CallbackQuery, conn: AsyncConnection):
        user = event.from_user
        if not user:
            return False

        role = await get_user_role(conn, user_id = user.id)
        if role is None:
            return False

        return role in self.roles


class UnregisteredUserFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery, conn: AsyncConnection):
        user = event.from_user
        if not user:
            return False
        role = await get_user_role(conn, user_id = user.id)
        return role is None
    
LAT_TO_CYR = str.maketrans({
    # заглавные
    "A":"А","B":"В","C":"С","E":"Е","H":"Н","K":"К","M":"М","O":"О","P":"Р","T":"Т","X":"Х","Y":"У",
    # строчные
    "a":"а","b":"в","c":"с","e":"е","h":"н","k":"к","m":"м","o":"о","p":"р","t":"т","x":"х","y":"у",
})

def normalize_district(raw: str) -> str:
    s = raw.strip().translate(LAT_TO_CYR)  # латиницу -> кириллица
    s = s.replace(" ", "").upper()         # убираем пробелы и в верхний регистр
    # частые синонимы/слепания
    s = s.replace("С-З", "СЗ").replace("С З", "СЗ")
    s = s.replace("Ю-З", "ЮЗ").replace("Ю З", "ЮЗ")
    s = s.replace("С-В", "СВ").replace("С В", "СВ")
    s = s.replace("Ю-В", "ЮВ").replace("Ю В", "ЮВ")
    return s

def parse_location(text: str) -> tuple[str,int] | None:
    text = text.strip().translate(LAT_TO_CYR)
    text = re.sub(r"[–—−]", "-", text)
    text = re.sub(r"([A-Za-zА-Яа-яЁё]+)\s+([0-9]+)", r"\1-\2", text)

    PATTERN = re.compile(
        r'^\s*([A-Za-zА-Яа-яЁё]{1,3})\s*-\s*([0-9]{1,3})\s*$',
        re.IGNORECASE
    )
    m = PATTERN.match(text)
    if not m:
        return None

    district_raw, num_raw = m.group(1), m.group(2)
    district = normalize_district(district_raw)
    number = int(num_raw)
    return district, number