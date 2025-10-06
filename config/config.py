import logging
import os
from dataclasses import dataclass

from environs import Env

logger = logging.getLogger(__name__)

@dataclass
class BotSettings:
    token: str
    admin_pass: int

@dataclass
class DatabaseSettings:
    name: str
    host: str
    port: int
    user: str
    password: str

@dataclass
class RedisSettings:
    host: str
    port: int
    db: int
    password: str
    username: str

@dataclass 
class LogSettings:
    level: str
    format: str

@dataclass
class GoogleSettings:
    sa_json_path: str
    sources_path: str | None
    sync_path: str | None


@dataclass 
class SheetsFlags:
    import_on_start: bool
    import_interval_min: int
    sync_on_start: bool
    sync_interval_min: int

@dataclass
class Config:
    bot: BotSettings
    db: DatabaseSettings
    redis: RedisSettings
    log: LogSettings
    google: GoogleSettings
    sheets: SheetsFlags

def load_config(path: str | None = None) -> Config:
    env = Env()

    if path:
        if not os.path.exists(path):
            logger.warning(".env file not found at '%s', skipping...", path)
        else:
            logger.info("Loading .env from '%s'", path)

    env.read_env(path)

    token = env("BOT_TOKEN")
    admin_pass = env("ADMIN_PASS")

    if not token:
        raise ValueError("BOT_TOKEN must not be empty")

    
    sa_json_path = env("SA_JSON_PATH")
    
    db = DatabaseSettings(
        name=env("POSTGRES_DB"),
        host=env("POSTGRES_HOST"),
        port=env.int("POSTGRES_PORT"),
        user=env("POSTGRES_USER"),
        password=env("POSTGRES_PASSWORD"),
    )

    redis = RedisSettings(
        host=env("REDIS_HOST"),
        port=env.int("REDIS_PORT"),
        db=env.int("REDIS_DATABASE"),
        password=env("REDIS_PASSWORD", default=""),
        username=env("REDIS_USERNAME", default=""),
    )
    
    logg_settings = LogSettings(
        level=env("LOG_LEVEL"),
        format=env("LOG_FORMAT"),
    )

    google = GoogleSettings(
        sa_json_path=sa_json_path,
        sources_path=env("GSHEETS_SOURCES_PATH", default=None),
        sync_path=env("GSHEETS_SYNC_PATH", default=None),
    )

    sheets = SheetsFlags(
        import_on_start=env.bool("SHEETS_SYNC_ON_START", default=False),
        import_interval_min= env.int("SHEETS_IMPORT_INTERVAL_MIN", default=0),
        sync_on_start=env.bool("SHEETS_SYNC_ON_START", default=False),
        sync_interval_min=env.int("SHEETS_SYNC_INTERVAL_MIN", default=0),
    )

    logger.info("Configuration loaded successfully")

    return Config(
        bot=BotSettings(token=token, admin_pass=admin_pass),
        db=db,
        redis=redis,
        log=logg_settings,
        google=google,
        sheets=sheets
    )
