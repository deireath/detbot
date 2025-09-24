import logging

import psycopg_pool
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from app.bot.handlers.admin import admin_router
from app.bot.handlers.user import user_router
from app.bot.handlers.other import other_router
from app.bot.middlewares.database import DataBaseMiddleware
from app.infrastructure.database.connection import get_pg_pool
from config.config import Config
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

async def main(config: Config) -> None:
    logger.info('Starting bot...')

    bot = Bot(token=config.bot.token)
    dp = Dispatcher()

    db_pool: psycopg_pool.AsyncConnectionPool = await get_pg_pool(
        db_name=config.db.name,
        host=config.db.host,
        port=config.db.port,
        user=config.db.user,
        password=config.db.password,
    )

    logger.info('Including routers...')
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(other_router)

    logger.info('Including middlewares...')
    dp.update.middleware(DataBaseMiddleware())

    try:
        await dp.start_polling(
            bot, db_pool=db_pool,
            admin_ids=config.bot.admin_ids
        )
    except Exception as e:
        logger.exception(e)
    finally:
        await db_pool.close()
        logger.info("Connection to Postgres closed")