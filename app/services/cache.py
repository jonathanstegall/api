import inspect
import json
from datetime import datetime, timedelta
from redis.asyncio import Redis
from typing import Any, Optional, Callable, TypeVar
from functools import wraps
from app.core.config import settings

# Redis credentials
REDIS_TTL = settings.REDIS_TTL

T = TypeVar('T')

class CacheService:
    def __init__(self, redis: Redis, prefix: str = "cache"):
        self.redis = redis
        self.prefix = prefix

    def _key(self, name: str) -> str:
        return f"{self.prefix}:{name}"

    async def get(self, key: str) -> Optional[Any]:
        data = await self.redis.get(self._key(key))
        if data:
            return json.loads(data)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = REDIS_TTL
    ) -> None:
        await self.redis.setex(
            self._key(key),
            ttl,
            json.dumps(value, default=str)
        )

    async def delete(self, key: str) -> None:
        await self.redis.delete(self._key(key))

    async def exists(self, key: str) -> bool:
        return await self.redis.exists(self._key(key)) > 0

    async def remember(
        self,
        key: str,
        callback: Callable[[], T],
        options: dict[str, bool] | None = None,
    ) -> T:
        cached = await self.get(key)
        cache_data = options.get("cache_data", False)
        overwrite_cache = options.get("overwrite_cache", False)
        bypass_cache = options.get("bypass_cache", False)
        cache_ttl = options.get("cache_ttl", REDIS_TTL)

        data = {}
        data["cache_ttl"] = cache_ttl

        if cached is not None and bypass_cache is False and overwrite_cache is False:
            data["result"] = cached
            data["from_cache"] = True
            data["cache_generated"] = await self.get("{}_generated".format(key))
            data["cache_generated"] = datetime.strptime(data["cache_generated"], '%Y-%m-%d %H:%M:%S.%f')
        else:
            result = await callback() if inspect.iscoroutinefunction(callback) else callback()
            data["result"] = result
            data["from_cache"] = False
            if cache_data is True or overwrite_cache is True:
                data["cache_generated"] = datetime.now()
                await self.set(key, result, cache_ttl)
                await self.set("{}_generated".format(key), data["cache_generated"], cache_ttl)

        data["cache_expiration"] = data["cache_generated"] + timedelta(0, data["cache_ttl"])
        return data

    async def flush_pattern(self, pattern: str) -> int:
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor,
                match=self._key(pattern),
                count=100
            )
            if keys:
                deleted += await self.redis.delete(*keys)
            if cursor == 0:
                break
        return deleted
