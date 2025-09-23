from enum import Enums


class UserRole(str, Enum):
    ADMIN = 'admin'
    USER = 'user'
    GUEST = 'guest'
