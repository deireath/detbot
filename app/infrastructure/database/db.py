import logging 
from datetime import datetime, timezone
from typing import Any

from app.bot.enums.roles import UserRole
from psycopg import AsyncConnection

logger = logging.getLogger(__name__)

async def add_user(
        conn: AsyncConnection,
        *,
        user_id:int,
        username: str | None = None,
        role: UserRole = UserRole.USER,       
) -> None: 
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                INSERT INTO users(user_id, username, role),
                VALUES(
                    %(user_id)s,
                    %(username)s,
                    %(role)s
                ) ON CONFLICT DO NOTHING;
        """,
        params={
            "user_id": user_id,
            "username": username,
            "role": role,
        },
        ) 
    logger.info("User added. Table='%s', user_id=%d, created_at='%s', role=%s, ",
        "users",
        user_id,
        datetime.now(timezone.utc),
        role,
        )
 
async def get_user(
        conn: AsyncConnection,
        *,
        user_id: int,
) -> tuple[Any, ...] | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT
                    id,
                    user_id, 
                    username,
                    role,
                    created_at
                    FROM users WHERE user_id = %s;
        """,
        params=(user_id,)
        )
        row = await data.fetchone()
    logger.info("Row is %s", row)
    return row if row else None

async def get_user_role(
        conn: AsyncConnection,
        *,
        user_id: int,
) -> UserRole | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT role FROM users WHERE user_id = %s;
        """,
        params=(user_id,),
        )
        row = await data.fetchone()
    if row:
        logger.info("The user with `user_id`=%s has the role is %s", user_id, row[0])
    else:
        logger.warning("No user with `user_id`=%s found in the database", user_id)
    return UserRole(row[0]) if row else None