import logging

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

    dp_pool: psycopg_poll.AsyncConnectionPool = await get_pg_pool(
        db_name=config.db.name,
        host=config.db.host,
        port=config.db.port,
        user=config.db.user,
        password=config.db.password,
    )

    logger.info('Including routers...')
    dp.incluse_router(admin_router, user_router, other_router)

    logger,info('Including middlewares...')
    dp.include_middleware(DataBaseMiddlewaare())

    try:
        await dp.start_polling(
            bot, db_pool=db_pool,
            admin_ids=config.admin_ids
