import loggig

import psycopg_pool
from aiogram import Bot,Dispatcher
from aiogram.client.default import DefaulBotPoroperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from bot.handlers.admin import
from bot.handlers.user import
from bot.handlers.other import
from bot.handlers.settings import
from app.infrasructure.database.connection import gey_pg_pool
from config.config import Config
from redis.asyncio import Redis
