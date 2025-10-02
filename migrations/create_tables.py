import asyncio
import logging
import os
import sys
from psycopg import AsyncConnection, Error

from app.infrastructure.database.connection import get_pg_connection
from config.config import Config, load_config

config: Config = load_config()

logging.basicConfig(
    level=logging.getLevelName(level=config.log.level),
    format=config.log.format
)

logger = logging.getLogger(__name__)

if sys.platform.startswith("win") or os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    connection: AsyncConnection | None = None

    try:
        connection = await get_pg_connection(
            db_name=config.db.name,
            host=config.db.host,
            port=config.db.port,
            user=config.db.user,
            password=config.db.password,
        )
        async with connection:
            async with connection.transaction():
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        query="""
                            CREATE TABLE IF NOT EXISTS users(
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL UNIQUE,
                            username VARCHAR(50),
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            role VARCHAR(30) NOT NULL
                            );
                        """
                    )
                    await cursor.execute(
                        query="""
                            CREATE TABLE IF NOT EXISTS places(
                            id SERIAL PRIMARY KEY,
                            tag VARCHAR(50),
                            district VARCHAR(10),
                            number INT,
                            name VARCHAR(50),
                            answer TEXT,
                            papka INT,
                            CONSTRAINT places_uq UNIQUE (district, number)
                            );
                        """
                    )
                    await cursor.execute(
                        query="""
                            CREATE TABLE IF NOT EXISTS teams(
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL UNIQUE,
                            team INT,
                            role VARCHAR(30),
                            travels INT,
                            clue INT
                            );
                        """
                    )
                logger.info("Table 'user' were successfully created")
    except Error as db_error:
        logger.exception("Database-specific error: %s", db_error)
    except Exception as e:
        logger.exception("Unhandled error: %s", e)
    finally:
        if connection:
            await connection.close()
            logger.info("Connection to Postgres closed")

asyncio.run(main())
