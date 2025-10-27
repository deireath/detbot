import logging 
from datetime import datetime, timezone
from typing import Any
from psycopg import AsyncConnection

from app.bot.enums.roles import UserRole

logger = logging.getLogger(__name__)

async def add_user(
        conn: AsyncConnection,
        *,
        user_id: int,
        username: str | None = None,
        role: UserRole,       
) -> None: 
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                INSERT INTO users(user_id, username, role)
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
    # if row:
    #     logger.info("The user with `user_id`=%s has the role is %s", user_id, row[0])
    # else:
    #     logger.warning("No user with `user_id`=%s found in the database", user_id)
    return UserRole(row[0]) if row else None

async def add_team(
        conn: AsyncConnection,
        *,
        user_id: int,
        team: int,
        role: UserRole,
):
    async with conn.cursor() as cursor:
        result = await cursor.execute(
            query="""
                INSERT INTO teams(user_id, team, role)
                VALUES(
                %(user_id)s,
                %(team)s,
                %(role)s
                ) ON CONFLICT DO NOTHING
                RETURNING team;
            """,
            params={
                "user_id":user_id,
                "team":team,
                "role": role,
            },
        )
        row = await result.fetchone()
        if row:
            logger.info("Team added. Table='%s', user_id=%d, team='%s', role=%s, ",
            "teams",
            user_id,
            team,
            role,
            )
        return row is not None

async def get_admins(conn: AsyncConnection):
    async with conn.cursor() as cursor:
        data  = await cursor.execute("SELECT user_id FROM users WHERE role = 'admin'")
        rows = await data.fetchall()
        admins = [row[0] for row in rows]
        return admins

async def get_users(conn: AsyncConnection):
    async with conn.cursor() as cursor:
        data  = await cursor.execute("SELECT user_id FROM teams WHERE role = 'user'")
        rows = await data.fetchall()
        users = [row[0] for row in rows]
        return users

async def get_tags(conn: AsyncConnection):
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT DISTINCT tag
                FROM places
                ORDER BY tag;
            """
        )
        rows = await data.fetchall()
        tags= [row[0] for row in rows]
        return tags

async def get_places_by_tag(conn: AsyncConnection, tag: str):
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT district, number, name
                FROM places
                WHERE tag = %(tag)s
                ORDER BY district, number;
            """,
            params={"tag":tag,}
        )
        rows = await data.fetchall()
        return rows
    
async def get_districts(conn: AsyncConnection):
    async with conn.cursor() as cursor:
        data = await cursor.execute("SELECT DISTINCT district FROM places ORDER BY district;")
        rows = await data.fetchall()
        districts = [row[0] for row in rows]
        return districts
    
async def get_places_by_district(conn: AsyncConnection, district: str):
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT district, number, name
                FROM places
                WHERE district = %(district)s
                ORDER BY number;
            """,
            params={"district":district,}
        )
        row = await data.fetchall()
        return row

async def get_answer(conn: AsyncConnection, district: str, number: int):
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT name, answer, papka
                FROM places
                WHERE district = %(district)s AND number = %(number)s;
            """,
            params={"district": district,
                    "number": number,}
        )
        row = await data.fetchone()
        return row
    
async def get_team_by_user(conn: AsyncConnection, user_id: int):
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT team
                FROM teams
                WHERE user_id = %(user_id)s;
            """,
            params={"user_id": user_id,}
        )
        row = await data.fetchone()
        return row

async def get_user_by_team(conn: AsyncConnection, team: int):
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            """
                SELECT user_id
                FROM teams
                WHERE team = %s;
            """, (team,))
        row = await data.fetchone()
        return row

async def add_travel(conn: AsyncConnection, team: int):
    async with conn.cursor() as cursor:
        await cursor.execute("""
                            UPDATE teams
                            SET travels = COALESCE(travels, 0) + 1
                            WHERE team = %s;
                        """, (team,))

async def add_clue(conn: AsyncConnection, team: int):
    async with conn.cursor() as cursor:
        await cursor.execute("""
                            UPDATE teams
                            SET clue = COALESCE(clue, 0) + 1
                            WHERE team = %s;
                        """, (team,))

async def delete_team(conn: AsyncConnection, team: int):
    user_row = await get_user_by_team(conn, team)
    user_id = user_row[0] if user_row else None

    async with conn.cursor() as cursor:
        await cursor.execute("""
                            DELETE FROM teams
                            WHERE team = %s;
                        """, (team,))
        deleted_count = cursor.rowcount
        if deleted_count and user_id:
            await cursor.execute(
                """
                    DELETE FROM users 
                    WHERE user_id = %s;
            """, (user_id,)
            )
        return deleted_count > 0
    
async def add_answer(conn: AsyncConnection, text: str, user_id: int):
    async with conn.cursor() as cursor:
        await cursor.execute("""
                            UPDATE teams
                            SET text = %s
                            WHERE user_id = %s;
                        """, (text, user_id)
        )
        return cursor.rowcount > 0