from aiogram import BaseMiddleware
from typing import Callable, Awaitable, Any, Dict
from redis.asyncio import Redis

class RedisMiddleware(BaseMiddleware):
    def __init__(self, redis: Redis):
        super().__init__()
        self.redis = redis

    async def __call__(
            self,
            handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
            event: Any,
            data: Dict[str, Any],
    ):
        data["redis"] = self.redis
        return await handler(event, data)