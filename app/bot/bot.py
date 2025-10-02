import logging
import asyncio
from contextlib import suppress

import psycopg_pool
from redis.asyncio import Redis
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from config.config import Config
from app.bot.handlers.admin import admin_router
from app.bot.handlers.user import user_router
from app.bot.handlers.other import other_router
from app.bot.handlers.registration import registration_router
from app.bot.middlewares.database import DataBaseMiddleware
from app.infrastructure.database.connection import get_pg_pool
from app.infrastructure.integration.sheets_import import import_all_from_config
from app.infrastructure.integration.sheets_sync import sync_all


logger = logging.getLogger(__name__)

async def _periodic_worker(
    pool: psycopg_pool.AsyncConnectionPool,
    interval_min: int,
    coro,
    name: str,
):

    while True:
        try:
            await coro(pool)
            logger.info("[%s] tick done", name)
        except Exception:
            logger.exception("[%s] tick failed", name)
        try:
            await asyncio.sleep(max(1, interval_min) * 60)
        except asyncio.CancelledError:
            logger.info("[%s] cancelled", name)
            raise




async def main(config: Config) -> None:
    logger.info('Starting bot...')

    storage = RedisStorage(
        redis=Redis(
            host=config.redis.host,     
            port=config.redis.port,
            db=config.redis.db,
            password=config.redis.password,
            username=config.redis.username,
        )
    )

    bot = Bot(token=config.bot.token)
    dp = Dispatcher(storage=storage)

    db_pool: psycopg_pool.AsyncConnectionPool = await get_pg_pool(
        db_name=config.db.name,
        host=config.db.host,
        port=config.db.port,
        user=config.db.user,
        password=config.db.password,
    )

    logger.info('Including routers...')
    dp.include_router(registration_router)
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(other_router)

    logger.info('Including middlewares...')
    dp.update.middleware(DataBaseMiddleware())

    sync_task: asyncio.Task | None = None
    import_task: asyncio.Task | None = None


    try:
        if getattr(config.sheets, "import_on_start", False):
            try:
                res = await import_all_from_config(db_pool)
                logger.info("[import] on start: %s", res)
            except Exception:
                logger.exception("[import] on start failed")

        if getattr(config.sheets, "sync_on_start", False):
            try:
                res = await sync_all(db_pool)
                logger.info("[sync] on start: %s", res)
            except Exception:
                logger.exception("[sync] on start failed")

        if getattr(config.sheets, "sync_interval_min", 0) and config.sheets.sync_interval_min > 0:
            sync_task = asyncio.create_task(
                _periodic_worker(db_pool, config.sheets.sync_interval_min, sync_all, "sheets-sync"),
                name="sheets-sync",
            )
            logger.info("[sync] periodic worker started: every %s min", config.sheets.sync_interval_min)

        await dp.start_polling(
            bot,
            db_pool=db_pool,
        )
    except Exception as e:
        logger.exception(e)
    finally:
        for task in (sync_task, import_task):
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
        await db_pool.close()
        logger.info("Connection to Postgres closed")